"""
Unit tests for Model Comparator module.

Tests the ModelComparator class including NDCG@3 calculation,
model comparison logic, improvement percentage calculation,
and performance degradation warnings.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.4, 8.5
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, MagicMock, patch
from scripts.analysis.model_comparator import ModelComparator


class TestModelComparatorInit:
    """Test suite for ModelComparator initialization."""
    
    def test_init(self):
        """Test initialization."""
        comparator = ModelComparator()
        assert comparator is not None


class TestModelComparatorCompare:
    """Test suite for model comparison logic."""
    
    def test_compare_with_valid_models(self):
        """Test comparison with valid baseline and optimized models."""
        # Create mock models
        baseline_model = Mock()
        baseline_model.model = Mock()
        baseline_model.feature_names = ['f1', 'f2', 'f3', 'f4', 'f5']
        
        optimized_model = Mock()
        optimized_model.model = Mock()
        optimized_model.feature_names = ['f1', 'f2', 'f3']
        
        # Create test data
        test_data = pd.DataFrame({
            'f1': [1, 2, 3],
            'f2': [4, 5, 6],
            'f3': [7, 8, 9],
            'f4': [10, 11, 12],
            'f5': [13, 14, 15]
        })
        
        config_module = Mock()
        
        comparator = ModelComparator()
        
        # Mock _calculate_ndcg to return fixed values
        with patch.object(comparator, '_calculate_ndcg') as mock_ndcg:
            mock_ndcg.side_effect = [0.62, 0.65]  # baseline, optimized
            
            result = comparator.compare(
                baseline_model,
                optimized_model,
                test_data,
                config_module
            )
        
        assert result['baseline_ndcg3'] == 0.62
        assert result['optimized_ndcg3'] == 0.65
        assert result['baseline_features'] == 5
        assert result['optimized_features'] == 3
        assert abs(result['improvement_pct'] - 4.84) < 0.01
    
    def test_compare_with_none_baseline_model_raises_error(self):
        """Test that None baseline model raises ValueError."""
        optimized_model = Mock()
        optimized_model.model = Mock()
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with pytest.raises(ValueError, match="baseline_model must be a trained model"):
            comparator.compare(None, optimized_model, test_data, config_module)
    
    def test_compare_with_untrained_baseline_model_raises_error(self):
        """Test that untrained baseline model raises ValueError."""
        baseline_model = Mock()
        baseline_model.model = None
        
        optimized_model = Mock()
        optimized_model.model = Mock()
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with pytest.raises(ValueError, match="baseline_model must be a trained model"):
            comparator.compare(baseline_model, optimized_model, test_data, config_module)
    
    def test_compare_with_none_optimized_model_raises_error(self):
        """Test that None optimized model raises ValueError."""
        baseline_model = Mock()
        baseline_model.model = Mock()
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with pytest.raises(ValueError, match="optimized_model must be a trained model"):
            comparator.compare(baseline_model, None, test_data, config_module)
    
    def test_compare_with_empty_test_data_raises_error(self):
        """Test that empty test data raises ValueError."""
        baseline_model = Mock()
        baseline_model.model = Mock()
        
        optimized_model = Mock()
        optimized_model.model = Mock()
        
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with pytest.raises(ValueError, match="test_data cannot be empty"):
            comparator.compare(baseline_model, optimized_model, pd.DataFrame(), config_module)
    
    def test_compare_with_performance_degradation_logs_warning(self, caplog):
        """Test that performance degradation triggers warning log."""
        baseline_model = Mock()
        baseline_model.model = Mock()
        baseline_model.feature_names = ['f1', 'f2', 'f3']
        
        optimized_model = Mock()
        optimized_model.model = Mock()
        optimized_model.feature_names = ['f1', 'f2']
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        # Mock _calculate_ndcg to return degraded performance
        with patch.object(comparator, '_calculate_ndcg') as mock_ndcg:
            mock_ndcg.side_effect = [0.65, 0.60]  # baseline better than optimized
            
            result = comparator.compare(
                baseline_model,
                optimized_model,
                test_data,
                config_module
            )
        
        assert result['baseline_ndcg3'] == 0.65
        assert result['optimized_ndcg3'] == 0.60
        assert result['improvement_pct'] < 0
        
        # Check that warning was logged
        assert any("Performance degradation detected" in record.message 
                   for record in caplog.records)
    
    def test_compare_with_zero_baseline_ndcg(self, caplog):
        """Test handling of zero baseline NDCG."""
        baseline_model = Mock()
        baseline_model.model = Mock()
        baseline_model.feature_names = ['f1', 'f2']
        
        optimized_model = Mock()
        optimized_model.model = Mock()
        optimized_model.feature_names = ['f1']
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        # Mock _calculate_ndcg to return zero baseline
        with patch.object(comparator, '_calculate_ndcg') as mock_ndcg:
            mock_ndcg.side_effect = [0.0, 0.50]
            
            result = comparator.compare(
                baseline_model,
                optimized_model,
                test_data,
                config_module
            )
        
        assert result['baseline_ndcg3'] == 0.0
        assert result['optimized_ndcg3'] == 0.50
        assert result['improvement_pct'] == 0.0
        
        # Check that warning was logged
        assert any("Baseline NDCG@3 is 0" in record.message 
                   for record in caplog.records)
    
    def test_compare_feature_count_validation(self, caplog):
        """Test that optimized model with more features triggers warning."""
        baseline_model = Mock()
        baseline_model.model = Mock()
        baseline_model.feature_names = ['f1', 'f2']
        
        optimized_model = Mock()
        optimized_model.model = Mock()
        optimized_model.feature_names = ['f1', 'f2', 'f3', 'f4']
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with patch.object(comparator, '_calculate_ndcg') as mock_ndcg:
            mock_ndcg.side_effect = [0.62, 0.65]
            
            result = comparator.compare(
                baseline_model,
                optimized_model,
                test_data,
                config_module
            )
        
        assert result['baseline_features'] == 2
        assert result['optimized_features'] == 4
        
        # Check that warning was logged
        assert any("Optimized model has MORE features" in record.message 
                   for record in caplog.records)


class TestModelComparatorCalculateNDCG:
    """Test suite for NDCG@k calculation."""
    
    @patch('models.ranking_model.RankingModel')
    def test_calculate_ndcg_with_valid_data(self, mock_ranking_model_class):
        """Test NDCG calculation with valid data."""
        # Create mock model
        model = Mock()
        model.model = Mock()
        model.feature_names = ['f1', 'f2', 'f3']
        
        # Mock predictions
        model.model.predict.return_value = np.array([0.9, 0.7, 0.5, 0.8, 0.6, 0.4])
        
        # Create test data
        test_data = pd.DataFrame({
            'f1': [1, 2, 3, 4, 5, 6],
            'f2': [7, 8, 9, 10, 11, 12],
            'f3': [13, 14, 15, 16, 17, 18]
        })
        
        # Mock RankingModel instance
        mock_test_model = Mock()
        mock_ranking_model_class.return_value = mock_test_model
        
        # Mock prepare_data to return test features and labels
        X_test = pd.DataFrame({
            'f1': [1, 2, 3, 4, 5, 6],
            'f2': [7, 8, 9, 10, 11, 12],
            'f3': [13, 14, 15, 16, 17, 18]
        })
        y_test = pd.Series([3, 2, 1, 3, 2, 1])  # Rankings
        groups = np.array([3, 3])  # Two groups of 3
        
        mock_test_model.prepare_data.return_value = (X_test, y_test, groups)
        
        config_module = Mock()
        
        comparator = ModelComparator()
        ndcg = comparator._calculate_ndcg(model, test_data, config_module, k=3)
        
        assert isinstance(ndcg, float)
        assert 0.0 <= ndcg <= 1.0
    
    def test_calculate_ndcg_with_none_model_raises_error(self):
        """Test that None model raises ValueError."""
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with pytest.raises(ValueError, match="Model must be trained"):
            comparator._calculate_ndcg(None, test_data, config_module, k=3)
    
    def test_calculate_ndcg_with_untrained_model_raises_error(self):
        """Test that untrained model raises ValueError."""
        model = Mock()
        model.model = None
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with pytest.raises(ValueError, match="Model must be trained"):
            comparator._calculate_ndcg(model, test_data, config_module, k=3)
    
    def test_calculate_ndcg_with_empty_data_raises_error(self):
        """Test that empty data raises ValueError."""
        model = Mock()
        model.model = Mock()
        
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with pytest.raises(ValueError, match="Data cannot be empty"):
            comparator._calculate_ndcg(model, pd.DataFrame(), config_module, k=3)
    
    def test_calculate_ndcg_with_invalid_k_raises_error(self):
        """Test that invalid k raises ValueError."""
        model = Mock()
        model.model = Mock()
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with pytest.raises(ValueError, match="k must be positive"):
            comparator._calculate_ndcg(model, test_data, config_module, k=0)
        
        with pytest.raises(ValueError, match="k must be positive"):
            comparator._calculate_ndcg(model, test_data, config_module, k=-1)
    
    @patch('models.ranking_model.RankingModel')
    def test_calculate_ndcg_with_empty_prepared_data_returns_zero(self, mock_ranking_model_class):
        """Test that empty prepared data returns NDCG=0."""
        model = Mock()
        model.model = Mock()
        model.feature_names = ['f1', 'f2']
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        
        # Mock RankingModel to return empty data
        mock_test_model = Mock()
        mock_ranking_model_class.return_value = mock_test_model
        mock_test_model.prepare_data.return_value = (pd.DataFrame(), pd.Series(), np.array([]))
        
        config_module = Mock()
        
        comparator = ModelComparator()
        ndcg = comparator._calculate_ndcg(model, test_data, config_module, k=3)
        
        assert ndcg == 0.0
    
    @patch('models.ranking_model.RankingModel')
    def test_calculate_ndcg_with_nan_predictions_returns_zero(self, mock_ranking_model_class):
        """Test that NaN predictions return NDCG=0."""
        model = Mock()
        model.model = Mock()
        model.feature_names = ['f1', 'f2']
        
        # Mock predictions with NaN
        model.model.predict.return_value = np.array([0.9, np.nan, 0.5])
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        
        # Mock RankingModel
        mock_test_model = Mock()
        mock_ranking_model_class.return_value = mock_test_model
        
        X_test = pd.DataFrame({'f1': [1, 2, 3], 'f2': [4, 5, 6]})
        y_test = pd.Series([3, 2, 1])
        groups = np.array([3])
        
        mock_test_model.prepare_data.return_value = (X_test, y_test, groups)
        
        config_module = Mock()
        
        comparator = ModelComparator()
        ndcg = comparator._calculate_ndcg(model, test_data, config_module, k=3)
        
        assert ndcg == 0.0
    
    @patch('models.ranking_model.RankingModel')
    def test_calculate_ndcg_validates_range(self, mock_ranking_model_class):
        """Test that NDCG is validated to be in [0, 1] range."""
        model = Mock()
        model.model = Mock()
        model.feature_names = ['f1', 'f2']
        
        # Mock predictions
        model.model.predict.return_value = np.array([0.9, 0.7, 0.5])
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        
        # Mock RankingModel
        mock_test_model = Mock()
        mock_ranking_model_class.return_value = mock_test_model
        
        X_test = pd.DataFrame({'f1': [1, 2, 3], 'f2': [4, 5, 6]})
        y_test = pd.Series([3, 2, 1])
        groups = np.array([3])
        
        mock_test_model.prepare_data.return_value = (X_test, y_test, groups)
        
        config_module = Mock()
        
        comparator = ModelComparator()
        ndcg = comparator._calculate_ndcg(model, test_data, config_module, k=3)
        
        # NDCG should be in valid range
        assert 0.0 <= ndcg <= 1.0
    
    @patch('models.ranking_model.RankingModel')
    def test_calculate_ndcg_skips_small_groups(self, mock_ranking_model_class):
        """Test that groups smaller than k are skipped."""
        model = Mock()
        model.model = Mock()
        model.feature_names = ['f1', 'f2']
        
        # Mock predictions
        model.model.predict.return_value = np.array([0.9, 0.7, 0.5, 0.8])
        
        test_data = pd.DataFrame({'f1': [1, 2, 3, 4]})
        
        # Mock RankingModel
        mock_test_model = Mock()
        mock_ranking_model_class.return_value = mock_test_model
        
        X_test = pd.DataFrame({'f1': [1, 2, 3, 4], 'f2': [5, 6, 7, 8]})
        y_test = pd.Series([2, 1, 3, 2])
        groups = np.array([2, 2])  # Two groups of 2, but k=3
        
        mock_test_model.prepare_data.return_value = (X_test, y_test, groups)
        
        config_module = Mock()
        
        comparator = ModelComparator()
        ndcg = comparator._calculate_ndcg(model, test_data, config_module, k=3)
        
        # Should return 0 since all groups are too small
        assert ndcg == 0.0
    
    @patch('models.ranking_model.RankingModel')
    def test_calculate_ndcg_handles_no_common_features(self, mock_ranking_model_class):
        """Test handling when model and test data have no common features."""
        model = Mock()
        model.model = Mock()
        model.feature_names = ['f1', 'f2']
        
        test_data = pd.DataFrame({'f3': [1, 2, 3], 'f4': [4, 5, 6]})
        
        # Mock RankingModel
        mock_test_model = Mock()
        mock_ranking_model_class.return_value = mock_test_model
        
        X_test = pd.DataFrame({'f3': [1, 2, 3], 'f4': [4, 5, 6]})
        y_test = pd.Series([3, 2, 1])
        groups = np.array([3])
        
        mock_test_model.prepare_data.return_value = (X_test, y_test, groups)
        
        config_module = Mock()
        
        comparator = ModelComparator()
        ndcg = comparator._calculate_ndcg(model, test_data, config_module, k=3)
        
        assert ndcg == 0.0


class TestModelComparatorImprovementCalculation:
    """Test suite for improvement percentage calculation."""
    
    def test_improvement_calculation_positive(self):
        """Test improvement percentage calculation with positive improvement."""
        baseline_model = Mock()
        baseline_model.model = Mock()
        baseline_model.feature_names = ['f1', 'f2']
        
        optimized_model = Mock()
        optimized_model.model = Mock()
        optimized_model.feature_names = ['f1']
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with patch.object(comparator, '_calculate_ndcg') as mock_ndcg:
            mock_ndcg.side_effect = [0.6217, 0.6500]
            
            result = comparator.compare(
                baseline_model,
                optimized_model,
                test_data,
                config_module
            )
        
        # Expected: ((0.6500 - 0.6217) / 0.6217) * 100 = 4.55%
        assert abs(result['improvement_pct'] - 4.55) < 0.01
    
    def test_improvement_calculation_negative(self):
        """Test improvement percentage calculation with negative improvement."""
        baseline_model = Mock()
        baseline_model.model = Mock()
        baseline_model.feature_names = ['f1', 'f2']
        
        optimized_model = Mock()
        optimized_model.model = Mock()
        optimized_model.feature_names = ['f1']
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with patch.object(comparator, '_calculate_ndcg') as mock_ndcg:
            mock_ndcg.side_effect = [0.65, 0.60]
            
            result = comparator.compare(
                baseline_model,
                optimized_model,
                test_data,
                config_module
            )
        
        # Expected: ((0.60 - 0.65) / 0.65) * 100 = -7.69%
        assert abs(result['improvement_pct'] - (-7.69)) < 0.01
    
    def test_improvement_calculation_no_change(self):
        """Test improvement percentage calculation with no change."""
        baseline_model = Mock()
        baseline_model.model = Mock()
        baseline_model.feature_names = ['f1', 'f2']
        
        optimized_model = Mock()
        optimized_model.model = Mock()
        optimized_model.feature_names = ['f1']
        
        test_data = pd.DataFrame({'f1': [1, 2, 3]})
        config_module = Mock()
        
        comparator = ModelComparator()
        
        with patch.object(comparator, '_calculate_ndcg') as mock_ndcg:
            mock_ndcg.side_effect = [0.62, 0.62]
            
            result = comparator.compare(
                baseline_model,
                optimized_model,
                test_data,
                config_module
            )
        
        assert result['improvement_pct'] == 0.0
