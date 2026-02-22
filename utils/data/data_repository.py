"""
Data Repository.

This module handles data fetching from multiple sources.
Follows the Single Responsibility Principle by separating data fetching
from caching, validation, and transformation.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import warnings
import logging

logger = logging.getLogger(__name__)


class DataRepository:
    """
    Fetches data from multiple sources with fallback logic.
    
    Responsibilities:
    - Fetch data from Yahoo Finance
    - Fetch data from İş Yatırım (fallback)
    - Handle network errors and retries
    - Provide unified data fetching interface
    
    This class focuses on data retrieval without caching or validation.
    """
    
    def __init__(self, start_date: str, end_date: str):
        """
        Initialize DataRepository.
        
        Args:
            start_date: Start date for data fetching (YYYY-MM-DD)
            end_date: End date for data fetching (YYYY-MM-DD)
        """
        self.start_date = start_date
        self.end_date = end_date
        logger.info(f"DataRepository initialized: {start_date} to {end_date}")
    
    def fetch_from_yahoo(self, ticker: str, interval: str = '1d', 
                        period: str = None) -> pd.DataFrame:
        """
        Fetch data from Yahoo Finance.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'THYAO.IS')
            interval: Data interval ('1d', '1h', '1m', etc.)
            period: Period for data ('1d', '5d', '1mo', etc.) - overrides start/end dates
            
        Returns:
            DataFrame with OHLCV data, or None if fetch fails
        """
        try:
            logger.debug(f"Fetching {ticker} from Yahoo Finance (interval={interval})")
            
            if period:
                # Use period-based fetching (for live data)
                df = yf.download(ticker, period=period, interval=interval, progress=False)
            else:
                # Use date range fetching (for historical data)
                df = yf.download(
                    ticker, 
                    start=self.start_date, 
                    end=self.end_date, 
                    interval=interval,
                    progress=False
                )
            
            if df.empty:
                logger.warning(f"Yahoo Finance returned empty data for {ticker}")
                return None
            
            # Handle MultiIndex columns (when downloading multiple tickers)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            logger.info(f"Successfully fetched {len(df)} rows for {ticker} from Yahoo Finance")
            return df
            
        except Exception as e:
            logger.error(f"Yahoo Finance fetch failed for {ticker}: {e}")
            return None
    
    def fetch_from_is_yatirim(self, ticker: str) -> pd.DataFrame:
        """
        Fetch data from İş Yatırım (fallback source).
        
        Args:
            ticker: Stock ticker symbol (e.g., 'THYAO.IS')
            
        Returns:
            DataFrame with OHLCV data, or None if fetch fails
        """
        try:
            from isyatirimhisse import fetch_stock_data
            import requests
            
            logger.debug(f"Fetching {ticker} from İş Yatırım")
            
            # Symbol conversion (remove .IS suffix)
            symbol = ticker.replace('.IS', '')
            
            # Special mappings for İş Yatırım
            symbol_mapping = {
                'KOZAL': 'TRALT'  # Gold fund special case
            }
            symbol = symbol_mapping.get(symbol, symbol)
            
            # Date format: DD-MM-YYYY
            end_date_str = datetime.now().strftime('%d-%m-%Y')
            start_date_str = pd.to_datetime(self.start_date).strftime('%d-%m-%Y')
            
            # Temporarily disable SSL verification for İş Yatırım
            with self._no_ssl_verification():
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    df = fetch_stock_data(symbol, start_date_str, end_date_str)
            
            if df is None or df.empty:
                logger.warning(f"İş Yatırım returned empty data for {ticker}")
                return None
            
            # Standardize column names
            df = self._standardize_is_yatirim_columns(df)
            
            logger.info(f"Successfully fetched {len(df)} rows for {ticker} from İş Yatırım")
            return df
            
        except ImportError:
            logger.error("isyatirimhisse library not installed")
            return None
        except Exception as e:
            logger.error(f"İş Yatırım fetch failed for {ticker}: {e}")
            return None
    
    def fetch_with_fallback(self, ticker: str, interval: str = '1d',
                           period: str = None) -> pd.DataFrame:
        """
        Fetch data with automatic fallback to İş Yatırım if Yahoo fails.
        
        Args:
            ticker: Stock ticker symbol
            interval: Data interval
            period: Period for data (optional)
            
        Returns:
            DataFrame with OHLCV data, or None if all sources fail
        """
        # Try Yahoo Finance first
        df = self.fetch_from_yahoo(ticker, interval, period)
        
        if df is not None and not df.empty:
            return df
        
        # Fallback to İş Yatırım (only for daily data)
        if interval == '1d' and period is None:
            logger.info(f"Yahoo Finance failed for {ticker}, trying İş Yatırım fallback")
            df = self.fetch_from_is_yatirim(ticker)
            
            if df is not None and not df.empty:
                logger.info(f"Fallback successful for {ticker}")
                return df
        
        logger.error(f"All data sources failed for {ticker}")
        return None
    
    def fetch_live_data(self, ticker: str, interval: str = '1m', 
                       period: str = '1d') -> pd.DataFrame:
        """
        Fetch live/recent data for paper trading.
        
        Args:
            ticker: Stock ticker symbol
            interval: Data interval (default: '1m' for 1-minute bars)
            period: Period for data (default: '1d' for last day)
            
        Returns:
            DataFrame with recent OHLCV data, or None if fetch fails
        """
        return self.fetch_from_yahoo(ticker, interval=interval, period=period)
    
    # ─────────────────────────────────────────────────────────────
    # PRIVATE HELPER METHODS
    # ─────────────────────────────────────────────────────────────
    
    def _standardize_is_yatirim_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize İş Yatırım column names to match Yahoo Finance format.
        
        Args:
            df: DataFrame from İş Yatırım
            
        Returns:
            DataFrame with standardized column names
        """
        # İş Yatırım typically uses Turkish column names
        column_mapping = {
            'Tarih': 'Date',
            'Açılış': 'Open',
            'Yüksek': 'High',
            'Düşük': 'Low',
            'Kapanış': 'Close',
            'Hacim': 'Volume',
            # Add more mappings as needed
        }
        
        # Rename columns if they exist
        df = df.rename(columns=column_mapping)
        
        # Ensure Date is index
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
        
        return df
    
    class _no_ssl_verification:
        """Context manager to temporarily disable SSL verification."""
        
        def __enter__(self):
            import requests
            self.old_request = requests.Session.request
            self.old_init = requests.Session.__init__
            
            def new_init(obj, *args, **kwargs):
                self.old_init(obj, *args, **kwargs)
                obj.verify = False
            
            requests.Session.__init__ = new_init
            return self
        
        def __exit__(self, exc_type, exc_value, traceback):
            import requests
            requests.Session.__init__ = self.old_init
