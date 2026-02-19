"""
Feature Importance Visualizer Module

This module provides visualization functionality for feature importance analysis.
It creates charts for top features, SHAP summary plots, and model comparisons.

Requirements: 3.4, 4.1, 4.2, 4.3
"""

import logging
import os
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments

log = logging.getLogger(__name__)


class FeatureImportanceVisualizer:
    """
    Visualizer for feature importance analysis results.
    
    This class creates various visualizations including:
    - Top-N feature importance bar charts
    - SHAP summary plots
    - Baseline vs Optimized model comparison charts
    
    All visualizations are saved as PNG files to the specified output directory.
    
    Attributes:
        output_dir: Directory where visualization files will be saved
    
    Requirements: 4.1, 4.2, 4.3
    """
    
    def __init__(self, output_dir: str = "reports/feature_importance"):
        """
        Initialize Feature Importance Visualizer.
        
        Creates the output directory if it doesn't exist.
        
        Args:
            output_dir: Directory path for saving visualization files.
                       Default: "reports/feature_importance"
        
        Raises:
            ValueError: If output_dir is None or empty
            OSError: If directory creation fails
        
        Requirements: 4.2
        """
        if not output_dir:
            raise ValueError("output_dir cannot be None or empty")
        
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            log.info(f"FeatureImportanceVisualizer initialized with output_dir={output_dir}")
        except Exception as e:
            log.error(f"Failed to create output directory {output_dir}: {str(e)}")
            raise OSError(f"Failed to create output directory: {str(e)}")
    
    def plot_top_features(
        self, 
        importance_df: pd.DataFrame, 
        top_n: int = 20,
        filename: str = "top_features.png"
    ):
        """
        Create bar chart of top-N features by importance.
        
        This method:
        1. Selects top-N features from importance DataFrame
        2. Creates a horizontal bar chart
        3. Saves the chart as PNG file
        
        Args:
            importance_df: DataFrame with 'feature' and 'importance' columns,
                          sorted by importance in descending order
            top_n: Number of top features to display (default: 20)
            filename: Output filename (default: "top_features.png")
        
        Raises:
            ValueError: If importance_df is invalid or empty
            IOError: If file cannot be saved
        
        Requirements: 4.1
        """
        if importance_df is None or len(importance_df) == 0:
            raise ValueError("importance_df cannot be empty")
        
        if 'feature' not in importance_df.columns:
            raise ValueError("importance_df must contain 'feature' column")
        
        if 'importance' not in importance_df.columns:
            raise ValueError("importance_df must contain 'importance' column")
        
        if top_n <= 0:
            raise ValueError(f"top_n must be positive, got {top_n}")
        
        # Select top-N features
        top_features = importance_df.head(top_n).copy()
        
        # Reverse order for better visualization (highest at top)
        top_features = top_features.iloc[::-1]
        
        log.info(f"Creating bar chart for top {len(top_features)} features")
        
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(10, max(6, len(top_features) * 0.3)))
            
            # Create horizontal bar chart
            bars = ax.barh(
                range(len(top_features)), 
                top_features['importance'],
                color='steelblue',
                edgecolor='navy',
                alpha=0.7
            )
            
            # Set y-axis labels
            ax.set_yticks(range(len(top_features)))
            ax.set_yticklabels(top_features['feature'])
            
            # Set labels and title
            ax.set_xlabel('Feature Importance (Mean |SHAP|)', fontsize=12)
            ax.set_ylabel('Feature', fontsize=12)
            ax.set_title(f'Top {len(top_features)} Features by Importance', fontsize=14, fontweight='bold')
            
            # Add grid for better readability
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            
            # Add value labels on bars
            for i, (bar, value) in enumerate(zip(bars, top_features['importance'])):
                ax.text(
                    value, 
                    i, 
                    f' {value:.4f}',
                    va='center',
                    fontsize=9
                )
            
            # Adjust layout to prevent label cutoff
            plt.tight_layout()
            
            # Save figure
            output_path = os.path.join(self.output_dir, filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            log.info(f"Top features bar chart saved to {output_path}")
        
        except Exception as e:
            log.error(f"Failed to create top features chart: {str(e)}")
            plt.close('all')  # Clean up any open figures
            raise IOError(f"Failed to create visualization: {str(e)}")
    
    def plot_shap_summary(
        self,
        shap_values: np.ndarray,
        X: pd.DataFrame,
        filename: str = "shap_summary.png"
    ):
        """
        Create SHAP summary plot.
        
        This method uses the SHAP library to create a summary plot showing
        the distribution of SHAP values for each feature.
        
        Args:
            shap_values: SHAP values array (n_samples, n_features)
            X: Feature matrix used for SHAP calculation
            filename: Output filename (default: "shap_summary.png")
        
        Raises:
            ImportError: If SHAP library is not installed
            ValueError: If shap_values or X are invalid
            IOError: If file cannot be saved
        
        Requirements: 4.3
        """
        if shap_values is None:
            raise ValueError("shap_values cannot be None")
        
        if X is None or len(X) == 0:
            raise ValueError("X cannot be empty")
        
        if not isinstance(shap_values, np.ndarray):
            raise ValueError(f"shap_values must be numpy array, got {type(shap_values)}")
        
        if shap_values.shape[1] != len(X.columns):
            raise ValueError(
                f"shap_values shape {shap_values.shape} doesn't match "
                f"X columns {len(X.columns)}"
            )
        
        # Check if SHAP is available
        try:
            import shap
        except ImportError:
            raise ImportError(
                "SHAP library is not installed. "
                "Please install it using: pip install shap"
            )
        
        log.info("Creating SHAP summary plot")
        
        try:
            # Create SHAP summary plot
            plt.figure(figsize=(10, 8))
            shap.summary_plot(
                shap_values, 
                X, 
                show=False,
                max_display=20
            )
            
            # Save figure
            output_path = os.path.join(self.output_dir, filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            log.info(f"SHAP summary plot saved to {output_path}")
        
        except Exception as e:
            log.error(f"Failed to create SHAP summary plot: {str(e)}")
            plt.close('all')  # Clean up any open figures
            raise IOError(f"Failed to create SHAP visualization: {str(e)}")
    
    def plot_comparison(
        self,
        comparison_results: Dict[str, Any],
        filename: str = "model_comparison.png"
    ):
        """
        Create model comparison visualization.
        
        This method creates a comparison chart showing:
        - NDCG@3 scores for baseline and optimized models
        - Feature counts for both models
        - Improvement percentage
        
        Args:
            comparison_results: Dictionary with comparison metrics:
                - baseline_ndcg3: Baseline model NDCG@3 score
                - optimized_ndcg3: Optimized model NDCG@3 score
                - improvement_pct: Percentage improvement
                - baseline_features: Number of features in baseline
                - optimized_features: Number of features in optimized
            filename: Output filename (default: "model_comparison.png")
        
        Raises:
            ValueError: If comparison_results is invalid or missing keys
            IOError: If file cannot be saved
        
        Requirements: 3.4
        """
        if comparison_results is None:
            raise ValueError("comparison_results cannot be None")
        
        # Validate required keys
        required_keys = [
            'baseline_ndcg3', 'optimized_ndcg3', 'improvement_pct',
            'baseline_features', 'optimized_features'
        ]
        
        missing_keys = [key for key in required_keys if key not in comparison_results]
        if missing_keys:
            raise ValueError(f"comparison_results missing keys: {missing_keys}")
        
        log.info("Creating model comparison chart")
        
        try:
            # Extract values
            baseline_ndcg = comparison_results['baseline_ndcg3']
            optimized_ndcg = comparison_results['optimized_ndcg3']
            improvement_pct = comparison_results['improvement_pct']
            baseline_features = comparison_results['baseline_features']
            optimized_features = comparison_results['optimized_features']
            
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Subplot 1: NDCG@3 Comparison
            models = ['Baseline', 'Optimized']
            ndcg_values = [baseline_ndcg, optimized_ndcg]
            colors = ['#FF6B6B' if improvement_pct < 0 else '#4ECDC4', '#45B7D1']
            
            bars1 = ax1.bar(models, ndcg_values, color=colors, edgecolor='black', alpha=0.7)
            ax1.set_ylabel('NDCG@3 Score', fontsize=12)
            ax1.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
            ax1.set_ylim([0, 1.0])
            ax1.grid(axis='y', alpha=0.3, linestyle='--')
            
            # Add value labels on bars
            for bar, value in zip(bars1, ndcg_values):
                height = bar.get_height()
                ax1.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{value:.4f}',
                    ha='center',
                    va='bottom',
                    fontsize=11,
                    fontweight='bold'
                )
            
            # Add improvement text
            improvement_color = 'green' if improvement_pct >= 0 else 'red'
            ax1.text(
                0.5, 0.95,
                f'Improvement: {improvement_pct:+.2f}%',
                transform=ax1.transAxes,
                ha='center',
                va='top',
                fontsize=12,
                fontweight='bold',
                color=improvement_color,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
            
            # Subplot 2: Feature Count Comparison
            feature_counts = [baseline_features, optimized_features]
            bars2 = ax2.bar(models, feature_counts, color=['#95E1D3', '#F38181'], 
                           edgecolor='black', alpha=0.7)
            ax2.set_ylabel('Number of Features', fontsize=12)
            ax2.set_title('Feature Count Comparison', fontsize=14, fontweight='bold')
            ax2.grid(axis='y', alpha=0.3, linestyle='--')
            
            # Add value labels on bars
            for bar, value in zip(bars2, feature_counts):
                height = bar.get_height()
                ax2.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{value}',
                    ha='center',
                    va='bottom',
                    fontsize=11,
                    fontweight='bold'
                )
            
            # Add feature reduction text
            features_removed = baseline_features - optimized_features
            reduction_pct = (features_removed / baseline_features) * 100 if baseline_features > 0 else 0
            ax2.text(
                0.5, 0.95,
                f'Removed: {features_removed} ({reduction_pct:.1f}%)',
                transform=ax2.transAxes,
                ha='center',
                va='top',
                fontsize=12,
                fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5)
            )
            
            # Adjust layout
            plt.tight_layout()
            
            # Save figure
            output_path = os.path.join(self.output_dir, filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            log.info(f"Model comparison chart saved to {output_path}")
        
        except Exception as e:
            log.error(f"Failed to create model comparison chart: {str(e)}")
            plt.close('all')  # Clean up any open figures
            raise IOError(f"Failed to create comparison visualization: {str(e)}")
