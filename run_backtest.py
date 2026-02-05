
import pandas as pd
import numpy as np
import os
import joblib
import config
import argparse
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel
from core.backtesting import Backtester
from configs import banking as config_banking

def get_vectorized_macro_gate(df, thresholds):
    """
    Tarihsel veri üzerinde vektörel Macro Gate maskesi oluşturur.
    True: Blocked, False: Open
    """
    mask = pd.Series(False, index=df.index)
    if 'VIX' in df.columns:
        mask |= (df['VIX'].shift(1) > thresholds['VIX_HIGH'])
    if 'USDTRY' in df.columns:
        usd_change = df['USDTRY'].pct_change(5).shift(1)
        mask |= (usd_change > thresholds['USDTRY_CHANGE_5D'])
    if 'SP500' in df.columns:
        sp_mom = df['SP500'].pct_change(5).shift(1)
        mask |= (sp_mom < thresholds['SP500_MOMENTUM'])
    return mask.fillna(False)

def main():
    if not os.path.exists("reports"):
        os.makedirs("reports")


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
             from models.ranking_model_catboost import CatBoostRankingModel
             ranker = CatBoostRankingModel.load("models/saved/global_ranker_catboost.cbm", config_banking)
        elif args.model == 'ensemble':
             from models.ranking_model_catboost import CatBoostRankingModel
             from models.ensemble_model import EnsembleModel
             lgbm = RankingModel.load("models/saved/global_ranker.pkl", config_banking)
             cat = CatBoostRankingModel.load("models/saved/global_ranker_catboost.cbm", config_banking)
             
             # Load best weights if exist, else default
             weights = {'lgbm': 0.5, 'catboost': 0.5}
             if os.path.exists("models/saved/ensemble_weights.joblib"):
                 weights = joblib.load("models/saved/ensemble_weights.joblib")
                 print(f"✅ Ensemble weights loaded: {weights}")
             
             ranker = EnsembleModel(lgbm, cat, weights)
             
        if ranker is None: raise FileNotFoundError
        print(f"✅ {args.model.upper()} Ranking Model loaded.")
    except Exception as e:
        print(f"❌ {args.model.upper()} Model NOT found or error: {e}")
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
            gate_mask = get_vectorized_macro_gate(raw, config.MACRO_GATE_THRESHOLDS)
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

    # 3. Predict Scores (Vectorized)
    print("Predicting Ranks...")
    full_df = pd.concat(all_data.values())
    
    # Save original index to restore after predict
    # Predict expects columns, doesn't care about index structure
    # But we need to assign scores back.
    
    scores = ranker.predict(full_df)
    full_df['Score'] = scores
    
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
    weight_strategy = getattr(config, 'WEIGHTING_STRATEGY', 'RankWeighted')
    
    print(f"Portfolio Size: {port_size}, Weighting: {weight_strategy}")
    
    # weights_pivot: Index=Date, Cols=Ticker, Values=Weight
    weights_pivot = pd.DataFrame(0.0, index=ranks_pivot.index, columns=ranks_pivot.columns)
    
    # 1. Identify Top N mask
    top_n_mask = (ranks_pivot <= port_size)
    
    # NEW: Momentum Filter (Top N içinde olsa bile ivmesi negatif olanı alma)
    if getattr(config, 'ENABLE_MOMENTUM_FILTER', False):
        # Close üzerinden 5 günlük momentum (hızlı momentum)
        close_pivot = full_df_reset.pivot(index='Date', columns='Ticker', values='Close')
        mom_5 = close_pivot.pct_change(5)
        mom_mask = (mom_5 > 0).fillna(True)
        top_n_mask = top_n_mask & mom_mask
    
    if weight_strategy == 'Equal' or weight_strategy == 'EqualWeight':
        # Equal weighting among top N
        # weight = 1/N
        weights_pivot[top_n_mask] = 1.0 / port_size
        
    elif weight_strategy == 'RankWeighted':
        # Decreasing weights for top ranks
        # Example for Top 5: [0.35, 0.25, 0.20, 0.12, 0.08]
        # Generic rank weighting: W = (N - rank + 1) / sum(1..N)
        rank_sum = sum(range(1, port_size + 1))
        for r in range(1, port_size + 1):
            weight_val = (port_size - r + 1) / rank_sum
            weights_pivot[ranks_pivot == float(r)] = weight_val
            
    elif weight_strategy == 'RiskParity':
        # Weight inversely proportional to volatility
        # We need historical volatility (Volatility_20)
        # Pivot volatility first
        vol_pivot = full_df_reset.pivot(index='Date', columns='Ticker', values='Volatility_20').fillna(0.5)
        
        # Calculate inverse volatility for Top N
        inv_vol = 1.0 / (vol_pivot + 1e-9)
        inv_vol_top = inv_vol.where(top_n_mask, 0.0)
        
        # Normalize so each row sums to 1.0
        row_sum = inv_vol_top.sum(axis=1)
        weights_pivot = inv_vol_top.div(row_sum, axis=0).fillna(0.0)
    
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
