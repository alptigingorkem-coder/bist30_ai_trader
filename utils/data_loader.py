"""
DataLoader - Facade for data operations.

This module provides a simplified interface for data loading operations.
It delegates to specialized components following the Single Responsibility Principle.
"""

import pandas as pd
import config
from datetime import datetime
import concurrent.futures
import time

# SSL Patch (SAFE): Only suppress warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from utils.logging_config import get_logger
from utils.db_manager import DBManager
from utils.macro_data_loader import TurkeyMacroData
from utils.data import DataRepository, DataCache, DataValidator, DataTransformer

log = get_logger(__name__)


class DataLoader:
    """
    Facade for data loading operations.
    
    This class provides a simplified interface that delegates to specialized components:
    - DataRepository: Fetches data from multiple sources
    - DataCache: Manages data caching
    - DataValidator: Validates data quality
    - DataTransformer: Transforms and cleans data
    
    Maintains backward compatibility with existing API.
    """
    
    def __init__(self, start_date=config.START_DATE, end_date=config.END_DATE):
        """
        Initialize DataLoader with specialized components.
        
        Args:
            start_date: Start date for data fetching
            end_date: End date for data fetching
        """
        self.start_date = start_date
        self.end_date = end_date
        self.tickers = config.TICKERS
        self.macro_tickers = config.MACRO_TICKERS
        self._macro_cache = None
        
        # Initialize specialized components
        self.repository = DataRepository(start_date, end_date)
        self.cache = DataCache()
        self.validator = DataValidator(
            min_volume_tl=getattr(config, 'MIN_DAILY_VOLUME_TL', 0)
        )
        self.transformer = DataTransformer(
            timeframe=getattr(config, 'TIMEFRAME', 'D')
        )
        
        # Database manager
        self.db = DBManager()
        
        log.info(f"DataLoader initialized: {start_date} to {end_date}")
    
    def fetch_live_data(self, ticker: str, interval: str = '1m', 
                       period: str = '1d') -> pd.DataFrame:
        """
        Fetch live/recent data for paper trading.
        
        Args:
            ticker: Stock ticker symbol
            interval: Data interval (default: '1m')
            period: Period for data (default: '1d')
            
        Returns:
            DataFrame with recent OHLCV data, or None if fetch fails
        """
        return self.repository.fetch_live_data(ticker, interval, period)
    
    def fetch_macro_data(self) -> pd.DataFrame:
        """
        Fetch macroeconomic data (cached).
        
        Returns:
            DataFrame with macro indicators
        """
        if self._macro_cache is not None:
            return self._macro_cache
        
        log.info("Fetching macroeconomic data...")
        
        # Use specialized macro loader
        macro_loader = TurkeyMacroData()
        macro_df = macro_loader.fetch_all(start_date=self.start_date)
        
        if macro_df is None or macro_df.empty:
            log.warning("Macro data fetch failed!")
            macro_df = pd.DataFrame()
        
        # Apply lag adjustments for US data
        us_tickers = ['VIX', 'SP500']
        for col in us_tickers:
            if col in macro_df.columns:
                macro_df[col] = macro_df[col].shift(1)
        
        self._macro_cache = macro_df
        return macro_df
    
    def get_combined_data(self, ticker: str) -> pd.DataFrame:
        """
        Get stock data combined with macro data.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            DataFrame with stock and macro data combined
        """
        try:
            # Fetch stock data
            stock_data = self.fetch_stock_data(ticker)
            if stock_data is None:
                return None
            
            # Fetch macro data
            macro_data = self.fetch_macro_data()
            
            # Combine data
            combined_df = stock_data.join(macro_data, how='left')
            
            # Forward fill macro data gaps
            combined_df = combined_df.ffill()
            
            # Resample if needed
            combined_df = self.resample_to_weekly(combined_df)
            
            return combined_df
            
        except Exception as e:
            log.error(f"get_combined_data error for {ticker}: {e}")
            raise e
    
    def fetch_stock_data(self, ticker: str) -> pd.DataFrame:
        """
        Fetch stock data with caching and validation.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            DataFrame with OHLCV data, or None if fetch fails
        """
        log.info(f"Fetching data for {ticker}...")
        
        # Check for data gaps in DB
        is_missing = self.db.check_missing_data(ticker, days=3)
        if is_missing:
            log.warning(f"{ticker}: Data gap detected, forcing fresh fetch")
        
        # Try to load from DB
        data = self.db.fetch_data(ticker, self.start_date, self.end_date)
        
        if data is not None and not data.empty:
            last_date = data.index[-1]
            now = datetime.now()
            if last_date.tzinfo is not None:
                now = now.replace(tzinfo=last_date.tzinfo)
            
            # Check if data is recent
            if (now - last_date).days < 2:
                log.info(f"[DB] Data is current: {ticker} ({len(data)} rows)")
                return self.sanitize_data(data, ticker)
            else:
                log.info(f"[DB] Data is stale ({last_date.date()}), updating...")
        
        # Fetch from repository with fallback
        data = self.repository.fetch_with_fallback(ticker)
        
        if data is not None and not data.empty:
            # Clean data
            data = self.sanitize_data(data, ticker)
            
            # Validate data quality
            is_valid, reason = self.validator.validate_data(data, ticker)
            if not is_valid:
                log.warning(f"{ticker}: Validation failed: {reason}")
                return None
            
            # Save to DB
            self.db.save_data(data, ticker)
        
        return data
    
    def sanitize_data(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Clean and sanitize data.
        
        Args:
            df: DataFrame to clean
            ticker: Ticker symbol (for logging)
            
        Returns:
            Cleaned DataFrame
        """
        return self.transformer.clean_data(df, ticker)
    
    def resample_to_weekly(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Resample data to weekly timeframe if configured.
        
        Args:
            data: DataFrame to resample
            
        Returns:
            Resampled DataFrame
        """
        timeframe = getattr(config, 'TIMEFRAME', 'D')
        if timeframe != 'W':
            return data
        
        return self.transformer.resample_data(data, timeframe='W')
    
    def fetch_data_parallel(self, tickers: list, max_workers: int = 10) -> dict:
        """
        Fetch data for multiple tickers in parallel.
        
        Args:
            tickers: List of ticker symbols
            max_workers: Maximum number of parallel workers
            
        Returns:
            Dictionary mapping tickers to DataFrames
        """
        start_t = time.time()
        results = {}
        
        # Prime macro cache to avoid race conditions
        self.fetch_macro_data()
        
        log.info(f"🚀 Parallel fetch starting: {len(tickers)} tickers, {max_workers} workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ticker = {
                executor.submit(self.get_combined_data, ticker): ticker
                for ticker in tickers
            }
            
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result()
                    if data is not None and not data.empty:
                        results[ticker] = data
                    else:
                        log.warning(f"❌ {ticker}: Empty data returned")
                except Exception as e:
                    log.error(f"❌ {ticker}: Fetch error: {e}")
        
        duration = time.time() - start_t
        log.info(
            f"✅ Parallel fetch completed. "
            f"Duration: {duration:.2f}s. Success: {len(results)}/{len(tickers)}"
        )
        return results


if __name__ == "__main__":
    # Test
    loader = DataLoader()
    sample_data = loader.get_combined_data("THYAO.IS")
    if sample_data is not None:
        log.info("%s", sample_data.head())
        log.info("%s", sample_data.tail())
    else:
        log.info("Data fetch failed.")
