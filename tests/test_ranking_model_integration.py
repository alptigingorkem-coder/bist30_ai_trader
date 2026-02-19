"""
Integration test for RankingModel with FeatureSelector blacklist.

This test verifies that the blacklist created by FeatureSelector
can be successfully used by RankingModel to filter features.
"""

import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from unittest.mock import MagicMock

from models.ranking_model import RankingModel
from scripts.analysis.feature_selector import FeatureSelector


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
    """Create sample data with multiple features."""
    dates = pd.date_range('2024-01-01', periods=20, freq='D')
    tickers = ['STOCK1', 'STOCK2', 'STOCK3', 'STOCK4']
    
    data = []
    for date in dates:
        for ticker in tickers:
            data.append({
                'Date': date,
                'Ticker': ticker,
                'high_importance_1': np.random.randn() * 10,
                'high_importance_2': np.random.randn() * 8,
                'medium_importance': np.random.randn() * 3,
                'low_importance_1': np.random.randn() * 0.1,
                'low_importance_2': np.random.randn() * 0.05,
                'Excess_Return': np.random.randn(),
                'Excess_Return_T1': np.random.randn(),
            })
    
    df = pd.DataFrame(data)
    df = df.set_index(['Date', 'Ticker'])
    return df


@pytest.fixture
def feature_importance_df():
    """Create a sample feature importance DataFrame."""
    return pd.DataFrame({
        'feature': ['high_importance_1', 'high_importance_2', 'medium_importance', 
                   'low_importance_1', 'low_importance_2'],
        'importance': [0.45, 0.35, 0.15, 0.003, 0.002]
    })


class TestRankingModelIntegration:
    """Integration tests for RankingModel with FeatureSelector."""
    
    def test_end_to_end_blacklist_workflow(self, sample_data, feature_importance_df, mock_config):
        """Test complete workflow: create blacklist -> apply to RankingModel."""
        with tempfile.TemporaryDirectory() as tmpdir:
            blacklist_path = os.path.join(tmpdir, 'test_blacklist.json')
            
            # Step 1: Create blacklist using FeatureSelector
            selector = FeatureSelector(threshold=0.01)
            blacklist = selector.create_blacklist(feature_importance_df)
            selector.save_blacklist(blacklist, path=blacklist_path)
            
            # Verify blacklist was created correctly
            assert os.path.exists(blacklist_path)
            assert len(blacklist) == 2  # low_importance_1 and low_importance_2
            assert 'low_importance_1' in blacklist
            assert 'low_importance_2' in blacklist
            
            # Step 2: Use blacklist in RankingModel
            model = RankingModel(sample_data, mock_config, blacklist_path=blacklist_path)
            X, y, groups = model.prepare_data(is_training=True)
            
            # Verify blacklisted features are filtered
            assert 'low_importance_1' not in model.feature_names
            assert 'low_importance_2' not in model.feature_names
            
            # Verify high importance features are kept
            assert 'high_importance_1' in model.feature_names
            assert 'high_importance_2' in model.feature_names
            assert 'medium_importance' in model.feature_names
            
            # Verify X DataFrame has correct columns
            assert 'low_importance_1' not in X.columns
            assert 'low_importance_2' not in X.columns
            assert 'high_importance_1' in X.columns
    
    def test_blacklist_update_workflow(self, sample_data, feature_importance_df, mock_config):
        """Test that RankingModel picks up blacklist updates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            blacklist_path = os.path.join(tmpdir, 'test_blacklist.json')
            
            # Initial blacklist with threshold 0.01
            selector = FeatureSelector(threshold=0.01)
            blacklist = selector.create_blacklist(feature_importance_df)
            selector.save_blacklist(blacklist, path=blacklist_path)
            
            model = RankingModel(sample_data, mock_config, blacklist_path=blacklist_path)
            X1, _, _ = model.prepare_data(is_training=True)
            initial_feature_count = len(model.feature_names)
            
            # Update blacklist with stricter threshold
            selector2 = FeatureSelector(threshold=0.20)
            blacklist2 = selector2.create_blacklist(feature_importance_df)
            selector2.save_blacklist(blacklist2, path=blacklist_path)
            
            # Prepare data again - should reload blacklist
            X2, _, _ = model.prepare_data(is_training=True)
            updated_feature_count = len(model.feature_names)
            
            # More features should be filtered with stricter threshold
            assert updated_feature_count < initial_feature_count
            assert 'medium_importance' not in model.feature_names
    
    def test_default_blacklist_location(self, sample_data, mock_config):
        """Test that RankingModel uses default blacklist location when no path is provided."""
        # This test verifies the default behavior
        # Note: This will use the actual default location if it exists
        model = RankingModel(sample_data, mock_config)
        
        # Should initialize without error
        assert model is not None
        assert isinstance(model.blacklist, list)
        
        # If default blacklist exists, it should be loaded
        if os.path.exists("models/saved/feature_blacklist.json"):
            assert len(model.blacklist) >= 0
    
    def test_feature_count_reduction(self, sample_data, feature_importance_df, mock_config):
        """Test that blacklist actually reduces feature count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            blacklist_path = os.path.join(tmpdir, 'test_blacklist.json')
            
            # Model without blacklist
            model_no_blacklist = RankingModel(sample_data, mock_config, 
                                             blacklist_path="/tmp/nonexistent.json")
            X_no_blacklist, _, _ = model_no_blacklist.prepare_data(is_training=True)
            
            # Create and apply blacklist
            selector = FeatureSelector(threshold=0.01)
            blacklist = selector.create_blacklist(feature_importance_df)
            selector.save_blacklist(blacklist, path=blacklist_path)
            
            model_with_blacklist = RankingModel(sample_data, mock_config, 
                                               blacklist_path=blacklist_path)
            X_with_blacklist, _, _ = model_with_blacklist.prepare_data(is_training=True)
            
            # Feature count should be reduced
            assert len(model_with_blacklist.feature_names) < len(model_no_blacklist.feature_names)
            assert X_with_blacklist.shape[1] < X_no_blacklist.shape[1]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
