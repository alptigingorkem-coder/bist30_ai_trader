
import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from utils.data_loader import DataLoader

def check_dates():
    print("Veri tarih aralıkları kontrol ediliyor...")
    loader = DataLoader(start_date="2010-01-01") # Mümkün olduğunca eski iste
    
    results = []
    
    for ticker in config.TICKERS:
        try:
            # Sadece stock data çek, makro ile birleştirme (saf veri tarihi için)
            df = loader.fetch_stock_data(ticker)
            if df is not None and not df.empty:
                start_date = df.index.min().strftime('%Y-%m-%d')
                end_date = df.index.max().strftime('%Y-%m-%d')
                count = len(df)
                results.append({
                    'Ticker': ticker,
                    'Start': start_date,
                    'End': end_date,
                    'Rows': count
                })
                print(f"{ticker}: {start_date} -> {end_date} ({count} gün)")
            else:
                print(f"{ticker}: Veri YOK")
        except Exception as e:
            print(f"{ticker}: Hata - {e}")

    if results:
        df_res = pd.DataFrame(results)
        print("\n--- ÖZET ---")
        print(df_res.sort_values('Start'))
        
        # En ortak başlangıç tarihini bul (örneğin %80'inin verisi olduğu tarih)
        most_common_start = df_res['Start'].mode()[0] if not df_res.empty else "N/A"
        earliest = df_res['Start'].min()
        latest_start = df_res['Start'].max()
        
        print(f"\nEn Erken Veri: {earliest}")
        print(f"En Geç Başlangıç: {latest_start}")
        print(f"En Yaygın Başlangıç: {most_common_start}")

if __name__ == "__main__":
    check_dates()
