
import sys
import os
import time
import pandas as pd
import numpy as np

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_loader import DataLoader
from core.backtest.portfolio_engine import PortfolioBacktester
from utils.db_manager import DBManager
import config
from utils.logging_config import get_logger

log = get_logger(__name__)

def run_stress_test():
    log.info("🚀 STARTING BIST100 OPERATIONAL STRESS TEST")
    start_time_total = time.time()
    
    # 1. Configuration Load (Dynamic from SQL)
    log.info("--- Step 1: Configuration & Discovery ---")
    db = DBManager()
    active_stocks = db.get_active_tickers()
    
    # Fallback/Expand: If DB has few stocks (dev mode), lets try to use headers from JSON or config if possible
    # But strictly we should use what's in DB.
    if not active_stocks:
        log.error("CRITICAL: No active stocks found in DB. Stress test aborted.")
        return
        
    log.info(f"Target Universe: {len(active_stocks)} Assets")
    
    # 2. Data Fetching (Parallel + Integrity Check)
    log.info("--- Step 2: Data Loading (Parallel) ---")
    dl = DataLoader(start_date="2020-01-01", end_date="2024-12-31")
    
    t0 = time.time()
    # DataLoader.fetch_data_parallel is the optimized method
    # It might rely on config.TICKERS, but we can pass list explicitly if method allows
    # Looking at viewed code, fetch_data_parallel(tickers, ...) exists.
    
    data_map = dl.fetch_data_parallel(active_stocks, max_workers=10)
    
    # Validate Data
    valid_data = {}
    for ticker, df in data_map.items():
        if df is not None and not df.empty:
            valid_data[ticker] = df
            
    load_time = time.time() - t0
    log.info(f"Data Loaded: {len(valid_data)}/{len(active_stocks)} Success. Time: {load_time:.2f}s")
    
    if len(valid_data) == 0:
        log.error("CRITICAL: No valid data loaded.")
        return

    # 3. Align Data for Vectorized Engine
    log.info("--- Step 3: Vector Alignment ---")
    t0 = time.time()
    
    # Create Panel Data
    prices = pd.DataFrame({t: df['Close'] for t, df in valid_data.items()}).astype('float64')
    volumes = pd.DataFrame({t: df['Volume'] for t, df in valid_data.items()}).astype('float64')
    
    # Forward Fill / Dropna
    prices.ffill(inplace=True)
    prices.bfill(inplace=True)
    volumes.fillna(0, inplace=True)
    
    # Generate Mock Signals (Equal Weight Rebalancing Monthly)
    # In production this comes from Model -> FeatureStore
    log.info("Generating Mock Signals (Equal Weight Risk Parity simulation)...")
    signals = pd.DataFrame(index=prices.index, columns=prices.columns).astype('float64')
    
    # Rebalance Monthly
    signals[:] = 0.0
    monthly_steps = prices.resample('ME').last().index
    
    for date in monthly_steps:
        if date in signals.index:
            # Simple Equal Weight
            valid_assets = prices.loc[date] > 0
            n = valid_assets.sum()
            if n > 0:
                signals.loc[date, valid_assets] = 1.0 / n
                
    # Forward fill weights (Hold until rebalance)
    signals.ffill(inplace=True)
    
    align_time = time.time() - t0
    log.info(f"Alignment Complete. Matrix Shape: {prices.shape}. Time: {align_time:.2f}s")
    
    # 4. Execution (Vectorized Engine)
    log.info("--- Step 4: Vectorized Execution (O(1)) ---")
    engine = PortfolioBacktester(initial_capital=100_000.0)
    
    t0 = time.time()
    results = engine.run_backtest(prices, signals, volumes)
    exec_time = time.time() - t0
    
    # 5. Reporting
    log.info("--- Step 5: Results & Performance ---")
    
    final_equity = results['Equity'].iloc[-1]
    ret = (final_equity - 100_000) / 100_000
    dd = results['Drawdown'].min()
    
    total_duration = time.time() - start_time_total
    
    report = f"""
    =============================================
    ✅ STRESS TEST COMPLETED SUCCESSFULLY
    =============================================
    Performance Metrics:
    --------------------
    Total Assets Loaded : {len(valid_data)}
    Simulation Period   : {prices.index[0].date()} -> {prices.index[-1].date()} ({len(prices)} days)
    
    Speed:
    - Data Loading      : {load_time:.2f}s
    - Matrix Alignment  : {align_time:.2f}s
    - Engine Execution  : {exec_time:.4f}s
    - Total Pipeline    : {total_duration:.2f}s
    
    Financial Result (Mock Strategy):
    - Initial Capital   : 100,000 TL
    - Final Equity      : {final_equity:,.2f} TL
    - Total Return      : {ret:.2%}
    - Max Drawdown      : {dd:.2%}
    =============================================
    """
    
    print(report)
    log.info("Test Complete.")

if __name__ == "__main__":
    run_stress_test()
