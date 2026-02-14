
import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.feature_engineering import FeatureEngineer
import config

class TestFeatureEngineering(unittest.TestCase):
    def setUp(self):
        """Test ortamını hazırla - Sentetik veri oluştur."""
        # SMA 200 için en az 200+ gün veri gerekli
        dates = pd.date_range(end=datetime.today(), periods=300, freq='B')
        self.ticker = "TEST.IS"
        
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 300)
        price = 100 * (1 + returns).cumprod()
        
        self.df = pd.DataFrame({
            'Open': price * (1 + np.random.normal(0, 0.005, 300)),
            'High': price * (1 + np.abs(np.random.normal(0, 0.01, 300))),
            'Low': price * (1 - np.abs(np.random.normal(0, 0.01, 300))),
            'Close': price,
            'Volume': np.random.randint(100000, 5000000, 300).astype(float),
            'XU100': price * 0.9 # Mock index data
        }, index=dates)
        
        # Init with data
        self.fe = FeatureEngineer(self.df)

    def test_technical_features(self):
        """Teknik indikatörlerin hesaplanmasını test et."""
        # Mixin methods use internal self.data
        df_processed = self.fe.add_technical_indicators()
        self.fe.add_custom_indicators()
        self.fe.add_volume_and_extra_indicators()
        
        # Check core indicators
        self.assertIn('RSI', self.fe.data.columns)
        self.assertIn('MACD', self.fe.data.columns)
        self.assertIn('SMA_50', self.fe.data.columns)
        self.assertIn('ATR', self.fe.data.columns)
        
        # Check BBL loosely (name varies by version)
        bbl_cols = [c for c in self.fe.data.columns if 'BBL' in c]
        self.assertTrue(len(bbl_cols) > 0, "BBL column missing")

    def test_volatility_features(self):
        """Volatilite feature'larını test et."""
        self.fe.add_volatility_estimators()
        
        expected_cols = ['Vol_GarmanKlass', 'Vol_RogersSatchell', 'Vol_Parkinson']
        for col in expected_cols:
            self.assertIn(col, self.fe.data.columns)

    def test_derived_features(self):
        """Türetilmiş feature'ları test et."""
        # derived requires TIMEFRAME config, ensure defaults
        self.fe.add_derived_features()
        
        expected_cols = ['Log_Return', 'Volatility_20', 'Excess_Return_Current']
        for col in expected_cols:
            self.assertIn(col, self.fe.data.columns)

    def test_process_all(self):
        """Tüm işlem zincirini test et."""
        # Re-init fresh
        fe = FeatureEngineer(self.df)
        try:
            # process_all(self, ticker=None)
            df_final = fe.process_all(ticker=self.ticker)
            self.assertFalse(df_final.empty)
            self.assertIn('RSI', df_final.columns)
            self.assertIn('Vol_GarmanKlass', df_final.columns)
        except Exception as e:
            self.fail(f"process_all() hata fırlattı: {e}")

if __name__ == '__main__':
    unittest.main()
