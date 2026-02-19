import sys
import os
import torch
import mlflow
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

import config
from utils.db_manager import DBManager
from utils.logging_config import get_logger
from models.ensemble_model import HybridEnsemble

log = get_logger("IntegrationCheck")

def check_gpu():
    print("\n--- 1. GPU / ROCm Check ---")
    if torch.cuda.is_available():
        print(f"✅ GPU Available: {torch.cuda.get_device_name(0)}")
        print(f"   Torch Version: {torch.__version__}")
        try:
            t = torch.tensor([1.0, 2.0]).cuda()
            print(f"   Tensor Test: Passed (Device: {t.device})")
            return True
        except Exception as e:
            print(f"❌ Tensor Test Failed: {e}")
            return False
    else:
        print("❌ GPU Not Available (Running on CPU)")
        return False

def check_database():
    print("\n--- 2. Database (TimescaleDB) Check ---")
    try:
        db = DBManager()
        with db.connection() as conn:
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"✅ Database Connected: {version}")
                
                # Check tables
                tables = ["market_data", "trades", "portfolio_stats"]
                missing = []
                for t in tables:
                    cur.execute(f"SELECT to_regclass('public.{t}');")
                    if cur.fetchone()[0] is None:
                        missing.append(t)
                
                if not missing:
                    print("✅ All required tables exist.")
                    return True
                else:
                    print(f"❌ Missing tables: {missing}")
                    return False
            else:
                print("❌ Connection Failed (None returned)")
                return False
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return False

def check_mlflow():
    print("\n--- 3. MLOps (MLflow) Check ---")
    try:
        client = mlflow.tracking.MlflowClient()
        experiments = client.search_experiments()
        print(f"✅ MLflow Client Connected. Found {len(experiments)} experiments.")
        for exp in experiments[:3]:
            print(f"   - {exp.name} (ID: {exp.experiment_id})")
        return True
    except Exception as e:
        print(f"❌ MLflow Error: {e}")
        return False

def check_models():
    print("\n--- 4. Model Loading Check ---")
    try:
        ensemble = HybridEnsemble()
        # Mock paths
        lgbm_path = "models/saved/global_ranker.pkl"
        tft_path = "models/saved/tft_model.pth"
        tft_config_path = "models/saved/tft_config.joblib"
        catboost_path = "models/saved/global_ranker_catboost.cbm"
        
        ensemble.load_models(lgbm_path, tft_path, tft_config=joblib.load(tft_config_path) if os.path.exists(tft_config_path) else None, catboost_path=catboost_path)
        
        if ensemble.lgbm: print("✅ LightGBM Loaded")
        else: print("❌ LightGBM NOT Loaded")
        
        if ensemble.tft: print("✅ TFT Loaded")
        else: print("❌ TFT NOT Loaded")
        
        if ensemble.catboost: print("✅ CatBoost Loaded")
        else: print("❌ CatBoost NOT Loaded")
        
        return True
    except Exception as e:
        print(f"❌ Model Loading Error: {e}")
        import traceback
        traceback.print_exc()
        return False

import joblib # Needed for config load check above

if __name__ == "__main__":
    print(f"System Integration Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    status_gpu = check_gpu()
    status_db = check_database()
    status_mlflow = check_mlflow()
    status_models = check_models()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print(f"GPU      : {'✅' if status_gpu else '❌'}")
    print(f"Database : {'✅' if status_db else '❌'}")
    print(f"MLflow   : {'✅' if status_mlflow else '❌'}")
    print(f"Models   : {'✅' if status_models else '❌'}")
    print("="*60)
