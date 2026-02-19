"""
Integration tests for FeatureSelector with SHAPAnalyzer

Tests the integration between SHAP analysis and feature selection.

Requirements: 1.2, 1.4, 2.1, 2.2, 8.2
"""

import tempfile
import os
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock
from scripts.analysis.shap_analyzer import SHAPAnalyzer
from scripts.analysis.feature_selector import FeatureSelector


class TestSHAPAnalyzerFeatureSelectorIntegration:
    """Test integration between SHAPAnalyzer and FeatureSelector"""
    
    def test_shap_to_selector_workflow(self):
        """Test complete workflow from SHAP analysis to blacklist creation"""
        # Create mock model
        mock_model = Mock()
        
        # Create mock SHAP module
        mock_shap = MagicMock()
        mock_explainer = MagicMock()
        
        # Mock SHAP values (2D array: samples x features)
        mock_shap_values = np.array([
            [0.1, 0.005, 0.02, 0.008, 0.15],
            [0.12, 0.004, 0.018, 0.009, 0.14],
            [0.09, 0.006, 0.021, 0.007, 0.16]
        ])
        
        mock_explainer.shap_values.return_value = mock_shap_values
        mock_shap.TreeExplainer.return_value = mock_explainer
        
        # Create SHAPAnalyzer with mocked SHAP
        analyzer = SHAPAnalyzer(mock_model, sample_size=1000)
        analyzer._shap = mock_shap
        
        # Create feature matrix
        X = pd.DataFrame({
            'f1': [1, 2, 3],
            'f2': [4, 5, 6],
            'f3': [7, 8, 9],
            'f4': [10, 11, 12],
            'f5': [13, 14, 15]
        })
        
        # Compute importance
        importance_df = analyzer.compute_importance(X)
        
        # Verify importance DataFrame structure
        assert 'feature' in importance_df.columns
        assert 'importance' in importance_df.columns
        assert len(importance_df) == 5
        
        # Verify sorting (descending order)
        assert importance_df['importance'].is_monotonic_decreasing
        
        # Create FeatureSelector
        selector = FeatureSelector(threshold=0.01)
        
        # Create blacklist
        blacklist = selector.create_blacklist(importance_df)
        
        # Verify blacklist (f2 and f4 should be blacklisted based on mock values)
        assert len(blacklist) > 0
        assert all(isinstance(f, str) for f in blacklist)
        
        # Validate blacklist
        is_valid = selector.validate_blacklist(blacklist, len(importance_df))
        assert is_valid is True  # Should be within 80% limit
    
    def test_shap_to_selector_with_persistence(self):
        """Test workflow including blacklist save/load"""
        # Create mock model and SHAP
        mock_model = Mock()
        mock_shap = MagicMock()
        mock_explainer = MagicMock()
        
        # Mock SHAP values with clear low/high importance features
        mock_shap_values = np.array([
            [0.5, 0.001, 0.4, 0.002, 0.3],
            [0.6, 0.0015, 0.35, 0.0018, 0.32]
        ])
        
        mock_explainer.shap_values.return_value = mock_shap_values
        mock_shap.TreeExplainer.return_value = mock_explainer
        
        # Create analyzer
        analyzer = SHAPAnalyzer(mock_model, sample_size=1000)
        analyzer._shap = mock_shap
        
        # Create feature matrix
        X = pd.DataFrame({
            'high_imp_1': [1, 2],
            'low_imp_1': [3, 4],
            'high_imp_2': [5, 6],
            'low_imp_2': [7, 8],
            'high_imp_3': [9, 10]
        })
        
        # Compute importance
        importance_df = analyzer.compute_importance(X)
        
        # Create selector with threshold that will blacklist low importance features
        selector = FeatureSelector(threshold=0.01)
        blacklist = selector.create_blacklist(importance_df)
        
        # Save and load blacklist
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test_blacklist.json')
            
            # Save
            selector.save_blacklist(blacklist, path)
            
            # Load
            loaded_blacklist = selector.load_blacklist(path)
            
            # Verify round-trip
            assert loaded_blacklist == blacklist
            
            # Verify we can use loaded blacklist for validation
            is_valid = selector.validate_blacklist(loaded_blacklist, len(importance_df))
            assert isinstance(is_valid, bool)
    
    def test_selector_with_all_high_importance_features(self):
        """Test selector when all features have high importance"""
        # Create mock model and SHAP
        mock_model = Mock()
        mock_shap = MagicMock()
        mock_explainer = MagicMock()
        
        # All features have high importance
        mock_shap_values = np.array([
            [0.5, 0.4, 0.6, 0.3, 0.7],
            [0.55, 0.45, 0.55, 0.35, 0.65]
        ])
        
        mock_explainer.shap_values.return_value = mock_shap_values
        mock_shap.TreeExplainer.return_value = mock_explainer
        
        # Create analyzer
        analyzer = SHAPAnalyzer(mock_model, sample_size=1000)
        analyzer._shap = mock_shap
        
        # Create feature matrix
        X = pd.DataFrame({
            'f1': [1, 2],
            'f2': [3, 4],
            'f3': [5, 6],
            'f4': [7, 8],
            'f5': [9, 10]
        })
        
        # Compute importance
        importance_df = analyzer.compute_importance(X)
        
        # Create selector
        selector = FeatureSelector(threshold=0.01)
        blacklist = selector.create_blacklist(importance_df)
        
        # No features should be blacklisted
        assert len(blacklist) == 0
        
        # Validation should pass
        is_valid = selector.validate_blacklist(blacklist, len(importance_df))
        assert is_valid is True
    
    def test_selector_with_excessive_blacklist_warning(self):
        """Test selector when blacklist would exceed 80% limit"""
        # Create mock model and SHAP
        mock_model = Mock()
        mock_shap = MagicMock()
        mock_explainer = MagicMock()
        
        # Most features have low importance
        mock_shap_values = np.array([
            [0.001, 0.002, 0.0015, 0.0018, 0.0012, 0.0019, 0.0011, 0.0016, 0.0014, 0.5],
        ])
        
        mock_explainer.shap_values.return_value = mock_shap_values
        mock_shap.TreeExplainer.return_value = mock_explainer
        
        # Create analyzer
        analyzer = SHAPAnalyzer(mock_model, sample_size=1000)
        analyzer._shap = mock_shap
        
        # Create feature matrix with 10 features
        X = pd.DataFrame({
            f'f{i}': [i] for i in range(10)
        })
        
        # Compute importance
        importance_df = analyzer.compute_importance(X)
        
        # Create selector with threshold that will blacklist most features
        selector = FeatureSelector(threshold=0.01)
        blacklist = selector.create_blacklist(importance_df)
        
        # Most features should be blacklisted
        assert len(blacklist) >= 8
        
        # Validation should fail (exceeds 80%)
        is_valid = selector.validate_blacklist(blacklist, len(importance_df))
        assert is_valid is False
