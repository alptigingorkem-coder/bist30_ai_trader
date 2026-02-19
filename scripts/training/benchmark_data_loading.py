
import sys
import os
import time
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config
from utils.data_loader import DataLoader
from utils.logging_config import get_logger

log = get_logger(__name__)

def benchmark():
    print("="*60)
    print("🚀 BENCHMARK: Data Loader (Sequential vs Parallel)")
    print("="*60)
    
    loader = DataLoader()
    tickers = config.TICKERS[:10] # Test with first 10 for speed
    print(f"Testing with {len(tickers)} tickers: {tickers}")
    
    # 1. Sequential Benchmark
    print("\n1️⃣  Running Sequential Load...")
    start_seq = time.time()
    seq_results = {}
    for t in tickers:
        df = loader.get_combined_data(t)
        if df is not None: seq_results[t] = df
    time_seq = time.time() - start_seq
    print(f"   ⏱️  Sequential Time: {time_seq:.2f} seconds")
    
    # 2. Parallel Benchmark
    print("\n2️⃣  Running Parallel Load...")
    start_par = time.time()
    par_results = loader.fetch_data_parallel(tickers, max_workers=5)
    time_par = time.time() - start_par
    print(f"   ⏱️  Parallel Time:   {time_par:.2f} seconds")
    
    # Results
    speedup = time_seq / time_par if time_par > 0 else 0
    print("\n📊 RESULTS:")
    print(f"   Speedup Factor: {speedup:.2f}x")
    if speedup > 1.5:
        print("   ✅ SUCCESS: Parallel loading is significantly faster.")
    else:
        print("   ⚠️ NOTE: Speedup < 1.5x. (Maybe data is cached/local or overhead is high for small N)")
        
    # Liquidity Check Report
    print("\n💧 LIQUIDITY CHECK (Sample):")
    for t, df in par_results.items():
        if df is not None and not df.empty:
            vol = (df['Close'] * df['Volume']).mean()
            print(f"   {t:<10}: Avg Daily Vol {vol:,.0f} TL")
            
if __name__ == "__main__":
    benchmark()
