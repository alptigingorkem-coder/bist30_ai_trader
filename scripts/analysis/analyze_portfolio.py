
import pandas as pd
import numpy as np

from scripts.analysis.utils import calculate_max_drawdown, calculate_sharpe_ratio

def analyze():
    # Load daily returns
    df = pd.read_csv('reports/daily_returns_concatenated.csv', index_col='Date', parse_dates=True)
    
    # Calculate Portfolio Return (Assuming Equal Weight of active assets for simplicity, or sum if these are weighted returns)
    # Since we don't know the exact daily weights from this CSV, we'll try two approaches:
    # 1. Sum of returns (assuming these are weighted contributions)
    # 2. Mean of non-zero returns (assuming equal weight among active stats)
    
    # Approach 1: Sum
    portfolio_returns_sum = df.sum(axis=1)
    
    # Calculate Cumulative
    portfolio_value = (1 + portfolio_returns_sum).cumprod()
    
    max_dd = calculate_max_drawdown(portfolio_value)
    sharpe = calculate_sharpe_ratio(portfolio_returns_sum)
    
    print(f"Analysis Results (Sum Approach):")
    print(f"Max Drawdown: {max_dd:.4f}")
    print(f"Sharpe Ratio: {sharpe:.4f}")
    print(f"Total Return: {portfolio_value.iloc[-1] - 1:.4f}")

if __name__ == "__main__":
    analyze()
