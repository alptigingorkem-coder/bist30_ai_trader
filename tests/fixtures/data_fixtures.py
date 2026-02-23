"""
Shared fixtures for data-related tests.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV data for testing."""
    dates = pd.date_range('2023-01-01', periods=100)
    np.random.seed(42)
    
    return pd.DataFrame({
        'Open': np.random.uniform(90, 110, 100),
        'High': np.random.uniform(95, 115, 100),
        'Low': np.random.uniform(85, 105, 100),
        'Close': np.random.uniform(90, 110, 100),
        'Volume': np.random.uniform(1e6, 5e6, 100)
    }, index=dates)


@pytest.fixture
def sample_price_data():
    """Sample price data for multiple tickers."""
    dates = pd.date_range('2023-01-01', periods=100)
    tickers = ['THYAO', 'GARAN', 'ISCTR']
    
    np.random.seed(42)
    data = {}
    for ticker in tickers:
        data[ticker] = 100 + np.random.randn(100).cumsum()
    
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def sample_signals():
    """Sample trading signals."""
    dates = pd.date_range('2023-01-01', periods=100)
    tickers = ['THYAO', 'GARAN', 'ISCTR']
    
    np.random.seed(42)
    signals = np.random.choice([0, 1], size=(100, len(tickers)), p=[0.7, 0.3])
    
    return pd.DataFrame(signals, index=dates, columns=tickers)


@pytest.fixture
def sample_weights():
    """Sample portfolio weights."""
    dates = pd.date_range('2023-01-01', periods=100)
    tickers = ['THYAO', 'GARAN', 'ISCTR']
    
    # Equal weight
    weights = np.ones((100, len(tickers))) / len(tickers)
    
    return pd.DataFrame(weights, index=dates, columns=tickers)


@pytest.fixture
def sample_volumes():
    """Sample volume data."""
    dates = pd.date_range('2023-01-01', periods=100)
    tickers = ['THYAO', 'GARAN', 'ISCTR']
    
    np.random.seed(42)
    volumes = np.random.uniform(500000, 2000000, size=(100, len(tickers)))
    
    return pd.DataFrame(volumes, index=dates, columns=tickers)


@pytest.fixture
def sample_features():
    """Sample feature data for ML models."""
    dates = pd.date_range('2023-01-01', periods=100)
    
    np.random.seed(42)
    return pd.DataFrame({
        'SMA_20': np.random.uniform(90, 110, 100),
        'SMA_50': np.random.uniform(85, 115, 100),
        'RSI': np.random.uniform(30, 70, 100),
        'MACD': np.random.uniform(-2, 2, 100),
        'Volume_MA': np.random.uniform(1e6, 3e6, 100),
        'Volatility': np.random.uniform(0.01, 0.05, 100)
    }, index=dates)


@pytest.fixture
def sample_ticker_list():
    """Sample list of tickers."""
    return ['THYAO', 'GARAN', 'ISCTR', 'AKBNK', 'EREGL']


@pytest.fixture
def date_range_config():
    """Standard date range configuration."""
    return {
        'train_start': '2023-01-01',
        'train_end': '2023-06-30',
        'test_start': '2023-07-01',
        'test_end': '2023-12-31'
    }
