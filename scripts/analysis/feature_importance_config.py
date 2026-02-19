"""
Feature Importance Analysis Configuration Module

This module defines the configuration and result data structures for the
LightGBM feature importance analysis system.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import pandas as pd


@dataclass
class AnalysisConfig:
    """
    Configuration for feature importance analysis.
    
    Attributes:
        sample_size: Number of samples for SHAP calculation (default: 1000)
        importance_threshold: Threshold for blacklisting features (default: 0.001)
        start_date: Analysis start date (None uses config.START_DATE)
        end_date: Analysis end date (None uses config.END_DATE)
        tickers: List of tickers to analyze (None uses config.TICKERS)
        output_dir: Directory for saving results (default: "reports/feature_importance")
        save_models: Whether to save baseline and optimized models (default: False)
    
    Requirements: 5.1, 5.2, 5.3, 5.4
    """
    sample_size: int = 1000
    importance_threshold: float = 0.001
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    tickers: Optional[List[str]] = None
    output_dir: str = "reports/feature_importance"
    save_models: bool = False
    
    def __post_init__(self):
        """
        Validate configuration parameters after initialization.
        
        Raises:
            ValueError: If any configuration parameter is invalid
            
        Requirements: 5.5
        """
        self._validate()
    
    def _validate(self):
        """
        Validate all configuration parameters.
        
        Validates:
        - sample_size must be positive
        - importance_threshold must be non-negative
        - date formats must be valid if provided
        - dates must be in logical order (start_date <= end_date)
        
        Raises:
            ValueError: If validation fails with descriptive message
            
        Requirements: 5.5
        """
        # Validate sample_size
        if self.sample_size <= 0:
            raise ValueError(
                f"sample_size must be positive, got {self.sample_size}. "
                f"Valid range: 1 to 100000"
            )
        
        # Validate importance_threshold
        if self.importance_threshold < 0:
            raise ValueError(
                f"importance_threshold must be non-negative, got {self.importance_threshold}. "
                f"Valid range: 0.0 to 1.0"
            )
        
        # Validate date formats if provided
        if self.start_date is not None:
            try:
                start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(
                    f"start_date must be in YYYY-MM-DD format, got '{self.start_date}'. "
                    f"Error: {str(e)}"
                )
        
        if self.end_date is not None:
            try:
                end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(
                    f"end_date must be in YYYY-MM-DD format, got '{self.end_date}'. "
                    f"Error: {str(e)}"
                )
        
        # Validate date order if both provided
        if self.start_date is not None and self.end_date is not None:
            start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
            if start_dt > end_dt:
                raise ValueError(
                    f"start_date ({self.start_date}) must be before or equal to "
                    f"end_date ({self.end_date})"
                )
        
        # Validate tickers if provided
        if self.tickers is not None:
            if not isinstance(self.tickers, list):
                raise ValueError(
                    f"tickers must be a list, got {type(self.tickers).__name__}"
                )
            if len(self.tickers) == 0:
                raise ValueError("tickers list cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary for serialization.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'sample_size': self.sample_size,
            'importance_threshold': self.importance_threshold,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'tickers': self.tickers,
            'output_dir': self.output_dir,
            'save_models': self.save_models
        }


@dataclass
class AnalysisResult:
    """
    Container for feature importance analysis results.
    
    Attributes:
        timestamp: When the analysis was performed
        config: Configuration used for the analysis
        importance_df: DataFrame with feature importance values
        blacklist: List of features to be blacklisted
        baseline_ndcg3: NDCG@3 score for baseline model
        optimized_ndcg3: NDCG@3 score for optimized model
        improvement_pct: Percentage improvement in NDCG@3
        total_features: Total number of features analyzed
        blacklisted_features: Number of features blacklisted
        remaining_features: Number of features remaining after blacklist
        data_size: Number of data points analyzed
        tickers_analyzed: List of tickers successfully analyzed
        analysis_duration: Time taken for analysis in seconds
    
    Requirements: 10.2, 10.5
    """
    timestamp: datetime
    config: Dict[str, Any]
    importance_df: pd.DataFrame
    blacklist: List[str]
    baseline_ndcg3: float
    optimized_ndcg3: float
    improvement_pct: float
    total_features: int
    blacklisted_features: int
    remaining_features: int
    data_size: int
    tickers_analyzed: List[str]
    analysis_duration: float
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary for serialization.
        
        Returns:
            Dictionary representation of results (excluding DataFrame)
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'config': self.config,
            'blacklist': self.blacklist,
            'baseline_ndcg3': self.baseline_ndcg3,
            'optimized_ndcg3': self.optimized_ndcg3,
            'improvement_pct': self.improvement_pct,
            'total_features': self.total_features,
            'blacklisted_features': self.blacklisted_features,
            'remaining_features': self.remaining_features,
            'data_size': self.data_size,
            'tickers_analyzed': self.tickers_analyzed,
            'analysis_duration': self.analysis_duration
        }
    
    def summary(self) -> str:
        """
        Generate a human-readable summary of the analysis results.
        
        Returns:
            Formatted summary string
        """
        return f"""
Feature Importance Analysis Summary
====================================
Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {self.analysis_duration:.2f} seconds

Data:
- Tickers analyzed: {len(self.tickers_analyzed)}
- Data points: {self.data_size}

Features:
- Total features: {self.total_features}
- Blacklisted: {self.blacklisted_features} ({self.blacklisted_features/self.total_features*100:.1f}%)
- Remaining: {self.remaining_features} ({self.remaining_features/self.total_features*100:.1f}%)

Model Performance:
- Baseline NDCG@3: {self.baseline_ndcg3:.4f}
- Optimized NDCG@3: {self.optimized_ndcg3:.4f}
- Improvement: {self.improvement_pct:+.2f}%

Configuration:
- Sample size: {self.config.get('sample_size', 'N/A')}
- Importance threshold: {self.config.get('importance_threshold', 'N/A')}
- Date range: {self.config.get('start_date', 'N/A')} to {self.config.get('end_date', 'N/A')}
"""
