import sys
import os
sys.path.append(os.getcwd())
from core.feature_store import feature_store
import pandas as pd
import numpy as np
import config

def analyze_sector_distributions():
    print("Loading data from Feature Store...")
    df = feature_store.load_fundamentals()
    
    if df.empty:
        print("No data found!")
        return

    # Sektör bilgisini ekle
    # df'de 'Ticker' var (örn: AKBNK.IS), config.get_sector bunu halleder
    df['Sector'] = df['Ticker'].apply(lambda x: config.get_sector(x))
    
    # Analiz edilecek rasyolar
    ratios = ['Forward_PE', 'PB_Ratio', 'EBITDA_Margin', 'Debt_to_Equity']
    
    # Sektör bazlı loop
    sectors = df['Sector'].unique()
    
    print(f"\n{'='*20} DISTRIBUTION ANALYSIS {'='*20}")
    
    stats_dict = {}
    
    for sector in sectors:
        print(f"\n--- SECTOR: {sector} ---")
        sector_df = df[df['Sector'] == sector]
        
        sector_stats = {}
        
        for ratio in ratios:
            if ratio not in sector_df.columns: continue
            
            # Temizlik (Outlier ve NaN temizliği)
            data = pd.to_numeric(sector_df[ratio], errors='coerce').dropna()
            
            # Remove extreme outliers for better stats (Interquartile Range)
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            data_clean = data[~((data < (Q1 - 1.5 * IQR)) | (data > (Q3 + 1.5 * IQR)))]
            
            if data_clean.empty:
                print(f"{ratio}: No valid data")
                continue
                
            mean = data_clean.mean()
            std = data_clean.std()
            skew = data_clean.skew()
            median = data_clean.median()
            
            # Dağılım Tespiti (Basit Heuristic)
            dist_type = "Normal"
            if abs(skew) > 1:
                dist_type = "LogNormal / Skewed"
                
            print(f"{ratio:15} | Mean: {mean:6.2f} | Median: {median:6.2f} | Std: {std:6.2f} | Skew: {skew:5.2f} | Dist: {dist_type}")
            
            sector_stats[ratio] = {
                "mean": mean,
                "std": std,
                "dist": dist_type,
                "min": data_clean.min(),
                "max": data_clean.max()
            }
        
        stats_dict[sector] = sector_stats
        
    return stats_dict

if __name__ == "__main__":
    analyze_sector_distributions()
