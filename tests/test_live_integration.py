
import sys
import os
import pandas as pd

# Proje kök dizinini path'e ekle
sys.path.append(os.getcwd())

from core.live_data_engine import live_engine
import config

print("="*50)
print("🧪 CANLI VERİ ENTEGRASYON TESTİ")
print("="*50)

tickers = config.TICKERS[:3] # İlk 3 hisseyi test et (örnek)
print(f"Test edilecek hisseler: {tickers}")

try:
    print("\n[1] Veri çekiliyor...")
    data, source = live_engine.fetch_live_data(tickers)
    
    print(f"\n[2] Sonuç (Kaynak: {source}):")
    
    if isinstance(data, dict):
        for t in tickers:
            if t in data and not data[t].empty:
                last_price = data[t]['Close'].iloc[-1]
                last_date = data[t].index[-1]
                print(f"   ✅ {t:<10}: {last_price:.2f} TL (Tarih: {last_date})")
            else:
                print(f"   ❌ {t:<10}: Veri YOK!")
    else:
        print("   ❌ Beklenmedik veri formatı!")

except Exception as e:
    print(f"\n❌ TEST BAŞARISIZ! Hata: {e}")

print("\n"+"="*50)
