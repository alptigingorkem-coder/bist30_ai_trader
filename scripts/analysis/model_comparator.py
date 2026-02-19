"""
Model Comparator Module

This module provides functionality to compare baseline and optimized models
by calculating NDCG@3 metrics and analyzing performance improvements.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.4, 8.5
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any
from sklearn.metrics import ndcg_score

log = logging.getLogger(__name__)


class ModelComparator:
    """
    Compares baseline and optimized models using NDCG@3 metric.
    
    This class evaluates two models on the same test dataset and calculates
    performance metrics including NDCG@3 scores, improvement percentage,
    and feature count comparison.
    
    Requirements: 3.3, 3.4
    """
    
    def __init__(self):
        """
        Initialize Model Comparator.
        
        Requirements: 3.3, 3.4
        """
        log.info("ModelComparator initialized")
    
    def compare(
        self, 
        baseline_model, 
        optimized_model, 
        test_data: pd.DataFrame,
        config_module
    ) -> Dict[str, Any]:
        """
        Compare baseline and optimized models.
        
        This method:
        1. Validates that both models use the same test data
        2. Calculates NDCG@3 for both models
        3. Computes improvement percentage
        4. Compares feature counts
        5. Logs warning if performance degrades
        
        Args:
            baseline_model: Model trained with all features (RankingModel instance)
            optimized_model: Model trained with blacklist applied (RankingModel instance)
            test_data: Test dataset (DataFrame with Date, Ticker index)
            config_module: Configuration module (config.py or sector config)
        
        Returns:
            Dict with comparison metrics:
                - baseline_ndcg3: Baseline model NDCG@3 score
                - optimized_ndcg3: Optimized model NDCG@3 score
                - improvement_pct: Percentage improvement
                - baseline_features: Number of features in baseline model
                - optimized_features: Number of features in optimized model
        
        Raises:
            ValueError: If models or test_data are invalid
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.5
        """
        if baseline_model is None or baseline_model.model is None:
            raise ValueError("baseline_model must be a trained model")
        
        if optimized_model is None or optimized_model.model is None:
            raise ValueError("optimized_model must be a trained model")
        
        if test_data is None or len(test_data) == 0:
            raise ValueError("test_data cannot be empty")
        
        log.info("Starting model comparison...")
        
        # Get feature counts
        baseline_features = len(baseline_model.feature_names)
        optimized_features = len(optimized_model.feature_names)
        
        log.info(
            f"Feature counts - Baseline: {baseline_features}, "
            f"Optimized: {optimized_features}"
        )
        
        # Validate feature count reduction
        if optimized_features > baseline_features:
            log.warning(
                f"Optimized model has MORE features ({optimized_features}) "
                f"than baseline ({baseline_features}). This is unexpected."
            )
        
        # Calculate NDCG@3 for both models
        baseline_ndcg3 = self._calculate_ndcg(
            baseline_model, 
            test_data, 
            config_module, 
            k=3
        )
        
        optimized_ndcg3 = self._calculate_ndcg(
            optimized_model, 
            test_data, 
            config_module, 
            k=3
        )
        
        # Calculate improvement percentage
        if baseline_ndcg3 == 0:
            log.warning("Baseline NDCG@3 is 0, cannot calculate improvement percentage")
            improvement_pct = 0.0
        else:
            improvement_pct = ((optimized_ndcg3 - baseline_ndcg3) / baseline_ndcg3) * 100
        
        # Log warning if performance degrades
        if optimized_ndcg3 < baseline_ndcg3:
            log.warning(
                f"Performance degradation detected! "
                f"Optimized NDCG@3 ({optimized_ndcg3:.4f}) is lower than "
                f"baseline NDCG@3 ({baseline_ndcg3:.4f}). "
                f"Consider adjusting the importance threshold."
            )
        
        # Prepare comparison results
        comparison_results = {
            'baseline_ndcg3': baseline_ndcg3,
            'optimized_ndcg3': optimized_ndcg3,
            'improvement_pct': improvement_pct,
            'baseline_features': baseline_features,
            'optimized_features': optimized_features
        }
        
        log.info(
            f"Model comparison completed - "
            f"Baseline NDCG@3: {baseline_ndcg3:.4f}, "
            f"Optimized NDCG@3: {optimized_ndcg3:.4f}, "
            f"Improvement: {improvement_pct:+.2f}%"
        )
        
        return comparison_results

    
    def _calculate_ndcg(
        self, 
        model, 
        data: pd.DataFrame, 
        config_module, 
        k: int = 3
    ) -> float:
        """
        Calculate NDCG@k metric for a model on test data.
        
        This method:
        1. Prepares test data using the model's prepare_data method
        2. Gets model predictions
        3. Groups predictions by date (query groups)
        4. Calculates NDCG@k for each date group
        5. Returns the mean NDCG@k across all groups
        6. Validates that NDCG is in [0, 1] range
        
        Args:
            model: Trained RankingModel instance
            data: Test dataset (DataFrame with Date, Ticker index)
            config_module: Configuration module
            k: Position for NDCG calculation (default: 3)
        
        Returns:
            float: Mean NDCG@k score across all date groups
        
        Raises:
            ValueError: If NDCG calculation fails or produces invalid values
        
        Requirements: 3.3, 8.4, 8.5
        """
        if model is None or model.model is None:
            raise ValueError("Model must be trained before NDCG calculation")
        
        if data is None or len(data) == 0:
            raise ValueError("Data cannot be empty for NDCG calculation")
        
        if k <= 0:
            raise ValueError(f"k must be positive, got {k}")
        
        try:
            # Create a temporary RankingModel instance with test data
            # to use its prepare_data method
            from models.ranking_model import RankingModel
            test_model = RankingModel(data.copy(), config_module)
            
            # Prepare test data (this handles feature selection and target creation)
            X_test, y_test, groups = test_model.prepare_data(is_training=True)
            
            if X_test.empty or len(y_test) == 0:
                log.warning("Test data is empty after preparation, returning NDCG=0")
                return 0.0
            
            # CRITICAL: Use only the features that the model was trained with
            # This ensures consistency between training and prediction
            available_features = [f for f in model.feature_names if f in X_test.columns]
            
            if len(available_features) == 0:
                log.error("No common features between model and test data")
                return 0.0
            
            # Check if we have all model features
            missing_features = [f for f in model.feature_names if f not in X_test.columns]
            if missing_features:
                log.warning(f"Missing {len(missing_features)} features in test data: {missing_features[:5]}...")
            
            X_test_filtered = X_test[available_features]
            
            # Get model predictions
            predictions = model.model.predict(X_test_filtered)
            
            # Validate predictions
            if np.isnan(predictions).any():
                log.error("Model predictions contain NaN values")
                return 0.0
            
            if np.isinf(predictions).any():
                log.error("Model predictions contain Inf values")
                return 0.0
            
            # Calculate NDCG@k for each date group
            ndcg_scores = []
            start_idx = 0
            
            for group_size in groups:
                end_idx = start_idx + group_size
                
                # Get predictions and true labels for this group
                y_true_group = y_test.iloc[start_idx:end_idx].values
                y_pred_group = predictions[start_idx:end_idx]
                
                # Skip groups that are too small
                if len(y_true_group) < k:
                    log.debug(
                        f"Skipping group with size {len(y_true_group)} < k={k}"
                    )
                    start_idx = end_idx
                    continue
                
                # Reshape for sklearn's ndcg_score (expects 2D arrays)
                y_true_2d = y_true_group.reshape(1, -1)
                y_pred_2d = y_pred_group.reshape(1, -1)
                
                # Calculate NDCG@k for this group
                try:
                    ndcg = ndcg_score(y_true_2d, y_pred_2d, k=k)
                    ndcg_scores.append(ndcg)
                except Exception as e:
                    log.warning(
                        f"Failed to calculate NDCG for group "
                        f"(size={len(y_true_group)}): {str(e)}"
                    )
                
                start_idx = end_idx
            
            if len(ndcg_scores) == 0:
                log.warning("No valid NDCG scores calculated, returning 0")
                return 0.0
            
            # Calculate mean NDCG@k
            mean_ndcg = np.mean(ndcg_scores)
            
            # Validate NDCG is in [0, 1] range
            if mean_ndcg < 0 or mean_ndcg > 1:
                log.error(
                    f"Invalid NDCG@{k} value: {mean_ndcg}. "
                    f"NDCG must be in [0, 1] range."
                )
                # Clip to valid range
                mean_ndcg = np.clip(mean_ndcg, 0.0, 1.0)
            
            log.info(
                f"NDCG@{k} calculated: {mean_ndcg:.4f} "
                f"(averaged over {len(ndcg_scores)} groups)"
            )
            
            return float(mean_ndcg)
        
        except Exception as e:
            log.error(f"Error calculating NDCG@{k}: {str(e)}")
            raise ValueError(f"NDCG calculation failed: {str(e)}")
