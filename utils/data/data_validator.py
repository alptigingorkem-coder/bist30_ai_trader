"""
Data Validator.

This module handles data quality validation.
Follows the Single Responsibility Principle by separating validation
from fetching, caching, and transformation.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates data quality and integrity.
    
    Responsibilities:
    - Validate OHLCV data structure
    - Check for data gaps
    - Detect anomalies (price spikes, crashes)
    - Validate column presence
    - Check liquidity requirements
    
    This class contains validation logic without side effects.
    """
    
    # Default validation thresholds
    DEFAULT_MIN_ROWS = 10
    DEFAULT_MAX_PRICE_DROP = -0.60  # -60% (potential split)
    DEFAULT_MAX_PRICE_SPIKE = 0.50  # +50% (potential error)
    DEFAULT_MAX_GAP_DAYS = 7
    DEFAULT_MIN_VOLUME_TL = 0  # No minimum by default
    
    def __init__(self, min_rows: int = None, max_price_drop: float = None,
                 max_price_spike: float = None, max_gap_days: int = None,
                 min_volume_tl: float = None):
        """
        Initialize DataValidator with thresholds.
        
        Args:
            min_rows: Minimum number of rows required
            max_price_drop: Maximum allowed price drop (negative value)
            max_price_spike: Maximum allowed price spike (positive value)
            max_gap_days: Maximum allowed gap between dates
            min_volume_tl: Minimum daily volume in TL
        """
        self.min_rows = min_rows or self.DEFAULT_MIN_ROWS
        self.max_price_drop = max_price_drop or self.DEFAULT_MAX_PRICE_DROP
        self.max_price_spike = max_price_spike or self.DEFAULT_MAX_PRICE_SPIKE
        self.max_gap_days = max_gap_days or self.DEFAULT_MAX_GAP_DAYS
        self.min_volume_tl = min_volume_tl or self.DEFAULT_MIN_VOLUME_TL
        
        logger.info(
            f"DataValidator initialized: min_rows={self.min_rows}, "
            f"max_price_drop={self.max_price_drop}, max_gap_days={self.max_gap_days}"
        )
    
    def validate_data(self, data: pd.DataFrame, ticker: str = None) -> Tuple[bool, str]:
        """
        Comprehensive data validation.
        
        Args:
            data: DataFrame to validate
            ticker: Ticker symbol (for logging)
            
        Returns:
            Tuple of (is_valid, reason)
        """
        ticker = ticker or "UNKNOWN"
        
        # Check if data exists
        if data is None or data.empty:
            return False, f"{ticker}: Data is None or empty"
        
        # Check minimum rows
        if len(data) < self.min_rows:
            return False, f"{ticker}: Insufficient data ({len(data)} < {self.min_rows} rows)"
        
        # Validate columns
        is_valid, reason = self.validate_columns(data, ticker)
        if not is_valid:
            return False, reason
        
        # Check for gaps
        gaps = self.check_for_gaps(data, ticker)
        if gaps:
            logger.warning(f"{ticker}: Found {len(gaps)} data gaps")
        
        # Check for anomalies
        anomalies = self.check_for_anomalies(data, ticker)
        if anomalies:
            logger.warning(f"{ticker}: Found {len(anomalies)} anomalies")
        
        # Check liquidity (if configured)
        if self.min_volume_tl > 0:
            is_liquid, reason = self.check_liquidity(data, ticker)
            if not is_liquid:
                return False, reason
        
        logger.info(f"{ticker}: Data validation passed ({len(data)} rows)")
        return True, "OK"
    
    def validate_columns(self, data: pd.DataFrame, ticker: str = None) -> Tuple[bool, str]:
        """
        Validate required columns are present.
        
        Args:
            data: DataFrame to validate
            ticker: Ticker symbol (for logging)
            
        Returns:
            Tuple of (is_valid, reason)
        """
        ticker = ticker or "UNKNOWN"
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        missing = [col for col in required_columns if col not in data.columns]
        
        if missing:
            return False, f"{ticker}: Missing columns: {missing}"
        
        return True, "OK"
    
    def check_for_gaps(self, data: pd.DataFrame, ticker: str = None) -> List[dict]:
        """
        Check for gaps in time series data.
        
        Args:
            data: DataFrame with DatetimeIndex
            ticker: Ticker symbol (for logging)
            
        Returns:
            List of gap dictionaries with start_date, end_date, days
        """
        ticker = ticker or "UNKNOWN"
        gaps = []
        
        if not isinstance(data.index, pd.DatetimeIndex):
            logger.warning(f"{ticker}: Index is not DatetimeIndex, cannot check gaps")
            return gaps
        
        if len(data) < 2:
            return gaps
        
        # Calculate differences between consecutive dates
        date_diffs = data.index.to_series().diff()
        
        # Find gaps larger than threshold
        large_gaps = date_diffs[date_diffs > pd.Timedelta(days=self.max_gap_days)]
        
        for idx, gap_size in large_gaps.items():
            gap_days = gap_size.days
            prev_idx = data.index.get_loc(idx) - 1
            
            if prev_idx >= 0:
                gaps.append({
                    'start_date': data.index[prev_idx],
                    'end_date': idx,
                    'days': gap_days
                })
                logger.debug(f"{ticker}: Gap found: {gap_days} days")
        
        return gaps
    
    def check_for_anomalies(self, data: pd.DataFrame, ticker: str = None) -> List[dict]:
        """
        Check for price anomalies (crashes, spikes).
        
        Args:
            data: DataFrame with OHLCV data
            ticker: Ticker symbol (for logging)
            
        Returns:
            List of anomaly dictionaries with date, type, value
        """
        ticker = ticker or "UNKNOWN"
        anomalies = []
        
        if 'Close' not in data.columns:
            return anomalies
        
        # Calculate daily returns
        daily_returns = data['Close'].pct_change()
        
        # Check for crashes (large drops)
        crashes = daily_returns[daily_returns < self.max_price_drop]
        for date, value in crashes.items():
            anomalies.append({
                'date': date,
                'type': 'crash',
                'value': value,
                'description': f"Price drop: {value:.2%}"
            })
            logger.debug(f"{ticker}: Crash detected on {date}: {value:.2%}")
        
        # Check for spikes (large gains)
        spikes = daily_returns[daily_returns > self.max_price_spike]
        for date, value in spikes.items():
            anomalies.append({
                'date': date,
                'type': 'spike',
                'value': value,
                'description': f"Price spike: {value:.2%}"
            })
            logger.debug(f"{ticker}: Spike detected on {date}: {value:.2%}")
        
        # Check for zero/negative prices
        if 'Close' in data.columns:
            invalid_prices = data[data['Close'] <= 0]
            for date in invalid_prices.index:
                anomalies.append({
                    'date': date,
                    'type': 'invalid_price',
                    'value': data.loc[date, 'Close'],
                    'description': f"Invalid price: {data.loc[date, 'Close']}"
                })
                logger.debug(f"{ticker}: Invalid price on {date}")
        
        return anomalies
    
    def check_liquidity(self, data: pd.DataFrame, ticker: str = None) -> Tuple[bool, str]:
        """
        Check if data meets liquidity requirements.
        
        Args:
            data: DataFrame with Close and Volume columns
            ticker: Ticker symbol (for logging)
            
        Returns:
            Tuple of (is_liquid, reason)
        """
        ticker = ticker or "UNKNOWN"
        
        if 'Close' not in data.columns or 'Volume' not in data.columns:
            return True, "Cannot check liquidity (missing columns)"
        
        # Calculate daily volume in TL
        daily_vol_tl = data['Close'] * data['Volume']
        
        # Calculate 20-day average
        if len(data) < 20:
            avg_vol_tl = daily_vol_tl.mean()
        else:
            avg_vol_tl = daily_vol_tl.rolling(20).mean().iloc[-1]
        
        if pd.isna(avg_vol_tl):
            return True, "Cannot calculate average volume"
        
        if avg_vol_tl < self.min_volume_tl:
            return False, f"{ticker}: Insufficient liquidity ({avg_vol_tl:,.0f} TL < {self.min_volume_tl:,.0f} TL)"
        
        return True, "OK"
    
    def validate_ohlcv(self, data: pd.DataFrame, ticker: str = None) -> bool:
        """
        Validate OHLCV data structure and relationships.
        
        Args:
            data: DataFrame with OHLCV data
            ticker: Ticker symbol (for logging)
            
        Returns:
            True if valid, False otherwise
        """
        ticker = ticker or "UNKNOWN"
        
        # Check columns exist
        is_valid, _ = self.validate_columns(data, ticker)
        if not is_valid:
            return False
        
        # Check OHLC relationships (High >= Low, etc.)
        try:
            # High should be >= Low
            if not (data['High'] >= data['Low']).all():
                logger.warning(f"{ticker}: High < Low in some rows")
                return False
            
            # High should be >= Open and Close
            if not (data['High'] >= data['Open']).all():
                logger.warning(f"{ticker}: High < Open in some rows")
                return False
            
            if not (data['High'] >= data['Close']).all():
                logger.warning(f"{ticker}: High < Close in some rows")
                return False
            
            # Low should be <= Open and Close
            if not (data['Low'] <= data['Open']).all():
                logger.warning(f"{ticker}: Low > Open in some rows")
                return False
            
            if not (data['Low'] <= data['Close']).all():
                logger.warning(f"{ticker}: Low > Close in some rows")
                return False
            
            # Volume should be non-negative
            if not (data['Volume'] >= 0).all():
                logger.warning(f"{ticker}: Negative volume in some rows")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"{ticker}: OHLCV validation error: {e}")
            return False
    
    def get_data_quality_score(self, data: pd.DataFrame, ticker: str = None) -> float:
        """
        Calculate overall data quality score (0-100).
        
        Args:
            data: DataFrame to score
            ticker: Ticker symbol (for logging)
            
        Returns:
            Quality score from 0 to 100
        """
        ticker = ticker or "UNKNOWN"
        score = 100.0
        
        # Penalty for insufficient data
        if len(data) < self.min_rows:
            score -= 50
        elif len(data) < 50:
            score -= 20
        
        # Penalty for missing columns
        is_valid, _ = self.validate_columns(data, ticker)
        if not is_valid:
            score -= 30
        
        # Penalty for gaps
        gaps = self.check_for_gaps(data, ticker)
        if gaps:
            score -= min(20, len(gaps) * 5)
        
        # Penalty for anomalies
        anomalies = self.check_for_anomalies(data, ticker)
        if anomalies:
            score -= min(20, len(anomalies) * 2)
        
        # Penalty for OHLCV violations
        if not self.validate_ohlcv(data, ticker):
            score -= 20
        
        return max(0, score)
