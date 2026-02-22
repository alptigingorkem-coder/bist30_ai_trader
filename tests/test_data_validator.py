"""
Unit tests for DataValidator.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from utils.data.data_validator import DataValidator


class TestDataValidatorInit(unittest.TestCase):
    """Test DataValidator initialization."""
    
    def test_init_default(self):
        validator = DataValidator()
        self.assertEqual(validator.min_rows, 10)
        self.assertEqual(validator.max_price_drop, -0.60)
        self.assertEqual(validator.max_gap_days, 7)
    
    def test_init_custom(self):
        validator = DataValidator(
            min_rows=20,
            max_price_drop=-0.50,
            max_gap_days=5,
            min_volume_tl=1000000
        )
        self.assertEqual(validator.min_rows, 20)
        self.assertEqual(validator.max_price_drop, -0.50)
        self.assertEqual(validator.max_gap_days, 5)
        self.assertEqual(validator.min_volume_tl, 1000000)


class TestValidateColumns(unittest.TestCase):
    """Test column validation."""
    
    def setUp(self):
        self.validator = DataValidator()
    
    def test_valid_columns(self):
        df = pd.DataFrame({
            'Open': [100],
            'High': [102],
            'Low': [99],
            'Close': [101],
            'Volume': [1000]
        })
        
        is_valid, reason = self.validator.validate_columns(df, 'TEST')
        self.assertTrue(is_valid)
        self.assertEqual(reason, "OK")
    
    def test_missing_columns(self):
        df = pd.DataFrame({
            'Open': [100],
            'Close': [101]
        })
        
        is_valid, reason = self.validator.validate_columns(df, 'TEST')
        self.assertFalse(is_valid)
        self.assertIn("Missing columns", reason)


class TestValidateData(unittest.TestCase):
    """Test comprehensive data validation."""
    
    def setUp(self):
        self.validator = DataValidator()
        self.valid_df = pd.DataFrame({
            'Open': list(range(100, 115)),
            'High': list(range(102, 117)),
            'Low': list(range(99, 114)),
            'Close': list(range(101, 116)),
            'Volume': [1000 + i*100 for i in range(15)]
        }, index=pd.date_range('2023-01-01', periods=15))
    
    def test_validate_valid_data(self):
        is_valid, reason = self.validator.validate_data(self.valid_df, 'TEST')
        self.assertTrue(is_valid)
        self.assertEqual(reason, "OK")
    
    def test_validate_none_data(self):
        is_valid, reason = self.validator.validate_data(None, 'TEST')
        self.assertFalse(is_valid)
        self.assertIn("None or empty", reason)
    
    def test_validate_empty_data(self):
        is_valid, reason = self.validator.validate_data(pd.DataFrame(), 'TEST')
        self.assertFalse(is_valid)
        self.assertIn("None or empty", reason)
    
    def test_validate_insufficient_rows(self):
        df = self.valid_df.head(5)
        validator = DataValidator(min_rows=10)
        
        is_valid, reason = validator.validate_data(df, 'TEST')
        self.assertFalse(is_valid)
        self.assertIn("Insufficient data", reason)


class TestCheckForGaps(unittest.TestCase):
    """Test gap detection."""
    
    def setUp(self):
        self.validator = DataValidator(max_gap_days=3)
    
    def test_no_gaps(self):
        df = pd.DataFrame({
            'Close': [100, 101, 102]
        }, index=pd.date_range('2023-01-01', periods=3, freq='D'))
        
        gaps = self.validator.check_for_gaps(df, 'TEST')
        self.assertEqual(len(gaps), 0)
    
    def test_with_gaps(self):
        # Create data with a 10-day gap
        dates = pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-15'])
        df = pd.DataFrame({
            'Close': [100, 101, 102]
        }, index=dates)
        
        gaps = self.validator.check_for_gaps(df, 'TEST')
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]['days'], 13)
    
    def test_non_datetime_index(self):
        df = pd.DataFrame({
            'Close': [100, 101, 102]
        })
        
        gaps = self.validator.check_for_gaps(df, 'TEST')
        self.assertEqual(len(gaps), 0)


class TestCheckForAnomalies(unittest.TestCase):
    """Test anomaly detection."""
    
    def setUp(self):
        self.validator = DataValidator()
    
    def test_no_anomalies(self):
        df = pd.DataFrame({
            'Close': [100, 101, 102, 103]
        }, index=pd.date_range('2023-01-01', periods=4))
        
        anomalies = self.validator.check_for_anomalies(df, 'TEST')
        self.assertEqual(len(anomalies), 0)
    
    def test_crash_detection(self):
        # Create data with a crash (-70%)
        df = pd.DataFrame({
            'Close': [100, 30, 31]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        anomalies = self.validator.check_for_anomalies(df, 'TEST')
        crashes = [a for a in anomalies if a['type'] == 'crash']
        self.assertGreater(len(crashes), 0)
    
    def test_spike_detection(self):
        # Create data with a spike (+60%)
        df = pd.DataFrame({
            'Close': [100, 160, 161]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        anomalies = self.validator.check_for_anomalies(df, 'TEST')
        spikes = [a for a in anomalies if a['type'] == 'spike']
        self.assertGreater(len(spikes), 0)
    
    def test_invalid_price_detection(self):
        # Create data with zero/negative prices
        df = pd.DataFrame({
            'Close': [100, 0, -10]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        anomalies = self.validator.check_for_anomalies(df, 'TEST')
        invalid = [a for a in anomalies if a['type'] == 'invalid_price']
        self.assertEqual(len(invalid), 2)


class TestCheckLiquidity(unittest.TestCase):
    """Test liquidity checking."""
    
    def test_sufficient_liquidity(self):
        validator = DataValidator(min_volume_tl=1000000)
        
        df = pd.DataFrame({
            'Close': [100] * 30,
            'Volume': [20000] * 30  # 100 * 20000 = 2M TL per day
        }, index=pd.date_range('2023-01-01', periods=30))
        
        is_liquid, reason = validator.check_liquidity(df, 'TEST')
        self.assertTrue(is_liquid)
    
    def test_insufficient_liquidity(self):
        validator = DataValidator(min_volume_tl=5000000)
        
        df = pd.DataFrame({
            'Close': [100] * 30,
            'Volume': [10000] * 30  # 100 * 10000 = 1M TL per day
        }, index=pd.date_range('2023-01-01', periods=30))
        
        is_liquid, reason = validator.check_liquidity(df, 'TEST')
        self.assertFalse(is_liquid)
        self.assertIn("Insufficient liquidity", reason)
    
    def test_missing_columns(self):
        validator = DataValidator(min_volume_tl=1000000)
        
        df = pd.DataFrame({
            'Close': [100, 101, 102]
        })
        
        is_liquid, reason = validator.check_liquidity(df, 'TEST')
        self.assertTrue(is_liquid)  # Cannot check, so pass
        self.assertIn("missing columns", reason)


class TestValidateOHLCV(unittest.TestCase):
    """Test OHLCV validation."""
    
    def setUp(self):
        self.validator = DataValidator()
    
    def test_valid_ohlcv(self):
        df = pd.DataFrame({
            'Open': [100, 101],
            'High': [102, 103],
            'Low': [99, 100],
            'Close': [101, 102],
            'Volume': [1000, 1100]
        })
        
        is_valid = self.validator.validate_ohlcv(df, 'TEST')
        self.assertTrue(is_valid)
    
    def test_high_less_than_low(self):
        df = pd.DataFrame({
            'Open': [100],
            'High': [98],  # Invalid: High < Low
            'Low': [99],
            'Close': [101],
            'Volume': [1000]
        })
        
        is_valid = self.validator.validate_ohlcv(df, 'TEST')
        self.assertFalse(is_valid)
    
    def test_high_less_than_close(self):
        df = pd.DataFrame({
            'Open': [100],
            'High': [100],  # Invalid: High < Close
            'Low': [99],
            'Close': [102],
            'Volume': [1000]
        })
        
        is_valid = self.validator.validate_ohlcv(df, 'TEST')
        self.assertFalse(is_valid)
    
    def test_low_greater_than_open(self):
        df = pd.DataFrame({
            'Open': [100],
            'High': [102],
            'Low': [101],  # Invalid: Low > Open
            'Close': [101],
            'Volume': [1000]
        })
        
        is_valid = self.validator.validate_ohlcv(df, 'TEST')
        self.assertFalse(is_valid)
    
    def test_negative_volume(self):
        df = pd.DataFrame({
            'Open': [100],
            'High': [102],
            'Low': [99],
            'Close': [101],
            'Volume': [-1000]  # Invalid: negative volume
        })
        
        is_valid = self.validator.validate_ohlcv(df, 'TEST')
        self.assertFalse(is_valid)


class TestGetDataQualityScore(unittest.TestCase):
    """Test data quality scoring."""
    
    def setUp(self):
        self.validator = DataValidator()
    
    def test_perfect_score(self):
        # Create perfect data with 60 rows (>50 for no penalty)
        df = pd.DataFrame({
            'Open': list(range(100, 160)),
            'High': list(range(102, 162)),
            'Low': list(range(99, 159)),
            'Close': list(range(101, 161)),
            'Volume': [1000 + i*100 for i in range(60)]
        }, index=pd.date_range('2023-01-01', periods=60))
        
        score = self.validator.get_data_quality_score(df, 'TEST')
        self.assertEqual(score, 100.0)
    
    def test_score_with_insufficient_data(self):
        # Create data with only 5 rows (min is 10)
        df = pd.DataFrame({
            'Open': [100, 101, 102, 103, 104],
            'High': [102, 103, 104, 105, 106],
            'Low': [99, 100, 101, 102, 103],
            'Close': [101, 102, 103, 104, 105],
            'Volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        score = self.validator.get_data_quality_score(df, 'TEST')
        self.assertLess(score, 100.0)
    
    def test_score_with_anomalies(self):
        # Create data with crash
        df = pd.DataFrame({
            'Open': [100, 101, 30, 31, 32],
            'High': [102, 103, 32, 33, 34],
            'Low': [99, 100, 29, 30, 31],
            'Close': [101, 102, 30, 31, 32],
            'Volume': [1000, 1100, 1200, 1300, 1400]
        }, index=pd.date_range('2023-01-01', periods=5))
        
        score = self.validator.get_data_quality_score(df, 'TEST')
        self.assertLess(score, 100.0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        self.validator = DataValidator()
    
    def test_single_row_data(self):
        df = pd.DataFrame({
            'Open': [100],
            'High': [102],
            'Low': [99],
            'Close': [101],
            'Volume': [1000]
        })
        
        # Should fail minimum rows check
        is_valid, reason = self.validator.validate_data(df, 'TEST')
        self.assertFalse(is_valid)
    
    def test_data_with_nan(self):
        df = pd.DataFrame({
            'Open': [100, np.nan, 102],
            'High': [102, 103, 104],
            'Low': [99, 100, 101],
            'Close': [101, 102, 103],
            'Volume': [1000, 1100, 1200]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        # Should still validate (NaN handling is up to transformer)
        is_valid, _ = self.validator.validate_columns(df, 'TEST')
        self.assertTrue(is_valid)
    
    def test_very_large_dataset(self):
        # Test with 1000 rows
        df = pd.DataFrame({
            'Open': range(1000),
            'High': range(1, 1001),
            'Low': range(0, 1000),
            'Close': range(1, 1001),
            'Volume': [1000] * 1000
        }, index=pd.date_range('2020-01-01', periods=1000))
        
        is_valid, reason = self.validator.validate_data(df, 'TEST')
        self.assertTrue(is_valid)


if __name__ == '__main__':
    unittest.main()
