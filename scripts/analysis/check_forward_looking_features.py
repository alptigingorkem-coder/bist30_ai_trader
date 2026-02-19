
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
import config

def check_forward_looking_features():
    """
    Feature'ların gelecek verisi içerip içermediğini kontrol et.
    """
    
    print("="*70)
    print("FORWARD-LOOKING FEATURE KONTROLÜ")
    print("="*70)
    
    # Veri yükle
    print("\n📥 Veri yükleniyor (Örnek Ticker: AKBNK.IS)...")
    loader = DataLoader()
    ticker = "AKBNK.IS"
    
    # Load ample history around test date
    start_date = "2024-01-01"
    end_date = "2024-08-01"
    
    try:
        data = loader.fetch_stock_data(ticker)
        if data is None or data.empty:
            print("❌ Veri yüklenemedi!")
            return
            
        # Filter range
        data = data[(data.index >= start_date) & (data.index <= end_date)]
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return
    
    # Feature engineering (1 gün için)
    # fe = FeatureEngineer() removed, instantiated later per data chunk
    # Ensure date exists
    if len(data) < 50:
        print("❌ Veri çok az!")
        return
        
    test_date_idx = len(data) // 2
    test_date = data.index[test_date_idx]
    
    print(f"\n🔍 Test Tarihi: {test_date.date()}")
    print(f"   Bu tarihte hesaplanan feature'lar SADECE")
    print(f"   {test_date.date()} ve ÖNCESİ verileri kullanmalı!")
    
    # Sadece test tarihine kadar olan veriyi ver
    # IMPORTANT: We must pass data ONLY up to test_date
    data_until_test = data[data.index <= test_date].copy()
    
    # Feature'ları hesapla (Senaryo 1: Gelecek Yok)
    # We need to process this chunk. 
    # NOTE: Some features (SMA 200) need history. data_until_test has history up to test_date.
    print("   Senaryo 1: Geçmiş verilerle hesaplama...")
    fe1 = FeatureEngineer(data_until_test)
    features_test = fe1.process_all(ticker=ticker)
    
    # Test tarihindeki feature'ları al
    # Standardize column names if needed
    if isinstance(features_test.columns, pd.MultiIndex):
        pass # Handle if needed
        
    try:
        features_on_test_date = features_test.loc[test_date]
        # Handle if multiple rows (rare for one ticker)
        if isinstance(features_on_test_date, pd.DataFrame):
            features_on_test_date = features_on_test_date.iloc[0]
    except KeyError:
        print(f"❌ Test tarihi {test_date} sonuçta bulunamadı!")
        return
    
    # Şimdi GELECEKTEKİ veriyi de ekleyerek tekrar hesapla
    future_date = data.index[test_date_idx + 5] # 5 gün sonra
    data_with_future = data[data.index <= future_date].copy()
    
    print(f"   Senaryo 2: Gelecek verisi ({future_date.date()}) dahil edilerek hesaplama...")
    fe2 = FeatureEngineer(data_with_future)
    features_with_future = fe2.process_all(ticker=ticker)
    
    # Aynı test tarihindeki feature'ları al
    try:
        features_on_test_date_v2 = features_with_future.loc[test_date]
        if isinstance(features_on_test_date_v2, pd.DataFrame):
            features_on_test_date_v2 = features_on_test_date_v2.iloc[0]
    except KeyError:
        print(f"❌ Test tarihi {test_date} 2. senaryoda bulunamadı!")
        return
    
    # KARŞILAŞTIR: Feature değerleri değişti mi?
    print("\n📊 Feature Karşılaştırması:")
    
    # Tüm feature'lar için karşılaştır
    # Ignore 'NextReturn', 'Target' which might explicitly use future
    # Also ignore config.LEAKAGE_COLS as they are known/excluded by model
    ignore_cols = ['Target', 'NextDay_Return', 'NextReturn', 'future', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
    if hasattr(config, 'LEAKAGE_COLS'):
        ignore_cols.extend(config.LEAKAGE_COLS)
    
    feature_cols = []
    for col in features_on_test_date.index:
        if col in ignore_cols: continue
        if col.startswith('NextDay') or col.startswith('Excess_Return'): continue
        if col.startswith('future_'): continue
        feature_cols.append(col)
    
    changed_features = []
    
    for col in feature_cols:
        val1 = features_on_test_date[col]
        val2 = features_on_test_date_v2[col]
        
        # Check types
        if isinstance(val1, (int, float, np.number)) and isinstance(val2, (int, float, np.number)):
            if pd.isna(val1) and pd.isna(val2):
                continue
            if pd.isna(val1) or pd.isna(val2):
                changed_features.append((col, 9999)) # One is NaN
                continue
                
            diff = abs(val1 - val2)
            if diff > 1e-6:
                changed_features.append((col, diff))
        else:
            # Categorical/Object
            if str(val1) != str(val2):
                changed_features.append((col, -1))

    if len(changed_features) > 0:
        print("🔴 UYARI: Gelecek verisi eklenince değişen feature'lar bulundu!")
        print("   Bu feature'lar gelecek verisi kullanıyor (LEAKAGE):")
        print()
        
        # Sort by diff
        # Handle non-numeric diffs
        numeric_diffs = [x for x in changed_features if x[1] != -1]
        non_numeric = [x for x in changed_features if x[1] == -1]
        
        numeric_diffs.sort(key=lambda x: x[1], reverse=True)
        
        for feat, diff in numeric_diffs[:10]:
            print(f"   - {feat:30s}: Diff = {diff:.6f}")
        for feat, _ in non_numeric[:5]:
            print(f"   - {feat:30s}: Changed (Object/String)")
        
        print(f"\n   Toplam {len(changed_features)} feature değişti.")
        return True
    else:
        print("✅ İyi: Hiçbir feature gelecek verisi kullanmıyor.")
        print("   Tüm feature'lar sadece geçmiş verilere dayanıyor.")
        return False

if __name__ == "__main__":
    has_leakage = check_forward_looking_features()
    
    if has_leakage is True:
        print("\n⚠️  FORWARD-LOOKING FEATURE TESPİT EDİLDİ!")
    elif has_leakage is False:
        print("\n✅ Forward-looking feature testi geçildi!")
    else:
        print("\n❌ Test tamamlanamadı (Veri hatası vb).")
