
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def run_monte_carlo(n_sims=1000, initial_capital=10000):
    print("Loading daily returns...")
    try:
        df = pd.read_csv("reports/daily_returns_concatenated.csv", index_col=0)
    except FileNotFoundError:
        print("Error: reports/daily_returns_concatenated.csv not found.")
        return

    # Assume Equal Weight Portfolio of all tested tickers
    # Missing values (0.0) imply flat or no data, which is fine for return calc
    portfolio_daily_rets = df.mean(axis=1) # Average return of the basket
    
    # Statistics
    mu = portfolio_daily_rets.mean()
    sigma = portfolio_daily_rets.std()
    
    print(f"Portfolio Daily Mean: {mu:.4%}")
    print(f"Portfolio Daily Vol:  {sigma:.4%}")
    
    sim_results = []
    ruin_count = 0
    drawdowns = []
    
    print(f"Running {n_sims} simulations (Bootstrap method)...")
    
    n_days = len(portfolio_daily_rets)
    
    plt.figure(figsize=(10, 6))
    
    for i in range(n_sims):
        # Bootstrap resampling with replacement
        sim_rets = np.random.choice(portfolio_daily_rets, size=n_days, replace=True)
        
        # Cumulative Return Path
        equity_curve = initial_capital * (1 + sim_rets).cumprod()
        
        # Metrics
        final_equity = equity_curve[-1]
        total_ret = (final_equity / initial_capital) - 1
        
        # Max Drawdown
        running_max = np.maximum.accumulate(equity_curve)
        dd = (equity_curve - running_max) / running_max
        max_dd = dd.min()
        
        sim_results.append(total_ret)
        drawdowns.append(max_dd)
        
        # Ruin Check (50% loss)
        if max_dd < -0.50:
            ruin_count += 1
            
        # Plot first 50 paths
        if i < 50:
            plt.plot(equity_curve, color='blue', alpha=0.1)
            
    # Add Baseline
    baseline = initial_capital * (1 + portfolio_daily_rets).cumprod()
    plt.plot(baseline.values, color='red', linewidth=2, label='Actual Historical')
    
    plt.title(f"Monte Carlo Simulation ({n_sims} runs)")
    plt.xlabel("Days")
    plt.ylabel("Equity")
    plt.legend()
    plt.grid(True)
    plt.savefig("reports/monte_carlo_paths.png")
    plt.close()
    
    # Analysis
    results_series = pd.Series(sim_results)
    dd_series = pd.Series(drawdowns)
    
    var_95 = np.percentile(sim_results, 5)
    dd_95 = np.percentile(drawdowns, 5) # Worst 5% drawdown
    
    prob_ruin = ruin_count / n_sims
    
    print("\n" + "="*40)
    print("MONTE CARLO RESULTS")
    print("="*40)
    print(f"Simulations: {n_sims}")
    print(f"Mean Return: {results_series.mean():.2%}")
    print(f"Median Return: {results_series.median():.2%}")
    print(f"VaR 95% (Total Ret): {var_95:.2%}")
    print(f"Worst Case Drawdown (95% Conf): {dd_95:.2%}")
    print(f"Probability of Ruin (>50% DD): {prob_ruin:.1%}")
    print("="*40)
    
    # Histogram of Returns
    plt.figure(figsize=(10, 6))
    plt.hist(results_series, bins=50, color='skyblue', edgecolor='black')
    plt.axvline(results_series.mean(), color='red', linestyle='dashed', linewidth=1, label='Mean')
    plt.title("Distribution of Simulated Returns")
    plt.legend()
    plt.savefig("reports/monte_carlo_dist.png")
    plt.close()

if __name__ == "__main__":
    run_monte_carlo()
