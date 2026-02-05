
from isyatirimhisse import fetch_stock_data
import pandas as pd
from datetime import datetime

def test_symbols():
    symbols = ['TRALT', 'KOZAA', 'KOZAL']
    print(f"Semboller test ediliyor: {symbols}")
    
    end_date = datetime.now().strftime('%d-%m-%Y')
    start_date = '01-01-2025'
    
    for sym in symbols:
        print(f"\n--- Testing {sym} ---")
        try:
            df = fetch_stock_data(symbols=[sym], start_date=start_date, end_date=end_date)
            if df is not None and not df.empty:
                print(f"BAŞARILI: {sym}")
                print(df.tail(2))
            else:
                print(f"BAŞARISIZ: {sym} (Veri yok)")
        except Exception as e:
            print(f"HATA {sym}: {e}")

if __name__ == "__main__":
    test_symbols()
