
import pandas as pd
import numpy as np

def calculate_sharpe(returns, risk_free_rate=0.0):
    excess_ret = returns - rf_daily
    if excess_ret.std() == 0: return 0
    return (excess_ret.mean() / excess_ret.std()) * np.sqrt(52) # Weekly data in concatenated? No, daily.

# Concatenated seems to be daily returns (lots of 0.0, sparse trades?)
# Let's check dates 2023-01-02 to 2023-01-09... Looks like weekly intervals (7 days)
# 2023-01-02, 09, 16... Yes, weekly.
# So Annualization Factor is 52.

rf_daily = 0.0 # Weekly risk free approx 0 for simplicity or relative comparison

def main():
    df = pd.read_csv('reports/daily_returns_concatenated.csv', index_col=0, parse_dates=True)
    
    # Calculate Total Return for each ticker
    total_returns = (1 + df).prod() - 1
    print("Total Returns per Ticker:")
    print(total_returns.sort_values(ascending=False))
    
    best_ticker = total_returns.idxmax()
    best_return = total_returns.max()
    print(f"\n🏆 Best Ticker: {best_ticker} ({best_return:.2%})")
    
    # 1. Full Portfolio (Equal Weight)
    # Average across all columns
    portfolio_returns = df.mean(axis=1)
    port_total_ret = (1 + portfolio_returns).prod() - 1
    port_sharpe = calculate_sharpe(portfolio_returns)
    
    print(f"\n--- Full Portfolio ---")
    print(f"Total Return: {port_total_ret:.2%}")
    print(f"Sharpe Ratio: {port_sharpe:.2f}")
    
    # 2. Portfolio WITHOUT Best Ticker
    df_excluded = df.drop(columns=[best_ticker])
    portfolio_ex_returns = df_excluded.mean(axis=1)
    port_ex_total_ret = (1 + portfolio_ex_returns).prod() - 1
    port_ex_sharpe = calculate_sharpe(portfolio_ex_returns)
    
    print(f"\n--- Portfolio WITHOUT {best_ticker} ---")
    print(f"Total Return: {port_ex_total_ret:.2%}")
    print(f"Sharpe Ratio: {port_ex_sharpe:.2f}")
    
    # Validation
    sharpe_drop = (port_sharpe - port_ex_sharpe) / port_sharpe
    print(f"\nImpact on Sharpe: {sharpe_drop:.1%} Drop")
    
    if port_ex_sharpe > 0.5: # Reasonable threshold
        print("✅ PASS: System remains profitable without the star performer.")
    else:
        print("❌ FAIL: System collapses without the star performer.")

if __name__ == "__main__":
    main()
