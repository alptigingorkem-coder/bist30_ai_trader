import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import yfinance as yf
from data_loader import DataLoader
import config

def verify_lag():
    print("Makro Veri Lag Kontrolü Başlıyor...\n")
    loader = DataLoader(start_date="2023-12-01", end_date="2024-01-10")
    
    # Kendi internal methoduyla çekilen veriyi al (Lag uygulanmış hali)
    print("1. Loader üzerinden veri çekiliyor (Shift uygulanmalı)...")
    macro_data_shifted = loader.fetch_macro_data()
    vix_shifted = macro_data_shifted['VIX']
    
    # Ham veriyi yfinance ile çek (Referans - Shift uygulanmamış)
    print("\n2. Yfinance ile ham veri çekiliyor (Referans)...")
    vix_raw = yf.download("^VIX", start="2023-12-01", end="2024-01-10", progress=False)
    if isinstance(vix_raw.columns, pd.MultiIndex):
        vix_raw.columns = vix_raw.columns.droplevel(1)
    
    # Karşılaştırma
    print("\n3. Karşılaştırma (Tarih bazlı):")
    
    # Ortak tarihler
    common_dates = vix_shifted.index.intersection(vix_raw.index)
    
    test_passed = True
    for date in common_dates[5:10]: # Rastgele 5 gün kontrol et
        date_str = date.strftime('%Y-%m-%d')
        val_shifted = vix_shifted.loc[date]
        
        # Shifted verideki bugünün değeri, Raw verideki DÜNÜN değeri olmalı
        # Raw veride dünü bulmak için indexte geri gitmeliyiz
        loc_idx = vix_raw.index.get_loc(date)
        if loc_idx > 0:
            val_raw_prev = vix_raw['Close'].iloc[loc_idx - 1]
            
            diff = abs(val_shifted - val_raw_prev)
            is_match = diff < 0.0001
            
            print(f"Tarih: {date_str} | Shifted: {val_shifted:.4f} | Raw (Dün): {val_raw_prev:.4f} | Eşleşme: {'OK' if is_match else 'HATA'}")
            
            if not is_match:
                test_passed = False
    
    if test_passed:
        print("\nSONUÇ: BAŞARILI. Veriler 1 gün gecikmeli geliyor.")
    else:
        print("\nSONUÇ: HATA VAR. Veriler eşleşmedi.")

if __name__ == "__main__":
    verify_lag()
