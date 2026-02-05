
import sys
import os
import pandas as pd

# Proje kök dizinini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import DataLoader
import config

def test_dataloader_kozal():
    print("DataLoader ile KOZAL verisi çekme testi...")
    
    loader = DataLoader(start_date="2025-01-01", end_date=None)
    
    # KOZAL.IS (yfinance'da yok, fallback ile isyatirim'dan gelmeli)
    ticker = "KOZAL.IS"
    
    df = loader.fetch_stock_data(ticker)
    
    if df is not None and not df.empty:
        print(f"BAŞARILI: {ticker} verisi alındı!")
        print(df.tail())
        print("Sütunlar:", df.columns)
    else:
        print(f"BAŞARISIZ: {ticker} verisi alınamadı.")

if __name__ == "__main__":
    test_dataloader_kozal()
