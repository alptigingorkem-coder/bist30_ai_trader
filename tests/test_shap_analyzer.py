"""
Unit tests for SHAP Analyzer module.

Tests the SHAPAnalyzer class including TreeExplainer creation,
SHAP value computation, multi-class handling, and error handling.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.1
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, MagicMock, patch
from scripts.analysis.shap_analyzer import SHAPAnalyzer


class TestSHAPAnalyzerInit:
    """Test suite for SHAPAnalyzer initialization."""
    
    def test_init_with_valid_model(self):
        """Test initialization with valid model."""
        model = Mock()
        analyzer = SHAPAnalyzer(model, sample_size=500)
        
        assert analyzer.model == model
        assert analyzer.sample_size == 500
        assert analyzer.explainer is None
    
    def test_init_with_default_sample_size(self):
        """Test initialization with default sample size."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        assert analyzer.sample_size == 1000
    
    def test_init_with_none_model_raises_error(self):
        """Test that None model raises ValueError."""
        with pytest.raises(ValueError, match="Model cannot be None"):
            SHAPAnalyzer(None)
    
    def test_init_with_negative_sample_size_raises_error(self):
        """Test that negative sample_size raises ValueError."""
        model = Mock()
        with pytest.raises(ValueError, match="sample_size must be positive"):
            SHAPAnalyzer(model, sample_size=-100)
    
    def test_init_with_zero_sample_size_raises_error(self):
        """Test that zero sample_size raises ValueError."""
        model = Mock()
        with pytest.raises(ValueError, match="sample_size must be positive"):
            SHAPAnalyzer(model, sample_size=0)


class TestSHAPAnalyzerSampling:
    """Test suite for data sampling logic."""
    
    def test_sample_data_small_dataset(self):
        """Test that small datasets (<= 1000 rows) are not sampled."""
        model = Mock()
        analyzer = SHAPAnalyzer(model, sample_size=1000)
        
        X = pd.DataFrame(np.random.rand(500, 10))
        X_sampled = analyzer._sample_data(X)
        
        assert len(X_sampled) == 500
        assert X_sampled.equals(X)
    
    def test_sample_data_large_dataset(self):
        """Test that large datasets (> 1000 rows) are sampled."""
        model = Mock()
        analyzer = SHAPAnalyzer(model, sample_size=1000)
        
        X = pd.DataFrame(np.random.rand(5000, 10))
        X_sampled = analyzer._sample_data(X)
        
        assert len(X_sampled) == 1000
        assert len(X_sampled) < len(X)
    
    def test_sample_data_respects_sample_size(self):
        """Test that sampling respects the configured sample_size."""
        model = Mock()
        analyzer = SHAPAnalyzer(model, sample_size=500)
        
        X = pd.DataFrame(np.random.rand(2000, 10))
        X_sampled = analyzer._sample_data(X)
        
        assert len(X_sampled) == 500


class TestSHAPAnalyzerMulticlassHandling:
    """Test suite for multi-class SHAP output handling."""
    
    def test_handle_2d_array(self):
        """Test handling of 2D array (binary/regression)."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        shap_values = np.random.rand(100, 10)
        result = analyzer._handle_multiclass_output(shap_values)
        
        assert result.shape == (100, 10)
        assert isinstance(result, np.ndarray)

    
    def test_handle_3d_array(self):
        """Test handling of 3D array (multi-class)."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        # 3 classes, 100 samples, 10 features
        shap_values = np.random.rand(3, 100, 10)
        result = analyzer._handle_multiclass_output(shap_values)
        
        assert result.shape == (100, 10)
        assert isinstance(result, np.ndarray)
    
    def test_handle_list_of_arrays(self):
        """Test handling of list of arrays (multi-class)."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        # List of 3 arrays, each (100, 10)
        shap_values = [np.random.rand(100, 10) for _ in range(3)]
        result = analyzer._handle_multiclass_output(shap_values)
        
        assert result.shape == (100, 10)
        assert isinstance(result, np.ndarray)
    
    def test_handle_invalid_format_raises_error(self):
        """Test that invalid format raises ValueError."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        # 1D array is invalid
        shap_values = np.random.rand(100)
        with pytest.raises(ValueError, match="Unexpected SHAP values format"):
            analyzer._handle_multiclass_output(shap_values)


class TestSHAPAnalyzerValidation:
    """Test suite for SHAP value validation."""
    
    def test_validate_valid_shap_values(self):
        """Test validation passes for valid SHAP values."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        shap_values = np.random.rand(100, 10)
        # Should not raise any exception
        analyzer._validate_shap_values(shap_values)
    
    def test_validate_nan_values_raises_error(self):
        """Test that NaN values raise ValueError."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        shap_values = np.random.rand(100, 10)
        shap_values[0, 0] = np.nan
        
        with pytest.raises(ValueError, match="SHAP values contain .* NaN values"):
            analyzer._validate_shap_values(shap_values)

    
    def test_validate_inf_values_raises_error(self):
        """Test that Inf values raise ValueError."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        shap_values = np.random.rand(100, 10)
        shap_values[0, 0] = np.inf
        
        with pytest.raises(ValueError, match="SHAP values contain .* Inf values"):
            analyzer._validate_shap_values(shap_values)


class TestSHAPAnalyzerComputeImportance:
    """Test suite for compute_importance method."""
    
    @patch('scripts.analysis.shap_analyzer.SHAPAnalyzer._create_explainer')
    def test_compute_importance_empty_dataframe_raises_error(self, mock_explainer):
        """Test that empty DataFrame raises ValueError."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        X = pd.DataFrame()
        with pytest.raises(ValueError, match="Feature matrix X cannot be empty"):
            analyzer.compute_importance(X)
    
    @patch('scripts.analysis.shap_analyzer.SHAPAnalyzer._create_explainer')
    def test_compute_importance_returns_sorted_dataframe(self, mock_explainer):
        """Test that compute_importance returns sorted DataFrame."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        # Mock explainer
        mock_exp = Mock()
        mock_exp.shap_values.return_value = np.array([
            [0.1, 0.5, 0.3],
            [0.2, 0.4, 0.6],
            [0.3, 0.3, 0.4]
        ])
        mock_explainer.return_value = mock_exp
        
        X = pd.DataFrame(
            np.random.rand(3, 3),
            columns=['feature_a', 'feature_b', 'feature_c']
        )
        
        result = analyzer.compute_importance(X)
        
        # Check result structure
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ['feature', 'importance']
        assert len(result) == 3
        
        # Check sorting (descending order)
        assert result['importance'].is_monotonic_decreasing

    
    @patch('scripts.analysis.shap_analyzer.SHAPAnalyzer._create_explainer')
    def test_compute_importance_with_multiclass_output(self, mock_explainer):
        """Test compute_importance with multi-class SHAP output."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        # Mock explainer with multi-class output (list of arrays)
        mock_exp = Mock()
        mock_exp.shap_values.return_value = [
            np.array([[0.1, 0.2], [0.3, 0.4]]),
            np.array([[0.2, 0.3], [0.4, 0.5]]),
            np.array([[0.3, 0.4], [0.5, 0.6]])
        ]
        mock_explainer.return_value = mock_exp
        
        X = pd.DataFrame(
            np.random.rand(2, 2),
            columns=['feature_1', 'feature_2']
        )
        
        result = analyzer.compute_importance(X)
        
        # Should successfully handle multi-class output
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result['importance'].is_monotonic_decreasing


class TestSHAPAnalyzerCreateExplainer:
    """Test suite for TreeExplainer creation."""
    
    def test_create_explainer_success(self):
        """Test successful TreeExplainer creation."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        mock_explainer = Mock()
        analyzer._shap.TreeExplainer = Mock(return_value=mock_explainer)
        
        result = analyzer._create_explainer()
        
        assert result == mock_explainer
        assert analyzer.explainer == mock_explainer
        analyzer._shap.TreeExplainer.assert_called_once_with(model)
    
    def test_create_explainer_reuses_existing(self):
        """Test that explainer is reused if already created."""
        model = Mock()
        analyzer = SHAPAnalyzer(model)
        
        mock_explainer = Mock()
        analyzer.explainer = mock_explainer
        
        # Mock TreeExplainer to track calls
        analyzer._shap.TreeExplainer = Mock()
        
        result = analyzer._create_explainer()
        
        assert result == mock_explainer
        # TreeExplainer should not be called again
        analyzer._shap.TreeExplainer.assert_not_called()
