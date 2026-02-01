
import pandas as pd
import numpy as np
import os
import glob
import warnings

warnings.filterwarnings('ignore')

def calculate_sharpe(returns, risk_free_rate=0.40):
    rf_daily = (1 + 0.05)**(1/252) - 1
    excess_ret = returns - rf_daily
    if excess_ret.std() == 0: return 0
    return (excess_ret.mean() / excess_ret.std()) * np.sqrt(252)

def simulate_ticker_time_shift(ticker, n_simulations=50):
    daily_file = f"reports/daily_series_{ticker}.csv"
    trades_file = f"reports/backtest_trades_{ticker}.csv"
    
    if not os.path.exists(daily_file) or not os.path.exists(trades_file):
        print(f"Skipping {ticker}: Files not found.")
        return None
        
    df_daily = pd.read_csv(daily_file, parse_dates=['Date'])
    df_daily = df_daily.set_index('Date').sort_index()
    
    if 'Close' not in df_daily.columns:
        print(f"Skipping {ticker}: 'Close' column missing in daily series.")
        return None
        
    df_trades = pd.read_csv(trades_file, parse_dates=['Entry Date', 'Exit Date'])
    if df_trades.empty:
        return None

    # Original Sharpe
    # Reconstruct original equity curve from trades? Or use stored Net_Strategy_Return?
    # Stored Net_Strategy_Return is best for baseline comparison
    orig_returns = df_daily['Net_Strategy_Return']
    orig_sharpe = calculate_sharpe(orig_returns)
    
    sim_sharpes = []
    
    for i in range(n_simulations):
        # Create a blank return series
        sim_returns = pd.Series(0.0, index=df_daily.index)
        
        for _, trade in df_trades.iterrows():
            market_entry_date = trade['Entry Date']
            market_exit_date = trade['Exit Date']
            
            # Random shift: -3 to +3 days
            shift = np.random.randint(-3, 4) 
            
            # Shift dates (using array index math for speed, assuming daily sorted index)
            # Find index location of dates
            try:
                entry_loc = df_daily.index.get_loc(market_entry_date)
                exit_loc = df_daily.index.get_loc(market_exit_date)
            except KeyError:
                continue # Trade date not in index? Skip
                
            new_entry_loc = max(0, min(len(df_daily)-1, entry_loc + shift))
            new_exit_loc = max(0, min(len(df_daily)-1, exit_loc + shift))
            
            if new_entry_loc >= new_exit_loc:
                continue # Invalid trade after shift
            
            # Calculate return for this shifted period
            # We assume position is held from new_entry to new_exit
            # Position = 1 from new_entry+1 to new_exit
            # Calculate daily returns: price change / prev price
            
            # Vectorized approach: set position mask
            # Note: Overlapping trades in simulation might double count if we just sum returns.
            # But backtester handles 1 position usually. 
            # Simplified: Assuming non-overlapping trades or just summing returns (portfolio of independent trades)
            
            # Get price slice
            price_slice = df_daily['Close'].iloc[new_entry_loc:new_exit_loc+1]
            trade_daily_ret = price_slice.pct_change().fillna(0)
            
            # Apply transaction costs (slippage/comm) roughly on entry/exit?
            # Let's just look at raw price action robustness first.
            # Adding cost: -0.002 on entry and exit day
            
            trade_daily_ret.iloc[0] -= 0.002 # Entry cost
            trade_daily_ret.iloc[-1] -= 0.002 # Exit cost
            
            # Add to simulation returns (accumulate if overlaps)
            # Map back to original index dates
            valid_dates = df_daily.index[new_entry_loc:new_exit_loc+1]
            sim_returns.loc[valid_dates] = sim_returns.loc[valid_dates] + trade_daily_ret.values

        sim_sharpe = calculate_sharpe(sim_returns)
        sim_sharpes.append(sim_sharpe)
        
    avg_sim_sharpe = np.mean(sim_sharpes)
    return {
        'Ticker': ticker,
        'Orig Sharpe': orig_sharpe,
        'Avg Sim Sharpe': avg_sim_sharpe,
        'Pass': avg_sim_sharpe > 0
    }

def main():
    tickers = ["ASELS.IS", "TSKB.IS", "EREGL.IS", "GARAN.IS", "TUPRS.IS", "AKBNK.IS"]
    print(f"{'Ticker':<10} | {'Orig Sharpe':<12} | {'Avg Sim Sharpe (±3 Days)':<25} | {'Result':<10}")
    print("-" * 70)
    
    results = []
    for t in tickers:
        res = simulate_ticker_time_shift(t)
        if res:
            results.append(res)
            status = "✅ PASS" if res['Pass'] else "❌ FAIL"
            print(f"{res['Ticker']:<10} | {res['Orig Sharpe']:.2f}         | {res['Avg Sim Sharpe']:.2f}                      | {status}")
            
    pd.DataFrame(results).to_csv('reports/time_robustness_test.csv', index=False)

if __name__ == "__main__":
    main()
