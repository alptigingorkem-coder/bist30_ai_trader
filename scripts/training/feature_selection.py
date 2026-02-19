
import sys
import os
import pandas as pd
import numpy as np
import joblib
import json
import lightgbm as lgb
import shap

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel
from utils.logging_config import get_logger

log = get_logger(__name__)

def run_feature_selection():
    log.info("🔍 Feature Selection Analizi Başlıyor...")
    
    # 1. Veri Yükle (Son 1 Yıl Yeterli)
    start_date = (pd.to_datetime('today') - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    loader = DataLoader(start_date=start_date)
    
    # Sadece TIER_1 (Ana 10 hisse) veya Tüm 30 hisse ile analiz yapılabilir
    # Faz 5.1A: Tüm hisselerle feature selection
    tickers = config.TICKERS 
    
    all_dfs = []
    for ticker in tickers:
        try:
            raw = loader.get_combined_data(ticker)
            if raw is None or len(raw) < 100: continue
            
            fe = FeatureEngineer(raw)
            df = fe.process_all(ticker)
            df['Ticker'] = ticker
            all_dfs.append(df)
        except:
            pass
            
    if not all_dfs:
        log.error("Veri yok!")
        return

    full_data = pd.concat(all_dfs)
    full_data.reset_index(inplace=True)
    full_data.set_index(['Date', 'Ticker'], inplace=True)
    
    log.info(f"Veri boyutu: {full_data.shape}")
    
    # 2. Model Eğit (Hızlı)
    # Mevcut config kullan
    from configs import banking as config_banking
    
    # Geçici Ranker
    ranker = RankingModel(full_data, config_banking)
    X, y, q = ranker.prepare_data(is_training=True)
    
    params = {
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'boosting_type': 'gbdt',
        'n_estimators': 100,
        'learning_rate': 0.1,
        'verbosity': -1
    }
    
    model = lgb.LGBMRanker(**params)
    model.fit(X, y, group=q)
    
    # 3. SHAP Analizi
    log.info("SHAP Analizi hesaplanıyor...")
    explainer = shap.TreeExplainer(model)
    # Sample data for speed
    sample = X.sample(min(1000, len(X)))
    shap_values = explainer.shap_values(sample)
    
    # Ortalama mutlak SHAP değeri
    if isinstance(shap_values, list):
        importances = np.abs(shap_values[0]).mean(0)
    else:
        importances = np.abs(shap_values).mean(0)
        
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    # 4. Blacklist Belirle
    # Eşik: Ortalama katkısı 0'a çok yakın olanlar
    threshold = 0.001 
    blacklist = feature_importance[feature_importance['importance'] < threshold]['feature'].tolist()
    
    log.info(f"Toplam Feature: {len(feature_importance)}")
    log.info(f"Önerilen Blacklist ({len(blacklist)}): {blacklist}")
    
    # 5. Kaydet
    os.makedirs("models/saved", exist_ok=True)
    save_path = "models/saved/feature_blacklist.json"
    with open(save_path, 'w') as f:
        json.dump(blacklist, f, indent=2)
        
    log.info(f"Blacklist kaydedildi: {save_path}")

if __name__ == "__main__":
    run_feature_selection()
