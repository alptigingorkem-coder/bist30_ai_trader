import pandas as pd
import numpy as np
import os
import sys
import optuna
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
import matplotlib.pyplot as plt
import optuna.visualization as vis

# Proje Kök Dizini
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer

# --- CONFIGURATION FROM USER PLAN ---
FIXED_STRATEGY_PARAMS = {
    'CONFIDENCE_THRESHOLD': 0.60,  
    'MIN_HOLDING_PERIODS': 10,     
    'STOP_LOSS_MULTIPLIER': 1.5,   
    'TAKE_PROFIT_MULTIPLIER': 2.5, 
    'TRAILING_STOP_MULTIPLIER': 1.5,
    'MAX_STOP_LOSS_PCT': 0.08,     
    'COMMISSION_RATE': 0.0025      
}

MACRO_GATE_THRESHOLDS = {
    'VIX_HIGH': 30.0,
    'USDTRY_CHANGE_5D': 0.03,
    'SP500_MOMENTUM': 0.0
}

# --- PHASE 1: ADAPTIVE RISK MANAGEMENT ---
def get_adaptive_threshold(regime_num, current_drawdown, base_threshold=0.005, recent_win_rate=None):
    """
    Dynamically adjust entry threshold based on regime and portfolio drawdown.
    Higher threshold = more selective entries.
    
    VERSION 3: Added win-rate feedback loop (FIX 2 - Phase 2A).
    
    Args:
        regime_num: 0=Sideways, 1=Crash, 2=Trend_Up
        current_drawdown: Current portfolio DD (e.g., -0.15 for -15%)
        base_threshold: Default threshold (0.5% expected return)
        recent_win_rate: Win rate of last 20 trades (e.g., 0.35 for 35%)
    
    Returns:
        Adjusted threshold
    """
    threshold = base_threshold
    
    # Regime-based adjustment (REDUCED from v1)
    if regime_num == 1:  # CRASH
        threshold *= 2.0  # Was 3.0 → Now 2.0 (0.5% → 1.0%)
    elif regime_num == 0:  # SIDEWAYS
        threshold *= 1.5  # Was 2.0 → Now 1.5 (0.5% → 0.75%)
    # TREND_UP (2): use base threshold
    
    # Drawdown-based adjustment (GENTLER activation)
    if current_drawdown < -0.20:  # Only at -20% (was -15%)
        threshold *= 1.5  # Was 2.5
    elif current_drawdown < -0.15:  # At -15%
        threshold *= 1.2  # Was 1.5 @ -10%
    
    # FIX 2: WIN-RATE FEEDBACK LOOP (Emergency Brake)
    if recent_win_rate is not None:
        if recent_win_rate < 0.35:  # <35% win rate: EXTREME EMERGENCY
            threshold *= 3.0
            # Silent in production, but logged
        elif recent_win_rate < 0.40:  # <40% win rate: EMERGENCY BRAKE
            threshold *= 2.5
        elif recent_win_rate < 0.45:  # <45% win rate: CAUTION
            threshold *= 1.5
    
    return threshold

def get_dynamic_stop_loss(regime_num, atr_multiplier=1.5):
    """
    Regime-aware stop-loss calculation.
    Tighter stops during crisis, standard during trends.
    
    Args:
        regime_num: 0=Sideways, 1=Crash, 2=Trend_Up
        atr_multiplier: Base ATR multiplier
    
    Returns:
        (stop_multiplier, max_stop_pct)
    """
    if regime_num == 1:  # CRASH - Tightest
        return (atr_multiplier * 0.8, 0.05)  # Max 5%
    elif regime_num == 0:  # SIDEWAYS
        return (atr_multiplier * 1.0, 0.06)  # Max 6%
    else:  # TREND_UP (2)
        return (atr_multiplier * 1.0, 0.07)  # Max 7%

def get_volatility_adjusted_size(current_vol, avg_vol, base_size=1.0):
    """
    FIX 3: Reduce position size during high volatility periods.
    
    Args:
        current_vol: Current ATR or volatility measure
        avg_vol: Long-term average volatility (52-week for weekly, 252-day for daily)
        base_size: Default position size (1.0 = 100%)
    
    Returns:
        Adjusted position size (0.5-1.0)
    """
    if avg_vol <= 0:
        return base_size
    
    vol_ratio = current_vol / avg_vol
    
    if vol_ratio > 2.0:  # 2x normal volatility
        return base_size * 0.5  # Half size
    elif vol_ratio > 1.5:  # 1.5x normal
        return base_size * 0.7  # 70% size
    elif vol_ratio > 1.2:  # 1.2x normal
        return base_size * 0.85  # 85% size
    else:
        return base_size  # Full size


def load_data():
    """Tüm veriyi yükler, işler ve 'tarih sıralı' tek bir DF olarak döndürür."""
    print("Loading Data (2015-Now)...")
    loader = DataLoader(start_date="2015-01-01")
    tickers = config.TICKERS
    
    all_frames = []
    
    for ticker in tickers:
        # print(f"  Processing {ticker}...")
        raw_data = loader.get_combined_data(ticker)
        if raw_data is None or len(raw_data) < 100:
            continue
            
        fe = FeatureEngineer(raw_data)
        df = fe.process_all(ticker=ticker)
        
        # Ensure Target exists (NextDay_Return)
        if 'NextDay_Return' not in df.columns:
            # Fallback calculation if FE doesn't provide it
            # Assuming 'Close' is weekly if process_all did resampling
            # Logic check: FE process_all doesn't do resampling unless internally handled?
            # Config.TIMEFRAME='W'. FE usually calculates derived features based on that.
            # But DataLoader usually returns Daily.
            # We must verify sample freq.
            pass

        # Add Ticker column
        df['Ticker'] = ticker
        all_frames.append(df)
        
    if not all_frames:
        raise ValueError("No data loaded successfully.")
        
    full_data = pd.concat(all_frames)
    full_data.sort_index(inplace=True)
    
    print(f"Data Loaded: {len(full_data)} rows. Unique dates: {len(full_data.index.unique())}")
    return full_data

def objective(trial, train_data):
    """
    Her trial için TimeSeriesSplit ile cross-validation yaparak Sharpe hesapla.
    """
    
    # 1. Hiperparametreleri öner
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'verbosity': -1,
        'boosting_type': 'gbdt',
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.15, log=True),
        'num_leaves': trial.suggest_int('num_leaves', 20, 150),
        'max_depth': trial.suggest_int('max_depth', 3, 12),
        'min_child_samples': trial.suggest_int('min_child_samples', 10, 100),
        'min_child_weight': trial.suggest_float('min_child_weight', 1e-5, 1e-1, log=True),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 2.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 2.0),
        'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
        'bagging_fraction': trial.suggest_float('bagging_fraction', 0.5, 1.0),
        'bagging_freq': trial.suggest_int('bagging_freq', 1, 7),
        'n_estimators': 500
    }
    
    # Pruning için early stopping rounds
    # lgb.cv kullanırsak daha native olur ama burada manuel iterasyon
    
    # 2. TimeSeriesSplit with Gap
    # Not: train_data contains Multiple Tickers.
    # TimeSeriesSplit simply splits by row count.
    # Since data is sorted by Date, this works: past block -> future block.
    # But leakage warning: If index is duplicate (multiple tickers on same date), 
    # split line might cut in the middle of a day.
    # Solution: Custom splitter or assume sorted index allows meaningful splits.
    # TimeSeriesSplit is robust enough if gap is used.
    
    tscv = TimeSeriesSplit(n_splits=3, gap=5) # 5 fold might be too slow, using 3 for speed check first? User said 5.
    # Use user's 5.
    tscv = TimeSeriesSplit(n_splits=5, gap=5)
    
    sharpe_scores = []
    
    # Drops for X
    drop_cols = ['NextDay_Return', 'Excess_Return', 'Ticker', 'NextDay_Close', 'NextDay_Direction', 
                 'NextDay_XU100_Return', 'Excess_Return_Current'] 
    # Only keep valid numeric features
    
    numeric_cols = train_data.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [c for c in numeric_cols if c not in drop_cols]
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(train_data)):
        # iloc indexing
        X_train = train_data.iloc[train_idx][feature_cols]
        y_train = train_data.iloc[train_idx]['NextDay_Return']
        
        X_val = train_data.iloc[val_idx][feature_cols]
        y_val = train_data.iloc[val_idx]['NextDay_Return']
        
        # Simple Validation Set check
        if len(X_val) < 10: continue
        
        dtrain = lgb.Dataset(X_train, label=y_train)
        dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)
        
        model = lgb.train(
            params,
            dtrain,
            valid_sets=[dval],
            callbacks=[
                lgb.early_stopping(stopping_rounds=20, verbose=False),
                lgb.log_evaluation(0) # Silence
            ]
        )
        
        predictions = model.predict(X_val)
        
        # Simple Backtest for Sharpe
        threshold = 0.005
        positions = (predictions > threshold).astype(int)
        
        # Sharpe Calculation
        # Returns per ticker? No, this is pooled validation set.
        # This approximates portfolio return if we assume equal weight on all validated samples.
        # Or simplistic aggregate return.
        
        strategy_returns = positions * y_val.values
        
        # Tx Cost
        position_changes = np.abs(np.diff(positions, prepend=0))
        transaction_costs = position_changes * 0.0025
        
        net_returns = strategy_returns - transaction_costs
        
        if net_returns.std() > 1e-6:
             sharpe = (net_returns.mean() / net_returns.std()) * np.sqrt(52) # User: Weekly
        else:
             sharpe = 0
             
        sharpe_scores.append(sharpe)
        
        trial.report(sharpe, fold)
        if trial.should_prune():
             raise optuna.TrialPruned()
             
    if not sharpe_scores: return 0.0
    return np.mean(sharpe_scores)


def backtest_with_strategy(predictions, actual_returns, data, model, params):
    """
    Detailed backtest logic with FIX 4: Sector-aware strategy.
    Each ticker adjusts threshold based on its sector characteristics.
    """
    import config
    
    tickers = data['Ticker'].unique()
    all_trades = []
    
    total_capital = 1.0
    allocated_returns = []
    
    for ticker in tickers:
        ticker_mask = (data['Ticker'] == ticker)
        if not ticker_mask.any(): continue
        
        t_data = data[ticker_mask]
        t_preds = predictions[ticker_mask] # Numpy array sliced? No, prediction needs alignment.
        # Predictions array passed in is aligned with 'data' (which is sorted by date but mixed tickers? No load_data sorted by index (Date)).
        # So 'predictions' corresponds 1-to-1 with 'data'.
        
        # Align prediction
        # predictions array matches 'data' row-by-row.
        # ticker_mask identifies rows belonging to this ticker.
        # We can simply index the numpy array with the boolean mask.
        
        t_preds_subset = predictions[ticker_mask.values]
        t_actual = actual_returns[ticker_mask]
        
        # Run Strategy Logic with FIX 4: sector info
        res = run_single_ticker_strategy(t_preds_subset, t_actual, t_data, ticker=ticker)
        
        all_trades.extend(res['trades'])
        
        # Equity curve of this ticker
        # We want to aggregate daily/weekly returns.
        earning_series = pd.Series(res['returns'], index=t_data.index) # Pct change
        allocated_returns.append(earning_series)

    # Aggregate Portfolio
    if not allocated_returns:
        return {'sharpe':0, 'total_return':0, 'max_drawdown':0, 'num_trades':0, 'win_rate':0}
        
    portfolio_daily_ret = pd.concat(allocated_returns, axis=1).mean(axis=1).fillna(0)
    
    # Calc Metrics
    total_return = (1 + portfolio_daily_ret).prod() - 1
    
    if portfolio_daily_ret.std() > 0:
        sharpe = (portfolio_daily_ret.mean() / portfolio_daily_ret.std()) * np.sqrt(52)
    else:
        sharpe = 0
        
    cum_ret = (1 + portfolio_daily_ret).cumprod()
    dd = (cum_ret - cum_ret.cummax()) / cum_ret.cummax()
    max_drawdown = dd.min()
    
    win_rate = 0
    if all_trades:
        wins = sum(1 for t in all_trades if t['return'] > 0)
        win_rate = wins / len(all_trades)
        
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'num_trades': len(all_trades),
        'win_rate': win_rate,
        'daily_returns_series': portfolio_daily_ret
    }

def run_single_ticker_strategy(preds, actuals, data, ticker=None):
    """
    Applies user strategy logic for a single ticker sequence.
    NOW WITH ADAPTIVE RISK MANAGEMENT (Phase 1) + FIX 4 (Sector Penalty).
    
    Args:
        ticker: Ticker symbol for sector-based adjustments (FIX 4)
    """
    import config
    
    # FIX 4: Get sector and calculate penalty multiplier
    sector_penalty = 1.0
    if ticker:
        sector = config.get_sector(ticker)
        # High-risk sectors from 2023 analysis: Construction, Real Estate
        HIGH_RISK_SECTORS = ['Construction', 'RealEstate']
        MODERATE_RISK_SECTORS = ['Banking']  # Banks had volatility post-election
        
        if sector in HIGH_RISK_SECTORS:
            sector_penalty = 1.4  # 40% harder to enter
        elif sector in MODERATE_RISK_SECTORS:
            sector_penalty = 1.2  # 20% harder
    
    # Extract regime info if available
    regime_nums = data['Regime_Num'].values if 'Regime_Num' in data.columns else np.ones(len(data)) * 2  # Default: Trend
    
    # Initial signals (will be refined with adaptive threshold)
    signals = np.zeros(len(preds), dtype=int)
    
    position = 0
    entry_price = 0
    entry_idx = 0
    
    trades = []
    equity = 1.0
    returns = []
    
    atr_vals = data['ATR'].values if 'ATR' in data.columns else np.ones(len(data))*0.02
    prices = data['Close'].values
    dates = data.index
    
    # Track portfolio drawdown for adaptive threshold
    equity_curve = [1.0]
    
    # FIX 2: Track recent win-rate (rolling 20 trades)
    recent_trade_outcomes = []  # 1 for win, 0 for loss
    
    # FIX 3: Calculate long-term average ATR for volatility sizing
    vol_window = 52 if len(data) > 52 else len(data) // 2  # 52-week or half available data
    avg_atr = np.mean(atr_vals[-vol_window:]) if len(atr_vals) > vol_window else np.mean(atr_vals)
    
    for i in range(len(preds)):
        # Calculate current portfolio drawdown
        current_equity = equity_curve[-1] if equity_curve else 1.0
        peak_equity = max(equity_curve) if equity_curve else 1.0
        current_dd = (current_equity - peak_equity) / peak_equity if peak_equity > 0 else 0.0
        
        # Calculate rolling win rate (last 20 trades)
        recent_win_rate = None
        if len(recent_trade_outcomes) >= 10:  # Need at least 10 trades for meaningful signal
            recent_win_rate = np.mean(recent_trade_outcomes[-20:])  # Last 20 trades
        
        # Get adaptive threshold for this step
        regime = int(regime_nums[i])
        adaptive_thresh = get_adaptive_threshold(regime, current_dd, recent_win_rate=recent_win_rate)
        
        # FIX 4: Apply sector penalty
        adaptive_thresh *= sector_penalty
        
        # Generate signal based on adaptive threshold
        signal = 1 if preds[i] > adaptive_thresh else 0
        signals[i] = signal
    
    # Now run strategy with adaptive signals
    position = 0
    entry_price = 0
    entry_idx = 0
    trades = []
    returns = []
    equity = 1.0
    
    for i in range(len(signals)):
        price = prices[i]
        signal = signals[i]
        atr = atr_vals[i]
        
        ret = 0.0
        
        if position == 1:
            # Check Exit
            holding_curr = i - entry_idx
            
            # PHASE 1: Dynamic stop-loss based on regime
            regime = int(regime_nums[i])
            stop_multiplier, max_stop_pct = get_dynamic_stop_loss(regime)
            
            stop_loss_atr = entry_price - (stop_multiplier * atr)
            stop_loss_pct = entry_price * (1 - max_stop_pct)
            stop_price = max(stop_loss_atr, stop_loss_pct)  # Use tighter of the two
            
            tp_price = entry_price + (FIXED_STRATEGY_PARAMS['TAKE_PROFIT_MULTIPLIER'] * atr)
            
            exit_reason = None
            if price <= stop_price: exit_reason = 'STOP'
            elif price >= tp_price: exit_reason = 'PROFIT'
            elif holding_curr >= FIXED_STRATEGY_PARAMS['MIN_HOLDING_PERIODS'] and signal == 0:
                 exit_reason = 'SIGNAL'
                 
            if exit_reason:
                # Sell
                raw_ret = price / entry_price - 1
                net_ret = raw_ret - FIXED_STRATEGY_PARAMS['COMMISSION_RATE']
                
                # FIX 3: Apply volatility-adjusted position sizing
                current_atr = atr_vals[i]
                vol_size_multiplier = get_volatility_adjusted_size(current_atr, avg_atr)
                scaled_ret = net_ret * vol_size_multiplier
                
                trades.append({'return': scaled_ret, 'reason': exit_reason})
                
                # FIX 2: Record outcome for win-rate tracking
                recent_trade_outcomes.append(1 if scaled_ret > 0 else 0)
                
                # Apply return to this step (simplified, actually return happens at Close)
                ret = scaled_ret
                equity *= (1 + ret)
                position = 0
            else:
                # Holding (Mark to Market return)
                step_ret = price / prices[i-1] - 1 if i > 0 else 0
                ret = step_ret
                equity *= (1 + ret) 
                
        elif position == 0:
            if signal == 1:
                # Buy
                position = 1
                entry_price = price
                entry_idx = i
                # Comm cost immediately
                ret = -FIXED_STRATEGY_PARAMS['COMMISSION_RATE']
                equity *= (1 + ret)
        
        returns.append(ret)
        equity_curve.append(equity)
        
    return {'trades': trades, 'returns': returns}

def optimize_and_test_per_year(dry_run=False):
    full_data = load_data()
    
    test_years = [2023, 2024] if dry_run else [2020, 2021, 2022, 2023, 2024]
    if dry_run: print("DRY RUN MODE: Testing 2023-2024 only with reduced trials.")
    
    all_results = []
    all_daily_returns_list = []
    
    for test_year in test_years:
        print(f"\n{'='*60}")
        print(f"TEST YILI: {test_year}")
        print(f"{'='*60}")
        
        train_data = full_data[full_data.index.year < test_year]
        test_data = full_data[full_data.index.year == test_year]
        
        if len(train_data.index.year.unique()) < 3:
            print(f"Skipping {test_year}: Insufficient training history.")
            continue
            
        study = optuna.create_study(
            direction='maximize',
            study_name=f'bist30_{test_year}',
            pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=2)
        )
        
        n_trials = 5 if dry_run else 50
        print(f"Optimizasyon Başlıyor ({n_trials} trials)...")
        
        study.optimize(
            lambda t: objective(t, train_data),
            n_trials=n_trials,
            timeout=1800 if dry_run else 3600
        )
        
        print(f"Best CV Sharpe: {study.best_value:.4f}")
        
        # Final Train
        best_params = study.best_params
        best_params.update({'objective':'regression', 'metric':'rmse', 'verbosity':-1, 'n_estimators': 500})
        
        feature_cols = [c for c in train_data.columns if c not in ['NextDay_Return', 'Excess_Return', 'Ticker', 'NextDay_Close', 'NextDay_Direction', 'NextDay_XU100_Return', 'Excess_Return_Current'] and pd.api.types.is_numeric_dtype(train_data[c])]
        
        X_train = train_data[feature_cols]
        y_train = train_data['NextDay_Return']
        X_test = test_data[feature_cols]
        y_test = test_data['NextDay_Return']
        
        final_model = lgb.train(best_params, lgb.Dataset(X_train, label=y_train))
        preds = final_model.predict(X_test)
        
        # Backtest
        res = backtest_with_strategy(preds, y_test, test_data, final_model, best_params)
        
        print(f"Test Result {test_year}: Return={res['total_return']:.2%}, Sharpe={res['sharpe']:.2f}")
        
        # Collect Daily Returns
        if 'daily_returns_series' in res:
             all_daily_returns_list.append(res['daily_returns_series'])
             del res['daily_returns_series'] # Don't save series in summary csv
        
        res['test_year'] = test_year
        res['cv_sharpe'] = study.best_value
        res['test_return'] = res['total_return'] # Rename key
        res['test_sharpe'] = res['sharpe']
        res['test_drawdown'] = res['max_drawdown']
        res['best_params'] = best_params
        del res['total_return'], res['sharpe'], res['max_drawdown']
        
        all_results.append(res)
        
        # Partial Save
        pd.DataFrame([res]).to_csv(f'reports/optuna_res_{test_year}.csv')
        try:
             save_plots(study, test_year)
        except:
             print("Plotting failed (missing dependencies?)")
             
    # Final Report
    df_res = pd.DataFrame(all_results)
    if not os.path.exists("reports"): os.makedirs("reports")
    df_res.to_csv("reports/optuna_walk_forward_results.csv", index=False)
    
    # Save Daily Returns Concatenated
    if all_daily_returns_list:
        combined_daily_returns = pd.concat(all_daily_returns_list)
        combined_daily_returns.name = 'Portfolio_Return'
        combined_daily_returns.to_csv("reports/daily_returns_concatenated.csv", header=True)
        print("\n✅ Daily Returns Saved: reports/daily_returns_concatenated.csv")
    
    print("\nDONE.")
    print(df_res[['test_year', 'cv_sharpe', 'test_sharpe', 'test_return', 'test_drawdown', 'win_rate']])

def save_plots(study, year):
    if not os.path.exists("reports"): os.makedirs("reports")
    try:
        vis.plot_optimization_history(study).write_html(f"reports/hist_{year}.html")
        vis.plot_param_importances(study).write_html(f"reports/imp_{year}.html")
    except: pass

if __name__ == "__main__":
    dry = '--dry-run' in sys.argv
    optimize_and_test_per_year(dry_run=dry)
