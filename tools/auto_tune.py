import optuna
import pandas as pd
import numpy as np
import os
import sys
import argparse
import joblib
from datetime import datetime, timedelta

# Add project root to path BEFORE importing project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel
from configs import banking as config_banking
from core.backtesting import Backtester

# Suppress logs
optuna.logging.set_verbosity(optuna.logging.WARNING)

def get_vectorized_macro_gate(df, vix_thresh, usd_thresh):
    mask = pd.Series(False, index=df.index)
    if 'VIX' in df.columns:
        mask |= (df['VIX'].shift(1) > vix_thresh)
    if 'USDTRY' in df.columns:
        usd_change = df['USDTRY'].pct_change(5).shift(1)
        # Debug
        # print(f"DEBUG: USD Thresh: {usd_thresh} (Type: {type(usd_thresh)})")
        # print(f"DEBUG: USD Change Head: {usd_change.head()}")
        
        # Safe comparison
        if usd_thresh is not None:
             mask |= (usd_change.fillna(0) > usd_thresh)
    return mask.fillna(False)

def run_strategy_simulation(params, data_dict, ranker_predictions, full_macro_df):
    """
    Runs a vector-ish backtest using the given risk parameters AND macro thresholds.
    """
    # Override Config locally for Simulation
    original_sl = config.ATR_STOP_LOSS_MULTIPLIER
    original_ts = config.ATR_TRAILING_STOP_MULTIPLIER
    
    config.ATR_STOP_LOSS_MULTIPLIER = params['stop_loss']
    config.ATR_TRAILING_STOP_MULTIPLIER = params['trailing_stop']
    
    # 1. Macro Gate Check (Dynamic)
    # We need to construct the gate mask based on NEW params
    # full_macro_df must contain VIX, USDTRY (aligned with Dates)
    
    gate_mask = get_vectorized_macro_gate(full_macro_df, params['vix_thresh'], params['usdtry_thresh'])
    
    # 2. Generate Signals
    full_df = ranker_predictions.copy()
    
    # Align Gate with Predictions
    # Assume full_df has 'Date' column
    # Map gate_mask (Index=Date) to full_df (Column=Date)
    
    # Pivot Scores first (Date x Ticker)
    pivot_score = full_df.pivot(index='Date', columns='Ticker', values='Score')
    
    # Reindex Gate to match Pivot Index
    gate_aligned = gate_mask.reindex(pivot_score.index).fillna(False)
    
    # Apply Gate (Block all tickers on blocked days)
    # If gate is True, set score to -9999
    # Broadcast gate_aligned (Series) to DataFrame columns
    pivot_score = pivot_score.apply(lambda col: col.mask(gate_aligned, -9999.0))
    
    # Rank
    ranks = pivot_score.rank(axis=1, ascending=False)
    
    # Select Top 5
    top_n = 5
    signals = (ranks <= top_n).astype(int)
    
    # 3. Run Backtest loop
    total_sharpe = 0
    tickers_with_signals = signals.columns[signals.sum() > 0]
    daily_returns_list = []
    
    for t in tickers_with_signals:
        if t not in data_dict: continue
        
        df = data_dict[t]
        ticker_signals = signals[t].reindex(df.index).fillna(0)
        
        if ticker_signals.sum() == 0: continue
            
        bt = Backtester(df, initial_capital=10000)
        bt.run_backtest(ticker_signals)
        
        if hasattr(bt, 'results') and not bt.results.empty:
            d_ret = bt.results['Net_Strategy_Return']
            daily_returns_list.append(d_ret)
            
    # Restore Config
    config.ATR_STOP_LOSS_MULTIPLIER = original_sl
    config.ATR_TRAILING_STOP_MULTIPLIER = original_ts

    if not daily_returns_list:
        return -999

    # Portfolio Sharpe
    port_daily_ret = pd.concat(daily_returns_list, axis=1).fillna(0).mean(axis=1)
    
    # Annualized Sharpe
    if port_daily_ret.std() == 0: return -999
    metric = port_daily_ret.mean() / port_daily_ret.std() * (252**0.5)
    return metric

def optimize_model_hyperparameters(trials=20):
    print(f"Auto-Tuning MODEL Hyperparameters (Trials: {trials})...")
    
    # 1. Load Data
    loader = DataLoader(start_date=config.START_DATE) # Use full history for model tuning
    tickers = config.TICKERS
    all_dfs = []
    
    print("Loading Data for Model Tuning...")
    for t in tickers:
        df = loader.get_combined_data(t)
        if df is None or len(df) < 100: continue
        fe = FeatureEngineer(df)
        df = fe.process_all(t)
        df['Ticker'] = t
        all_dfs.append(df)
        
    full_df = pd.concat(all_dfs)
    full_df.reset_index(inplace=True)
    full_df.set_index(['Date', 'Ticker'], inplace=True)
    full_df.sort_index(inplace=True)
    
    # Split Train/Valid
    dates = full_df.index.get_level_values('Date').unique()
    split_idx = int(len(dates) * 0.9) # 90/10 Split
    test_start_date = dates[split_idx]
    
    train_mask = full_df.index.get_level_values('Date') < test_start_date
    valid_mask = full_df.index.get_level_values('Date') >= test_start_date
    
    df_train = full_df[train_mask]
    df_valid = full_df[valid_mask]
    
    print(f"Train Size: {len(df_train)}, Valid Size: {len(df_valid)}")

    # 2. Objective Function
    def objective(trial):
        params = {
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
            'num_leaves': trial.suggest_int('num_leaves', 20, 150),
            'max_depth': trial.suggest_int('max_depth', -1, 15),
            'min_child_samples': trial.suggest_int('min_child_samples', 10, 100),
            'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
            'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
            'n_estimators': 300, # Fixed for speed, or tune
            'objective': 'lambdarank',
            'metric': 'ndcg',
            'verbosity': -1
        }
        
        try:
            # Train Ranker
            ranker = RankingModel(df_train, config_banking)
            model = ranker.train(valid_df=df_valid, custom_params=params)
            
            # 1. NDCG Score (Technical)
            ndcg_score = model.best_score_['valid_0']['ndcg@5']
            
            # 2. Sharpe Ratio Score (Financial)
            # Predict on Validation data
            # df_valid has (Date, Ticker) MultiIndex
            preds = model.predict(df_valid[ranker.feature_names])
            eval_df = df_valid.copy()
            eval_df['Score'] = preds
            
            # Simple simulation: Top 5 average daily return
            # Pivot scores and daily returns (Close pct_change)
            pivot_score = eval_df.pivot_table(index='Date', columns='Ticker', values='Score')
            
            # Need Close prices for returns (df_valid should have it if it comes from FeatureEngineer)
            # But eval_df might not have 'Close' if it was dropped? No, it should have it in data_dict.
            # Let's check if df_valid has 'Close' or returns.
            # If not, we can use the 'Excess_Return' which is available.
            pivot_ret = eval_df.pivot_table(index='Date', columns='Ticker', values='Excess_Return')
            
            # Rank Top 5 per day
            ranks = pivot_score.rank(axis=1, ascending=False)
            top_5_mask = (ranks <= 5)
            
            # Portfolio Return = Average of Top 5 returns
            port_ret = pivot_ret[top_5_mask].mean(axis=1).fillna(0)
            
            # Annualized Sharpe (simplified)
            if port_ret.std() == 0:
                sharpe_score = 0
            else:
                sharpe_score = (port_ret.mean() / port_ret.std()) * (252**0.5)
            
            # Combined Objective: Optimize for both
            # Normalize Sharpe to be in similar range as NDCG (roughly 0-1)
            # Sharpe of 1.0 is good, 2.0 is great.
            normalized_sharpe = max(0, min(1, sharpe_score / 2.0))
            
            final_score = 0.5 * ndcg_score + 0.5 * normalized_sharpe
            
            print(f"Trial done. NDCG: {ndcg_score:.4f}, Sharpe: {sharpe_score:.4f}, Total: {final_score:.4f}")
            return final_score

        except Exception as e:
            import traceback
            print(f"Trial Pruned due to error: {e}")
            # traceback.print_exc()
            return 0.0

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=trials)
    
    print("\n" + "="*50)
    print("MODEL OPTIMIZATION RESULTS")
    print("="*50)
    print(f"Best NDCG@5: {study.best_value:.4f}")
    print(f"Best Hyperparameters: {study.best_params}")
    return study.best_params

def optimize(days_back=180, trials=30, mode='strategy'):
    if mode == 'model':
        return optimize_model_hyperparameters(trials)

    print(f"Auto-Tuning STRATEGY Risk Params (Last {days_back} days)...")
    
    # 1. Load Data
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    loader = DataLoader(start_date=start_date)
    tickers = config.TICKERS
    
    data_dict = {}
    all_dfs = []
    
    print("Loading Data...")
    for t in tickers:
        df = loader.get_combined_data(t)
        if df is None or len(df) < 50: continue
        
        fe = FeatureEngineer(df)
        df = fe.process_all(t)
        df['Ticker'] = t
        
        data_dict[t] = df
        all_dfs.append(df)
        
    if not all_dfs:
        print("No data found.")
        return

    full_df = pd.concat(all_dfs)
    
    # 2. Pre-Calculate Model Predictions
    print("Pre-calculating Model Scores...")
    try:
        ranker = RankingModel.load("models/saved/global_ranker.pkl", config_banking)
        scores = ranker.predict(full_df)
        full_df['Score'] = scores
        
        # Keep only relevant cols for backtest to save memory
        # We need Date, Ticker, Score for Ranking
        # And OHLC + ATR for Backtester
        
        # For simulation, we pass data_dict (OHLC) and prediction DF
        prediction_df = full_df[['Ticker', 'Score']].reset_index() # Ensure Date is column
        
    except Exception as e:
        print(f"Model Error: {e}")
        return

    # 3. Macro Data Preparation for Gate
    # Need a representative DF with VIX/USDTRY (using the first one available or a dedicated macro fetch)
    # Since all DFs in data_dict have macro cols (processed by FE), we can pick any single one
    # provided it aligns with dates.
    # Ideally, we should fetch raw macro data once.
    # FE puts macro data into ticker DFs.
    
    # Pick first ticker's DF as macro proxy (assuming it has VIX etc)
    first_ticker = tickers[0]
    macro_proxy_df = data_dict.get(first_ticker)
    
    if macro_proxy_df is None:
        print("Error: No data available for Macro proxy.")
        return

    # 4. Optuna Objective
    def objective(trial):
        params = {
            'stop_loss': trial.suggest_float('stop_loss', 2.0, 5.0, step=0.1),
            'trailing_stop': trial.suggest_float('trailing_stop', 1.5, 4.0, step=0.1),
            'vix_thresh': trial.suggest_float('vix_thresh', 20.0, 40.0, step=1.0),
            'usdtry_thresh': trial.suggest_float('usdtry_thresh', 0.01, 0.05, step=0.005)
        }
        
        return run_strategy_simulation(params, data_dict, prediction_df, macro_proxy_df)

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=trials)
    
    print("\n" + "="*50)
    print("OPTIMIZATION RESULTS")
    print("="*50)
    print(f"Best Sharpe Ratio: {study.best_value:.2f}")
    print(f"Best Parameters: {study.best_params}")
    print("-" * 50)
    print("Current Config:")
    print(f"SL: {config.ATR_STOP_LOSS_MULTIPLIER}")
    print(f"TS: {config.ATR_TRAILING_STOP_MULTIPLIER}")
    
    # Suggest Update
    print("\nTo update, modify config.py manually or implement auto-write.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='strategy', choices=['strategy', 'model'], help='Optimization mode')
    parser.add_argument('--trials', type=int, default=30, help='Number of trials')
    args = parser.parse_args()
    
    optimize(trials=args.trials, mode=args.mode)
