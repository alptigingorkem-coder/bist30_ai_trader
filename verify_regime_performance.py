
import pandas as pd
import numpy as np
import glob
import os
import warnings

warnings.filterwarnings('ignore')

def calculate_sharpe(returns, risk_free_rate=0.0):
    # Daily data
    excess_ret = returns - risk_free_rate
    if excess_ret.std() == 0: return 0
    return (excess_ret.mean() / excess_ret.std()) * np.sqrt(252)

def analyze_regime_performance():
    files = glob.glob("reports/daily_series_*.csv")
    if not files:
        print("No daily series files found.")
        return

    all_data = []
    
    for file in files:
        ticker = os.path.basename(file).replace("daily_series_", "").replace(".csv", "")
        # Filter for our core portfolio if needed, but comprehensive is better
        # Let's stick to the core ones to be consistent with previous reports if possible
        # Or just use all available. Let's use all available OOS data.
        
        try:
            df = pd.read_csv(file, parse_dates=['Date'])
            if 'Regime' not in df.columns or 'Net_Strategy_Return' not in df.columns:
                continue
                
            df['Ticker'] = ticker
            all_data.append(df[['Date', 'Ticker', 'Regime', 'Net_Strategy_Return']])
        except Exception as e:
            print(f"Error reading {file}: {e}")

    if not all_data:
        print("No valid data found.")
        return

    full_df = pd.concat(all_data)
    
    # Analyze by Regime
    print(f"{'Regime':<15} | {'Avg Daily Ret':<15} | {'Ann. Return':<15} | {'Sharpe Ratio':<15} | {'Count (Days)':<10}")
    print("-" * 80)
    
    regimes = full_df['Regime'].unique()
    results = []
    
    for regime in regimes:
        regime_df = full_df[full_df['Regime'] == regime]
        
        # Calculate aggregate metrics for this regime across all tickers
        # Assuming equal weight portfolio of all tickers in this regime
        # Correct way: Average return of all tickers on each day in this regime, then Sharpe of that series
        # But here we have stacked data. 
        # Let's group by Date first to get Portfolio Return for that regime's days
        
        # Pivot to get returns matrix: Index=Date, Cols=Ticker
        # Then filter dates where *Market* was in that regime? 
        # Wait, Regime is determined per ticker or global?
        # Regime detector uses global/macro data usually but calculated per ticker in current architecture?
        # Let's check if Regime is same for all tickers on same day.
        # It depends on file content. Usually RegimeDetection is passed 'df' which might be ticker specific prices.
        # But Macro factors are global.
        # Let's assume it can vary if it uses ticker volatility.
        
        # Simple aggregation: Treat all ticker-days in this regime as a single return distribution (Pooled)
        # This gives the expected value of a trade taken in this regime.
        
        avg_daily_ret = regime_df['Net_Strategy_Return'].mean()
        daily_std = regime_df['Net_Strategy_Return'].std()
        
        ann_ret = (1 + avg_daily_ret) ** 252 - 1
        if daily_std == 0:
            sharpe = 0
        else:
            sharpe = (avg_daily_ret / daily_std) * np.sqrt(252)
            
        count = len(regime_df)
        
        print(f"{regime:<15} | {avg_daily_ret:.4%}          | {ann_ret:.2%}          | {sharpe:.2f}            | {count:<10}")
        
        results.append({
            'Regime': regime,
            'Sharpe': sharpe,
            'Return': ann_ret
        })
        
    # Validation
    positive_regimes = [r for r in results if r['Sharpe'] > 0]
    print("\n" + "="*40)
    if len(positive_regimes) >= 2:
        print(f"✅ PASS: Positive performance in {len(positive_regimes)}/{len(regimes)} regimes.")
    else:
        print(f"❌ FAIL: Positive performance in only {len(positive_regimes)}/{len(regimes)} regimes.")
        
    print("="*40)

if __name__ == "__main__":
    analyze_regime_performance()
