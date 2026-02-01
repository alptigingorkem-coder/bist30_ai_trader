
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')

def calculate_sharpe(returns, risk_free_rate=0.0):
    # Weekly data in concatenated file (confirmed in previous steps)
    # Annualization factor for weekly = 52
    excess_ret = returns - risk_free_rate
    if excess_ret.std() == 0: return 0
    return (excess_ret.mean() / excess_ret.std()) * np.sqrt(52)

def main():
    file_path = 'reports/daily_returns_concatenated.csv'
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return

    # Calculate Portfolio Return (Equal Weighted)
    df['Portfolio'] = df.mean(axis=1)
    
    # Get years
    years = df.index.year.unique()
    
    results = []
    
    print(f"{'Year':<6} | {'Portfolio Sharpe':<18} | {'Best Ticker':<12} | {'Worst Ticker':<12}")
    print("-" * 60)
    
    for year in years:
        df_year = df[df.index.year == year]
        if len(df_year) < 10: continue # Skip if too few data points (e.g. 2026 start)
        
        # Calculate Sharpe for all columns
        sharpes = {}
        for col in df_year.columns:
            sharpes[col] = calculate_sharpe(df_year[col])
            
        port_sharpe = sharpes['Portfolio']
        
        # Find best and worst individual ticker sharpe
        # Exclude 'Portfolio' from min/max check
        ticker_sharpes = {k:v for k,v in sharpes.items() if k != 'Portfolio'}
        best_ticker = max(ticker_sharpes, key=ticker_sharpes.get)
        worst_ticker = min(ticker_sharpes, key=ticker_sharpes.get)
        
        print(f"{year:<6} | {port_sharpe:.2f}               | {best_ticker:<5} ({ticker_sharpes[best_ticker]:.1f}) | {worst_ticker:<5} ({ticker_sharpes[worst_ticker]:.1f})")
        
        results.append({
            'Year': year,
            'Portfolio Sharpe': port_sharpe,
            'Best': f"{best_ticker} ({ticker_sharpes[best_ticker]:.1f})",
            'Worst': f"{worst_ticker} ({ticker_sharpes[worst_ticker]:.1f})"
        })

    # Check for consistency
    port_sharpes = [r['Portfolio Sharpe'] for r in results]
    if all(s > 0 for s in port_sharpes):
        print("\n✅ PASS: Portfolio Sharpe is consistently positive across all years.")
    else:
        print("\n⚠️ WARNING: Portfolio Sharpe dipped below zero in some years.")
        
    pd.DataFrame(results).to_csv('reports/walk_forward_analysis.csv', index=False)

if __name__ == "__main__":
    main()
