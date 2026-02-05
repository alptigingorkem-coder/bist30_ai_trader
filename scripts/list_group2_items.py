from isyatirimhisse import fetch_financials
import pandas as pd
from datetime import datetime

symbol = 'AKBNK'
group = '2'
year = str(datetime.now().year - 2)

print(f"Fetching {symbol} Group {group} Year {year}...")
fin = fetch_financials(symbols=[symbol], start_year=year, end_year=year, financial_group=group)

if fin is not None:
    print("Columns:", fin.columns.tolist()[:5])
    items = fin['FINANCIAL_ITEM_NAME_TR'].unique().tolist()
    
    print("\n--- Searching for KAR ---")
    for i in items:
        if 'KAR' in str(i).upper() and 'NET' in str(i).upper():
            print(i)
            
    print("\n--- Searching for OZKAYNAK ---")
    for i in items:
        if 'KAYNAK' in str(i).upper():
            print(i)
