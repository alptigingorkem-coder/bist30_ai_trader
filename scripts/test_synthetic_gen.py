import sys
import os
sys.path.append(os.getcwd())
from core.augmented_feature_generator import augmented_generator
import pandas as pd

def test_gen():
    ticker = 'TEST_BANK.IS' # Banking sektöründen taklit
    # Sektör map'e manuel ekleme trick (Config'de yoksa Other alır, ama AKBNK gibi davranmasını istiyoruz)
    # Generator içindeki config.get_sector AKBNK referansı alırsa çalışır.
    # Biz direkt AKBNK verip sahte tarih üretelim en iyisi.
    
    ticker = 'AKBNK.IS'
    print(f"Generating synthetic data for {ticker} (Banking)...")
    
    # Geçmiş bir tarih (gerçek veri ile çakışmayacak)
    df_syn = augmented_generator.generate_synthetic_data(
        ticker=ticker,
        start_date="2010-01-01",
        end_date="2012-01-01"
    )
    
    print("\n--- Synthetic Data Stats ---")
    print(df_syn.describe())
    
    print("\n--- First 5 Rows ---")
    print(df_syn.head())
    
    # Basit "Grafik" (ASCII)
    print("\n--- ASCII Chart: Forward_PE ---")
    pe = df_syn['Forward_PE'].values
    min_v, max_v = pe.min(), pe.max()
    
    # Downsample for display (her 30. gün)
    for i in range(0, len(pe), 30):
        val = pe[i]
        norm = int((val - min_v) / (max_v - min_v) * 50)
        bar = '#' * norm
        print(f"{df_syn.index[i].date()}: {val:6.2f} | {bar}")

if __name__ == "__main__":
    test_gen()
