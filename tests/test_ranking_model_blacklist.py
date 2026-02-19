"""
Unit tests for RankingModel blacklist integration.

Tests verify that the blacklist functionality correctly filters features
during data preparation and supports dynamic reloading.
"""

import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from models.ranking_model import RankingModel


@pytest.fixture
def mock_config():
    """Create a mock config module for testing."""
    config = MagicMock()
    config.SECTOR_NAME = "TEST"
    config.LEAKAGE_COLS = ['NextDay_Return', 'Future_Price']
    config.LABEL_TYPE = 'RawRank'
    config.FORWARD_WINDOWS = [1]
    config.ENABLE_CORRELATION_FILTER = False
    return config


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    dates = pd.date_range('2024-01-01', periods=10, freq='D')
    tickers = ['STOCK1', 'STOCK2', 'STOCK3']
    
    data = []
    for date in dates:
        for ticker in tickers:
            data.append({
                'Date': date,
                'Ticker': ticker,
                'feature_1': np.random.randn(),
                'feature_2': np.random.randn(),
                'feature_3': np.random.randn(),
                'feature_4': np.random.randn(),
                'Excess_Return': np.random.randn(),
                'Excess_Return_T1': np.random.randn(),
            })
    
    df = pd.DataFrame(data)
    df = df.set_index(['Date', 'Ticker'])
    return df


@pytest.fixture
def temp_blacklist_file():
    """Create a temporary blacklist file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        blacklist = ['feature_2', 'feature_4']
        json.dump(blacklist, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


class TestRankingModelBlacklist:
    """Test suite for RankingModel blacklist functionality."""
    
    def test_init_without_blacklist(self, sample_data, mock_config):
        """Test that RankingModel initializes correctly without a blacklist."""
        # Use a non-existent path to ensure no blacklist is loaded
        model = RankingModel(sample_data, mock_config, blacklist_path="/tmp/nonexistent_blacklist.json")
        
        assert model.blacklist == []
        assert model.data is not None
        assert model.config == mock_config
    
    def test_init_with_nonexistent_blacklist(self, sample_data, mock_config):
        """Test that RankingModel handles nonexistent blacklist file gracefully."""
        model = RankingModel(sample_data, mock_config, blacklist_path="nonexistent.json")
        
        assert model.blacklist == []
    
    def test_init_with_blacklist(self, sample_data, mock_config, temp_blacklist_file):
        """Test that RankingModel loads blacklist correctly."""
        model = RankingModel(sample_data, mock_config, blacklist_path=temp_blacklist_file)
        
        assert len(model.blacklist) == 2
        assert 'feature_2' in model.blacklist
        assert 'feature_4' in model.blacklist
    
    def test_prepare_data_filters_blacklisted_features(self, sample_data, mock_config, temp_blacklist_file):
        """Test that prepare_data filters out blacklisted features."""
        model = RankingModel(sample_data, mock_config, blacklist_path=temp_blacklist_file)
        
        X, y, groups = model.prepare_data(is_training=True)
        
        # Check that blacklisted features are not in the feature list
        assert 'feature_2' not in model.feature_names
        assert 'feature_4' not in model.feature_names
        
        # Check that non-blacklisted features are present
        assert 'feature_1' in model.feature_names
        assert 'feature_3' in model.feature_names
        
        # Check that X only contains non-blacklisted features
        assert 'feature_2' not in X.columns
        assert 'feature_4' not in X.columns
        assert 'feature_1' in X.columns
        assert 'feature_3' in X.columns
    
    def test_prepare_data_without_blacklist_uses_all_features(self, sample_data, mock_config):
        """Test that prepare_data uses all features when no blacklist is provided."""
        # Use a non-existent path to ensure no blacklist is loaded
        model = RankingModel(sample_data, mock_config, blacklist_path="/tmp/nonexistent_blacklist.json")
        
        X, y, groups = model.prepare_data(is_training=True)
        
        # All numeric features should be present
        assert 'feature_1' in model.feature_names
        assert 'feature_2' in model.feature_names
        assert 'feature_3' in model.feature_names
        assert 'feature_4' in model.feature_names
    
    def test_blacklist_reload_on_prepare_data(self, sample_data, mock_config, temp_blacklist_file):
        """Test that blacklist is reloaded on each prepare_data call."""
        model = RankingModel(sample_data, mock_config, blacklist_path=temp_blacklist_file)
        
        # First call
        X1, _, _ = model.prepare_data(is_training=True)
        initial_feature_count = len(model.feature_names)
        
        # Update blacklist file
        with open(temp_blacklist_file, 'w') as f:
            json.dump(['feature_1', 'feature_2', 'feature_3'], f)
        
        # Second call should reload the blacklist
        X2, _, _ = model.prepare_data(is_training=True)
        updated_feature_count = len(model.feature_names)
        
        # Feature count should be different after blacklist update
        assert updated_feature_count < initial_feature_count
        assert 'feature_1' not in model.feature_names
        assert 'feature_3' not in model.feature_names
    
    def test_blacklist_with_invalid_json(self, sample_data, mock_config):
        """Test that invalid JSON in blacklist file is handled gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            temp_path = f.name
        
        try:
            model = RankingModel(sample_data, mock_config, blacklist_path=temp_path)
            
            # Should fall back to empty blacklist
            assert model.blacklist == []
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_feature_count_logging(self, sample_data, mock_config, temp_blacklist_file, caplog):
        """Test that feature filtering is logged correctly."""
        model = RankingModel(sample_data, mock_config, blacklist_path=temp_blacklist_file)
        
        with caplog.at_level('INFO'):
            X, y, groups = model.prepare_data(is_training=True)
        
        # Check that logging messages are present
        log_messages = [record.message for record in caplog.records]
        assert any('Blacklist applied' in msg for msg in log_messages)
        assert any('features filtered' in msg for msg in log_messages)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
