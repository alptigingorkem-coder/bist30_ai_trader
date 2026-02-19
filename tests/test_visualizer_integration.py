"""
Integration tests for FeatureImportanceVisualizer with other components

Tests the visualizer working with real SHAP analyzer and feature selector outputs.

Requirements: 4.1, 4.2, 4.3
"""

import os
import pytest
import numpy as np
import pandas as pd
import tempfile
import shutil
from unittest.mock import MagicMock

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.analysis.visualizer import FeatureImportanceVisualizer
from scripts.analysis.feature_selector import FeatureSelector


class TestVisualizerIntegration:
    """Integration tests for visualizer with other components"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.tmpdir = tempfile.mkdtemp()
        self.visualizer = FeatureImportanceVisualizer(output_dir=self.tmpdir)
        
        # Create realistic feature importance data
        np.random.seed(42)
        n_features = 50
        self.importance_df = pd.DataFrame({
            'feature': [f'feature_{i}' for i in range(n_features)],
            'importance': np.random.exponential(scale=0.1, size=n_features)
        }).sort_values('importance', ascending=False).reset_index(drop=True)
        
        # Create realistic SHAP values
        n_samples = 200
        self.shap_values = np.random.randn(n_samples, n_features) * 0.1
        self.X = pd.DataFrame(
            np.random.randn(n_samples, n_features),
            columns=[f'feature_{i}' for i in range(n_features)]
        )
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_visualizer_with_feature_selector_output(self):
        """Test visualizer with feature selector output"""
        # Create feature selector
        selector = FeatureSelector(threshold=0.05)
        
        # Create blacklist
        blacklist = selector.create_blacklist(self.importance_df)
        
        # Visualize top features (excluding blacklisted ones)
        remaining_features = self.importance_df[
            ~self.importance_df['feature'].isin(blacklist)
        ]
        
        self.visualizer.plot_top_features(remaining_features, top_n=20)
        
        output_path = os.path.join(self.tmpdir, "top_features.png")
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    
    def test_visualizer_creates_all_plots(self):
        """Test that visualizer can create all plot types"""
        # Mock shap module for summary plot
        import sys
        mock_shap = MagicMock()
        mock_shap.summary_plot = MagicMock()
        sys.modules['shap'] = mock_shap
        
        try:
            # Create all three plot types
            self.visualizer.plot_top_features(self.importance_df, top_n=20)
            self.visualizer.plot_shap_summary(self.shap_values, self.X)
            
            comparison_results = {
                'baseline_ndcg3': 0.6217,
                'optimized_ndcg3': 0.6500,
                'improvement_pct': 4.55,
                'baseline_features': 50,
                'optimized_features': 35
            }
            self.visualizer.plot_comparison(comparison_results)
            
            # Verify all files exist
            assert os.path.exists(os.path.join(self.tmpdir, "top_features.png"))
            assert os.path.exists(os.path.join(self.tmpdir, "shap_summary.png"))
            assert os.path.exists(os.path.join(self.tmpdir, "model_comparison.png"))
        
        finally:
            if 'shap' in sys.modules:
                del sys.modules['shap']
    
    def test_visualizer_with_custom_filenames(self):
        """Test visualizer with custom filenames"""
        # Create plots with custom filenames
        self.visualizer.plot_top_features(
            self.importance_df, 
            top_n=15, 
            filename="custom_top_features.png"
        )
        
        comparison_results = {
            'baseline_ndcg3': 0.6217,
            'optimized_ndcg3': 0.6500,
            'improvement_pct': 4.55,
            'baseline_features': 50,
            'optimized_features': 35
        }
        self.visualizer.plot_comparison(
            comparison_results, 
            filename="custom_comparison.png"
        )
        
        # Verify custom filenames
        assert os.path.exists(os.path.join(self.tmpdir, "custom_top_features.png"))
        assert os.path.exists(os.path.join(self.tmpdir, "custom_comparison.png"))
    
    def test_visualizer_handles_realistic_data_distribution(self):
        """Test visualizer with realistic feature importance distribution"""
        # Create realistic distribution: few high-importance, many low-importance
        n_features = 100
        importance_values = np.concatenate([
            np.random.uniform(0.5, 1.0, 5),      # Top 5 features
            np.random.uniform(0.1, 0.5, 15),     # Medium importance
            np.random.uniform(0.001, 0.1, 80)    # Low importance
        ])
        np.random.shuffle(importance_values)
        
        realistic_df = pd.DataFrame({
            'feature': [f'feature_{i}' for i in range(n_features)],
            'importance': importance_values
        }).sort_values('importance', ascending=False).reset_index(drop=True)
        
        # Create visualization
        self.visualizer.plot_top_features(realistic_df, top_n=20)
        
        output_path = os.path.join(self.tmpdir, "top_features.png")
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
