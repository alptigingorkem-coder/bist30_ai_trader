import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import pandas as pd
import numpy as np
from models.regime_detector import RegimeDetector
import config

def test_regime_integration():
    print("Testing Regime Detector Integration...")
    
    # Mock Market Data
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    market_df = pd.DataFrame({
        'VIX': [20.0]*5 + [40.0]*5 + [20.0]*10, # Normal -> Crisis -> Normal
        'USDTRY': [30.0]*20,
        'ATR': [1.0]*20,
        'SMA_20': [100]*20,
        'SMA_50': [100]*20
    }, index=dates)
    
    # Initialize Detector
    detector = RegimeDetector(config.__dict__)
    
    daily_regimes = {}
    for date, row in market_df.iterrows():
        current_slice = row.to_frame().T
        regime = detector.detect_regime(current_slice)
        daily_regimes[date] = regime
        
    print("\nRegime Timeline:")
    for d, r in daily_regimes.items():
        print(f"{d.date()}: {r}")
        
    # Check if Crisis detected
    regimes = list(daily_regimes.values())
    if "CRISIS" in regimes:
        print("\n✅ Crisis correctly detected.")
    else:
        print("\n❌ Crisis NOT detected (Check thresholds).")
        
    # Check Weight Config
    w = config.ENSEMBLE_REGIME_WEIGHTS.get("CRISIS")
    print(f"\nCrisis Weights (Should be LGBM 1.0): {w}")

if __name__ == "__main__":
    test_regime_integration()
