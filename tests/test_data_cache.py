"""
Unit tests for DataCache.
"""

import unittest
import tempfile
import shutil
import os
import time
import pandas as pd
from datetime import datetime, timedelta

from utils.data.data_cache import DataCache


class TestDataCacheInit(unittest.TestCase):
    """Test DataCache initialization."""
    
    def test_init_default(self):
        cache = DataCache()
        self.assertEqual(cache.max_age_hours, 24)
        self.assertTrue(os.path.exists(cache.cache_dir))
    
    def test_init_custom(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = DataCache(cache_dir=tmpdir, max_age_hours=12)
            self.assertEqual(cache.cache_dir, tmpdir)
            self.assertEqual(cache.max_age_hours, 12)


class TestCachePutGet(unittest.TestCase):
    """Test cache put and get operations."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache = DataCache(cache_dir=self.tmpdir)
        self.test_df = pd.DataFrame({
            'Close': [100, 101, 102],
            'Volume': [1000, 1100, 1200]
        }, index=pd.date_range('2023-01-01', periods=3))
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def test_put_and_get_success(self):
        # Put data
        result = self.cache.put('TEST', self.test_df)
        self.assertTrue(result)
        
        # Get data
        retrieved = self.cache.get('TEST')
        self.assertIsNotNone(retrieved)
        self.assertEqual(len(retrieved), 3)
        # Compare values only (index frequency may differ after parquet round-trip)
        pd.testing.assert_frame_equal(retrieved, self.test_df, check_freq=False)
    
    def test_put_empty_data(self):
        # Cannot cache empty DataFrame
        result = self.cache.put('EMPTY', pd.DataFrame())
        self.assertFalse(result)
    
    def test_put_none_data(self):
        # Cannot cache None
        result = self.cache.put('NONE', None)
        self.assertFalse(result)
    
    def test_get_nonexistent(self):
        # Get non-existent key
        result = self.cache.get('NONEXISTENT')
        self.assertIsNone(result)
    
    def test_get_expired(self):
        # Put data with very short max age
        cache = DataCache(cache_dir=self.tmpdir, max_age_hours=0.0001)  # ~0.36 seconds
        cache.put('EXPIRE', self.test_df)
        
        # Wait for expiration
        time.sleep(0.5)
        
        # Get should return None (expired)
        result = cache.get('EXPIRE')
        self.assertIsNone(result)


class TestCacheInvalidate(unittest.TestCase):
    """Test cache invalidation."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache = DataCache(cache_dir=self.tmpdir)
        self.test_df = pd.DataFrame({'Close': [100]})
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def test_invalidate_existing(self):
        # Put data
        self.cache.put('TEST', self.test_df)
        
        # Invalidate
        result = self.cache.invalidate('TEST')
        self.assertTrue(result)
        
        # Verify deleted
        retrieved = self.cache.get('TEST')
        self.assertIsNone(retrieved)
    
    def test_invalidate_nonexistent(self):
        # Invalidate non-existent key
        result = self.cache.invalidate('NONEXISTENT')
        self.assertFalse(result)


class TestCacheValidation(unittest.TestCase):
    """Test cache validation."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache = DataCache(cache_dir=self.tmpdir, max_age_hours=1)
        self.test_df = pd.DataFrame({'Close': [100]})
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def test_is_cache_valid_fresh(self):
        # Put fresh data
        self.cache.put('FRESH', self.test_df)
        
        # Should be valid
        self.assertTrue(self.cache.is_cache_valid('FRESH'))
    
    def test_is_cache_valid_expired(self):
        # Put data with very short max age
        cache = DataCache(cache_dir=self.tmpdir, max_age_hours=0.0001)
        cache.put('EXPIRE', self.test_df)
        
        # Wait for expiration
        time.sleep(0.5)
        
        # Should be invalid
        self.assertFalse(cache.is_cache_valid('EXPIRE'))
    
    def test_is_cache_valid_nonexistent(self):
        # Non-existent key should be invalid
        self.assertFalse(self.cache.is_cache_valid('NONEXISTENT'))


class TestCacheClear(unittest.TestCase):
    """Test cache clearing operations."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache = DataCache(cache_dir=self.tmpdir)
        self.test_df = pd.DataFrame({'Close': [100]})
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def test_clear_all(self):
        # Put multiple items
        self.cache.put('TEST1', self.test_df)
        self.cache.put('TEST2', self.test_df)
        self.cache.put('TEST3', self.test_df)
        
        # Clear all
        count = self.cache.clear_all()
        self.assertEqual(count, 3)
        
        # Verify all deleted
        self.assertIsNone(self.cache.get('TEST1'))
        self.assertIsNone(self.cache.get('TEST2'))
        self.assertIsNone(self.cache.get('TEST3'))
    
    def test_clear_all_empty(self):
        # Clear when empty
        count = self.cache.clear_all()
        self.assertEqual(count, 0)
    
    def test_clear_expired(self):
        # Create cache with 1 hour expiry
        cache = DataCache(cache_dir=self.tmpdir, max_age_hours=1)
        
        # Put some data
        cache.put('ITEM1', self.test_df)
        cache.put('ITEM2', self.test_df)
        cache.put('ITEM3', self.test_df)
        
        # Manually modify file times to make some expired
        import os
        old_time = time.time() - (2 * 3600)  # 2 hours ago
        
        # Make ITEM1 and ITEM2 expired
        filepath1 = cache._get_filepath('ITEM1')
        filepath2 = cache._get_filepath('ITEM2')
        os.utime(filepath1, (old_time, old_time))
        os.utime(filepath2, (old_time, old_time))
        
        # Clear expired
        count = cache.clear_expired()
        self.assertEqual(count, 2)
        
        # Verify ITEM3 still exists
        self.assertIsNotNone(cache.get('ITEM3'))
        
        # Verify ITEM1 and ITEM2 are gone
        self.assertIsNone(cache.get('ITEM1'))
        self.assertIsNone(cache.get('ITEM2'))


class TestCacheInfo(unittest.TestCase):
    """Test cache info retrieval."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache = DataCache(cache_dir=self.tmpdir)
        self.test_df = pd.DataFrame({'Close': [100, 101, 102]})
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def test_get_cache_info_existing(self):
        # Put data
        self.cache.put('TEST', self.test_df)
        
        # Get info
        info = self.cache.get_cache_info('TEST')
        
        self.assertTrue(info['exists'])
        self.assertTrue(info['valid'])
        self.assertIsNotNone(info['age_hours'])
        self.assertIsNotNone(info['size_bytes'])
        self.assertGreater(info['size_bytes'], 0)
        self.assertLess(info['age_hours'], 1)  # Should be very fresh
    
    def test_get_cache_info_nonexistent(self):
        # Get info for non-existent key
        info = self.cache.get_cache_info('NONEXISTENT')
        
        self.assertFalse(info['exists'])
        self.assertFalse(info['valid'])
        self.assertIsNone(info['age_hours'])
        self.assertIsNone(info['size_bytes'])


class TestCacheFilepath(unittest.TestCase):
    """Test cache filepath generation."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache = DataCache(cache_dir=self.tmpdir)
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def test_filepath_sanitization(self):
        # Test special characters are sanitized
        filepath1 = self.cache._get_filepath('TEST.IS')
        filepath2 = self.cache._get_filepath('TEST/SYMBOL')
        filepath3 = self.cache._get_filepath('TEST\\SYMBOL')
        
        # Should not contain special characters
        self.assertNotIn('.', os.path.basename(filepath1).replace('.parquet', ''))
        self.assertNotIn('/', os.path.basename(filepath2))
        self.assertNotIn('\\', os.path.basename(filepath3))
        
        # Should end with .parquet
        self.assertTrue(filepath1.endswith('.parquet'))
        self.assertTrue(filepath2.endswith('.parquet'))
        self.assertTrue(filepath3.endswith('.parquet'))


class TestCacheEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache = DataCache(cache_dir=self.tmpdir)
        self.test_df = pd.DataFrame({'Close': [100]})
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def test_put_large_dataframe(self):
        # Test with large DataFrame
        large_df = pd.DataFrame({
            'Close': range(10000),
            'Volume': range(10000, 20000)
        })
        
        result = self.cache.put('LARGE', large_df)
        self.assertTrue(result)
        
        retrieved = self.cache.get('LARGE')
        self.assertIsNotNone(retrieved)
        self.assertEqual(len(retrieved), 10000)
    
    def test_multiple_keys(self):
        # Test multiple different keys
        keys = ['KEY1', 'KEY2', 'KEY3', 'KEY4', 'KEY5']
        
        for key in keys:
            self.cache.put(key, self.test_df)
        
        for key in keys:
            retrieved = self.cache.get(key)
            self.assertIsNotNone(retrieved)
    
    def test_overwrite_existing(self):
        # Put initial data
        df1 = pd.DataFrame({'Close': [100]})
        self.cache.put('TEST', df1)
        
        # Overwrite with new data
        df2 = pd.DataFrame({'Close': [200, 201]})
        self.cache.put('TEST', df2)
        
        # Should get new data
        retrieved = self.cache.get('TEST')
        self.assertEqual(len(retrieved), 2)
        self.assertEqual(retrieved['Close'].iloc[0], 200)


if __name__ == '__main__':
    unittest.main()
