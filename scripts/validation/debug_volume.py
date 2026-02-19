
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_loader import DataLoader
from utils.logging_config import get_logger

log = get_logger(__name__)

def debug():
    loader = DataLoader()
    ticker = "AKBNK.IS"
    print(f"Fetching {ticker}...")
    df = loader.get_combined_data(ticker)
    
    if df is not None:
        print("\nColumns:", df.columns)
        print("\nHead:")
        print(df.head())
        print("\nTail:")
        print(df.tail())
        print("\nInfo:")
        print(df.info())
        
        if 'Volume' in df.columns:
            print("\nVolume Stats:")
            print(df['Volume'].describe())
            
            # Check calculation
            daily_vol_tl = df['Close'] * df['Volume']
            print("\nDaily Vol TL Stats:")
            print(daily_vol_tl.describe())
    else:
        print("Data is None")

if __name__ == "__main__":
    debug()
