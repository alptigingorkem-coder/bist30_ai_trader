"""
Unit tests for FeatureImportanceVisualizer

Tests cover:
- Initialization and output directory management
- Top features bar chart creation
- SHAP summary plot creation
- Model comparison chart creation
- Error handling and edge cases

Requirements: 4.1, 4.2, 4.3
"""

import os
import pytest
import numpy as np
import pandas as pd
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.analysis.visualizer import FeatureImportanceVisualizer


class TestFeatureImportanceVisualizerInit:
    """Test FeatureImportanceVisualizer initialization"""
    
    def test_init_creates_output_directory(self):
        """Test that initialization creates output directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "test_output")
            visualizer = FeatureImportanceVisualizer(output_dir=output_dir)
            
            assert os.path.exists(output_dir)
            assert visualizer.output_dir == output_dir
    
    def test_init_with_existing_directory(self):
        """Test initialization with existing directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            visualizer = FeatureImportanceVisualizer(output_dir=tmpdir)
            assert visualizer.output_dir == tmpdir
    
    def test_init_with_empty_output_dir_raises_error(self):
        """Test that empty output_dir raises ValueError"""
        with pytest.raises(ValueError, match="output_dir cannot be None or empty"):
            FeatureImportanceVisualizer(output_dir="")
    
    def test_init_with_none_output_dir_raises_error(self):
        """Test that None output_dir raises ValueError"""
        with pytest.raises(ValueError, match="output_dir cannot be None or empty"):
            FeatureImportanceVisualizer(output_dir=None)


class TestPlotTopFeatures:
    """Test plot_top_features method"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.tmpdir = tempfile.mkdtemp()
        self.visualizer = FeatureImportanceVisualizer(output_dir=self.tmpdir)
        
        # Create sample importance DataFrame
        self.importance_df = pd.DataFrame({
            'feature': [f'feature_{i}' for i in range(30)],
            'importance': np.linspace(1.0, 0.1, 30)
        })
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_plot_top_features_creates_file(self):
        """Test that plot_top_features creates PNG file"""
        filename = "test_top_features.png"
        self.visualizer.plot_top_features(self.importance_df, top_n=20, filename=filename)
        
        output_path = os.path.join(self.tmpdir, filename)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    
    def test_plot_top_features_with_custom_top_n(self):
        """Test plot_top_features with custom top_n"""
        filename = "test_top_10.png"
        self.visualizer.plot_top_features(self.importance_df, top_n=10, filename=filename)
        
        output_path = os.path.join(self.tmpdir, filename)
        assert os.path.exists(output_path)
    
    def test_plot_top_features_with_fewer_features_than_top_n(self):
        """Test plot_top_features when DataFrame has fewer features than top_n"""
        small_df = self.importance_df.head(5)
        filename = "test_small.png"
        
        self.visualizer.plot_top_features(small_df, top_n=20, filename=filename)
        
        output_path = os.path.join(self.tmpdir, filename)
        assert os.path.exists(output_path)
    
    def test_plot_top_features_with_empty_dataframe_raises_error(self):
        """Test that empty DataFrame raises ValueError"""
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="importance_df cannot be empty"):
            self.visualizer.plot_top_features(empty_df)
    
    def test_plot_top_features_with_none_dataframe_raises_error(self):
        """Test that None DataFrame raises ValueError"""
        with pytest.raises(ValueError, match="importance_df cannot be empty"):
            self.visualizer.plot_top_features(None)
    
    def test_plot_top_features_with_missing_feature_column_raises_error(self):
        """Test that missing 'feature' column raises ValueError"""
        invalid_df = pd.DataFrame({
            'name': ['f1', 'f2'],
            'importance': [0.5, 0.3]
        })
        
        with pytest.raises(ValueError, match="must contain 'feature' column"):
            self.visualizer.plot_top_features(invalid_df)
    
    def test_plot_top_features_with_missing_importance_column_raises_error(self):
        """Test that missing 'importance' column raises ValueError"""
        invalid_df = pd.DataFrame({
            'feature': ['f1', 'f2'],
            'value': [0.5, 0.3]
        })
        
        with pytest.raises(ValueError, match="must contain 'importance' column"):
            self.visualizer.plot_top_features(invalid_df)
    
    def test_plot_top_features_with_negative_top_n_raises_error(self):
        """Test that negative top_n raises ValueError"""
        with pytest.raises(ValueError, match="top_n must be positive"):
            self.visualizer.plot_top_features(self.importance_df, top_n=-5)
    
    def test_plot_top_features_with_zero_top_n_raises_error(self):
        """Test that zero top_n raises ValueError"""
        with pytest.raises(ValueError, match="top_n must be positive"):
            self.visualizer.plot_top_features(self.importance_df, top_n=0)


class TestPlotShapSummary:
    """Test plot_shap_summary method"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.tmpdir = tempfile.mkdtemp()
        self.visualizer = FeatureImportanceVisualizer(output_dir=self.tmpdir)
        
        # Create sample SHAP values and feature matrix
        n_samples = 100
        n_features = 10
        self.shap_values = np.random.randn(n_samples, n_features)
        self.X = pd.DataFrame(
            np.random.randn(n_samples, n_features),
            columns=[f'feature_{i}' for i in range(n_features)]
        )
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_plot_shap_summary_creates_file(self):
        """Test that plot_shap_summary creates PNG file"""
        # Create a mock shap module with summary_plot
        import sys
        mock_shap = MagicMock()
        mock_shap.summary_plot = MagicMock()
        sys.modules['shap'] = mock_shap
        
        try:
            filename = "test_shap_summary.png"
            self.visualizer.plot_shap_summary(self.shap_values, self.X, filename=filename)
            
            output_path = os.path.join(self.tmpdir, filename)
            assert os.path.exists(output_path)
            
            # Verify SHAP summary_plot was called
            mock_shap.summary_plot.assert_called_once()
        finally:
            # Clean up mock
            if 'shap' in sys.modules:
                del sys.modules['shap']
    
    def test_plot_shap_summary_with_none_shap_values_raises_error(self):
        """Test that None shap_values raises ValueError"""
        with pytest.raises(ValueError, match="shap_values cannot be None"):
            self.visualizer.plot_shap_summary(None, self.X)
    
    def test_plot_shap_summary_with_empty_X_raises_error(self):
        """Test that empty X raises ValueError"""
        empty_X = pd.DataFrame()
        
        with pytest.raises(ValueError, match="X cannot be empty"):
            self.visualizer.plot_shap_summary(self.shap_values, empty_X)
    
    def test_plot_shap_summary_with_none_X_raises_error(self):
        """Test that None X raises ValueError"""
        with pytest.raises(ValueError, match="X cannot be empty"):
            self.visualizer.plot_shap_summary(self.shap_values, None)
    
    def test_plot_shap_summary_with_non_array_shap_values_raises_error(self):
        """Test that non-array shap_values raises ValueError"""
        with pytest.raises(ValueError, match="shap_values must be numpy array"):
            self.visualizer.plot_shap_summary([1, 2, 3], self.X)
    
    def test_plot_shap_summary_with_mismatched_shapes_raises_error(self):
        """Test that mismatched shapes raise ValueError"""
        wrong_shape_shap = np.random.randn(100, 5)  # Wrong number of features
        
        with pytest.raises(ValueError, match="doesn't match"):
            self.visualizer.plot_shap_summary(wrong_shape_shap, self.X)


class TestPlotComparison:
    """Test plot_comparison method"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.tmpdir = tempfile.mkdtemp()
        self.visualizer = FeatureImportanceVisualizer(output_dir=self.tmpdir)
        
        # Create sample comparison results
        self.comparison_results = {
            'baseline_ndcg3': 0.6217,
            'optimized_ndcg3': 0.6500,
            'improvement_pct': 4.55,
            'baseline_features': 100,
            'optimized_features': 75
        }
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_plot_comparison_creates_file(self):
        """Test that plot_comparison creates PNG file"""
        filename = "test_comparison.png"
        self.visualizer.plot_comparison(self.comparison_results, filename=filename)
        
        output_path = os.path.join(self.tmpdir, filename)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    
    def test_plot_comparison_with_negative_improvement(self):
        """Test plot_comparison with negative improvement"""
        results = self.comparison_results.copy()
        results['optimized_ndcg3'] = 0.6000
        results['improvement_pct'] = -3.49
        
        filename = "test_negative_improvement.png"
        self.visualizer.plot_comparison(results, filename=filename)
        
        output_path = os.path.join(self.tmpdir, filename)
        assert os.path.exists(output_path)
    
    def test_plot_comparison_with_zero_improvement(self):
        """Test plot_comparison with zero improvement"""
        results = self.comparison_results.copy()
        results['optimized_ndcg3'] = results['baseline_ndcg3']
        results['improvement_pct'] = 0.0
        
        filename = "test_zero_improvement.png"
        self.visualizer.plot_comparison(results, filename=filename)
        
        output_path = os.path.join(self.tmpdir, filename)
        assert os.path.exists(output_path)
    
    def test_plot_comparison_with_none_results_raises_error(self):
        """Test that None comparison_results raises ValueError"""
        with pytest.raises(ValueError, match="comparison_results cannot be None"):
            self.visualizer.plot_comparison(None)
    
    def test_plot_comparison_with_missing_keys_raises_error(self):
        """Test that missing keys raise ValueError"""
        incomplete_results = {
            'baseline_ndcg3': 0.6217,
            'optimized_ndcg3': 0.6500
            # Missing other keys
        }
        
        with pytest.raises(ValueError, match="missing keys"):
            self.visualizer.plot_comparison(incomplete_results)
    
    def test_plot_comparison_with_all_required_keys(self):
        """Test that all required keys are validated"""
        # Remove each key one at a time and verify error
        required_keys = [
            'baseline_ndcg3', 'optimized_ndcg3', 'improvement_pct',
            'baseline_features', 'optimized_features'
        ]
        
        for key_to_remove in required_keys:
            results = self.comparison_results.copy()
            del results[key_to_remove]
            
            with pytest.raises(ValueError, match="missing keys"):
                self.visualizer.plot_comparison(results)


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_visualizer_with_single_feature(self):
        """Test visualizer with single feature"""
        with tempfile.TemporaryDirectory() as tmpdir:
            visualizer = FeatureImportanceVisualizer(output_dir=tmpdir)
            
            single_feature_df = pd.DataFrame({
                'feature': ['feature_1'],
                'importance': [0.5]
            })
            
            visualizer.plot_top_features(single_feature_df, top_n=20)
            
            output_path = os.path.join(tmpdir, "top_features.png")
            assert os.path.exists(output_path)
    
    def test_visualizer_with_very_long_feature_names(self):
        """Test visualizer with very long feature names"""
        with tempfile.TemporaryDirectory() as tmpdir:
            visualizer = FeatureImportanceVisualizer(output_dir=tmpdir)
            
            long_names_df = pd.DataFrame({
                'feature': [f'very_long_feature_name_that_might_cause_issues_{i}' for i in range(20)],
                'importance': np.linspace(1.0, 0.1, 20)
            })
            
            visualizer.plot_top_features(long_names_df, top_n=10)
            
            output_path = os.path.join(tmpdir, "top_features.png")
            assert os.path.exists(output_path)
    
    def test_visualizer_with_zero_importance_values(self):
        """Test visualizer with zero importance values"""
        with tempfile.TemporaryDirectory() as tmpdir:
            visualizer = FeatureImportanceVisualizer(output_dir=tmpdir)
            
            zero_importance_df = pd.DataFrame({
                'feature': [f'feature_{i}' for i in range(10)],
                'importance': [0.0] * 10
            })
            
            visualizer.plot_top_features(zero_importance_df, top_n=5)
            
            output_path = os.path.join(tmpdir, "top_features.png")
            assert os.path.exists(output_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
