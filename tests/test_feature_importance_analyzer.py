"""
Unit tests for FeatureImportanceAnalyzer orchestrator.

This module tests the main orchestrator that coordinates all components
for feature importance analysis.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.analysis.feature_importance_analyzer import FeatureImportanceAnalyzer
from scripts.analysis.feature_importance_config import AnalysisConfig, AnalysisResult


@pytest.fixture
def mock_config_module():
    """Create a mock configuration module."""
    config = Mock()
    config.START_DATE = "2023-01-01"
    config.END_DATE = "2023-12-31"
    config.TICKERS = ["AKBNK", "GARAN", "ISCTR"]
    config.LEAKAGE_COLS = ['Close', 'High', 'Low', 'Open', 'Volume']
    config.LABEL_TYPE = 'RawRank'
    config.FORWARD_WINDOWS = [1]
    return config


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    tickers = ['AKBNK', 'GARAN', 'ISCTR']
    
    data_frames = []
    for ticker in tickers:
        df = pd.DataFrame({
            'Date': dates,
            'Ticker': ticker,
            'feature_1': np.random.randn(100),
            'feature_2': np.random.randn(100),
            'feature_3': np.random.randn(100),
            'feature_4': np.random.randn(100),
            'feature_5': np.random.randn(100),
            'Excess_Return': np.random.randn(100),
            'Excess_Return_T1': np.random.randn(100)
        })
        data_frames.append(df)
    
    combined = pd.concat(data_frames, ignore_index=True)
    combined.set_index(['Date', 'Ticker'], inplace=True)
    return combined


class TestFeatureImportanceAnalyzer:
    """Test suite for FeatureImportanceAnalyzer."""
    
    def test_initialization_default_config(self, mock_config_module):
        """Test analyzer initialization with default configuration."""
        analyzer = FeatureImportanceAnalyzer(mock_config_module)
        
        assert analyzer.config_module == mock_config_module
        assert analyzer.analysis_config.sample_size == 1000
        assert analyzer.analysis_config.importance_threshold == 0.001
        assert analyzer.feature_selector is not None
        assert analyzer.model_comparator is not None
        assert analyzer.visualizer is not None
        assert analyzer.report_generator is not None
    
    def test_initialization_custom_config(self, mock_config_module):
        """Test analyzer initialization with custom configuration."""
        custom_config = {
            'sample_size': 500,
            'importance_threshold': 0.01,
            'start_date': '2023-06-01',
            'end_date': '2023-12-31'
        }
        
        analyzer = FeatureImportanceAnalyzer(mock_config_module, custom_config)
        
        assert analyzer.analysis_config.sample_size == 500
        assert analyzer.analysis_config.importance_threshold == 0.01
        assert analyzer.analysis_config.start_date == '2023-06-01'
        assert analyzer.analysis_config.end_date == '2023-12-31'
    
    def test_initialization_invalid_config(self, mock_config_module):
        """Test analyzer initialization with invalid configuration."""
        invalid_config = {
            'sample_size': -100,  # Invalid: negative
        }
        
        with pytest.raises(ValueError, match="sample_size must be positive"):
            FeatureImportanceAnalyzer(mock_config_module, invalid_config)
    
    def test_load_data_success(self, mock_config_module, sample_data):
        """Test successful data loading."""
        analyzer = FeatureImportanceAnalyzer(mock_config_module)
        
        # Mock DataLoader and FeatureEngineer (they are imported locally in the method)
        with patch('utils.data_loader.DataLoader') as mock_loader_class, \
             patch('utils.feature_engineering.FeatureEngineer') as mock_fe_class:
            
            # Setup mocks
            mock_loader = Mock()
            mock_loader_class.return_value = mock_loader
            
            # Return sample data for each ticker
            mock_loader.get_combined_data.return_value = sample_data.reset_index()
            
            mock_fe = Mock()
            mock_fe_class.return_value = mock_fe
            mock_fe.process_all.return_value = sample_data.reset_index().set_index('Date')
            
            # Call method
            result = analyzer._load_data()
            
            # Assertions
            assert result is not None
            assert len(result) > 0
            assert isinstance(result.index, pd.MultiIndex)
    
    def test_load_data_no_valid_data(self, mock_config_module):
        """Test data loading when no valid data is available."""
        analyzer = FeatureImportanceAnalyzer(mock_config_module)
        
        # Mock DataLoader to return None for all tickers (imported locally in the method)
        with patch('utils.data_loader.DataLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader_class.return_value = mock_loader
            mock_loader.get_combined_data.return_value = None
            
            # Should raise ValueError
            with pytest.raises(ValueError, match="No valid data could be loaded"):
                analyzer._load_data()
    
    def test_train_baseline_model(self, mock_config_module, sample_data):
        """Test baseline model training."""
        analyzer = FeatureImportanceAnalyzer(mock_config_module)
        
        # Mock RankingModel
        with patch('scripts.analysis.feature_importance_analyzer.RankingModel') as mock_model_class:
            mock_model = Mock()
            mock_model_class.return_value = mock_model
            
            # Setup mock behavior
            mock_model.prepare_data.return_value = (
                sample_data[['feature_1', 'feature_2', 'feature_3']],
                pd.Series(np.random.randn(len(sample_data))),
                [100, 100, 100]
            )
            mock_model.model = Mock()  # Trained model
            mock_model.feature_names = ['feature_1', 'feature_2', 'feature_3']
            
            # Call method
            result = analyzer._train_baseline_model(sample_data)
            
            # Assertions
            assert result is not None
            assert result.model is not None
            mock_model.train.assert_called_once()
    
    def test_train_baseline_model_empty_data(self, mock_config_module):
        """Test baseline model training with empty data."""
        analyzer = FeatureImportanceAnalyzer(mock_config_module)
        
        with pytest.raises(ValueError, match="Cannot train baseline model with empty data"):
            analyzer._train_baseline_model(pd.DataFrame())
    
    def test_create_blacklist(self, mock_config_module):
        """Test blacklist creation."""
        analyzer = FeatureImportanceAnalyzer(mock_config_module)
        
        # Create sample importance data
        importance_df = pd.DataFrame({
            'feature': ['feature_1', 'feature_2', 'feature_3', 'feature_4', 'feature_5'],
            'importance': [0.5, 0.3, 0.0005, 0.0003, 0.0001]
        })
        
        # Call method
        blacklist = analyzer._create_blacklist(importance_df)
        
        # Assertions
        assert isinstance(blacklist, list)
        assert len(blacklist) == 3  # Features below 0.001 threshold
        assert 'feature_3' in blacklist
        assert 'feature_4' in blacklist
        assert 'feature_5' in blacklist
    
    def test_create_blacklist_empty_importance(self, mock_config_module):
        """Test blacklist creation with empty importance data."""
        analyzer = FeatureImportanceAnalyzer(mock_config_module)
        
        with pytest.raises(ValueError, match="Cannot create blacklist from empty importance data"):
            analyzer._create_blacklist(pd.DataFrame())
    
    def test_compare_models(self, mock_config_module, sample_data):
        """Test model comparison."""
        analyzer = FeatureImportanceAnalyzer(mock_config_module)
        
        # Create mock models
        baseline_model = Mock()
        baseline_model.model = Mock()
        baseline_model.feature_names = ['feature_1', 'feature_2', 'feature_3']
        
        optimized_model = Mock()
        optimized_model.model = Mock()
        optimized_model.feature_names = ['feature_1', 'feature_2']
        
        # Mock ModelComparator
        analyzer.model_comparator = Mock()
        analyzer.model_comparator.compare.return_value = {
            'baseline_ndcg3': 0.6217,
            'optimized_ndcg3': 0.6500,
            'improvement_pct': 4.55,
            'baseline_features': 3,
            'optimized_features': 2
        }
        
        # Call method
        result = analyzer._compare_models(baseline_model, optimized_model, sample_data)
        
        # Assertions
        assert result is not None
        assert 'baseline_ndcg3' in result
        assert 'optimized_ndcg3' in result
        assert 'improvement_pct' in result
        assert result['optimized_ndcg3'] > result['baseline_ndcg3']
    
    def test_save_results(self, mock_config_module, tmp_path):
        """Test results saving."""
        # Use temporary directory for output
        custom_config = {
            'output_dir': str(tmp_path / 'test_output')
        }
        analyzer = FeatureImportanceAnalyzer(mock_config_module, custom_config)
        
        # Create sample analysis result
        importance_df = pd.DataFrame({
            'feature': ['feature_1', 'feature_2', 'feature_3'],
            'importance': [0.5, 0.3, 0.1]
        })
        
        analysis_result = AnalysisResult(
            timestamp=datetime.now(),
            config={'sample_size': 1000, 'importance_threshold': 0.001},
            importance_df=importance_df,
            blacklist=['feature_3'],
            baseline_ndcg3=0.6217,
            optimized_ndcg3=0.6500,
            improvement_pct=4.55,
            total_features=3,
            blacklisted_features=1,
            remaining_features=2,
            data_size=300,
            tickers_analyzed=['AKBNK', 'GARAN'],
            analysis_duration=120.5
        )
        
        comparison_results = {
            'baseline_ndcg3': 0.6217,
            'optimized_ndcg3': 0.6500,
            'improvement_pct': 4.55,
            'baseline_features': 3,
            'optimized_features': 2
        }
        
        # Call method
        analyzer._save_results(analysis_result, comparison_results)
        
        # Assertions - check that files were created
        assert os.path.exists(tmp_path / 'test_output')
        # Note: Blacklist is saved to models/saved/ not output_dir


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
