
import time
import pandas as pd
import numpy as np
import sys
import os

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.backtest.portfolio_engine import PortfolioBacktester
import config

# Simple mock config if needed
if not hasattr(config, 'MIN_LIQUIDITY_THRESHOLD'):
    config.MIN_LIQUIDITY_THRESHOLD = 20000000

def iterative_backtest_sim(prices, weights, volumes, initial_capital=10000.0, commission=0.002):
    # Iterative simulation of the core logic
    n_days, n_assets = prices.shape
    cash = initial_capital
    holdings_qty = np.zeros(n_assets)
    equity_curve = []
    
    # Pre-calc Avg Volume (Rolling) - using pandas for simplicity/speed parity baseline
    avg_vol = volumes.rolling(window=20, min_periods=1).mean().bfill()
    
    # Convert to numpy for the loop
    P = prices.values
    W = weights.values
    V = volumes.values
    AV = avg_vol.values
    
    for t in range(n_days):
        current_prices = P[t]
        target_w = W[t]
        current_av = AV[t]
        
        # 1. Equity Pre-Trade
        curr_holdings_val = np.sum(holdings_qty * current_prices)
        equity = cash + curr_holdings_val
        
        # 2. Target Qty
        target_val = equity * target_w
        target_qty = target_val / current_prices
        target_qty = np.nan_to_num(target_qty) # Handle div/0
        
        # 3. Trade Qty
        trade_qty = target_qty - holdings_qty
        
        # 4. Execute
        total_cost = 0.0
        
        # Inner loop over assets (O(N))
        for i in range(n_assets):
            qty = trade_qty[i]
            if abs(qty) > 1e-6:
                # Slippage
                inv_avg = 1.0/current_av[i] if current_av[i] > 0 else 0
                participation = abs(qty) * inv_avg
                impact = participation * 0.1
                slip = min(0.0005 + impact, 0.03)
                
                price = current_prices[i] * (1 + np.sign(qty) * slip)
                cost = qty * price
                comm = abs(cost) * commission
                
                total_cost += (cost + comm) # Subtracts from cash (cost is signed? No. Cost=Qty*Price. If Buy, Cost>0. Cash-=Cost. If Sell, Cost<0. Cash-=Cost -> Cash+=AbsCost? No.)
                # Correct Logic:
                # Buy (Qty>0): Cash -= (Qty*Price + Comm)
                # Sell (Qty<0): Cash -= (Qty*Price - Comm)? No. Cash += (AbsQty*Price - Comm)
                # Let's align with Vectorized Engine:
                # cost = qty * price (Signed)
                # comm = abs(cost) * comm_rate
                # cash_change = -cost - comm
                
                signed_cost = qty * price
                abs_cost = abs(signed_cost)
                comm_val = abs_cost * commission
                
                cash_change = -signed_cost - comm_val
                cash += cash_change
                holdings_qty[i] += qty
                
        # 5. Equity Post-Trade
        post_holdings_val = np.sum(holdings_qty * current_prices)
        equity_curve.append(cash + post_holdings_val)
        
    return equity_curve

def benchmark():
    print("🚀 Benchmarking Vectorized Engine vs Iterative Loop...")
    
    # Generate Synthetic Data (30 Assets, 1250 Days ~ 5 Years)
    n_days = 1250
    n_assets = 30
    tickers = [f"BIST_{i}" for i in range(n_assets)]
    dates = pd.date_range(start="2020-01-01", periods=n_days)
    
    print(f"Dataset: {n_assets} Assets x {n_days} Days")
    
    # Random Walk Prices
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.02, (n_days, n_assets))
    prices = pd.DataFrame(100 * np.cumprod(1 + returns, axis=0), index=dates, columns=tickers)
    
    # Random Weights (normalized)
    raw_weights = np.random.rand(n_days, n_assets)
    weights = pd.DataFrame(raw_weights / raw_weights.sum(axis=1)[:,None], index=dates, columns=tickers)
    
    # High Volumes to minimize slippage noise for parity check
    volumes = pd.DataFrame(1_000_000 + np.random.rand(n_days, n_assets)*100000, index=dates, columns=tickers)
    
    capital = 100_000.0
    
    # --- Vectorized ---
    bt = PortfolioBacktester(initial_capital=capital)
    t0 = time.time()
    res_vec = bt.run_backtest(prices, weights, volumes)
    t_vec = time.time() - t0
    final_eq_vec = res_vec['Equity'].iloc[-1]
    
    print(f"✅ Vectorized: {t_vec:.4f}s | Final Eq: {final_eq_vec:,.2f}")
    
    # --- Iterative ---
    t0 = time.time()
    eq_iter = iterative_backtest_sim(prices, weights, volumes, initial_capital=capital)
    t_iter = time.time() - t0
    final_eq_iter = eq_iter[-1]
    
    print(f"🐢 Iterative:  {t_iter:.4f}s | Final Eq: {final_eq_iter:,.2f}")
    
    # --- Stats ---
    speedup = t_iter / t_vec
    diff = abs(final_eq_vec - final_eq_iter)
    diff_pct = diff / final_eq_iter
    
    print(f"\n⚡ Speedup Factor: {speedup:.2f}x")
    print(f"⚖️ Parity Diff: {diff_pct:.4%} ({diff:,.2f} TL)")
    
    if diff_pct < 0.01:
        print("✅ PASS: Parity Confirmed (<1%)")
    else:
        print("❌ FAIL: Parity Deviation > 1%")

if __name__ == "__main__":
    benchmark()
