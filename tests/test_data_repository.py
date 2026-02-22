"""
Unit tests for DataRepository.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

from utils.data.data_repository import DataRepository


class TestDataRepositoryInit(unittest.TestCase):
    """Test DataRepository initialization."""
    
    def test_init_with_dates(self):
        repo = DataRepository('2020-01-01', '2023-12-31')
        self.assertEqual(repo.start_date, '2020-01-01')
        self.assertEqual(repo.end_date, '2023-12-31')


class TestFetchFromYahoo(unittest.TestCase):
    """Test Yahoo Finance fetching."""
    
    def setUp(self):
        self.repo = DataRepository('2020-01-01', '2023-12-31')
    
    @patch('utils.data.data_repository.yf.download')
    def test_fetch_success(self, mock_download):
        # Mock successful download
        mock_df = pd.DataFrame({
            'Open': [100, 101],
            'High': [102, 103],
            'Low': [99, 100],
            'Close': [101, 102],
            'Volume': [1000, 1100]
        }, index=pd.date_range('2023-01-01', periods=2))
        mock_download.return_value = mock_df
        
        result = self.repo.fetch_from_yahoo('THYAO.IS')
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        mock_download.assert_called_once()
    
    @patch('utils.data.data_repository.yf.download')
    def test_fetch_empty_data(self, mock_download):
        # Mock empty DataFrame
        mock_download.return_value = pd.DataFrame()
        
        result = self.repo.fetch_from_yahoo('INVALID.IS')
        
        self.assertIsNone(result)
    
    @patch('utils.data.data_repository.yf.download')
    def test_fetch_with_exception(self, mock_download):
        # Mock exception
        mock_download.side_effect = Exception("Network error")
        
        result = self.repo.fetch_from_yahoo('THYAO.IS')
        
        self.assertIsNone(result)
    
    @patch('utils.data.data_repository.yf.download')
    def test_fetch_with_period(self, mock_download):
        mock_df = pd.DataFrame({
            'Close': [100, 101]
        }, index=pd.date_range('2023-01-01', periods=2))
        mock_download.return_value = mock_df
        
        result = self.repo.fetch_from_yahoo('THYAO.IS', period='1d', interval='1m')
        
        self.assertIsNotNone(result)
        # Verify period was used instead of start/end dates
        call_kwargs = mock_download.call_args[1]
        self.assertEqual(call_kwargs['period'], '1d')
        self.assertEqual(call_kwargs['interval'], '1m')
    
    @patch('utils.data.data_repository.yf.download')
    def test_fetch_multiindex_columns(self, mock_download):
        # Mock MultiIndex columns (happens when downloading multiple tickers)
        mock_df = pd.DataFrame({
            ('Close', 'THYAO.IS'): [100, 101],
            ('Volume', 'THYAO.IS'): [1000, 1100]
        }, index=pd.date_range('2023-01-01', periods=2))
        mock_download.return_value = mock_df
        
        result = self.repo.fetch_from_yahoo('THYAO.IS')
        
        self.assertIsNotNone(result)
        # Verify columns were flattened
        self.assertNotIsInstance(result.columns, pd.MultiIndex)


class TestFetchFromIsYatirim(unittest.TestCase):
    """Test İş Yatırım fetching."""
    
    def setUp(self):
        self.repo = DataRepository('2020-01-01', '2023-12-31')
    
    @patch('isyatirimhisse.fetch_stock_data')
    def test_fetch_success(self, mock_fetch):
        # Mock successful fetch
        mock_df = pd.DataFrame({
            'Tarih': ['01-01-2023', '02-01-2023'],
            'Açılış': [100, 101],
            'Yüksek': [102, 103],
            'Düşük': [99, 100],
            'Kapanış': [101, 102],
            'Hacim': [1000, 1100]
        })
        mock_fetch.return_value = mock_df
        
        result = self.repo.fetch_from_is_yatirim('THYAO.IS')
        
        self.assertIsNotNone(result)
        # Verify columns were standardized
        self.assertIn('Close', result.columns)
        self.assertIn('Open', result.columns)
    
    @patch('isyatirimhisse.fetch_stock_data')
    def test_fetch_empty_data(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        
        result = self.repo.fetch_from_is_yatirim('INVALID.IS')
        
        self.assertIsNone(result)
    
    @patch('isyatirimhisse.fetch_stock_data')
    def test_fetch_with_exception(self, mock_fetch):
        mock_fetch.side_effect = Exception("Connection error")
        
        result = self.repo.fetch_from_is_yatirim('THYAO.IS')
        
        self.assertIsNone(result)
    
    @patch('isyatirimhisse.fetch_stock_data')
    def test_symbol_mapping(self, mock_fetch):
        mock_df = pd.DataFrame({
            'Tarih': ['01-01-2023'],
            'Kapanış': [100]
        })
        mock_fetch.return_value = mock_df
        
        # Test special symbol mapping
        self.repo.fetch_from_is_yatirim('KOZAL.IS')
        
        # Verify KOZAL was mapped to TRALT
        call_args = mock_fetch.call_args[0]
        self.assertEqual(call_args[0], 'TRALT')
    
    @patch('builtins.__import__', side_effect=ImportError("No module named 'isyatirimhisse'"))
    def test_import_error(self, mock_import):
        # Test when isyatirimhisse is not installed
        result = self.repo.fetch_from_is_yatirim('THYAO.IS')
        self.assertIsNone(result)


class TestFetchWithFallback(unittest.TestCase):
    """Test fallback mechanism."""
    
    def setUp(self):
        self.repo = DataRepository('2020-01-01', '2023-12-31')
    
    @patch.object(DataRepository, 'fetch_from_yahoo')
    @patch.object(DataRepository, 'fetch_from_is_yatirim')
    def test_yahoo_success_no_fallback(self, mock_is, mock_yahoo):
        # Yahoo succeeds, no fallback needed
        mock_df = pd.DataFrame({'Close': [100]})
        mock_yahoo.return_value = mock_df
        
        result = self.repo.fetch_with_fallback('THYAO.IS')
        
        self.assertIsNotNone(result)
        mock_yahoo.assert_called_once()
        mock_is.assert_not_called()
    
    @patch.object(DataRepository, 'fetch_from_yahoo')
    @patch.object(DataRepository, 'fetch_from_is_yatirim')
    def test_yahoo_fails_fallback_succeeds(self, mock_is, mock_yahoo):
        # Yahoo fails, fallback succeeds
        mock_yahoo.return_value = None
        mock_df = pd.DataFrame({'Close': [100]})
        mock_is.return_value = mock_df
        
        result = self.repo.fetch_with_fallback('THYAO.IS')
        
        self.assertIsNotNone(result)
        mock_yahoo.assert_called_once()
        mock_is.assert_called_once()
    
    @patch.object(DataRepository, 'fetch_from_yahoo')
    @patch.object(DataRepository, 'fetch_from_is_yatirim')
    def test_both_fail(self, mock_is, mock_yahoo):
        # Both sources fail
        mock_yahoo.return_value = None
        mock_is.return_value = None
        
        result = self.repo.fetch_with_fallback('INVALID.IS')
        
        self.assertIsNone(result)
        mock_yahoo.assert_called_once()
        mock_is.assert_called_once()
    
    @patch.object(DataRepository, 'fetch_from_yahoo')
    @patch.object(DataRepository, 'fetch_from_is_yatirim')
    def test_no_fallback_for_intraday(self, mock_is, mock_yahoo):
        # Fallback not used for intraday data
        mock_yahoo.return_value = None
        
        result = self.repo.fetch_with_fallback('THYAO.IS', interval='1m', period='1d')
        
        self.assertIsNone(result)
        mock_yahoo.assert_called_once()
        mock_is.assert_not_called()  # Fallback skipped for intraday


class TestFetchLiveData(unittest.TestCase):
    """Test live data fetching."""
    
    def setUp(self):
        self.repo = DataRepository('2020-01-01', '2023-12-31')
    
    @patch.object(DataRepository, 'fetch_from_yahoo')
    def test_fetch_live_data(self, mock_yahoo):
        mock_df = pd.DataFrame({'Close': [100, 101]})
        mock_yahoo.return_value = mock_df
        
        result = self.repo.fetch_live_data('THYAO.IS')
        
        self.assertIsNotNone(result)
        # Verify correct parameters were passed
        call_kwargs = mock_yahoo.call_args[1]
        self.assertEqual(call_kwargs['interval'], '1m')
        self.assertEqual(call_kwargs['period'], '1d')


class TestStandardizeColumns(unittest.TestCase):
    """Test column standardization."""
    
    def setUp(self):
        self.repo = DataRepository('2020-01-01', '2023-12-31')
    
    def test_standardize_turkish_columns(self):
        df = pd.DataFrame({
            'Tarih': ['2023-01-01', '2023-01-02'],
            'Açılış': [100, 101],
            'Yüksek': [102, 103],
            'Düşük': [99, 100],
            'Kapanış': [101, 102],
            'Hacim': [1000, 1100]
        })
        
        result = self.repo._standardize_is_yatirim_columns(df)
        
        # Verify English column names
        self.assertIn('Open', result.columns)
        self.assertIn('High', result.columns)
        self.assertIn('Low', result.columns)
        self.assertIn('Close', result.columns)
        self.assertIn('Volume', result.columns)
        
        # Verify Date is index
        self.assertIsInstance(result.index, pd.DatetimeIndex)
    
    def test_standardize_already_english(self):
        df = pd.DataFrame({
            'Open': [100],
            'Close': [101]
        }, index=pd.date_range('2023-01-01', periods=1))
        
        result = self.repo._standardize_is_yatirim_columns(df)
        
        # Should not break if columns are already in English
        self.assertIn('Open', result.columns)
        self.assertIn('Close', result.columns)


if __name__ == '__main__':
    unittest.main()
