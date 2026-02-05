
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from configs import banking as config_banking
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel
import lightgbm as lgb
from sklearn.linear_model import Ridge

def get_data():
    print("Loading Data...")
    loader = DataLoader(start_date=config.START_DATE)
    tickers = config.TICKERS
    all_data = []
    
    for t in tickers:
        raw = loader.get_combined_data(t)
        if raw is None or len(raw) < 100: continue
        fe = FeatureEngineer(raw)
        df = fe.process_all(t)
        df['Ticker'] = t
        if hasattr(config, 'TRAIN_END_DATE'):
             # We need full data to split manually 
             pass 
        all_data.append(df)
        
    full_df = pd.concat(all_data)
    # Sort
    full_df.reset_index(inplace=True)
    full_df.set_index(['Date', 'Ticker'], inplace=True)
    full_df.sort_index(inplace=True)
    
    return full_df

def backtest_predictions(predictions, prices, top_n=5):
    """
    predictions: DataFrame (Index: Date, Columns: Ticker, Values: Score)
    prices: DataFrame (Index: Date, Columns: Ticker, Values: Close/Return)
    """
    # Simple vector backtest
    # Rank daily
    ranks = predictions.rank(axis=1, ascending=False)
    
    # Signal: 1 if Rank <= Top N
    signals = (ranks <= top_n).astype(int)
    
    # Shift signals 1 day (Trade next day close-to-close) -> Standard backtest logic
    # Actually signals calculated at T close are executed at T+1 Close?
    # Our system: Signals generated at T (Night), Entry at T+1 Open/Close.
    # To keep simple: Use NextDay_Return (which is aligned with row T)
    
    # We have dataframe with 'NextDay_Return'.
    # If we predict row T, we capture NextDay_Return of row T.
    # So we multiply Signal(T) * NextDay_Return(T).
    
    # Need aligned returns
    aligned_rets = prices.reindex(signals.index).fillna(0)
    
    daily_pnl = (signals * aligned_rets).sum(axis=1) / top_n
    
    total_ret = (1 + daily_pnl).cumprod().iloc[-1] - 1
    sharpe = daily_pnl.mean() / daily_pnl.std() * (252**0.5)
    
    return total_ret, sharpe

def run_benchmark():
    full_data = get_data()
    
    # Split
    dates = full_data.index.get_level_values('Date').unique()
    split_idx = int(len(dates) * 0.8) # 80% Train, 20% Test
    test_start_date = dates[split_idx]
    
    print(f"Split Date: {test_start_date} | Test Size: {len(dates)-split_idx} days")
    
    train_mask = full_data.index.get_level_values('Date') < test_start_date
    test_mask = full_data.index.get_level_values('Date') >= test_start_date
    
    df_train = full_data[train_mask]
    df_test = full_data[test_mask]
    
    # Prepare Pivot for Returns (for backtesting)
    # Pivot NextDay_Return
    test_returns_pivot = df_test.reset_index().pivot(index='Date', columns='Ticker', values='NextDay_Return').fillna(0)
    
    results = []
    
    # --- 1. GLOBAL RANKING (Baseline) ---
    print("\n--- 1. Testing Global LightGBM Ranker ---")
    ranker = RankingModel(df_train, config_banking)
    ranker.train(valid_df=df_test) # Train on split
    
    scores = ranker.predict(df_test)
    df_test_scored = df_test.copy()
    df_test_scored['Score'] = scores
    
    pivot_scores = df_test_scored.reset_index().pivot(index='Date', columns='Ticker', values='Score')
    ret, sharpe = backtest_predictions(pivot_scores, test_returns_pivot)
    results.append({'Model': 'Global Ranker (LGBM)', 'Return': ret, 'Sharpe': sharpe})
    print(f"Result: Return {ret:.2%}, Sharpe {sharpe:.2f}")
    
    # --- 2. TICKER-SPECIFIC REGRESSION ---
    print("\n--- 2. Testing Ticker-Specific Regression ---")
    tickers = df_train.index.get_level_values('Ticker').unique()
    ts_preds = pd.DataFrame(index=df_test.index, columns=['Ticker', 'Score'])
    
    params = {'objective': 'regression', 'metric': 'rmse', 'verbose': -1}
    

    # Define excluded columns globally/robustly
    exclude_cols = [
        'Date', 'NextDay_Return', 'Top_N_Target',
        'NextDay_Close', 'NextDay_Direction', 'Excess_Return', 
        'NextDay_XU100_Return', 'Log_Return', 'Ticker'
    ]

    for t in tickers:
        # Filter Data
        t_train = df_train.xs(t, level='Ticker')
        t_test = df_test.xs(t, level='Ticker')
        
        if t_train.empty or t_test.empty: continue
        
        # Features (Exclude Future Cols)
        feat_cols = [c for c in t_train.columns if c not in exclude_cols]
        numeric_cols = t_train[feat_cols].select_dtypes(include=np.number).columns
        
        X_train = t_train[numeric_cols]
        y_train = t_train['NextDay_Return']
        X_test = t_test[numeric_cols]
        
        model = lgb.LGBMRegressor(**params)
        model.fit(X_train, y_train)
        
        pred = model.predict(X_test)
        
        # Save absolute preds
        series = pd.Series(pred, index=t_test.index)
        # Create small DF to concat later
        small_df = pd.DataFrame({'Score': series, 'Ticker': t})
        # Need to align indexes if using concat?
        # Actually easier to store in pivot directly?
        # Let's collect in list
        pass
        
    # Re-loop to fill pivot efficiently
    pivot_ts_scores = pd.DataFrame(index=test_returns_pivot.index, columns=test_returns_pivot.columns)
    
    for t in tickers:
        t_train = df_train.xs(t, level='Ticker')
        t_test = df_test.xs(t, level='Ticker')
        if t_train.empty or t_test.empty: continue
        
        feat_cols = [c for c in t_train.columns if c not in ['Date', 'NextDay_Return']]
        numeric_cols = t_train[feat_cols].select_dtypes(include=np.number).columns
        
        model = lgb.LGBMRegressor(**params)
        model.fit(t_train[numeric_cols], t_train['NextDay_Return'])
        
        preds = model.predict(t_test[numeric_cols])
        # Assign to pivot. Need to match dates
        # t_test index is Dates (since one level dropped).
        pivot_ts_scores.loc[t_test.index, t] = preds
        
    pivot_ts_scores = pivot_ts_scores.astype(float).fillna(-999)
    ret, sharpe = backtest_predictions(pivot_ts_scores, test_returns_pivot)
    results.append({'Model': 'Ticker-Specific Regressor', 'Return': ret, 'Sharpe': sharpe})
    print(f"Result: Return {ret:.2%}, Sharpe {sharpe:.2f}")

    # --- 3. HYBRID LINEAR + LGBM (Global) ---
    print("\n--- 3. Testing Hybrid (Linear + LGBM) ---")
    
    exclude_cols = [
        'Date', 'NextDay_Return', 'Top_N_Target',
        'NextDay_Close', 'NextDay_Direction', 'Excess_Return', 
        'NextDay_XU100_Return', 'Log_Return', 'Ticker'
    ]
    
    # Step 1: Linear
    feat_cols = [c for c in df_train.columns if c not in exclude_cols]
    num_cols = df_train[feat_cols].select_dtypes(include=np.number).columns
    
    lin_model = Ridge(alpha=1.0)
    # Fill NA
    X_train_clean = df_train[num_cols].fillna(0)
    y_train_clean = df_train['NextDay_Return'].fillna(0)
    X_test_clean = df_test[num_cols].fillna(0)
    
    lin_model.fit(X_train_clean, y_train_clean)
    
    train_lin_preds = lin_model.predict(X_train_clean)
    test_lin_preds = lin_model.predict(X_test_clean)
    
    # Step 2: Residuals
    residuals = y_train_clean - train_lin_preds
    
    # Train LGBM on residuals
    lgbm_res = lgb.LGBMRegressor(**params)
    lgbm_res.fit(X_train_clean, residuals)
    
    test_res_preds = lgbm_res.predict(X_test_clean)
    
    # Final
    final_preds = test_lin_preds + test_res_preds
    
    df_test_hybrid = df_test.copy()
    df_test_hybrid['Score'] = final_preds
    pivot_hybrid = df_test_hybrid.reset_index().pivot(index='Date', columns='Ticker', values='Score')
    
    ret, sharpe = backtest_predictions(pivot_hybrid, test_returns_pivot)
    results.append({'Model': 'Hybrid (Ridge + LGBM)', 'Return': ret, 'Sharpe': sharpe})
    print(f"Result: Return {ret:.2%}, Sharpe {sharpe:.2f}")

    print("\n" + "="*50)
    print("BENCHMARK RESULTS")
    print("="*50)
    res_df = pd.DataFrame(results)
    print(res_df.sort_values('Sharpe', ascending=False).to_string(index=False))

if __name__ == "__main__":
    run_benchmark()
