
from isyatirimhisse import fetch_stock_data
import pandas as pd
from datetime import datetime

def test_kozal():
    print("KOZAL verisi İş Yatırım'dan deneniyor...")
    try:
        # Son 10 gün
        end_date = datetime.now().strftime('%d-%m-%Y')
        start_date = '01-01-2025'
        
        # Sembol: KOZAL (yfinance gibi .IS yok)
        df = fetch_stock_data(symbols=['KOZAL'], start_date=start_date, end_date=end_date)
        
        if df is not None and not df.empty:
            print("BAŞARILI! Veri alındı.")
            print(df.head())
            print(df.tail())
            print("Sütunlar:", df.columns)
            
            # Formatı yfinance formatına benzetebilir miyiz?
            # yfinance: Open, High, Low, Close, Volume
            # isyatirim: HGDG_KAPANIS (Close), HGDG_EN_DUSUK (Low), HGDG_EN_YUKSEK (High) ?
            # Kontrol edelim.
        else:
            print("Veri boş döndü.")
            
    except Exception as e:
        print(f"HATA: {e}")

if __name__ == "__main__":
    test_kozal()
