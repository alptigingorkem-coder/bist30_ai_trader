import sys
import os
import joblib
import torch
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

# Import model structures
from models.ranking_model import RankingModel
# from models.ranking_model_catboost import CatBoostRankingModel # Might not exist as a class yet based on import check
try:
    from catboost import CatBoostRanker, CatBoostRegressor, CatBoostClassifier
except ImportError:
    pass

def inspect_lightgbm():
    print("\n--- LightGBM Model Metrics ---")
    path = "models/saved/global_ranker.pkl"
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return

    try:
        # RankingModel.load uses joblib
        model_wrapper = RankingModel.load(path)
        model = model_wrapper.model
        
        if hasattr(model, 'best_score_'):
            print("Best Score (Validation):")
            for dataset, metrics in model.best_score_.items():
                print(f"  Dataset: {dataset}")
                for metric, value in metrics.items():
                    print(f"    - {metric}: {value:.6f}")
        else:
            print("Model does not have 'best_score_' attribute.")

        if hasattr(model, 'best_iteration_'):
            print(f"Best Iteration: {model.best_iteration_}")
            
    except Exception as e:
        print(f"❌ Error inspecting LightGBM: {e}")

def inspect_catboost():
    print("\n--- CatBoost Model Metrics ---")
    path = "models/saved/global_ranker_catboost.cbm"
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return

    try:
        model = CatBoostRanker()
        model.load_model(path)
        
        if hasattr(model, 'get_best_score'):
            best_scores = model.get_best_score()
            print("Best Score (Validation):")
            if 'validation' in best_scores:
                for metric, value in best_scores['validation'].items():
                    print(f"    - {metric}: {value:.6f}")
            else:
                print(f"  Raw best_score: {best_scores}")
        else:
            print("Model does not have 'get_best_score' method.")
            
        if hasattr(model, 'get_best_iteration'):
             print(f"Best Iteration: {model.get_best_iteration()}")
             
        if hasattr(model, 'get_evals_result'):
            evals = model.get_evals_result()
            print("Evaluation Results (Last Value):")
            for dataset, metrics in evals.items():
                print(f"  Dataset: {dataset}")
                for metric, values in metrics.items():
                    if len(values) > 0:
                        print(f"    - {metric}: {values[-1]:.6f} (Iter: {len(values)})")
        
    except Exception as e:
        print(f"❌ Error inspecting CatBoost: {e}")

def check_lightning_logs():
    print("\n--- TFT Lightning Logs ---")
    log_dir = "lightning_logs"
    if not os.path.exists(log_dir):
        print("❌ lightning_logs directory not found.")
        return
        
    # Find latest version
    versions = [d for d in os.listdir(log_dir) if d.startswith("version_")]
    if not versions:
        print("No versions found in lightning_logs.")
        return
        
    latest = sorted(versions, key=lambda x: int(x.split("_")[1]))[-1]
    print(f"Latest Version: {latest}")
    
    metrics_path = os.path.join(log_dir, latest, "metrics.csv")
    if os.path.exists(metrics_path):
        try:
            df = pd.read_csv(metrics_path)
            print(f"Metrics ({metrics_path}):")
            # Print last non-NaN value for each column
            for col in df.columns:
                last_valid = df[col].dropna().iloc[-1] if not df[col].dropna().empty else "N/A"
                print(f"  - {col}: {last_valid}")
        except Exception as e:
            print(f"  Error reading metrics.csv: {e}")
    else:
        print("  metrics.csv not found.")

if __name__ == "__main__":
    inspect_lightgbm()
    inspect_catboost()
    check_lightning_logs()
    # inspect_tft() # Skipping direct pth load as it was uninformative
