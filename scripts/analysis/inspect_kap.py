
import sys
import os
from datetime import datetime
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# SSL Patch
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
original_init = requests.Session.__init__
def new_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    self.verify = False
requests.Session.__init__ = new_init

try:
    from isyatirimhisse import fetch_stock_data
    print("isyatirimhisse imported successfully.")
    
    start_date = "01-01-2024"
    end_date = datetime.now().strftime('%d-%m-%Y')
    sym="AKBNK"
    
    print(f"Fetching {sym} data ({start_date} - {end_date})...")
    df = fetch_stock_data(
        symbols=[sym],
        start_date=start_date,
        end_date=end_date
    )
    
    if df is not None:
        print("\nColumns:", df.columns.tolist())
        print("\nFirst row:")
        print(df.iloc[0])
        
        if 'HGDG_HACIM_LOT' in df.columns:
            print("\nVolume Stats (HGDG_HACIM_LOT):")
            print(df['HGDG_HACIM_LOT'].describe())
        else:
            print("\nHGDG_HACIM_LOT missing")
            
        if 'HGDG_HACIM_TL' in df.columns:
            print("\nVolume TL Stats (HGDG_HACIM_TL):")
            print(df['HGDG_HACIM_TL'].describe())
        else:
            print("\nHGDG_HACIM_TL missing")
            
    else:
        print("df is None")

except ImportError:
    print("isyatirimhisse package NOT installed.")
except Exception as e:
    print(f"Error: {e}")
