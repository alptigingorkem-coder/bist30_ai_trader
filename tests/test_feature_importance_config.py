"""
Unit tests for feature importance configuration module.

Tests the AnalysisConfig and AnalysisResult dataclasses including
validation logic.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import pytest
from datetime import datetime
import pandas as pd
from scripts.analysis.feature_importance_config import AnalysisConfig, AnalysisResult


class TestAnalysisConfig:
    """Test suite for AnalysisConfig dataclass."""
    
    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        config = AnalysisConfig()
        
        assert config.sample_size == 1000
        assert config.importance_threshold == 0.001
        assert config.start_date is None
        assert config.end_date is None
        assert config.tickers is None
        assert config.output_dir == "reports/feature_importance"
        assert config.save_models is False
    
    def test_custom_values(self):
        """Test that custom configuration values are accepted."""
        config = AnalysisConfig(
            sample_size=2000,
            importance_threshold=0.005,
            start_date="2023-01-01",
            end_date="2023-12-31",
            tickers=["THYAO", "GARAN"],
            output_dir="custom/output",
            save_models=True
        )
        
        assert config.sample_size == 2000
        assert config.importance_threshold == 0.005
        assert config.start_date == "2023-01-01"
        assert config.end_date == "2023-12-31"
        assert config.tickers == ["THYAO", "GARAN"]
        assert config.output_dir == "custom/output"
        assert config.save_models is True
    
    def test_negative_sample_size_raises_error(self):
        """Test that negative sample_size raises ValueError."""
        with pytest.raises(ValueError, match="sample_size must be positive"):
            AnalysisConfig(sample_size=-100)
    
    def test_zero_sample_size_raises_error(self):
        """Test that zero sample_size raises ValueError."""
        with pytest.raises(ValueError, match="sample_size must be positive"):
            AnalysisConfig(sample_size=0)
    
    def test_negative_threshold_raises_error(self):
        """Test that negative importance_threshold raises ValueError."""
        with pytest.raises(ValueError, match="importance_threshold must be non-negative"):
            AnalysisConfig(importance_threshold=-0.1)
    
    def test_invalid_start_date_format_raises_error(self):
        """Test that invalid start_date format raises ValueError."""
        with pytest.raises(ValueError, match="start_date must be in YYYY-MM-DD format"):
            AnalysisConfig(start_date="2023/01/01")
    
    def test_invalid_end_date_format_raises_error(self):
        """Test that invalid end_date format raises ValueError."""
        with pytest.raises(ValueError, match="end_date must be in YYYY-MM-DD format"):
            AnalysisConfig(end_date="01-01-2023")
    
    def test_start_date_after_end_date_raises_error(self):
        """Test that start_date after end_date raises ValueError."""
        with pytest.raises(ValueError, match="start_date .* must be before or equal to end_date"):
            AnalysisConfig(start_date="2023-12-31", end_date="2023-01-01")
    
    def test_equal_start_and_end_dates_allowed(self):
        """Test that equal start and end dates are allowed."""
        config = AnalysisConfig(start_date="2023-06-15", end_date="2023-06-15")
        assert config.start_date == "2023-06-15"
        assert config.end_date == "2023-06-15"
    
    def test_empty_tickers_list_raises_error(self):
        """Test that empty tickers list raises ValueError."""
        with pytest.raises(ValueError, match="tickers list cannot be empty"):
            AnalysisConfig(tickers=[])
    
    def test_non_list_tickers_raises_error(self):
        """Test that non-list tickers raises ValueError."""
        with pytest.raises(ValueError, match="tickers must be a list"):
            AnalysisConfig(tickers="THYAO")
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = AnalysisConfig(
            sample_size=1500,
            importance_threshold=0.002,
            start_date="2023-01-01",
            tickers=["THYAO"]
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['sample_size'] == 1500
        assert config_dict['importance_threshold'] == 0.002
        assert config_dict['start_date'] == "2023-01-01"
        assert config_dict['tickers'] == ["THYAO"]
        assert 'output_dir' in config_dict
        assert 'save_models' in config_dict


class TestAnalysisResult:
    """Test suite for AnalysisResult dataclass."""
    
    def test_create_result(self):
        """Test creating an AnalysisResult instance."""
        timestamp = datetime.now()
        config = {'sample_size': 1000, 'importance_threshold': 0.001}
        importance_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3'],
            'importance': [0.5, 0.3, 0.2]
        })
        
        result = AnalysisResult(
            timestamp=timestamp,
            config=config,
            importance_df=importance_df,
            blacklist=['f3'],
            baseline_ndcg3=0.62,
            optimized_ndcg3=0.65,
            improvement_pct=4.84,
            total_features=3,
            blacklisted_features=1,
            remaining_features=2,
            data_size=1000,
            tickers_analyzed=['THYAO', 'GARAN'],
            analysis_duration=120.5
        )
        
        assert result.timestamp == timestamp
        assert result.config == config
        assert len(result.importance_df) == 3
        assert result.blacklist == ['f3']
        assert result.baseline_ndcg3 == 0.62
        assert result.optimized_ndcg3 == 0.65
        assert result.improvement_pct == 4.84
        assert result.total_features == 3
        assert result.blacklisted_features == 1
        assert result.remaining_features == 2
        assert result.data_size == 1000
        assert result.tickers_analyzed == ['THYAO', 'GARAN']
        assert result.analysis_duration == 120.5
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        timestamp = datetime(2023, 6, 15, 10, 30, 0)
        config = {'sample_size': 1000}
        importance_df = pd.DataFrame({'feature': ['f1'], 'importance': [0.5]})
        
        result = AnalysisResult(
            timestamp=timestamp,
            config=config,
            importance_df=importance_df,
            blacklist=['f2'],
            baseline_ndcg3=0.62,
            optimized_ndcg3=0.65,
            improvement_pct=4.84,
            total_features=2,
            blacklisted_features=1,
            remaining_features=1,
            data_size=500,
            tickers_analyzed=['THYAO'],
            analysis_duration=60.0
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['timestamp'] == '2023-06-15T10:30:00'
        assert result_dict['config'] == config
        assert result_dict['blacklist'] == ['f2']
        assert result_dict['baseline_ndcg3'] == 0.62
        assert result_dict['optimized_ndcg3'] == 0.65
        assert result_dict['improvement_pct'] == 4.84
        assert result_dict['total_features'] == 2
        assert result_dict['blacklisted_features'] == 1
        assert result_dict['remaining_features'] == 1
        assert result_dict['data_size'] == 500
        assert result_dict['tickers_analyzed'] == ['THYAO']
        assert result_dict['analysis_duration'] == 60.0
        # DataFrame should not be in dict
        assert 'importance_df' not in result_dict
    
    def test_summary(self):
        """Test summary string generation."""
        timestamp = datetime(2023, 6, 15, 10, 30, 0)
        config = {
            'sample_size': 1000,
            'importance_threshold': 0.001,
            'start_date': '2023-01-01',
            'end_date': '2023-06-15'
        }
        importance_df = pd.DataFrame({'feature': ['f1'], 'importance': [0.5]})
        
        result = AnalysisResult(
            timestamp=timestamp,
            config=config,
            importance_df=importance_df,
            blacklist=['f2', 'f3'],
            baseline_ndcg3=0.6217,
            optimized_ndcg3=0.6500,
            improvement_pct=4.55,
            total_features=10,
            blacklisted_features=2,
            remaining_features=8,
            data_size=5000,
            tickers_analyzed=['THYAO', 'GARAN', 'EREGL'],
            analysis_duration=125.75
        )
        
        summary = result.summary()
        
        # Check that key information is in the summary
        assert '2023-06-15 10:30:00' in summary
        assert '125.75' in summary
        assert '3' in summary  # tickers count
        assert '5000' in summary  # data size
        assert '10' in summary  # total features
        assert '2' in summary  # blacklisted
        assert '8' in summary  # remaining
        assert '0.6217' in summary  # baseline
        assert '0.6500' in summary  # optimized
        assert '4.55' in summary or '+4.55' in summary  # improvement
        assert '1000' in summary  # sample size
        assert '0.001' in summary  # threshold
