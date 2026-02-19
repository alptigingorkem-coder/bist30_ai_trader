"""
SHAP Analyzer Module

This module provides SHAP-based feature importance analysis for LightGBM models.
It calculates SHAP values and computes feature importance scores.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.1
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional

log = logging.getLogger(__name__)


class SHAPAnalyzer:
    """
    SHAP-based feature importance analyzer for LightGBM models.
    
    This class uses SHAP TreeExplainer to compute feature importance values
    based on Shapley values. It handles large datasets through sampling and
    properly processes multi-class model outputs.
    
    Attributes:
        model: Trained LightGBM model
        sample_size: Maximum number of samples for SHAP calculation
        explainer: SHAP TreeExplainer instance (created lazily)
    
    Requirements: 1.1, 1.3
    """
    
    def __init__(self, model, sample_size: int = 1000):
        """
        Initialize SHAP Analyzer.
        
        Args:
            model: Trained LightGBM model (lgb.LGBMRanker or similar)
            sample_size: Maximum number of samples for SHAP calculation.
                        Used when dataset has more than 1000 rows.
                        Default: 1000
        
        Raises:
            ImportError: If SHAP library is not installed
            ValueError: If model is None or sample_size is invalid
        
        Requirements: 1.1, 1.3, 8.1
        """
        if model is None:
            raise ValueError("Model cannot be None")
        
        if sample_size <= 0:
            raise ValueError(
                f"sample_size must be positive, got {sample_size}"
            )
        
        self.model = model
        self.sample_size = sample_size
        self.explainer = None
        
        # Check if SHAP is available
        try:
            import shap
            self._shap = shap
        except ImportError:
            raise ImportError(
                "SHAP library is not installed. "
                "Please install it using: pip install shap"
            )
        
        log.info(
            f"SHAPAnalyzer initialized with sample_size={sample_size}"
        )
    
    def _create_explainer(self):
        """
        Create SHAP TreeExplainer for the model.
        
        This method lazily creates the TreeExplainer when needed.
        
        Returns:
            shap.TreeExplainer: SHAP explainer instance
        
        Requirements: 1.1
        """
        if self.explainer is None:
            try:
                self.explainer = self._shap.TreeExplainer(self.model)
                log.info("SHAP TreeExplainer created successfully")
            except Exception as e:
                log.error(f"Failed to create SHAP TreeExplainer: {str(e)}")
                raise
        
        return self.explainer
    
    def compute_importance(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Compute feature importance using SHAP values.
        
        This method:
        1. Samples data if necessary (>1000 rows)
        2. Creates TreeExplainer if not already created
        3. Computes SHAP values
        4. Handles multi-class outputs
        5. Calculates mean absolute SHAP values per feature
        6. Returns sorted DataFrame with feature importance
        
        Args:
            X: Feature matrix (pandas DataFrame)
        
        Returns:
            pd.DataFrame: Feature importance table with columns:
                - feature: Feature name
                - importance: Mean absolute SHAP value
                Sorted by importance in descending order
        
        Raises:
            ValueError: If X is empty or contains invalid values
            MemoryError: If SHAP calculation runs out of memory
        
        Requirements: 1.2, 1.3, 1.4, 1.5, 8.1
        """
        if X is None or len(X) == 0:
            raise ValueError("Feature matrix X cannot be empty")
        
        # Validate input data
        if X.isnull().any().any():
            log.warning("Feature matrix contains NaN values, this may affect SHAP calculation")
        
        # Sample data if necessary
        X_sample = self._sample_data(X)
        log.info(f"Computing SHAP values for {len(X_sample)} samples")
        
        try:
            # Create explainer if not already created
            explainer = self._create_explainer()
            
            # Compute SHAP values
            shap_values = explainer.shap_values(X_sample)
            
            # Handle multi-class output
            shap_values_processed = self._handle_multiclass_output(shap_values)
            
            # Validate SHAP values
            self._validate_shap_values(shap_values_processed)
            
            # Calculate mean absolute SHAP values
            mean_abs_shap = np.abs(shap_values_processed).mean(axis=0)
            
            # Create importance DataFrame
            importance_df = pd.DataFrame({
                'feature': X.columns,
                'importance': mean_abs_shap
            })
            
            # Sort by importance in descending order
            importance_df = importance_df.sort_values(
                'importance', 
                ascending=False
            ).reset_index(drop=True)
            
            log.info(
                f"Feature importance computed successfully. "
                f"Top feature: {importance_df.iloc[0]['feature']} "
                f"(importance: {importance_df.iloc[0]['importance']:.6f})"
            )
            
            return importance_df
            
        except MemoryError as e:
            log.error(
                f"Memory error during SHAP calculation. "
                f"Try reducing sample_size (current: {self.sample_size})"
            )
            # Try with reduced sample size
            if self.sample_size > 100:
                reduced_size = max(100, self.sample_size // 2)
                log.info(f"Retrying with reduced sample_size: {reduced_size}")
                self.sample_size = reduced_size
                return self.compute_importance(X)
            else:
                raise MemoryError(
                    f"Insufficient memory for SHAP calculation even with "
                    f"minimum sample size. Original error: {str(e)}"
                )
        
        except Exception as e:
            log.error(f"Error computing SHAP values: {str(e)}")
            raise
    
    def _sample_data(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Sample data if it exceeds the sample size threshold.
        
        For datasets with more than 1000 rows, randomly sample
        up to sample_size rows to speed up SHAP calculation.
        
        Args:
            X: Feature matrix
        
        Returns:
            pd.DataFrame: Sampled feature matrix
        
        Requirements: 1.3
        """
        if len(X) > 1000:
            sample_size = min(self.sample_size, len(X))
            log.info(
                f"Dataset has {len(X)} rows, sampling {sample_size} rows "
                f"for SHAP calculation"
            )
            return X.sample(n=sample_size, random_state=42)
        else:
            log.info(f"Dataset has {len(X)} rows, using all data for SHAP calculation")
            return X
    
    def _handle_multiclass_output(self, shap_values) -> np.ndarray:
        """
        Handle multi-class SHAP output.
        
        SHAP TreeExplainer can return:
        - 2D array for binary/regression: (n_samples, n_features)
        - 3D array for multi-class: (n_classes, n_samples, n_features)
        - List of 2D arrays for multi-class: [(n_samples, n_features), ...]
        
        This method converts all formats to a single 2D array by averaging
        across classes if necessary.
        
        Args:
            shap_values: SHAP values from TreeExplainer
        
        Returns:
            np.ndarray: 2D array of shape (n_samples, n_features)
        
        Requirements: 1.5
        """
        # Handle list of arrays (multi-class)
        if isinstance(shap_values, list):
            log.info(
                f"Multi-class SHAP output detected (list of {len(shap_values)} arrays)"
            )
            # Stack arrays and average across classes
            shap_values = np.abs(np.array(shap_values)).mean(axis=0)
        
        # Handle 3D array (multi-class)
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            log.info(
                f"Multi-class SHAP output detected "
                f"(3D array with shape {shap_values.shape})"
            )
            # Average across classes (first dimension)
            shap_values = np.abs(shap_values).mean(axis=0)
        
        # Handle 2D array (binary/regression)
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 2:
            log.info(
                f"Single-class SHAP output detected "
                f"(2D array with shape {shap_values.shape})"
            )
            # Already in correct format
            pass
        
        else:
            raise ValueError(
                f"Unexpected SHAP values format: {type(shap_values)} "
                f"with shape {getattr(shap_values, 'shape', 'N/A')}"
            )
        
        return shap_values
    
    def _validate_shap_values(self, shap_values: np.ndarray):
        """
        Validate SHAP values for NaN and Inf.
        
        Args:
            shap_values: SHAP values array
        
        Raises:
            ValueError: If SHAP values contain NaN or Inf
        
        Requirements: 8.1
        """
        if np.isnan(shap_values).any():
            nan_count = np.isnan(shap_values).sum()
            raise ValueError(
                f"SHAP values contain {nan_count} NaN values. "
                f"This may indicate issues with the model or input data."
            )
        
        if np.isinf(shap_values).any():
            inf_count = np.isinf(shap_values).sum()
            raise ValueError(
                f"SHAP values contain {inf_count} Inf values. "
                f"This may indicate numerical instability."
            )
        
        log.debug("SHAP values validation passed (no NaN or Inf)")
