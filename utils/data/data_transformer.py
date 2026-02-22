"""
Data Transformer.

This module handles data transformation and cleaning operations.
Follows the Single Responsibility Principle by separating transformation
from fetching, caching, and validation.
"""

import pandas as pd
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    """
    Transforms and cleans data.
    
    Responsibilities:
    - Clean data (remove outliers, invalid values)
    - Add technical indicators
    - Resample data to different timeframes
    - Align data from multiple sources
    
    This class focuses on data transformation without fetching or validation.
    """
    
    # Default transformation parameters
    DEFAULT_MAX_MARGIN = 1.25  # Max High/Low ratio (BIST limit)
    DEFAULT_TIMEFRAME = 'D'    # Daily by default
    
    def __init__(self, max_margin: float = None, timeframe: str = None):
        """
        Initialize DataTransformer.
        
        Args:
            max_margin: Maximum High/Low ratio for outlier detection
            timeframe: Target timeframe ('D' for daily, 'W' for weekly)
        """
        self.max_margin = max_margin or self.DEFAULT_MAX_MARGIN
        self.timeframe = timeframe or self.DEFAULT_TIMEFRAME
        
        logger.info(
            f"DataTransformer initialized: max_margin={self.max_margin}, "
            f"timeframe={self.timeframe}"
        )
    
    def clean_data(self, data: pd.DataFrame, ticker: str = None) -> pd.DataFrame:
        """
        Clean data by removing invalid values and outliers.
        
        Cleaning operations:
        1. Remove rows with Close <= 0
        2. Remove rows with Low <= 0
        3. Remove outliers (High/Low > max_margin)
        
        Args:
            data: DataFrame to clean
            ticker: Ticker symbol (for logging)
            
        Returns:
            Cleaned DataFrame
        """
        if data is None or data.empty:
            return data
        
        ticker = ticker or "UNKNOWN"
        initial_len = len(data)
        
        # 1. Remove zero/negative Close prices
        if 'Close' in data.columns:
            data = data[data['Close'] > 0]
        
        # 2. Remove zero/negative Low prices
        if 'Low' in data.columns:
            data = data[data['Low'] > 0]
        
        # 3. Remove outliers based on High/Low margin
        if 'High' in data.columns and 'Low' in data.columns:
            margin = data['High'] / data['Low']
            outliers = margin > self.max_margin
            
            if outliers.any():
                bad_dates = data.index[outliers]
                logger.warning(
                    f"{ticker}: Removed {len(bad_dates)} outlier bars "
                    f"(High/Low > {self.max_margin})"
                )
                data = data[~outliers]
        
        final_len = len(data)
        if initial_len != final_len:
            pct_removed = 100 * (initial_len - final_len) / initial_len
            logger.info(
                f"{ticker}: Data cleaning: {initial_len} -> {final_len} rows "
                f"({pct_removed:.1f}% removed)"
            )
        
        return data
    
    def add_technical_indicators(self, data: pd.DataFrame, 
                                 indicators: list = None) -> pd.DataFrame:
        """
        Add technical indicators to data.
        
        Args:
            data: DataFrame with OHLCV data
            indicators: List of indicators to add (default: ['SMA_20', 'RSI_14'])
            
        Returns:
            DataFrame with added indicators
        """
        if data is None or data.empty:
            return data
        
        if indicators is None:
            indicators = ['SMA_20', 'RSI_14']
        
        logger.debug(f"Adding technical indicators: {indicators}")
        
        for indicator in indicators:
            if indicator.startswith('SMA_'):
                # Simple Moving Average
                period = int(indicator.split('_')[1])
                data[indicator] = data['Close'].rolling(window=period).mean()
                
            elif indicator.startswith('EMA_'):
                # Exponential Moving Average
                period = int(indicator.split('_')[1])
                data[indicator] = data['Close'].ewm(span=period, adjust=False).mean()
                
            elif indicator.startswith('RSI_'):
                # Relative Strength Index
                period = int(indicator.split('_')[1])
                data[indicator] = self._calculate_rsi(data['Close'], period)
                
            elif indicator == 'MACD':
                # MACD (12, 26, 9)
                data['MACD'], data['MACD_Signal'] = self._calculate_macd(data['Close'])
                
            else:
                logger.warning(f"Unknown indicator: {indicator}")
        
        return data
    
    def resample_data(self, data: pd.DataFrame, 
                     timeframe: str = None) -> pd.DataFrame:
        """
        Resample data to different timeframe.
        
        Args:
            data: DataFrame with OHLCV data
            timeframe: Target timeframe ('D', 'W', 'M', etc.)
            
        Returns:
            Resampled DataFrame
        """
        if data is None or data.empty:
            return data
        
        timeframe = timeframe or self.timeframe
        
        # If already at target timeframe, return as-is
        if timeframe == 'D':
            return data
        
        logger.info(f"Resampling data to {timeframe} timeframe")
        
        # OHLCV aggregation rules
        agg_rules = {
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }
        
        # Add rules for other columns (use mean)
        other_cols = [c for c in data.columns if c not in agg_rules]
        for col in other_cols:
            agg_rules[col] = 'mean'
        
        # Resample based on timeframe
        if timeframe == 'W':
            # Weekly (Monday start)
            resampled = data.resample('W-MON').agg(agg_rules)
        elif timeframe == 'M':
            # Monthly
            resampled = data.resample('M').agg(agg_rules)
        elif timeframe == 'H':
            # Hourly
            resampled = data.resample('H').agg(agg_rules)
        else:
            logger.warning(f"Unknown timeframe: {timeframe}, returning original data")
            return data
        
        # Remove empty rows
        resampled = resampled.dropna(how='all')
        
        logger.info(f"Resampled: {len(data)} -> {len(resampled)} rows")
        return resampled
    
    def align_data(self, *dataframes: pd.DataFrame, 
                   method: str = 'inner') -> list:
        """
        Align multiple DataFrames by their index.
        
        Args:
            *dataframes: Variable number of DataFrames to align
            method: Alignment method ('inner', 'outer', 'left', 'right')
            
        Returns:
            List of aligned DataFrames
        """
        if not dataframes:
            return []
        
        if len(dataframes) == 1:
            return list(dataframes)
        
        logger.debug(f"Aligning {len(dataframes)} DataFrames using {method} join")
        
        # Start with first DataFrame
        aligned = [dataframes[0]]
        
        # Align each subsequent DataFrame
        for df in dataframes[1:]:
            if method == 'inner':
                # Keep only common dates
                common_idx = aligned[0].index.intersection(df.index)
                aligned[0] = aligned[0].loc[common_idx]
                aligned.append(df.loc[common_idx])
                
            elif method == 'outer':
                # Keep all dates, fill missing
                all_idx = aligned[0].index.union(df.index)
                aligned[0] = aligned[0].reindex(all_idx)
                aligned.append(df.reindex(all_idx))
                
            elif method == 'left':
                # Keep dates from first DataFrame
                aligned.append(df.reindex(aligned[0].index))
                
            elif method == 'right':
                # Keep dates from current DataFrame
                aligned[0] = aligned[0].reindex(df.index)
                aligned.append(df)
            
            else:
                logger.warning(f"Unknown alignment method: {method}")
                aligned.append(df)
        
        logger.info(f"Aligned {len(dataframes)} DataFrames: {len(aligned[0])} rows")
        return aligned
    
    # ─────────────────────────────────────────────────────────────
    # PRIVATE HELPER METHODS
    # ─────────────────────────────────────────────────────────────
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.
        
        Args:
            prices: Price series
            period: RSI period
            
        Returns:
            RSI series
        """
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, 
                       fast: int = 12, slow: int = 26, 
                       signal: int = 9) -> tuple:
        """
        Calculate MACD indicator.
        
        Args:
            prices: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period
            
        Returns:
            Tuple of (MACD line, Signal line)
        """
        # Calculate EMAs
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        return macd_line, signal_line
