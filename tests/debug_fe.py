
import sys
import os
import pandas as pd
import numpy as np
import traceback

sys.path.append(os.getcwd())

from utils.feature_engineering import FeatureEngineer
import config

def debug_fe():
    print("DEBUG: Feature Engineering başlatılıyor (300 points)...")
    
    # 300 point (SMA 200 için yeterli)
    dates = pd.date_range('2023-01-01', periods=300)
    df = pd.DataFrame({
        'Open': np.random.rand(300) * 10,
        'High': np.random.rand(300) * 12,
        'Low': np.random.rand(300) * 8,
        'Close': np.random.rand(300) * 10,
        'Volume': np.random.rand(300) * 1000,
        'XU100': np.random.rand(300) * 5000,
        'usdtry': np.random.rand(300) * 30
    }, index=dates)
    
    fe = FeatureEngineer(df)
    
    try:
        fe.add_technical_indicators()
        print("   add_technical_indicators OK")
        
        fe.add_transformer_features()
        print("   add_transformer_features OK")
        
    except:
        traceback.print_exc()

if __name__ == "__main__":
    debug_fe()
