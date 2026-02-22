"""
Unit tests for DataTransformer.

Tests data transformation and cleaning operations.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.data.data_transformer import DataTransformer


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    data = pd.DataFrame({
        'Open': np.random.uniform(90, 110, 100),
        'High': np.random.uniform(100, 120, 100),
        'Low': np.random.uniform(80, 100, 100),
        'Close': np.random.uniform(90, 110, 100),
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    # Ensure OHLC relationships are valid
    data['High'] = data[['Open', 'High', 'Close']].max(axis=1)
    data['Low'] = data[['Open', 'Low', 'Close']].min(axis=1)
    
    return data


@pytest.fixture
def transformer():
    """Create DataTransformer instance."""
    return DataTransformer()


# ─────────────────────────────────────────────────────────────
# CLEAN DATA TESTS
# ─────────────────────────────────────────────────────────────

def test_clean_data_removes_zero_close(transformer):
    """Test that clean_data removes rows with Close <= 0."""
    data = pd.DataFrame({
        'Open': [100, 100, 100],
        'High': [110, 110, 110],
        'Low': [90, 90, 90],
        'Close': [105, 0, 105],
        'Volume': [1000, 1000, 1000]
    }, index=pd.date_range('2024-01-01', periods=3))
    
    cleaned = transformer.clean_data(data, 'TEST')
    
    assert len(cleaned) == 2
    assert (cleaned['Close'] > 0).all()


def test_clean_data_removes_zero_low(transformer):
    """Test that clean_data removes rows with Low <= 0."""
    data = pd.DataFrame({
        'Open': [100, 100, 100],
        'High': [110, 110, 110],
        'Low': [90, 0, 90],
        'Close': [105, 105, 105],
        'Volume': [1000, 1000, 1000]
    }, index=pd.date_range('2024-01-01', periods=3))
    
    cleaned = transformer.clean_data(data, 'TEST')
    
    assert len(cleaned) == 2
    assert (cleaned['Low'] > 0).all()


def test_clean_data_removes_outliers(transformer):
    """Test that clean_data removes outliers based on High/Low margin."""
    data = pd.DataFrame({
        'Open': [100, 100, 100],
        'High': [110, 200, 110],  # Middle row has High/Low = 2.0 > 1.25
        'Low': [90, 100, 90],
        'Close': [105, 150, 105],
        'Volume': [1000, 1000, 1000]
    }, index=pd.date_range('2024-01-01', periods=3))
    
    cleaned = transformer.clean_data(data, 'TEST')
    
    assert len(cleaned) == 2
    # Check that remaining rows have valid margin
    margin = cleaned['High'] / cleaned['Low']
    assert (margin <= transformer.max_margin).all()


def test_clean_data_empty_input(transformer):
    """Test that clean_data handles empty DataFrame."""
    data = pd.DataFrame()
    cleaned = transformer.clean_data(data, 'TEST')
    
    assert cleaned.empty


def test_clean_data_none_input(transformer):
    """Test that clean_data handles None input."""
    cleaned = transformer.clean_data(None, 'TEST')
    
    assert cleaned is None


def test_clean_data_preserves_valid_data(transformer):
    """Test that clean_data preserves valid data."""
    # Create data with valid OHLC relationships (no outliers)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    data = pd.DataFrame({
        'Open': [100.0] * 100,
        'High': [105.0] * 100,
        'Low': [95.0] * 100,
        'Close': [102.0] * 100,
        'Volume': [1000000] * 100
    }, index=dates)
    
    initial_len = len(data)
    cleaned = transformer.clean_data(data, 'TEST')
    
    # Should preserve all valid data
    assert len(cleaned) == initial_len


# ─────────────────────────────────────────────────────────────
# ADD TECHNICAL INDICATORS TESTS
# ─────────────────────────────────────────────────────────────

def test_add_sma_indicator(transformer, sample_ohlcv_data):
    """Test adding Simple Moving Average indicator."""
    result = transformer.add_technical_indicators(
        sample_ohlcv_data.copy(), 
        indicators=['SMA_20']
    )
    
    assert 'SMA_20' in result.columns
    # First 19 values should be NaN
    assert result['SMA_20'].iloc[:19].isna().all()
    # Remaining values should be valid
    assert result['SMA_20'].iloc[19:].notna().all()


def test_add_ema_indicator(transformer, sample_ohlcv_data):
    """Test adding Exponential Moving Average indicator."""
    result = transformer.add_technical_indicators(
        sample_ohlcv_data.copy(), 
        indicators=['EMA_12']
    )
    
    assert 'EMA_12' in result.columns
    # EMA should have values after first row
    assert result['EMA_12'].iloc[1:].notna().any()


def test_add_rsi_indicator(transformer, sample_ohlcv_data):
    """Test adding RSI indicator."""
    result = transformer.add_technical_indicators(
        sample_ohlcv_data.copy(), 
        indicators=['RSI_14']
    )
    
    assert 'RSI_14' in result.columns
    # RSI should be between 0 and 100
    valid_rsi = result['RSI_14'].dropna()
    assert (valid_rsi >= 0).all()
    assert (valid_rsi <= 100).all()


def test_add_macd_indicator(transformer, sample_ohlcv_data):
    """Test adding MACD indicator."""
    result = transformer.add_technical_indicators(
        sample_ohlcv_data.copy(), 
        indicators=['MACD']
    )
    
    assert 'MACD' in result.columns
    assert 'MACD_Signal' in result.columns


def test_add_multiple_indicators(transformer, sample_ohlcv_data):
    """Test adding multiple indicators at once."""
    result = transformer.add_technical_indicators(
        sample_ohlcv_data.copy(), 
        indicators=['SMA_20', 'RSI_14', 'MACD']
    )
    
    assert 'SMA_20' in result.columns
    assert 'RSI_14' in result.columns
    assert 'MACD' in result.columns
    assert 'MACD_Signal' in result.columns


def test_add_indicators_empty_input(transformer):
    """Test adding indicators to empty DataFrame."""
    data = pd.DataFrame()
    result = transformer.add_technical_indicators(data, indicators=['SMA_20'])
    
    assert result.empty


def test_add_indicators_unknown_indicator(transformer, sample_ohlcv_data):
    """Test handling unknown indicator."""
    result = transformer.add_technical_indicators(
        sample_ohlcv_data.copy(), 
        indicators=['UNKNOWN_INDICATOR']
    )
    
    # Should not add unknown indicator
    assert 'UNKNOWN_INDICATOR' not in result.columns


# ─────────────────────────────────────────────────────────────
# RESAMPLE DATA TESTS
# ─────────────────────────────────────────────────────────────

def test_resample_to_weekly(transformer, sample_ohlcv_data):
    """Test resampling daily data to weekly."""
    result = transformer.resample_data(sample_ohlcv_data, timeframe='W')
    
    # Weekly data should have fewer rows
    assert len(result) < len(sample_ohlcv_data)
    # Should have approximately 1/5 of daily rows (5 trading days per week)
    assert len(result) <= len(sample_ohlcv_data) / 5 + 2


def test_resample_to_monthly(transformer, sample_ohlcv_data):
    """Test resampling daily data to monthly."""
    result = transformer.resample_data(sample_ohlcv_data, timeframe='M')
    
    # Monthly data should have much fewer rows
    assert len(result) < len(sample_ohlcv_data)
    # Should have approximately 1/20 of daily rows (20 trading days per month)
    assert len(result) <= len(sample_ohlcv_data) / 20 + 2


def test_resample_preserves_ohlcv_structure(transformer, sample_ohlcv_data):
    """Test that resampling preserves OHLCV structure."""
    result = transformer.resample_data(sample_ohlcv_data, timeframe='W')
    
    # Check all OHLCV columns exist
    assert 'Open' in result.columns
    assert 'High' in result.columns
    assert 'Low' in result.columns
    assert 'Close' in result.columns
    assert 'Volume' in result.columns


def test_resample_daily_returns_original(transformer, sample_ohlcv_data):
    """Test that resampling to daily returns original data."""
    result = transformer.resample_data(sample_ohlcv_data, timeframe='D')
    
    # Should return same data
    assert len(result) == len(sample_ohlcv_data)


def test_resample_empty_input(transformer):
    """Test resampling empty DataFrame."""
    data = pd.DataFrame()
    result = transformer.resample_data(data, timeframe='W')
    
    assert result.empty


def test_resample_unknown_timeframe(transformer, sample_ohlcv_data):
    """Test handling unknown timeframe."""
    result = transformer.resample_data(sample_ohlcv_data, timeframe='UNKNOWN')
    
    # Should return original data
    assert len(result) == len(sample_ohlcv_data)


# ─────────────────────────────────────────────────────────────
# ALIGN DATA TESTS
# ─────────────────────────────────────────────────────────────

def test_align_two_dataframes_inner(transformer):
    """Test aligning two DataFrames with inner join."""
    dates1 = pd.date_range('2024-01-01', periods=10)
    dates2 = pd.date_range('2024-01-05', periods=10)
    
    df1 = pd.DataFrame({'A': range(10)}, index=dates1)
    df2 = pd.DataFrame({'B': range(10)}, index=dates2)
    
    aligned = transformer.align_data(df1, df2, method='inner')
    
    assert len(aligned) == 2
    # Inner join should keep only common dates (6 days overlap)
    assert len(aligned[0]) == 6
    assert len(aligned[1]) == 6


def test_align_two_dataframes_outer(transformer):
    """Test aligning two DataFrames with outer join."""
    dates1 = pd.date_range('2024-01-01', periods=5)
    dates2 = pd.date_range('2024-01-03', periods=5)
    
    df1 = pd.DataFrame({'A': range(5)}, index=dates1)
    df2 = pd.DataFrame({'B': range(5)}, index=dates2)
    
    aligned = transformer.align_data(df1, df2, method='outer')
    
    assert len(aligned) == 2
    # Outer join should keep all dates (7 days total)
    assert len(aligned[0]) == 7
    assert len(aligned[1]) == 7


def test_align_two_dataframes_left(transformer):
    """Test aligning two DataFrames with left join."""
    dates1 = pd.date_range('2024-01-01', periods=5)
    dates2 = pd.date_range('2024-01-03', periods=5)
    
    df1 = pd.DataFrame({'A': range(5)}, index=dates1)
    df2 = pd.DataFrame({'B': range(5)}, index=dates2)
    
    aligned = transformer.align_data(df1, df2, method='left')
    
    assert len(aligned) == 2
    # Left join should keep dates from first DataFrame
    assert len(aligned[0]) == 5
    assert len(aligned[1]) == 5


def test_align_single_dataframe(transformer, sample_ohlcv_data):
    """Test aligning single DataFrame."""
    aligned = transformer.align_data(sample_ohlcv_data)
    
    assert len(aligned) == 1
    assert len(aligned[0]) == len(sample_ohlcv_data)


def test_align_no_dataframes(transformer):
    """Test aligning with no DataFrames."""
    aligned = transformer.align_data()
    
    assert len(aligned) == 0


def test_align_three_dataframes(transformer):
    """Test aligning three DataFrames."""
    dates1 = pd.date_range('2024-01-01', periods=10)
    dates2 = pd.date_range('2024-01-05', periods=10)
    dates3 = pd.date_range('2024-01-03', periods=10)
    
    df1 = pd.DataFrame({'A': range(10)}, index=dates1)
    df2 = pd.DataFrame({'B': range(10)}, index=dates2)
    df3 = pd.DataFrame({'C': range(10)}, index=dates3)
    
    aligned = transformer.align_data(df1, df2, df3, method='inner')
    
    assert len(aligned) == 3
    # All should have same length after alignment
    assert len(aligned[0]) == len(aligned[1]) == len(aligned[2])


# ─────────────────────────────────────────────────────────────
# INITIALIZATION TESTS
# ─────────────────────────────────────────────────────────────

def test_initialization_default_params():
    """Test DataTransformer initialization with default parameters."""
    transformer = DataTransformer()
    
    assert transformer.max_margin == DataTransformer.DEFAULT_MAX_MARGIN
    assert transformer.timeframe == DataTransformer.DEFAULT_TIMEFRAME


def test_initialization_custom_params():
    """Test DataTransformer initialization with custom parameters."""
    transformer = DataTransformer(max_margin=1.5, timeframe='W')
    
    assert transformer.max_margin == 1.5
    assert transformer.timeframe == 'W'
