
import pandas as pd
import numpy as np
from portfolio_optimizer import PortfolioOptimizer

def test_portfolio_optimizer():
    print("--- Portfolio Optimizer Test ---")
    
    # 1. Create Synthetic Historical Data (Weekly Returns)
    # Ticker A: High Return, High Volatility (Trend)
    # Ticker B: Low Return, Low Volatility (Safe)
    # Ticker C: Negative Correlation (Hedge)
    
    np.random.seed(42)
    n_weeks = 100
    
    returns_A = np.random.normal(0.005, 0.04, n_weeks)
    returns_B = np.random.normal(0.002, 0.01, n_weeks)
    returns_C = np.random.normal(0.001, 0.02, n_weeks)
    
    # Make C negatively correlated to A
    returns_C = returns_C - (returns_A * 0.3)
    
    hist_df = pd.DataFrame({
        'A': returns_A,
        'B': returns_B,
        'C': returns_C
    })
    
    print("Historical Covariance Matrix:")
    print(hist_df.cov())
    
    # 2. Predicted Returns (from Beta/Alpha Models)
    expected_returns = {
        'A': 0.02,  # Good trend expectancy
        'B': 0.005, # Stable
        'C': 0.001  # Poor
    }
    
    # 3. Optimize
    optimizer = PortfolioOptimizer(hist_df, risk_free_rate=0.40)
    weights = optimizer.optimize(expected_returns)
    
    print("\noptimized Weights:")
    for ticker, weight in weights.items():
        print(f"{ticker}: {weight:.4f}")
        
    # Validation check
    total_weight = sum(weights.values())
    print(f"\nTotal Weight: {total_weight:.4f}")

if __name__ == "__main__":
    test_portfolio_optimizer()
