
import pandas as pd
import numpy as np
import os
import joblib

# Konfigürasyonlar
import config
from configs import banking as config_banking
from configs import holding as config_holding
from configs import industrial as config_industrial
from configs import growth as config_growth

# Araçlar
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.regime_detection import RegimeDetector
from models.beta_model import BetaModel
from models.alpha_model import AlphaModel

def ensure_model_dir():
    if not os.path.exists("models/saved"):
        os.makedirs("models/saved")

def train_sector_models(sector_name, sector_config, tickers):
    print(f"\n{'='*50}")
    print(f"EĞİTİM BAŞLIYOR: {sector_name}")
    print(f"Hisseler: {tickers}")
    print(f"{'='*50}")

    # Tüm sektör verisini topla (Tek bir büyük DataFrame eğitim için daha iyi olabilir 
    # veya her hisse için ayrı ayrı eğitip ortalama model kullanabiliriz.
    # LightGBM genelleştirme yeteneği yüksektir, tüm sektör datası havuz yapılabilir.)
    
    all_data_frames = []
    
    loader = DataLoader(start_date="2018-01-01") # Eğitim için yeterli geçmiş
    
    for ticker in tickers:
        print(f"  Veri indiriliyor: {ticker}...")
        raw_data = loader.get_combined_data(ticker)
        
        if raw_data is None or len(raw_data) < 100:
            print(f"  [UYARI] Yetersiz veri: {ticker}")
            continue
            
        # Feature Engineering
        fe = FeatureEngineer(raw_data)
        features_df = fe.process_all(ticker=ticker)
        
        # Regime Detection
        rd = RegimeDetector(features_df)
        features_df = rd.detect_regimes()
        
        # Hisseleri Index'te tut veya column olarak ekle (Panel Data mantığı için)
        # Şimdilik basitçe üst üste ekliyoruz, feature'lar normalize olduğu sürece sorun yok.
        all_data_frames.append(features_df)
        
    if not all_data_frames:
        print(f"❌ {sector_name} için hiç veri bulunamadı.")
        return
        
    full_sector_data = pd.concat(all_data_frames)
    print(f"  Toplam Eğitim Verisi: {len(full_sector_data)} satır.")
    
    ensure_model_dir()
    
    # --- BETA MODEL EĞİTİMİ ---
    print(f"  > Beta Model Eğitiliyor...")
    beta_model = BetaModel(full_sector_data, sector_config)
    beta_model.optimize_and_train(n_trials=50) # Robust optimization
    beta_model.save(f"models/saved/{sector_name.lower()}_beta.pkl")
    
    # --- ALPHA MODEL EĞİTİMİ ---
    print(f"  > Alpha Model Eğitiliyor...")
    alpha_model = AlphaModel(full_sector_data, sector_config)
    alpha_model.optimize_and_train(n_trials=50)
    alpha_model.save(f"models/saved/{sector_name.lower()}_alpha.pkl")
    
    print(f"✅ {sector_name} Eğitimi Tamamlandı.")

def main():
    # 1. Banking
    train_sector_models("BANKING", config_banking, config_banking.TICKERS)
    
    # 2. Holding
    train_sector_models("HOLDING", config_holding, config_holding.TICKERS)
    
    # 3. Industrial
    train_sector_models("INDUSTRIAL", config_industrial, config_industrial.TICKERS)
    
    # 4. Growth
    train_sector_models("GROWTH", config_growth, config_growth.TICKERS)
    
    print("\n🎉 TÜM MODELLER EĞİTİLDİ VE KAYDEDİLDİ.")

if __name__ == "__main__":
    main()
