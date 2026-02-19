
import os
import sys
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import joblib
import numpy as np
import pandas as pd
import torch

import config
from configs import banking as config_banking
from core.backtesting import Backtester
from core.macro_gate import vectorized_macro_gate
from models.ranking_model import RankingModel
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer

def main():
    if not os.path.exists("reports"):
        os.makedirs("reports")

    print(f"✅ Config yüklendi")
    
    # YENİ: Rejim sistemi kontrolü
    print(f"🔍 Adaptive Regime: {getattr(config, 'USE_ADAPTIVE_REGIME', 'Unknown')}")
    print(f"📊 Regime Thresholds: {getattr(config, 'REGIME_THRESHOLDS', {})}")
    print(f"⚙️ Regime Actions: {getattr(config, 'REGIME_ACTIONS', {})}")
    
    if getattr(config, 'USE_ADAPTIVE_REGIME', False):
        print("✅ Regime-based risk management AKTİF")
    else:
        print("⚠️ UYARI: Regime detection devre dışı!")



    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='oos', choices=['oos', 'is'])
    parser.add_argument('--model', type=str, default='lightgbm', choices=['lightgbm', 'catboost', 'ensemble'], help='Model type to use')
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"BIST30 AI TRADER - DAILY RANKING BACKTEST ({args.mode.upper()})")
    print(f"Model: {args.model.upper()}")
    print(f"{'='*50}")

    # 1. Load Ranking Model
    try:
        ranker = None
        if args.model == 'lightgbm':
             ranker = RankingModel.load("models/saved/global_ranker.pkl", config_banking)
        elif args.model == 'catboost':
             # Deprecated or optional
             from models.ranking_model_catboost import CatBoostRankingModel
             ranker = CatBoostRankingModel.load("models/saved/global_ranker_catboost.cbm", config_banking)
        elif args.model == 'ensemble':
             from models.ensemble_model import HybridEnsemble
             # Load Hybrid Ensemble
             ranker = HybridEnsemble()
             
             # Fallback paths - In production these should be in config
             lgbm_path = "models/saved/global_ranker.pkl"
             tft_path = "models/saved/tft_model.pth"
             tft_config_path = "models/saved/tft_config.joblib"
             catboost_path = "models/saved/global_ranker_catboost.cbm"
             
             # Load TFT Config if exists
             tft_config = None
             if os.path.exists(tft_config_path):
                 tft_config = joblib.load(tft_config_path)
             else:
                 # Fallback: Use global config module
                 tft_config = config

             # Load models
             ranker.load_models(lgbm_path, tft_path, tft_config=tft_config, catboost_path=catboost_path)
             
             print(f"✅ Hybrid Ensemble (LightGBM + TFT + CatBoost) loaded.")
             
        if ranker is None: raise FileNotFoundError
        print(f"✅ {args.model.upper()} Ranking Model loaded.")
    except Exception as e:
        print(f"❌ {args.model.upper()} Model NOT found or error: {e}")
        # traceback for debugging
        import traceback
        traceback.print_exc()
        return

    # 2. Load & Process All Data
    # 2. Load & Process All Data
    tickers = config.TICKERS
    all_data = {}
    gate_masks = {}
    
    # Benchmark Data (XU100)
    loader = DataLoader(start_date=config.START_DATE)
    xu100_data = loader.fetch_stock_data("XU100.IS")
    # Clean and process benchmark
    if xu100_data is not None:
         # Resample if needed inside DataLoader but simpler here:
         # Just get Close and pct_change
         if isinstance(xu100_data.columns, pd.MultiIndex):
             xu100_data.columns = xu100_data.columns.droplevel(1)
         
         xu100_rets = xu100_data['Close'].pct_change().dropna()
         if args.mode == 'oos' and config.TEST_START_DATE:
             xu100_rets = xu100_rets[xu100_rets.index >= config.TEST_START_DATE]
         elif args.mode == 'is' and config.TEST_START_DATE:
             xu100_rets = xu100_rets[xu100_rets.index < config.TEST_START_DATE]
    else:
        xu100_rets = None
    print(f"Loading data for {len(tickers)} tickers...")
    
    for t in tickers:
        raw = loader.get_combined_data(t)
        if raw is None or len(raw) < 100: continue
        
        # Macro Gate Mask (Before dropping cols)
        if getattr(config, 'ENABLE_MACRO_GATE', True):
            gate_mask = vectorized_macro_gate(raw, getattr(config, 'MACRO_GATE_THRESHOLDS', None))
        else:
            gate_mask = pd.Series(False, index=raw.index)
        gate_masks[t] = gate_mask
        
        # Feature Engineering
        fe = FeatureEngineer(raw)
        df = fe.process_all(t)
        
        # Align Gate (Date index match)
        gate_mask = gate_mask.reindex(df.index).fillna(False)
        # Store Gate in DF temporarily for matrix pivot
        df['GATE_BLOCKED'] = gate_mask
        
        df['Ticker'] = t
        
        # Filter Date based on Mode
        if args.mode == 'oos' and config.TEST_START_DATE:
            df = df[df.index >= config.TEST_START_DATE]
        elif args.mode == 'is' and config.TEST_START_DATE:
            df = df[df.index < config.TEST_START_DATE]
            
        if not df.empty:
            all_data[t] = df

    if not all_data:
        print("No data available for backtest.")
        return

    from models.regime_detector import RegimeDetector
    regime_detector = RegimeDetector(config.__dict__) # Pass config dict

    # --- REGIME DETECTION PHASE ---
    print("Detecting Market Regimes...")
    
    # 1. Prepare Market Data (XU100 + Macro)
    # We need a dense dataframe with SMA, RSI, VIX, USDTRY
    if xu100_data is not None:
         # Feature Engineering on Benchmark to get SMAs, RSI, ATR
         fe_bench = FeatureEngineer(xu100_data)
         # Using a dummy ticker 'XU100' or similar
         market_df = fe_bench.process_all('XU100')
         
         # Ensure Macro data is present (VIX, USDTRY)
         # FeatureEngineer should have added them via MacroMixin
         # Key missing might be 'USDTRY' vs 'usdtry' casing. 
         # RegimeDetector looks for 'USDTRY', 'VIX' (upper).
         # Let's standardize columns if needed uppercasing
         market_df.columns = [c.upper() if c.lower() in ['vix', 'usdtry'] else c for c in market_df.columns]
    else:
         print("⚠️ Benchmark data missing! Defaulting to NORMAL regime.")
         market_df = pd.DataFrame()

    # 2. Daily Regime Loop
    daily_regimes = {}
    
    if not market_df.empty:
        # Sort by date
        market_df = market_df.sort_index()
        
        # Reset detector history
        regime_detector.regime_history = []
        
        # Optimize: Iterate only necessary rows or full history? 
        # Need full history for stability logic
        for date, row in market_df.iterrows():
            # Pass singular row DataFrame
            # detect_regime uses .iloc[-1]
            # row is Series, to_frame().T makes is DF
            current_slice = row.to_frame().T
            regime = regime_detector.detect_regime(current_slice)
            daily_regimes[date] = regime
    else:
        # Fallback
        daily_regimes = {d: 'NORMAL' for d in pd.date_range(start=config.START_DATE, end=pd.Timestamp.today())}

    print(f"Regime Detection Complete. Sample: {list(daily_regimes.items())[-5:]}")


    # 3. Predict Scores (Regime-Conditional)
    print("Predicting Ranks (Dynamic Regime-Based)...")
    full_df = pd.concat(all_data.values())
    
    # Map Regime to full_df
    # Align dates
    # full_df index is Date (or MultiIndex?). Usually Date.
    # Let's ensure index is datetime
    if not isinstance(full_df.index, pd.DatetimeIndex):
         full_df.index = pd.to_datetime(full_df.index)
         
    # Create Regime Series aligned with full_df
    # We can use map on index
    full_df['Regime'] = full_df.index.map(daily_regimes).fillna('NORMAL')
    
    # Predict by Group
    scores_series = pd.Series(index=full_df.index, dtype=float)
    
    # Group by unique Regime to avoid calling predict 1000 times
    # But predict needs CHUNKS of data? No, predict works on DataFrame rows.
    # Note: TFT might need sequence. HybridEnsemble.predict handles TFT internally.
    # Logic: 
    #   HybridEnsemble.predict -> calls TFT.predict -> needs sequence?
    #   If TFT is used, it usually needs the full time series context for that ticker.
    #   Splitting by regime breaks the time series continuity for TFT!
    
    # CRITICAL FIX: We cannot split by regime if TFT uses past windows.
    # TFT predicts independently? 
    # No, TFT needs "encoder_length" history.
    
    # BETTER APPROACH:
    # 1. Run prediction for ALL data (as before).
    # 2. But we need to vary weights.
    # HybridEnsemble.predict takes ONE regime.
    # We should modify HybridEnsemble to accept a LIST/SERIES of regimes?
    # Or, we calculate scores for ALL scenarios and blend them?
    
    # Strategy C: Calculate scores for ALL models individually, then blend manually here.
    # This avoids breaking TFT context.
    
    # Let's look at HybridEnsemble again.
    # it predicts LGBM, TFT, CatBoost separately.
    # Then it blends.
    # We can perform the blending HERE in run_backtest.py instead of inside predict?
    # Or add a method `predict_vectorized_regime` to HybridEnsemble.
    
    # Let's stick to the plan: Modify run_backtest to do the blending locally.
    # It's safer than modifying the model class again and potentially breaking it.
    
    # 3.1 Get Individual Model Predictions
    # We need access to individual models inside ranker.
    
    # 1. LGBM
    lgbm_model = None
    if args.model == 'lightgbm':
        lgbm_model = ranker
    elif args.model == 'ensemble' and hasattr(ranker, 'lgbm'):
        lgbm_model = ranker.lgbm
        
    lgbm_pred = None
    if lgbm_model:
        lgbm_feature_names = lgbm_model.feature_names if hasattr(lgbm_model, 'feature_names') else []
        if lgbm_feature_names:
            missing_cols = [c for c in lgbm_feature_names if c not in full_df.columns]
            if missing_cols:
                print(f"⚠️ LGBM: {len(missing_cols)} eksik sütun 0 ile dolduruldu: {missing_cols[:5]}...")
                for col in missing_cols:
                    full_df[col] = 0.0
        lgbm_pred = lgbm_model.predict(full_df)
    
    # 2. TFT
    tft_model = None
    if args.model == 'ensemble' and hasattr(ranker, 'tft'):
        tft_model = ranker.tft
        
    tft_pred = None
    if tft_model:
        try:
             df_tft = full_df.copy()
             
             # Multi-index'i column'lara taşı
             if df_tft.index.names and any(n in (df_tft.index.names or []) for n in ['Date', 'Ticker']):
                 df_tft = df_tft.reset_index()
             
             df_tft.columns = df_tft.columns.str.replace(".", "_", regex=False)
             
             # TFT için time_idx oluştur
             if 'time_idx' not in df_tft.columns:
                 if 'Date' in df_tft.columns:
                     dates = df_tft['Date']
                 else:
                     dates = None
                 
                 if dates is not None:
                     unique_dates = pd.Series(dates.unique()).sort_values(ignore_index=True)
                     date_map = {d: i for i, d in enumerate(unique_dates)}
                     df_tft['time_idx'] = dates.map(date_map).values
                     print(f"  ℹ️ TFT: time_idx oluşturuldu ({len(unique_dates)} unique date)")
             
             # Ticker sütunu kontrol et
             if 'Ticker' not in df_tft.columns:
                 df_tft['Ticker'] = 'DUMMY'
             
             # Sector sütunu oluştur
             if 'Sector' not in df_tft.columns and 'Ticker' in df_tft.columns:
                 df_tft['Sector'] = df_tft['Ticker'].apply(config.get_sector)
             
             # Index unique olmalı
             df_tft = df_tft.reset_index(drop=True)
             
             tft_out = tft_model.predict(df_tft, backtest=True)
             if isinstance(tft_out, torch.Tensor):
                 tft_pred = tft_out.cpu().numpy().flatten()
             else:
                 tft_pred = tft_out.flatten()
        except Exception as e:
             print(f"TFT Predict Error: {e}")
    
    # 3. CatBoost
    catboost_model = None
    if args.model == 'catboost':
        catboost_model = ranker
    elif args.model == 'ensemble' and hasattr(ranker, 'catboost'):
        catboost_model = ranker.catboost
        
    catboost_pred = None
    if catboost_model:
        try:
            # Use appropriate feature name attribute
            f_names = catboost_model.feature_names if hasattr(catboost_model, 'feature_names') else []
            if not f_names and hasattr(catboost_model, 'feature_names_'):
                f_names = catboost_model.feature_names_
            
            catboost_pred = catboost_model.predict(full_df[f_names])
        except Exception as e:
            print(f"CatBoost Predict Error: {e}")

    # 3.2 Align Lengths (Crop to min)
    valid_preds = [p for p in [lgbm_pred, tft_pred, catboost_pred] if p is not None]
    if not valid_preds:
        print("❌ No valid predictions generated by any model!")
        return
        
    lens = [len(p) for p in valid_preds]
    min_len = min(lens)
    
    if lgbm_pred is not None: lgbm_pred = lgbm_pred[-min_len:]
    if tft_pred is not None: tft_pred = tft_pred[-min_len:]
    if catboost_pred is not None: catboost_pred = catboost_pred[-min_len:]
    
    # Align DataFrame and Regimes to min_len (usually end of dataset)
    # Be careful with index alignment!
    # full_df might be larger than preds if TFT clips start.
    sliced_df = full_df.iloc[-min_len:].copy()
    sliced_regimes = sliced_df['Regime']
    
    # 3.3 Vectorized Blending
    from scipy.stats import rankdata
    
    # Normalize Ranks
    norm_rank_lgbm = rankdata(lgbm_pred) / len(lgbm_pred)
    norm_rank_tft = rankdata(tft_pred) / len(tft_pred) if tft_pred is not None else 0
    norm_rank_cat = rankdata(catboost_pred) / len(catboost_pred) if catboost_pred is not None else 0
    
    # Apply Weights Row-by-Row
    final_scores = np.zeros(min_len)
    
    # Get Weights Dict
    regime_weights = config.ENSEMBLE_REGIME_WEIGHTS
    
    # Iterate regimes (Groupby optimized)
    # Group indices by regime
    # sliced_regimes is a Series.
    unique_regimes = sliced_regimes.unique()
    
    for r in unique_regimes:
        mask = (sliced_regimes == r).values
        weights = regime_weights.get(r, regime_weights['NORMAL'])
        
        # Calculate score for this chunk
        chunk_score = weights.get('lgbm', 0.4) * norm_rank_lgbm[mask]
        if tft_pred is not None:
             chunk_score += weights.get('tft', 0.3) * norm_rank_tft[mask]
        if catboost_pred is not None:
             chunk_score += weights.get('catboost', 0.3) * norm_rank_cat[mask]
             
        final_scores[mask] = chunk_score
        
    full_df = sliced_df
    full_df['Score'] = final_scores
    
    # 4. Allocation (Top N)
    print("Allocating Portfolio (Top 5)...")
    
    # Pivot Scores: Index=Date, Cols=Ticker, Values=Score
    # reset_index needed if Date is index
    full_df_reset = full_df.reset_index()
    scores_pivot = full_df_reset.pivot(index='Date', columns='Ticker', values='Score')
    gate_pivot = full_df_reset.pivot(index='Date', columns='Ticker', values='GATE_BLOCKED').fillna(False)
    
    # EXPLICIT CAST to boolean to avoid TypeError
    gate_pivot = gate_pivot.astype(bool)
    
    # Apply Gate: If blocked, set score to -infinity so it's ranked last
    # Use .mask() for safer operation
    scores_pivot = scores_pivot.mask(gate_pivot, -9999.0)
    
    # Rank: Descending (Higher score = Top rank 1)
    # method='first' handles ties
    ranks_pivot = scores_pivot.rank(axis=1, ascending=False, method='first')
    
    # --- Dynamic Allocation (Top N & Weighting Strategy) ---
    port_size = getattr(config, 'PORTFOLIO_SIZE', 5)
    weight_strategy = getattr(config, 'WEIGHTING_STRATEGY', 'RiskParity')
    max_sector_pos = getattr(config, 'MAX_SECTOR_POSITIONS', 2)
    
    print(f"Portfolio Size: {port_size}, Weighting: {weight_strategy}, Max Sector Pos: {max_sector_pos}")
    
    # weights_pivot: Index=Date, Cols=Ticker, Values=Weight
    weights_pivot = pd.DataFrame(0.0, index=ranks_pivot.index, columns=ranks_pivot.columns)
    
    # 1. Identify Top N mask WITH SECTOR FILTER
    # Vectorized approach is hard for sector limits, using loop for correctness
    top_n_mask = pd.DataFrame(False, index=ranks_pivot.index, columns=ranks_pivot.columns)
    
    # Pre-compute sectors for speed
    ticker_sectors = {t: config.get_sector(t) for t in ranks_pivot.columns}
    
    print("Applying Sector Filter & Momentum...")
    
    # Calculate Momentum Mask outside loop
    mom_mask = None
    if getattr(config, 'ENABLE_MOMENTUM_FILTER', False):
        close_pivot = full_df_reset.pivot(index='Date', columns='Ticker', values='Close')
        # Simple 5-day return > 0
        mom_5 = close_pivot.pct_change(5)
        mom_mask = (mom_5 > 0).fillna(True) # Fillna True to not block start
        
    for date, row in ranks_pivot.iterrows():
        # row: Index=Ticker, Value=Rank. Lower is better.
        # Filter: Rank <= 30 (just to reduce sort size), valid ranks only
        valid_candidates = row.dropna().sort_values()
        
        selected_tickers = []
        sector_counts = {}
        
        for ticker, rank in valid_candidates.items():
            if len(selected_tickers) >= port_size:
                break
                
            # Momentum Check
            if mom_mask is not None:
                # If momentum is negative, skip this ticker
                # We need to access mom_mask for this date and ticker
                # Date might be Timestamp, map correctly
                try:
                    if not mom_mask.loc[date, ticker]:
                        continue
                except KeyError:
                    pass # Date mismatch or something, skip check
            
            # Sector Check
            sector = ticker_sectors.get(ticker, 'Other')
            current_count = sector_counts.get(sector, 0)
            
            if current_count < max_sector_pos:
                selected_tickers.append(ticker)
                sector_counts[sector] = current_count + 1
                
        # Mark selected
        if selected_tickers:
           top_n_mask.loc[date, selected_tickers] = True

    # 2. Assign Weights based on Top N Mask
    if weight_strategy == 'Equal' or weight_strategy == 'EqualWeight':
        # weight = 1/N
        weights_pivot[top_n_mask] = 1.0 / port_size
        
        # HEAD OF QUANT: Weight Smoothing (EWMA)
        # Prevent huge turnover on regime switch.
        # span=3 means ~2 day half-life. 
        print("Applying EWMA Smoothing (Span=3) to weights...")
        weights_pivot = weights_pivot.ewm(span=3, adjust=False).mean()
        
    elif weight_strategy == 'RankWeighted':
        # ... (Existing Rank logic needs to handle specific selected tickers, 
        # but since we selected top N, we can just rank the selected ones again or use their original rank?
        # Simpler: Assign weights to the Trues in top_n_mask based on their relative rank order)
        
        # Iterate again? Efficiency?
        # Or just: params calculated daily. 
        # Let's simplify RankWeighted to be handled via loop or masking
        # For now, let's keep it compatible with existing structure but valid only for Equal/RiskParity
        # RankWeighted logic in original code assumes ranks 1..N matches. 
        # Since we filtered, original ranks might be 1, 3, 5 (skipped 2, 4 due to sector).
        # We need to re-rank the SELECTED ones 1..N
        pass # Handle below
        
    elif weight_strategy == 'RiskParity':
        # Weight inversely proportional to volatility
        # We need historical volatility (Volatility_20)
        # Pivot volatility first
        vol_pivot = full_df_reset.pivot(index='Date', columns='Ticker', values='Volatility_20').fillna(0.02) # Default 2% daily vol
        
        # Calculate inverse volatility for Top N
        inv_vol = 1.0 / (vol_pivot + 1e-9)
        inv_vol_top = inv_vol.where(top_n_mask, 0.0)
        
        # Normalize so each row sums to 1.0
        row_sum = inv_vol_top.sum(axis=1)
        weights_pivot = inv_vol_top.div(row_sum, axis=0).fillna(0.0)

    # Re-implement RankWeighted correctly if selected
    if weight_strategy == 'RankWeighted':
         rank_sum = sum(range(1, port_size + 1))
         # We need to assign weights to top_n_mask True items based on their Score (or original rank)
         # Using scores to re-rank locally
         scores_pivot = full_df_reset.pivot(index='Date', columns='Ticker', values='Score')
         
         # Mask non-selected
         selected_scores = scores_pivot.where(top_n_mask, np.nan)
         # Rank descending (Higher score better) -> 1..N
         local_ranks = selected_scores.rank(axis=1, ascending=False, method='first')
         
         # Weight = (N - r + 1) / sum
         # rank_sum calculated above
         # Vectorized assignment
         weights_val = (port_size - local_ranks + 1) / rank_sum
         weights_pivot = weights_val.fillna(0.0)
    
    # 4. Filter Weights based on Frequency
    rebalance_freq = getattr(config, 'REBALANCE_FREQUENCY', 'D')
    if rebalance_freq == 'W':
        # Hafta başı (Pazartesi veya haftanın ilk günü) tespiti
        # Sadece haftanın ilk günündeki ağırlıkları koru, diğer günleri NaN yapıp ffill et
        is_week_start = weights_pivot.index.to_series().diff().dt.days >= 3 # Hafta sonu sonrası ilk gün
        # Daha güvenli yol: dayofweek < previous dayofweek
        is_week_start = (weights_pivot.index.dayofweek < pd.Series(weights_pivot.index.dayofweek).shift(1).values) | (pd.Series(weights_pivot.index.dayofweek).shift(1).isna().values)
        
        # Sadece hafta başında ağırlıkları güncelle, diğer günlerde mevcut ağırlığı koru
        weights_pivot_weekly = weights_pivot.copy()
        weights_pivot_weekly.loc[~is_week_start] = np.nan
        weights_pivot = weights_pivot_weekly.ffill().fillna(0)
        print(f"Weekly Rebalancing applied. Target weights fixed throughout the week.")

    # 5. Run Backtests
    all_metrics = []
    all_daily_returns = []
    
    print(f"\nExecuting Trades (Top {port_size} {weight_strategy} Portfolio)...")
    for t in all_data.keys():
        if t not in weights_pivot.columns: continue
        
        df = all_data[t]
        ticker_weights = weights_pivot[t].reindex(df.index).fillna(0)
        
        bt = Backtester(df, initial_capital=10000) 
        bt.run_backtest(ticker_weights)
        
        metrics = bt.calculate_metrics()
        metrics['Ticker'] = t
        all_metrics.append(metrics)
        
        # Save daily rets for agg
        d_rets = bt.results['Equity'].pct_change().fillna(0)
        d_rets.name = t
        all_daily_returns.append(d_rets)

    # 6. Aggregation
    if all_metrics:
        df_res = pd.DataFrame(all_metrics)
        cols = ['Ticker', 'Total Return', 'Sharpe Ratio', 'Max Drawdown', 'Win Rate', 'Num Trades']
        print("\n" + "="*60)
        print(df_res[cols].to_string(index=False))
        print("="*60)
        df_res.to_csv("reports/final_backtest_results.csv", index=False)
        
        if all_daily_returns:
            print("Aggregating Daily Returns...")
            concat_rets = pd.concat(all_daily_returns, axis=1).fillna(0)
            concat_rets.to_csv("reports/daily_returns_concatenated.csv")

            # Portfolio daily ret = weighted sum of per-ticker equity returns
            port_daily_ret = concat_rets.sum(axis=1)
            port_cum_ret   = (1 + port_daily_ret).cumprod()
            total_ret      = port_cum_ret.iloc[-1] - 1

            # FIX-A2: CAGR + risk_free = 0  (önceki 0.05 sabit Türkiye için meaningless)
            n_port_days  = max(len(port_daily_ret), 1)
            port_cagr    = (1 + total_ret) ** (252.0 / n_port_days) - 1 if total_ret > -1 else 0.0
            port_ann_vol = port_daily_ret.std() * np.sqrt(252)
            sharpe       = port_cagr / port_ann_vol if port_ann_vol > 0 else 0

            # Portfolio Max Drawdown & Calmar
            port_dd      = (port_cum_ret - port_cum_ret.cummax()) / port_cum_ret.cummax()
            port_max_dd  = port_dd.min()
            port_calmar  = port_cagr / abs(port_max_dd) if port_max_dd != 0 else 0

            print(f"\nPORTFOLIO PERFORMANCE:")
            print(f"  Total Return   : {total_ret:.2%}")
            print(f"  CAGR           : {port_cagr:.2%}")
            print(f"  Sharpe Ratio   : {sharpe:.2f}")
            print(f"  Max Drawdown   : {port_max_dd:.2%}")
            print(f"  Calmar Ratio   : {port_calmar:.2f}")

            # ── Per-ticker özet (Top 5 / Bottom 3) ──────────────────
            print(f"\n  {'─'*52}")
            print(f"  Per-Ticker Özet  (tam CSV: reports/final_backtest_results.csv)")
            print(f"  {'─'*52}")
            summary_cols = ['Ticker', 'Total Return', 'CAGR', 'Sharpe Ratio', 'Max Drawdown']
            avail_cols   = [c for c in summary_cols if c in df_res.columns]
            print("  ▲ Top 5:")
            print(df_res.nlargest(5,  'Total Return')[avail_cols].to_string(index=False))
            print("  ▼ Bottom 3:")
            print(df_res.nsmallest(3, 'Total Return')[avail_cols].to_string(index=False))

            # ── Alpha / Beta vs XU100 ──────────────────────────────
            if xu100_rets is not None:
                common_idx = port_daily_ret.index.intersection(xu100_rets.index)
                if len(common_idx) > 100:
                    y = port_daily_ret.loc[common_idx]
                    x = xu100_rets.loc[common_idx]

                    covariance = np.cov(y, x)[0][1]
                    variance   = np.var(x)
                    beta       = covariance / variance

                    # FIX-A2: benchmark de CAGR kullana
                    bench_total   = (1 + x).prod() - 1
                    n_bench       = max(len(x), 1)
                    ann_ret_bench = (1 + bench_total) ** (252.0 / n_bench) - 1 if bench_total > -1 else 0.0

                    # Jensen Alpha: R_p - (R_f + β·(R_m - R_f))  →  R_f = 0  →  R_p - β·R_m
                    alpha_jensen  = port_cagr - (beta * ann_ret_bench)
                    alpha_excess  = port_cagr - ann_ret_bench

                    print(f"\n  Benchmark (XU100)  : {bench_total:.2%}")
                    print(f"  Benchmark CAGR     : {ann_ret_bench:.2%}")
                    print(f"  Beta               : {beta:.2f}")
                    print(f"  Alpha (Excess)     : {alpha_excess:.2%}")
                    print(f"  Alpha (Jensen)     : {alpha_jensen:.2%}")

if __name__ == "__main__":
    main()
