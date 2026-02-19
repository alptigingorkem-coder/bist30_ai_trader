
import sys
import os
import joblib
sys.path.append(os.getcwd())

import config
from models.ensemble_model import HybridEnsemble
from utils.logging_config import get_logger

log = get_logger(__name__)

def verify_loading():
    print("="*50)
    print("🧪 MODEL YÜKLEME DOĞRULAMA TESTİ")
    print("="*50)
    
    lgbm_path = "models/saved/global_ranker.pkl"
    tft_path = "models/saved/tft_model.pth"
    
    print(f"Checking LGBM path: {lgbm_path} -> {'EXISTS' if os.path.exists(lgbm_path) else 'MISSING'}")
    print(f"Checking TFT path: {tft_path} -> {'EXISTS' if os.path.exists(tft_path) else 'MISSING'}")
    
    try:
        ensemble = HybridEnsemble()
        
        # Load logic similar to api/server.py
        use_tft = os.path.exists(tft_path)
        
        if os.path.exists(lgbm_path):
            print("\nYukleme baslatiliyor...")
            ensemble.load_models(lgbm_path, tft_path if use_tft else None, tft_config=config)
            
            print(f"Ensemble LGBM loaded: {ensemble.lgbm is not None}")
            print(f"Ensemble TFT loaded: {ensemble.tft is not None}")
            
            if ensemble.lgbm and (ensemble.tft or not use_tft):
                print("\n✅ Model yükleme BAŞARILI!")
            else:
                print("\n❌ Model yükleme KISMEN BAŞARISIZ!")
        else:
            print("\n❌ LGBM model yok, test edilemedi.")
            
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_loading()
