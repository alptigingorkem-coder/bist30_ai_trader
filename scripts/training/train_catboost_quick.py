"""
CatBoost Quick Training - Sadece 5 hisse ile hızlı test
"""
import pandas as pd
import numpy as np
import os
import sys
import joblib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config
from configs import banking as config_banking
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model_catboost import CatBoostRankingModel

def train_catboost_quick():
    print(f"\n{'='*50}")
    print(f"HIZLI TEST: CATBOOST (5 Hisse)")
    print(f"{'='*50}")

    # Sadece 5 hisse
    test_tickers = ['AKBNK.IS', 'GARAN.IS', 'YKBNK.IS', 'TSKB.IS', 'EREGL.IS']
    
    all_data_frames = []
    loader = DataLoader(start_date="2022-01-01")  # Daha kısa dönem
    
    for ticker in test_tickers:
        print(f"  Veri İşleniyor: {ticker}...")
        raw_data = loader.get_combined_data(ticker)
        
        if raw_data is None or len(raw_data) < 100: 
            continue
            
        fe = FeatureEngineer(raw_data)
        features_df = fe.process_all(ticker=ticker)
        features_df['Ticker'] = ticker
        
        # Train split
        if hasattr(config, 'TRAIN_END_DATE') and config.TRAIN_END_DATE:
            mask = features_df.index < config.TRAIN_END_DATE
            features_df = features_df[mask]
        
        all_data_frames.append(features_df)
        
    if not all_data_frames: 
        print("Veri yok!")
        return
        
    print("  Veriler birleştiriliyor...")
    full_data = pd.concat(all_data_frames)
    full_data.reset_index(inplace=True)
    full_data.set_index(['Date', 'Ticker'], inplace=True)
    full_data.sort_index(inplace=True) 
    
    print(f"  Toplam Veri: {len(full_data)} satır.")
    
    # Train-Val Split
    dates = full_data.index.get_level_values('Date').unique()
    split_idx = int(len(dates) * 0.9)
    test_start_date = dates[split_idx]
    
    train_mask = full_data.index.get_level_values('Date') < test_start_date
    valid_mask = full_data.index.get_level_values('Date') >= test_start_date
    
    df_train = full_data[train_mask]
    df_valid = full_data[valid_mask]
    
    print(f"  > Train: {len(df_train)}, Val: {len(df_valid)}")
    
    # Train
    ranker = CatBoostRankingModel(config=config_banking)
    ranker.train(df_train, valid_df=df_valid)
    
    # Save
    os.makedirs("models/saved", exist_ok=True)
    save_path = "models/saved/global_ranker_catboost.cbm"
    ranker.save(save_path)
    
    print(f"\n✅ Model kaydedildi: {save_path}")

if __name__ == "__main__":
    train_catboost_quick()
