"""
Feature Selector Module

This module provides feature selection functionality based on importance scores.
It creates blacklists of low-contribution features and manages their persistence.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 8.2, 8.3
"""

import json
import logging
import os
from typing import List, Optional
import pandas as pd

log = logging.getLogger(__name__)


class FeatureSelector:
    """
    Feature selector for identifying and managing low-contribution features.
    
    This class analyzes feature importance scores and creates blacklists of
    features that fall below a specified threshold. It handles blacklist
    persistence (save/load) and validation.
    
    Attributes:
        threshold: Importance threshold below which features are blacklisted
    
    Requirements: 2.1, 2.5
    """
    
    def __init__(self, threshold: float = 0.001):
        """
        Initialize Feature Selector.
        
        Args:
            threshold: Importance threshold for blacklisting features.
                      Features with importance below this value will be
                      blacklisted. Default: 0.001
        
        Raises:
            ValueError: If threshold is negative
        
        Requirements: 2.1, 2.5
        """
        if threshold < 0:
            raise ValueError(
                f"threshold must be non-negative, got {threshold}"
            )
        
        self.threshold = threshold
        log.info(f"FeatureSelector initialized with threshold={threshold}")
    
    def create_blacklist(self, importance_df: pd.DataFrame) -> List[str]:
        """
        Create blacklist of low-contribution features.
        
        Identifies features whose importance values fall below the configured
        threshold and returns them as a blacklist.
        
        Args:
            importance_df: DataFrame with 'feature' and 'importance' columns,
                          typically from SHAPAnalyzer.compute_importance()
        
        Returns:
            List[str]: List of feature names to be blacklisted
        
        Raises:
            ValueError: If importance_df is empty or missing required columns
        
        Requirements: 2.1, 2.5
        """
        if importance_df is None or len(importance_df) == 0:
            raise ValueError("importance_df cannot be empty")
        
        if 'feature' not in importance_df.columns:
            raise ValueError("importance_df must contain 'feature' column")
        
        if 'importance' not in importance_df.columns:
            raise ValueError("importance_df must contain 'importance' column")
        
        # Filter features below threshold
        blacklist_df = importance_df[importance_df['importance'] < self.threshold]
        blacklist = blacklist_df['feature'].tolist()
        
        log.info(
            f"Created blacklist with {len(blacklist)} features "
            f"(threshold: {self.threshold})"
        )
        
        if len(blacklist) > 0:
            log.debug(
                f"Blacklisted features: {blacklist[:5]}"
                f"{'...' if len(blacklist) > 5 else ''}"
            )
        
        return blacklist
    
    def save_blacklist(
        self, 
        blacklist: List[str], 
        path: str = "models/saved/feature_blacklist.json"
    ):
        """
        Save blacklist to JSON file.
        
        Saves the feature blacklist to a JSON file at the specified path.
        Creates parent directories if they don't exist.
        
        Args:
            blacklist: List of feature names to blacklist
            path: File path for saving the blacklist.
                 Default: "models/saved/feature_blacklist.json"
        
        Raises:
            IOError: If file cannot be written
        
        Requirements: 2.2, 2.3, 2.4
        """
        if blacklist is None:
            raise ValueError("blacklist cannot be None")
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        try:
            with open(path, 'w') as f:
                json.dump(blacklist, f, indent=2)
            
            log.info(
                f"Blacklist saved successfully: {len(blacklist)} features "
                f"saved to {path}"
            )
        
        except Exception as e:
            log.error(f"Failed to save blacklist to {path}: {str(e)}")
            raise IOError(f"Failed to save blacklist: {str(e)}")
    
    def load_blacklist(
        self, 
        path: str = "models/saved/feature_blacklist.json"
    ) -> List[str]:
        """
        Load blacklist from JSON file.
        
        Loads a previously saved feature blacklist from a JSON file.
        
        Args:
            path: File path for loading the blacklist.
                 Default: "models/saved/feature_blacklist.json"
        
        Returns:
            List[str]: List of blacklisted feature names
        
        Raises:
            FileNotFoundError: If blacklist file doesn't exist
            ValueError: If file contains invalid JSON or wrong format
        
        Requirements: 2.2, 2.3
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Blacklist file not found: {path}")
        
        try:
            with open(path, 'r') as f:
                blacklist = json.load(f)
            
            if not isinstance(blacklist, list):
                raise ValueError(
                    f"Blacklist file must contain a list, got {type(blacklist)}"
                )
            
            log.info(f"Blacklist loaded successfully: {len(blacklist)} features from {path}")
            return blacklist
        
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON in blacklist file {path}: {str(e)}")
            raise ValueError(f"Invalid JSON in blacklist file: {str(e)}")
        
        except Exception as e:
            log.error(f"Failed to load blacklist from {path}: {str(e)}")
            raise
    
    def validate_blacklist(
        self, 
        blacklist: List[str], 
        total_features: int
    ) -> bool:
        """
        Validate blacklist size.
        
        Checks that the blacklist doesn't contain more than 80% of total
        features. If it does, logs a warning and suggests adjusting the
        threshold.
        
        Args:
            blacklist: List of blacklisted feature names
            total_features: Total number of features in the dataset
        
        Returns:
            bool: True if blacklist is valid (<=80% of features),
                 False if blacklist is too large (>80% of features)
        
        Requirements: 8.2, 8.3
        """
        if total_features <= 0:
            raise ValueError(
                f"total_features must be positive, got {total_features}"
            )
        
        if blacklist is None:
            raise ValueError("blacklist cannot be None")
        
        blacklist_size = len(blacklist)
        blacklist_pct = (blacklist_size / total_features) * 100
        
        if blacklist_pct > 80:
            log.warning(
                f"Blacklist contains {blacklist_size} features "
                f"({blacklist_pct:.1f}% of {total_features} total features), "
                f"which exceeds the 80% limit. "
                f"Consider increasing the importance threshold (current: {self.threshold}) "
                f"to reduce the number of blacklisted features."
            )
            return False
        
        log.info(
            f"Blacklist validation passed: {blacklist_size} features "
            f"({blacklist_pct:.1f}% of {total_features} total features)"
        )
        return True
