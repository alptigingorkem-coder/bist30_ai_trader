
import pandas as pd
import config
from data_loader import DataLoader
from feature_engineering import FeatureEngineer
from regime_detection import RegimeDetector
from alpha_model import AlphaModel

def test_alpha_model():
    print("--- Alpha Model Test ---")
    
    # 1. Load Data
    loader = DataLoader()
    ticker = "KCHOL.IS"
    df = loader.get_combined_data(ticker)
    
    # 2. Add Features & Regime
    fe = FeatureEngineer(df)
    df = fe.process_all()
    
    rd = RegimeDetector(df)
    df = rd.detect_regimes(verbose=False)
    
    # MOCK REGIME FOR TESTING
    # Force last 150 rows to be Sideways (0) to test training loop
    df.loc[df.index[-150:], 'Regime_Num'] = 0
    
    # 3. Instantiate Alpha Model
    alpha_model = AlphaModel(df)
    
    # 4. Check Data Prep
    X, y = alpha_model.prepare_features(is_training=True)
    print(f"Training Data Shape (Sideways/Trend Only): {X.shape}")
    print(f"Original Data Shape: {df.shape}")
    print(f"Features in X: {X.columns.tolist()}")
    
    # 5. Train
    print("Optimization starting...")
    model = alpha_model.optimize_and_train(n_trials=2)
    
    if model:
        print("Alpha Model Trained Successfully.")
        # Predict on recent data
        recent_preds = alpha_model.predict(df.tail(10))
        print("Recent Predictions (Excess Return):")
        print(recent_preds.tail())
    else:
        print("Training Failed.")

if __name__ == "__main__":
    test_alpha_model()
