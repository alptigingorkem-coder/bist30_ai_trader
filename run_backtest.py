
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
    parser.add_argument('--model', type=str, default='lightgbm', choices=['lightgbm', 'catboost'], help='Model type to use')
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
             
        if ranker is None: raise FileNotFoundError
        print(f"✅ {args.model.upper()} Ranking Model loaded.")
    except:
        print(f"❌ {args.model.upper()} Model NOT found. Run train_models.py (LightGBM) or train_catboost.py (CatBoost) first.")
        return

    # 2. Load & Process All Data
    tickers = config.TICKERS
    all_data = {}
    gate_masks = {}
    
    loader = DataLoader(start_date=config.START_DATE)
    print(f"Loading data for {len(tickers)} tickers...")
    
    for t in tickers:
        raw = loader.get_combined_data(t)
        if raw is None or len(raw) < 100: continue
        
        # Macro Gate Mask (Before dropping cols)
        gate_mask = get_vectorized_macro_gate(raw, config.MACRO_GATE_THRESHOLDS)
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
    
    # Select Top 5
    top_n = 5
    signals_pivot = (ranks_pivot <= top_n).astype(int)
    
    # 5. Run Backtests
    all_metrics = []
    all_daily_returns = []
    
    print("\nExecuting Trades...")
    for t in all_data.keys():
        if t not in signals_pivot.columns: continue
        
        df = all_data[t]
        ticker_signals = signals_pivot[t].reindex(df.index).fillna(0)
        
        # Backtester expects weights/signals
        # Signal 1 = Buy/Hold, 0 = Sell
        # Backtester.run_backtest handles signal changes
        
        # Use our existing Backtester logic
        # Note: Backtester automatically applies Stop Loss / Trailing Stop inside.
        # If Signal goes 1->0, check_exit_conditions logic in backtester might override?
        # Actually standard Backtester usually checks signal for entry, and check_exit_conditions for exit.
        # But if signal becomes 0, we must force exit.
        # Let's check Backtesting logic assumption.
        # Assuming run_backtest(signals) handles "Signal=0 means Exit".
        
        bt = Backtester(df, initial_capital=10000 / top_n) # Equal weight initial
        bt.run_backtest(ticker_signals)
        
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
            
            # Portfolio Level Stats
            # Assuming equal allocation rebalancing daily (simplified)
            # Actually our PnL simulation above is "Separate Accounts".
            # Total Portfolio Return = Sum of Daily PnL / Total Initial Capital
            
            port_daily_ret = concat_rets.mean(axis=1) # Avg return of components
            port_cum_ret = (1 + port_daily_ret).cumprod()
            
            total_ret = port_cum_ret.iloc[-1] - 1
            sharpe = port_daily_ret.mean() / port_daily_ret.std() * (252**0.5)
            
            print(f"\nPORTFOLIO PERFORMANCE:")
            print(f"Total Return: {total_ret:.2%}")
            print(f"Sharpe Ratio: {sharpe:.2f}")

if __name__ == "__main__":
    main()
