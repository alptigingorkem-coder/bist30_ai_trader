
import pandas as pd
import numpy as np
import os
import joblib

# Konfigürasyonlar
import config
from configs import banking as config_banking

# Araçlar
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel

def ensure_model_dir():
    if not os.path.exists("models/saved"):
        os.makedirs("models/saved")

def train_global_ranker():
    print(f"\n{'='*50}")
    print(f"EĞİTİM BAŞLIYOR: GLOBAL DAILY RANKER")
    print(f"Timeframe: {config.TIMEFRAME}")
    print(f"Strict Mode: Veri kesim tarihi {config.TRAIN_END_DATE}")
    print(f"{'='*50}")

    all_data_frames = []
    loader = DataLoader(start_date=config.START_DATE)
    
    # Tüm Tickerlar (config.TICKERS - A1 Core)
    tickers = config.TICKERS
    
    for ticker in tickers:
        print(f"  Veri İşleniyor: {ticker}...")
        raw_data = loader.get_combined_data(ticker)
        
        if raw_data is None or len(raw_data) < 100:
            print(f"  [UYARI] Yetersiz veri: {ticker}")
            continue
            
        # Feature Engineering (Daily Logic will apply due to config change)
        fe = FeatureEngineer(raw_data)
        features_df = fe.process_all(ticker=ticker)
        
        # Add Ticker Column (Multi-Index için gerekli olabilir ama RankingModel level='Date' kullanıyor)
        features_df['Ticker'] = ticker
        
        # Validation Split (Tarihsel)
        if hasattr(config, 'TRAIN_END_DATE') and config.TRAIN_END_DATE:
            mask = features_df.index < config.TRAIN_END_DATE
            features_df = features_df[mask]
        
        all_data_frames.append(features_df)
        
    if not all_data_frames:
        print(f"❌ Hiç veri bulunamadı.")
        return
        
    # Combine All
    print("  Veriler birleştiriliyor...")
    full_data = pd.concat(all_data_frames)
    
    # Multi-Index (Date, Ticker) set et
    full_data.reset_index(inplace=True)
    full_data.set_index(['Date', 'Ticker'], inplace=True)
    full_data.sort_index(inplace=True) 
    
    print(f"  Toplam Eğitim Verisi: {len(full_data)} satır.")
    
    ensure_model_dir()
    
    # --- RANKING MODEL EĞİTİMİ ---
    print(f"  > Ranking Model Eğitiliyor...")
    
    # Config modülü olarak banking veriyoruz (Generic bir config yeterli)
    model = RankingModel(full_data, config_banking) 
    
    # Train-Validation Split (Son %10 validation)
    # Time-based split manually
    dates = full_data.index.get_level_values('Date').unique()
    split_idx = int(len(dates) * 0.9)
    test_start_date = dates[split_idx]
    
    print(f"  > Validasyon Başlangıç: {test_start_date}")
    
    # Split
    # Not: Bu çok basit bir split, RankingModel içinde de yapılabilirdi ama burada kontrol bizde.
    # RankingModel.prepare_data dropna yapıyor, o yüzden önce split edip sonra modele vermek daha güvenli.
    
    # Ancak RankingModel training ve validation df'ini ayrı ayrı alacak
    # O yüzden basitçe model.train e full data verip, içerde bölmesini veya
    # direkt ayrı df vermeyi tercih edelim.
    # RankingModel.train(valid_df=...) parametresi eklemiştik.
    
    # Dataframe split
    train_mask = full_data.index.get_level_values('Date') < test_start_date
    valid_mask = full_data.index.get_level_values('Date') >= test_start_date
    
    df_train = full_data[train_mask]
    df_valid = full_data[valid_mask]
    
    # Instantiate with Train
    ranker = RankingModel(df_train, config_banking)
    
    # Check for optimized params in config
    custom_params = getattr(config, 'OPTIMIZED_MODEL_PARAMS', None)
    if custom_params:
        print(f"  > Optimize Edilmiş Hiperparametreler Kullanılıyor: {custom_params}")
    
    ranker.train(valid_df=df_valid, custom_params=custom_params)
    
    ranker.save(f"models/saved/global_ranker.pkl")
    
    print(f"✅ Global Ranker Eğitimi Tamamlandı.")

def main():
    train_global_ranker()

if __name__ == "__main__":
    main()
