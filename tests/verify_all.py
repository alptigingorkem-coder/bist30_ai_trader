
import sys
import os
import pandas as pd
import numpy as np
import torch

# Path ekle
sys.path.append(os.getcwd())

def test_imports():
    print("Test 1: Imports...")
    try:
        import pytorch_forecasting
        import pytorch_lightning
        from evds import evdsAPI
        print("✅ Libraries imported successfully.")
        print(f"CUDA Available: {torch.cuda.is_available()}")
    except ImportError as e:
        print(f"❌ Import failed: {e}")

def test_macro_loader():
    print("\nTest 2: Macro Data Loader...")
    from utils.macro_data_loader import TurkeyMacroData
    try:
        # API key olmadan da başlatılabilmeli (Yahoo Finance fallback)
        loader = TurkeyMacroData(evds_key='TEST') 
        # Fetch çağırmıyoruz, sadece import ve init testi
        print("✅ TurkeyMacroData initialized.")
    except Exception as e:
        print(f"❌ Macro Loader failed: {e}")

def test_feature_engineering():
    print("\nTest 3: Feature Engineering (TFT Features)...")
    from utils.feature_engineering import FeatureEngineer, prepare_tft_dataset
    import config
    
    # Dummy Data
    dates = pd.date_range('2023-01-01', periods=100)
    df = pd.DataFrame({
        'Open': np.random.rand(100) * 10,
        'High': np.random.rand(100) * 12,
        'Low': np.random.rand(100) * 8,
        'Close': np.random.rand(100) * 10,
        'Volume': np.random.rand(100) * 1000,
        'XU100': np.random.rand(100) * 5000,
        'usdtry': np.random.rand(100) * 30 # Dummy macro
    }, index=dates)
    
    try:
        fe = FeatureEngineer(df)
        # Sadece feature ekleme metodlarını test et (process_all uzun sürer ve dosya ister)
        fe.add_technical_indicators()
        fe.add_transformer_features()
        
        cols = fe.data.columns
        if 'DayOfWeek' in cols and 'usdtry_shock' in cols:
             print("✅ TFT features added.")
        else:
             print(f"❌ Missing features: {cols}")
             
        # Dataset Config Check
        ds_config = prepare_tft_dataset(fe.data)
        if ds_config['max_encoder_length'] == 60:
             print("✅ prepare_tft_dataset works.")
             
    except Exception as e:
        print(f"❌ Feature Engineering failed: {e}")

def test_tft_model():
    print("\nTest 4: TFT Model Build...")
    from models.transformer_model import BIST30TransformerModel
    
    class DummyConfig:
        TFT_HIDDEN_SIZE = 16
        
    try:
        model = BIST30TransformerModel(DummyConfig)
        # Dataset oluşturmak için feature engineering çıktısı lazım ama dummy verelim
        # TimeSeriesDataSet deep checks yapıyor, atlayalım.
        # Sadece import ve init başarılı mı?
        print("✅ BIST30TransformerModel initialized.")
    except Exception as e:
        print(f"❌ TFT Model failed: {e}")

def test_kelly_sizer():
    print("\nTest 5: Kelly Position Sizer...")
    from core.position_sizing import KellyPositionSizer
    
    try:
        sizer = KellyPositionSizer()
        # 5 win 5 loss
        for _ in range(5): sizer.add_trade(0.10)
        for _ in range(5): sizer.add_trade(-0.05)
        
        kelly = sizer.calculate_kelly()
        print(f"✅ Kelly Fraction calculated: {kelly:.4f}")
    except Exception as e:
        print(f"❌ Kelly Sizer failed: {e}")

def test_ensemble():
    print("\nTest 6: Ensemble Model...")
    from models.ensemble_model import HybridEnsemble
    try:
        ens = HybridEnsemble()
        print("✅ HybridEnsemble initialized.")
    except Exception as e:
         print(f"❌ Ensemble failed: {e}")

if __name__ == "__main__":
    test_imports()
    test_macro_loader()
    test_feature_engineering()
    test_tft_model()
    test_kelly_sizer()
    test_ensemble()
