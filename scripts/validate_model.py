import pandas as pd
import numpy as np
import joblib
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from sklearn.metrics import ndcg_score

def validate():
    print("Model Validasyonu Başlıyor...")
    
    # Load Model
    model = joblib.load("models/saved/global_ranker.pkl")
    print(f"Model Yüklendi. Özellik Sayısı: {model.n_features_}")
    
    # Load Data (Sample for speed, or full/partial)
    # We use a recent period for "hold-out" test
    # Load enough history for indicators (SMA200)
    start_date = "2023-01-01"
    end_date = "2024-03-01"
    
    loader = DataLoader(start_date=start_date, end_date=end_date)
    tickers = config.TICKERS[:5] # Test with 5 tickers first
    
    all_data = []
    for ticker in tickers:
        df = loader.get_combined_data(ticker)
        if df is None or df.empty: continue
        fe = FeatureEngineer(df)
        df = fe.process_all(ticker)
        df['Ticker'] = ticker
        all_data.append(df)
        
    if not all_data:
        print("Veri yok.")
        return

    full_df = pd.concat(all_data)
    
    # Prepare Features
    feature_cols = model.feature_name_
    
    # Align features
    for f in feature_cols:
        if f not in full_df.columns:
            full_df[f] = 0
            
    X = full_df[feature_cols]
    
    # Predict
    preds = model.predict(X)
    full_df['Score'] = preds
    
    # Calculate simplistic NDCG (Daily)
    # Group by Date, rank by Return vs Score
    ndcg_list = []
    
    # Basic metric: Avg Rank Correlation
    corrs = []
    
    # Drop rows where target is NaN (last day usually)
    full_df = full_df.dropna(subset=['NextDay_Return'])
    
    for date, group in full_df.groupby(level=0):
        if len(group) < 2: continue
        
        # True Rank (Return)
        if 'NextDay_Return' in group.columns:
            true_relevance = group['NextDay_Return'].values.reshape(1, -1)
            # Min-Max scale to 0-1 for NDCG (or just rank order)
            # NDCG needs non-negative relevance usually.
            # Let's use rank correlation instead for simplicity here
            
            score_rank = group['Score'].rank(ascending=False)
            return_rank = group['NextDay_Return'].rank(ascending=False)
            
            corr = score_rank.corr(return_rank)
            corrs.append(corr)
            
    print(f"Ortalama Günlük Rank Korelasyonu (Spearman): {np.mean(corrs):.4f}")
    print(f"Test Dönemi: {start_date} - {end_date}")

if __name__ == "__main__":
    validate()
