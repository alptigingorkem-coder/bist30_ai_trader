
import sys
import os
import pandas as pd

# Add project root to path
# Add project root to path
# scripts/utility -> ../../ -> project_root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from utils.data_loader import DataLoader
from utils.logging_config import get_logger
import config

log = get_logger(__name__)

def test_macro_fetch():
    print("="*50)
    print("TEST: MACRO DATA FETCHING")
    print(f"Enable Macro Config: {config.ENABLE_MACRO_IN_MODEL}")
    print("="*50)
    
    loader = DataLoader(start_date="2024-01-01", end_date="2024-02-01")
    
    # 1. Fetch Raw Macro Data
    print("\n1. Fetching Macro Data...")
    macro_df = loader.fetch_macro_data()
    
    if macro_df is None or macro_df.empty:
        print("❌ Macro data is empty!")
        return
        
    print(f"✅ Macro Data Fetched: {len(macro_df)} rows")
    print("Columns:", macro_df.columns.tolist())
    print("\nHead:\n", macro_df.head())
    
    # 2. Fetch Combined Data (Stock + Macro)
    ticker = "THYAO.IS"
    print(f"\n2. Fetching Combined Data for {ticker}...")
    combined_df = loader.get_combined_data(ticker)
    
    if combined_df is None or combined_df.empty:
        print(f"❌ Combined data for {ticker} is empty!")
        return
        
    print(f"✅ Combined Data Fetched: {len(combined_df)} rows")
    print("Columns:", combined_df.columns.tolist())
    
    # Check if macro columns exist in combined
    missing_macros = [col for col in macro_df.columns if col not in combined_df.columns]
    if missing_macros:
         print(f"⚠️ Missing macro columns in combined df: {missing_macros}")
    else:
         print("✅ All macro columns present in combined df.")

    # Check for NaNs in macro columns
    for col in macro_df.columns:
        if col in combined_df.columns:
            nan_count = combined_df[col].isna().sum()
            print(f"   - {col}: {nan_count} NaNs")

if __name__ == "__main__":
    test_macro_fetch()
