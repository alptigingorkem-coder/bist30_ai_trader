
import pandas as pd
import config
from data_loader import DataLoader
from feature_engineering import FeatureEngineer
from regime_detection import RegimeDetector
from beta_model import BetaModel

def test_beta_model():
    print("--- Beta Model Test ---")
    
    # 1. Load Data
    loader = DataLoader()
    ticker = "KCHOL.IS"
    df = loader.get_combined_data(ticker)
    
    # 2. Add Features & Regime
    fe = FeatureEngineer(df)
    df = fe.process_all()
    
    rd = RegimeDetector(df)
    df = rd.detect_regimes(verbose=False)
    
    # MOCK REGIME FOR TESTING (Ensure enough data)
    # Force last 150 rows to be Trend_Up (2) to test training loop
    df.loc[df.index[-150:], 'Regime_Num'] = 2
    
    # 3. Instantiate Beta Model
    beta_model = BetaModel(df)
    
    # 4. Check Data Prep
    X, y = beta_model.prepare_features(is_training=True)
    print(f"Training Data Shape (Trend/Sideways Only): {X.shape}")
    print(f"Original Data Shape: {df.shape}")
    
    # 5. Train
    model = beta_model.optimize_and_train(n_trials=2)
    
    if model:
        print("Beta Model Trained Successfully.")
        # Predict on recent data
        recent_preds = beta_model.predict(df.tail(10))
        print("Recent Predictions (Next Week Returns):")
        print(recent_preds.tail())
    else:
        print("Training Failed.")

if __name__ == "__main__":
    test_beta_model()
