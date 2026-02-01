
import pandas as pd
import numpy as np
import os
import glob
import warnings

warnings.filterwarnings('ignore')

def calculate_sharpe(returns, risk_free_rate=0.40):
    # Annualized Sharpe (Assuming daily data)
    # Risk free rate (e.g. 40% annual in Turkey currently, but for Sharpe usually excess return)
    # Let's use 0.0 for pure Sharpe variability or 0.05 global standard
    # User's previous Sharpe was around 1.0-2.6
    rf_daily = (1 + 0.05)**(1/252) - 1
    
    excess_ret = returns - rf_daily
    if excess_ret.std() == 0: return 0
    return (excess_ret.mean() / excess_ret.std()) * np.sqrt(252)

def analyze_ticker_alpha(ticker):
    daily_file = f"reports/daily_series_{ticker}.csv"
    trades_file = f"reports/backtest_trades_{ticker}.csv"
    
    if not os.path.exists(daily_file) or not os.path.exists(trades_file):
        print(f"Skipping {ticker}: Files not found.")
        return None
        
    df_daily = pd.read_csv(daily_file, index_col=0, parse_dates=True)
    df_trades = pd.read_csv(trades_file, parse_dates=['Entry Date', 'Exit Date'])
    
    # Check if we have trades
    if df_trades.empty:
        print(f"Skipping {ticker}: No trades.")
        return None
        
    # Calculate Original Metrics
    orig_returns = df_daily['Net_Strategy_Return']
    orig_total_ret = (1 + orig_returns).prod() - 1
    orig_sharpe = calculate_sharpe(orig_returns)
    
    # Sort trades by Net Return
    df_trades_sorted = df_trades.sort_values('Net Return', ascending=False).reset_index(drop=True)
    
    num_trades = len(df_trades_sorted)
    
    # Scenarios
    scenarios = [0.05, 0.10]
    results = {
        'Ticker': ticker,
        'Num Trades': num_trades,
        'Orig Sharpe': orig_sharpe,
        'Orig Return': orig_total_ret
    }
    
    for pct in scenarios:
        remove_count = int(np.ceil(num_trades * pct))
        if remove_count == 0: remove_count = 1 # At least 1
        
        removed_trades = df_trades_sorted.head(remove_count)
        
        # Modify daily returns
        mod_returns = orig_returns.copy()
        
        for _, trade in removed_trades.iterrows():
            # Find dates in daily series corresponding to this trade
            # Entry Date to Exit Date (Inclusive?)
            # Entry logic: Position 0->1. Daily return on entry day is partial?
            # Daily Series has 'Net_Strategy_Return'. 
            # We assume effective dates are from Entry Date to Exit Date
            # BUT: Entry Date usually has return if Close > Open etc or close-to-close
            # Let's mask all dates in range [Entry, Exit]
            mask = (mod_returns.index >= trade['Entry Date']) & (mod_returns.index <= trade['Exit Date'])
            mod_returns[mask] = 0.0 # Set return to 0 (Cash)
            
        new_total_ret = (1 + mod_returns).prod() - 1
        new_sharpe = calculate_sharpe(mod_returns)
        
        results[f'Sharpe (Top {int(pct*100)}% Removed)'] = new_sharpe
        results[f'Return (Top {int(pct*100)}% Removed)'] = new_total_ret
        results[f'Retained Sharpe % (Top {int(pct*100)}%)'] = (new_sharpe / orig_sharpe) * 100 if orig_sharpe > 0 else 0
        
    return results

def main():
    tickers = ["ASELS.IS", "TSKB.IS", "EREGL.IS", "GARAN.IS", "TUPRS.IS", "AKBNK.IS"]
    all_results = []
    
    print(f"{'Ticker':<10} | {'Orig Sharpe':<12} | {'-5% Top':<12} | {'Retained%':<10} | {'-10% Top':<12} | {'Retained%':<10}")
    print("-" * 80)
    
    for t in tickers:
        res = analyze_ticker_alpha(t)
        if res:
            all_results.append(res)
            print(f"{res['Ticker']:<10} | {res['Orig Sharpe']:.2f}         | {res['Sharpe (Top 5% Removed)']:.2f}         | {res['Retained Sharpe % (Top 5%)']:.1f}%      | {res['Sharpe (Top 10% Removed)']:.2f}         | {res['Retained Sharpe % (Top 10%)']:.1f}%")
            
    # Save to CSV
    pd.DataFrame(all_results).to_csv('reports/alpha_concentration_test.csv', index=False)

if __name__ == "__main__":
    main()
