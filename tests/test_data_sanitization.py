
import sys
import os
import pandas as pd

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_loader import DataLoader
from utils.logging_config import get_logger

log = get_logger(__name__)

def test_sanitization():
    print("Testing Data Sanitization...")
    loader = DataLoader()
    
    # Test with a major ticker
    ticker = "THYAO.IS"
    print(f"Fetching {ticker}...")
    df = loader.fetch_stock_data(ticker)
    
    if df is not None:
        print(f"✅ Data fetched for {ticker}. Shape: {df.shape}")
        
        # Verify no zero volume
        zero_vol = df[df['Volume'] <= 0]
        if not zero_vol.empty:
            print(f"❌ FAILED: Found {len(zero_vol)} rows with zero volume!")
        else:
            print("✅ PASSED: No zero volume rows.")
            
        # Verify no outliers (approx check)
        # We can't know for sure if original had outliers without saving it before sanitization,
        # but we can check if current data respects limits.
        margin = df['High'] / df['Low']
        outliers = margin > 1.25
        if outliers.any():
            print(f"❌ FAILED: Found {outliers.sum()} rows with Margin > 1.25!")
        else:
            print("✅ PASSED: All rows respect price margin limits.")
            
    else:
        print("❌ FAILED: No data fetched.")

if __name__ == "__main__":
    test_sanitization()
