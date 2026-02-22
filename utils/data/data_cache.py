"""
Data Cache.

This module handles caching of data using Parquet files.
Follows the Single Responsibility Principle by separating caching
from fetching, validation, and transformation.
"""

import pandas as pd
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataCache:
    """
    Manages data caching using Parquet files.
    
    Responsibilities:
    - Store data in Parquet format
    - Retrieve cached data
    - Validate cache age
    - Invalidate expired cache
    
    This class focuses on caching without fetching or validation logic.
    """
    
    DEFAULT_CACHE_DIR = "data/live_cache"
    DEFAULT_MAX_AGE_HOURS = 24
    
    def __init__(self, cache_dir: str = None, max_age_hours: int = None):
        """
        Initialize DataCache.
        
        Args:
            cache_dir: Directory for cache files (default: data/live_cache)
            max_age_hours: Maximum cache age in hours (default: 24)
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.max_age_hours = max_age_hours or self.DEFAULT_MAX_AGE_HOURS
        
        # Create cache directory if it doesn't exist
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DataCache initialized: dir={self.cache_dir}, max_age={self.max_age_hours}h")
    
    def get(self, key: str) -> pd.DataFrame:
        """
        Get data from cache.
        
        Args:
            key: Cache key (typically ticker symbol)
            
        Returns:
            Cached DataFrame, or None if not found or expired
        """
        filepath = self._get_filepath(key)
        
        if not os.path.exists(filepath):
            logger.debug(f"Cache miss: {key} (file not found)")
            return None
        
        # Check if cache is valid (not expired)
        if not self.is_cache_valid(key):
            logger.debug(f"Cache expired: {key}")
            return None
        
        try:
            df = pd.read_parquet(filepath)
            logger.info(f"Cache hit: {key} ({len(df)} rows)")
            return df
        except Exception as e:
            logger.error(f"Cache read error for {key}: {e}")
            return None
    
    def put(self, key: str, data: pd.DataFrame) -> bool:
        """
        Store data in cache.
        
        Args:
            key: Cache key (typically ticker symbol)
            data: DataFrame to cache
            
        Returns:
            True if successful, False otherwise
        """
        if data is None or data.empty:
            logger.warning(f"Cannot cache empty data for {key}")
            return False
        
        filepath = self._get_filepath(key)
        
        try:
            data.to_parquet(filepath)
            logger.info(f"Cached {key}: {len(data)} rows")
            return True
        except Exception as e:
            logger.error(f"Cache write error for {key}: {e}")
            return False
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate (delete) cached data.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if file was deleted, False otherwise
        """
        filepath = self._get_filepath(key)
        
        if not os.path.exists(filepath):
            logger.debug(f"Cache invalidate: {key} (file not found)")
            return False
        
        try:
            os.remove(filepath)
            logger.info(f"Cache invalidated: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache invalidate error for {key}: {e}")
            return False
    
    def is_cache_valid(self, key: str) -> bool:
        """
        Check if cached data is still valid (not expired).
        
        Args:
            key: Cache key to check
            
        Returns:
            True if cache exists and is not expired, False otherwise
        """
        filepath = self._get_filepath(key)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            # Get file modification time
            mtime = os.path.getmtime(filepath)
            file_age = datetime.now() - datetime.fromtimestamp(mtime)
            
            # Check if file is within max age
            max_age = timedelta(hours=self.max_age_hours)
            is_valid = file_age < max_age
            
            if not is_valid:
                logger.debug(f"Cache expired: {key} (age: {file_age.total_seconds()/3600:.1f}h)")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Cache validation error for {key}: {e}")
            return False
    
    def clear_all(self) -> int:
        """
        Clear all cached files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.parquet'):
                    filepath = os.path.join(self.cache_dir, filename)
                    os.remove(filepath)
                    count += 1
            
            logger.info(f"Cleared {count} cache files")
            return count
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return count
    
    def clear_expired(self) -> int:
        """
        Clear only expired cache files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.parquet'):
                    # Extract key from filename
                    key = filename.replace('.parquet', '')
                    
                    if not self.is_cache_valid(key):
                        self.invalidate(key)
                        count += 1
            
            logger.info(f"Cleared {count} expired cache files")
            return count
            
        except Exception as e:
            logger.error(f"Cache clear expired error: {e}")
            return count
    
    def get_cache_info(self, key: str) -> dict:
        """
        Get information about cached data.
        
        Args:
            key: Cache key
            
        Returns:
            Dictionary with cache info (exists, age, size, valid)
        """
        filepath = self._get_filepath(key)
        
        info = {
            'exists': False,
            'age_hours': None,
            'size_bytes': None,
            'valid': False,
            'filepath': filepath
        }
        
        if not os.path.exists(filepath):
            return info
        
        info['exists'] = True
        
        try:
            # File age
            mtime = os.path.getmtime(filepath)
            file_age = datetime.now() - datetime.fromtimestamp(mtime)
            info['age_hours'] = file_age.total_seconds() / 3600
            
            # File size
            info['size_bytes'] = os.path.getsize(filepath)
            
            # Validity
            info['valid'] = self.is_cache_valid(key)
            
        except Exception as e:
            logger.error(f"Cache info error for {key}: {e}")
        
        return info
    
    # ─────────────────────────────────────────────────────────────
    # PRIVATE HELPER METHODS
    # ─────────────────────────────────────────────────────────────
    
    def _get_filepath(self, key: str) -> str:
        """
        Get cache file path for a key.
        
        Args:
            key: Cache key
            
        Returns:
            Full file path
        """
        # Sanitize key (remove special characters)
        safe_key = key.replace('/', '_').replace('\\', '_').replace('.', '_')
        filename = f"{safe_key}.parquet"
        return os.path.join(self.cache_dir, filename)
