
import sys
import os
import pandas as pd
import numpy as np

# Add project root to path BEFORE importing config or models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config
# Explicitly set settings.yaml path in config if needed, but it should load.
from models.regime_detector import RegimeDetector

# Detector oluştur (Tek seferlik)
# Models expect a dictionary-like config object with .get()
regime_config = {
    'REGIME_THRESHOLDS': getattr(config, 'REGIME_THRESHOLDS', {}),
    'REGIME_ACTIONS': getattr(config, 'REGIME_ACTIONS', {})
}
detector = RegimeDetector(regime_config)

# Test veri (farklı senaryolar)
scenarios = [
    {"name": "COVID Crash", "VIX": 65, "USDTRY_change": 0.05, "SMA_20": 2500, "SMA_50": 2600},
    {"name": "Normal Piyasa", "VIX": 18, "USDTRY_change": 0.002, "SMA_20": 2500, "SMA_50": 2450},
    {"name": "Yatay Piyasa", "VIX": 22, "USDTRY_change": 0.001, "SMA_20": 2500, "SMA_50": 2498},
    {"name": "Volatil", "VIX": 30, "USDTRY_change": 0.015, "SMA_20": 2500, "SMA_50": 2480, "ATR": 0.05, "ATR_MA": 0.05},
    {"name": "Trend Up", "VIX": 16, "USDTRY_change": 0.001, "SMA_20": 2600, "SMA_50": 2500, "ATR": 0.05, "ATR_MA": 0.05},
    {"name": "ATR Spike", "VIX": 20, "USDTRY_change": 0.001, "SMA_20": 2500, "SMA_50": 2490, "ATR": 0.10, "ATR_MA": 0.04}, # 2.5x spike
]

print("="*70)
print("REGIME DETECTOR TEST")
print("="*70)

for scenario in scenarios:
    # DataFrame oluştur
    detector.regime_history = [] 
    row_count = 5
    
    # Base columns
    data = pd.DataFrame({
        'VIX': [scenario['VIX']] * row_count,
        'USDTRY': [1.0] * row_count, 
        'SMA_20': [scenario['SMA_20']] * row_count,
        'SMA_50': [scenario['SMA_50']] * row_count,
        'ATR': [scenario.get('ATR', 0.05)] * row_count,
        'RSI': [50] * row_count,
    })
    
    # Add ATR_MA_60 if provided
    if 'ATR_MA' in scenario:
        data['ATR_MA_60'] = scenario['ATR_MA']
    
    # Update USDTRY to simulate change over 5 days
    start_usdtry = 1.0
    end_usdtry = 1.0 * (1.0 + scenario.get('USDTRY_change', 0)) # Fixed key access
    
    # Linspace from start to end
    data['USDTRY'] = np.linspace(start_usdtry, end_usdtry, row_count)
    
    # Rejim tespit et
    regime = detector.detect_regime(data)
    action = detector.get_trading_action(regime)
    
    print(f"\n{scenario['name']:20s} → Regime: {regime:15s}")
    print(f"  Trade: {action['trade']}, Position: {action['position_multiplier']*100:.0f}%, Max Stocks: {action['max_positions']}")

print("\n" + "="*70)
