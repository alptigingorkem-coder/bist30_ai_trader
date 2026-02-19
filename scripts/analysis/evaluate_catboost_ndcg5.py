"""
CatBoost modelini değerlendirip NDCG@5 skorunu hesapla
"""
import pandas as pd
import numpy as np
import os
import sys
from sklearn.metrics import ndcg_score

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config
from configs import banking as config_banking
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model_catboost import CatBoostRankingModel

def evaluate_catboost_ndcg5():
    """CatBoost modelini yükle ve NDCG@5 skorunu hesapla"""
    print("\n" + "="*60)
    print("🐱 CatBoost NDCG@5 Değerlendirmesi")
    print("="*60)
    
    # Model yükle
    model_path = "models/saved/global_ranker_catboost.cbm"
    if not os.path.exists(model_path):
        print(f"❌ Model bulunamadı: {model_path}")
        return None
    
    print(f"\n✅ Model yükleniyor: {model_path}")
    ranker = CatBoostRankingModel.load(model_path, config=config_banking)
    
    # Test verisi hazırla (validation split)
    print("\n📊 Test verisi hazırlanıyor...")
    all_data_frames = []
    loader = DataLoader(start_date=config.START_DATE)
    tickers = config.TICKERS
    
    for ticker in tickers:
        raw_data = loader.get_combined_data(ticker)
        if raw_data is None or len(raw_data) < 100:
            continue
            
        fe = FeatureEngineer(raw_data)
        features_df = fe.process_all(ticker=ticker)
        features_df['Ticker'] = ticker
        
        if hasattr(config, 'TRAIN_END_DATE') and config.TRAIN_END_DATE:
            mask = features_df.index < config.TRAIN_END_DATE
            features_df = features_df[mask]
        
        all_data_frames.append(features_df)
    
    if not all_data_frames:
        print("❌ Veri bulunamadı!")
        return None
    
    full_data = pd.concat(all_data_frames)
    full_data.reset_index(inplace=True)
    full_data.set_index(['Date', 'Ticker'], inplace=True)
    full_data.sort_index(inplace=True)
    
    # Validation split
    dates = full_data.index.get_level_values('Date').unique()
    split_idx = int(len(dates) * 0.9)
    test_start_date = dates[split_idx]
    
    valid_mask = full_data.index.get_level_values('Date') >= test_start_date
    df_valid = full_data[valid_mask]
    
    print(f"  > Validation veri: {len(df_valid)} satır")
    print(f"  > Validation başlangıç: {test_start_date}")
    
    # Prepare data
    from models.ranking_model import RankingModel
    temp_ranker = RankingModel(df_valid, config_banking)
    X_val, y_val, groups_val = temp_ranker.prepare_data(is_training=True)
    
    # Feature alignment (train ile aynı feature'ları kullan)
    if ranker.feature_names:
        missing_features = set(ranker.feature_names) - set(X_val.columns)
        extra_features = set(X_val.columns) - set(ranker.feature_names)
        
        if missing_features:
            for feat in missing_features:
                X_val[feat] = 0.0
        
        if extra_features:
            X_val = X_val.drop(columns=list(extra_features))
        
        X_val = X_val[ranker.feature_names]
    
    # Predict
    print("\n🔮 Tahminler yapılıyor...")
    predictions = ranker.predict(X_val)
    
    # NDCG@5 hesapla (grup bazlı)
    print("\n📈 NDCG@5 hesaplanıyor...")
    ndcg_scores = []
    
    group_start = 0
    for group_size in groups_val:
        group_end = group_start + group_size
        
        y_true = y_val.iloc[group_start:group_end].values.reshape(1, -1)
        y_pred = predictions[group_start:group_end].reshape(1, -1)
        
        if len(y_true[0]) >= 5:  # En az 5 eleman olmalı
            ndcg = ndcg_score(y_true, y_pred, k=5)
            ndcg_scores.append(ndcg)
        
        group_start = group_end
    
    # Sonuçlar
    mean_ndcg5 = np.mean(ndcg_scores)
    std_ndcg5 = np.std(ndcg_scores)
    
    print("\n" + "="*60)
    print("📊 SONUÇLAR")
    print("="*60)
    print(f"  ✅ NDCG@5 (Ortalama): {mean_ndcg5:.4f}")
    print(f"  📊 NDCG@5 (Std Dev):  {std_ndcg5:.4f}")
    print(f"  📈 Grup Sayısı:       {len(ndcg_scores)}")
    print("="*60)
    
    return {
        'ndcg@5_mean': mean_ndcg5,
        'ndcg@5_std': std_ndcg5,
        'num_groups': len(ndcg_scores)
    }

if __name__ == "__main__":
    evaluate_catboost_ndcg5()
