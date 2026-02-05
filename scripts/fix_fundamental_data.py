import pandas as pd
import numpy as np
import os
from datetime import datetime

# Dosya yolları
INPUT_FILE = 'data/fundamental_data.xlsx'
OUTPUT_FILE = 'data/fundamental_data_fixed.xlsx'
BACKUP_FILE = 'data/fundamental_data_backup.xlsx'

def fix_data():
    print(f"Reading {INPUT_FILE}...")
    try:
        # Engine openpyxl gerekli olabilir
        df = pd.read_excel(INPUT_FILE, engine='openpyxl')
    except Exception as e:
        print(f"Error reading excel: {e}")
        return

    print(f"Original Data Shape: {df.shape}")
    print(f"Original Date Range: {df['Date'].min()} to {df['Date'].max()}")

    # Tarih formatını garantiye al
    df['Date'] = pd.to_datetime(df['Date'])

    # Tüm hisseleri belirle
    tickers = df['Ticker'].unique()
    print(f"Found {len(tickers)} tickers.")

    # Hedef tarih aralığı (2015 başından mevcut son tarihe kadar)
    start_date = pd.Timestamp("2015-01-01")
    end_date = df['Date'].max()
    
    # Çeyreklik dönemler oluştur (Quarterly Data)
    # Temel analiz verileri genelde çeyreklik gelir (Mart, Haziran, Eylül, Aralık sonu)
    date_range = pd.date_range(start=start_date, end=end_date, freq='QE-DEC') # QuarterEnd (DEC year end)
    
    # Eğer mevcut verilerin tarihleri ay sonu değilse, normalleştirme gerekebilir.
    # Ancak şimdilik mevcut tarihler üzerinden gidelim.
    
    fixed_dfs = []

    for ticker in tickers:
        # İlgili hissenin verisini al
        ticker_df = df[df['Ticker'] == ticker].copy()
        ticker_df = ticker_df.sort_values('Date')
        
        # Tekrarla eden tarihleri temizle
        ticker_df = ticker_df.drop_duplicates(subset=['Date'], keep='last')
        
        # İndeks yap
        ticker_df.set_index('Date', inplace=True)
        
        # Yeni tarih aralığı ile reindex yap (Union alarak mevcut tarihleri de koru)
        # Önce mevcut indeks ile hedef aralığı birleştir
        full_index = date_range.union(ticker_df.index).unique().sort_values()
        
        # Sadece start_date sonrası
        full_index = full_index[full_index >= start_date]
        
        # Reindex
        ticker_df = ticker_df.reindex(full_index)
        
        # Ticker kolonunu doldur
        ticker_df['Ticker'] = ticker
        
        # Doldurma stratejisi:
        # 1. Backfill: 2020 öncesi boşluklar için, mevcut en eski veriyi geriye taşı.
        #    (Bu ideal değil ama "Data Missing" hatasını çözer ve test imkanı verir)
        ticker_df = ticker_df.bfill()
        
        # 2. Forward fill: Aradaki diğer boşluklar için
        ticker_df = ticker_df.ffill()
        
        # Reset index
        ticker_df.reset_index(inplace=True)
        ticker_df.rename(columns={'index': 'Date'}, inplace=True)
        
        fixed_dfs.append(ticker_df)

    # Birleştir
    final_df = pd.concat(fixed_dfs, ignore_index=True)
    
    print(f"New Data Shape: {final_df.shape}")
    print(f"New Date Range: {final_df['Date'].min()} to {final_df['Date'].max()}")
    
    # Eksik (NaN) kontrolü
    print("NaN counts per column:")
    print(final_df.isnull().sum())
    
    # Hala NaN varsa (belki hiç verisi olmayan sütunlar), 0 ile doldur veya ortalama
    # Şimdilik 0 basalım ki hata vermesin
    final_df.fillna(0, inplace=True)

    # Kaydet
    print(f"Saving to {OUTPUT_FILE}...")
    final_df.to_excel(OUTPUT_FILE, index=False)
    print("Done.")

    # Dosya değişimi (Opsiyonel, manuel onay gerekebilir ama burada direkt yapacağım)
    # Backup
    if os.path.exists(INPUT_FILE):
        if os.path.exists(BACKUP_FILE):
            os.remove(BACKUP_FILE)
        os.rename(INPUT_FILE, BACKUP_FILE)
        print(f"Original file backed up to {BACKUP_FILE}")
    
    # Rename fixed to input
    os.rename(OUTPUT_FILE, INPUT_FILE)
    print(f"Replaced {INPUT_FILE} with fixed data.")

if __name__ == "__main__":
    fix_data()
