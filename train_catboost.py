
import pandas as pd
import numpy as np
import os
import joblib
import config
from configs import banking as config_banking
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model_catboost import CatBoostRankingModel

def ensure_model_dir():
    if not os.path.exists("models/saved"):
        os.makedirs("models/saved")

def train_catboost_ranker():
    print(f"\n{'='*50}")
    print(f"EĞİTİM BAŞLIYOR: CATBOOST GLOBAL RANKER")
    print(f"Timeframe: {config.TIMEFRAME}")
    print(f"{'='*50}")

    all_data_frames = []
    loader = DataLoader(start_date=config.START_DATE)
    tickers = config.TICKERS
    
    for ticker in tickers:
        print(f"  Veri İşleniyor: {ticker}...")
        raw_data = loader.get_combined_data(ticker)
        
        if raw_data is None or len(raw_data) < 100: continue
            
        fe = FeatureEngineer(raw_data)
        features_df = fe.process_all(ticker=ticker)
        features_df['Ticker'] = ticker
        
        if hasattr(config, 'TRAIN_END_DATE') and config.TRAIN_END_DATE:
            mask = features_df.index < config.TRAIN_END_DATE
            features_df = features_df[mask]
        
        all_data_frames.append(features_df)
        
    if not all_data_frames: return
        
    print("  Veriler birleştiriliyor...")
    full_data = pd.concat(all_data_frames)
    full_data.reset_index(inplace=True)
    full_data.set_index(['Date', 'Ticker'], inplace=True)
    full_data.sort_index(inplace=True) 
    
    print(f"  Toplam Eğitim Verisi: {len(full_data)} satır.")
    ensure_model_dir()
    
    # Train-Validation Split
    dates = full_data.index.get_level_values('Date').unique()
    split_idx = int(len(dates) * 0.9)
    test_start_date = dates[split_idx]
    
    train_mask = full_data.index.get_level_values('Date') < test_start_date
    valid_mask = full_data.index.get_level_values('Date') >= test_start_date
    
    df_train = full_data[train_mask]
    df_valid = full_data[valid_mask]
    
    print(f"  > Validasyon Başlangıç: {test_start_date}")
    
    # Instantiate CatBoost Ranker
    ranker = CatBoostRankingModel(df_train, config_banking)
    ranker.train(valid_df=df_valid)
    
    # Save (Note: CatBoost uses .cbm or .pkl + internal save)
    # Our class handles saving
    save_path = "models/saved/global_ranker_catboost.cbm"
    ranker.save(save_path)
    
    print(f"✅ CatBoost Ranker Eğitimi Tamamlandı: {save_path}")

def main():
    train_catboost_ranker()

if __name__ == "__main__":
    main()
