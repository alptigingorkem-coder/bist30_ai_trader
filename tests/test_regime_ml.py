
import pandas as pd
import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.regime_detection import MLRegimeClassifier

def test_ml_regime():
    # 1. Load Data (Minimal)
    loader = DataLoader()
    ticker = "KCHOL.IS"
    df = loader.get_combined_data(ticker)
    
    # 2. Add Features
    fe = FeatureEngineer(df)
    df = fe.process_all()
    
    # 3. Instantiate ML Classifier
    ml_regime = MLRegimeClassifier(df)
    
    # 4. Prepare Features (Check dimensions)
    X, y = ml_regime.prepare_features()
    print(f"Features: {X.shape}, Labels: {y.shape}")
    print(f"Classes: {y.unique()}")
    
    # 5. Fast Optimization
    print("Running optimization...")
    model = ml_regime.optimize_and_train(n_trials=2)
    
    if model:
        print("Model trained successfully.")
        preds = ml_regime.predict_proba(X)
        print(f"Predictions shape: {preds.shape}")
    else:
        print("Training failed.")

if __name__ == "__main__":
    test_ml_regime()
