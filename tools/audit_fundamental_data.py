import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import config

try:
    df = pd.read_excel("data/fundamental_data.xlsx")
    print("Columns:", df.columns.tolist())
    print("Tickers in file:", df['Ticker'].unique().tolist())
    
    missing = [t for t in config.TICKERS if t not in df['Ticker'].unique()]
    print(f"MISSING_TICKERS_START")
    print(missing)
    print(f"MISSING_TICKERS_END")
    
except Exception as e:
    print(f"Error reading excel: {e}")
