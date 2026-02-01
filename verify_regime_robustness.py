
import pandas as pd
import numpy as np
import glob
import os
import warnings

warnings.filterwarnings('ignore')

def calculate_sharpe(returns, risk_free_rate=0.0):
    excess_ret = returns - risk_free_rate
    if excess_ret.std() == 0: return 0
    return (excess_ret.mean() / excess_ret.std()) * np.sqrt(252)

def simulate_regime_noise(ticker, n_simulations=50, noise_level=0.20):
    file_path = f"reports/daily_series_{ticker}.csv"
    if not os.path.exists(file_path):
        return None
        
    df = pd.read_csv(file_path, parse_dates=['Date'])
    
    # Required columns
    # NextDay_Return: The return of the asset for the period
    # Net_Strategy_Return: The actual return achieved
    # Regime: The regime that governed the decision
    
    if 'NextDay_Return' not in df.columns or 'Net_Strategy_Return' not in df.columns:
        return None
        
    # Original Metrics
    orig_sharpe = calculate_sharpe(df['Net_Strategy_Return'])
    
    sim_sharpes = []
    
    regime_types = ['Trend_Up', 'Sideways', 'Crash_Bear']
    
    # Transaction cost approximation (slippage + comm)
    # If we switch regime effectively, we might trade. 
    # Let's deduct a small cost for "Active" regimes to be conservative.
    cost = 0.001 
    
    for i in range(n_simulations):
        sim_returns = df['Net_Strategy_Return'].copy()
        
        # Determine which days to perturb
        # We assume independent errors day-to-day (worst case noise)
        n_days = len(df)
        flip_indices = np.random.choice(df.index, size=int(n_days * noise_level), replace=False)
        
        for idx in flip_indices:
            original_regime = df.loc[idx, 'Regime'] if 'Regime' in df.columns else 'Trend_Up' # Default
            
            # Pick a DIFFERENT random regime
            possible_flips = [r for r in regime_types if r != original_regime]
            new_regime = np.random.choice(possible_flips)
            
            market_ret = df.loc[idx, 'NextDay_Return']
            
            # Approximate Outcome based on New Regime
            if new_regime == 'Crash_Bear':
                # Cash position
                new_ret = 0.0
            elif new_regime == 'Trend_Up':
                # Full Long
                new_ret = market_ret - cost
            elif new_regime == 'Sideways':
                # Defensive Long (Alpha mode)
                # Assume 50% Beta exposure + Alpha (but we can't sim Alpha easily)
                # Let's be conservative: 50% of Market Return - Cost
                new_ret = (market_ret * 0.5) - cost
            
            sim_returns.loc[idx] = new_ret
            
        sim_sharpes.append(calculate_sharpe(sim_returns))
        
    avg_sim_sharpe = np.mean(sim_sharpes)
    
    return {
        'Ticker': ticker,
        'Orig Sharpe': orig_sharpe,
        'Avg Noise Sharpe': avg_sim_sharpe,
        'Pass': avg_sim_sharpe > 0 # Pass if it doesn't blow up (negative)
    }

def main():
    tickers = ["ASELS.IS", "TSKB.IS", "EREGL.IS", "GARAN.IS", "TUPRS.IS", "AKBNK.IS"]
    
    print(f"{'Ticker':<10} | {'Orig Sharpe':<12} | {'Noised Sharpe (20%)':<20} | {'Result':<10}")
    print("-" * 70)
    
    for t in tickers:
        res = simulate_regime_noise(t)
        if res:
            status = "✅ PASS" if res['Pass'] else "❌ FAIL"
            print(f"{res['Ticker']:<10} | {res['Orig Sharpe']:.2f}         | {res['Avg Noise Sharpe']:.2f}                 | {status}")
            
if __name__ == "__main__":
    main()
