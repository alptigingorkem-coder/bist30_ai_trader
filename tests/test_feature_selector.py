"""
Unit tests for FeatureSelector module

Tests the feature selection, blacklist management, and validation functionality.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 8.2, 8.3
"""

import json
import os
import tempfile
import pytest
import pandas as pd
from scripts.analysis.feature_selector import FeatureSelector


class TestFeatureSelectorInit:
    """Test FeatureSelector initialization"""
    
    def test_init_default_threshold(self):
        """Test initialization with default threshold"""
        selector = FeatureSelector()
        assert selector.threshold == 0.001
    
    def test_init_custom_threshold(self):
        """Test initialization with custom threshold"""
        selector = FeatureSelector(threshold=0.005)
        assert selector.threshold == 0.005
    
    def test_init_negative_threshold_raises_error(self):
        """Test that negative threshold raises ValueError"""
        with pytest.raises(ValueError, match="threshold must be non-negative"):
            FeatureSelector(threshold=-0.001)
    
    def test_init_zero_threshold(self):
        """Test initialization with zero threshold"""
        selector = FeatureSelector(threshold=0.0)
        assert selector.threshold == 0.0


class TestCreateBlacklist:
    """Test blacklist creation functionality"""
    
    def test_create_blacklist_basic(self):
        """Test basic blacklist creation with threshold filtering"""
        selector = FeatureSelector(threshold=0.01)
        
        importance_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3', 'f4', 'f5'],
            'importance': [0.1, 0.005, 0.02, 0.008, 0.15]
        })
        
        blacklist = selector.create_blacklist(importance_df)
        
        # f2 (0.005) and f4 (0.008) should be blacklisted
        assert len(blacklist) == 2
        assert 'f2' in blacklist
        assert 'f4' in blacklist
        assert 'f1' not in blacklist
        assert 'f3' not in blacklist
        assert 'f5' not in blacklist
    
    def test_create_blacklist_all_above_threshold(self):
        """Test blacklist creation when all features are above threshold"""
        selector = FeatureSelector(threshold=0.001)
        
        importance_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3'],
            'importance': [0.1, 0.05, 0.02]
        })
        
        blacklist = selector.create_blacklist(importance_df)
        assert len(blacklist) == 0
    
    def test_create_blacklist_all_below_threshold(self):
        """Test blacklist creation when all features are below threshold"""
        selector = FeatureSelector(threshold=0.1)
        
        importance_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3'],
            'importance': [0.01, 0.005, 0.02]
        })
        
        blacklist = selector.create_blacklist(importance_df)
        assert len(blacklist) == 3
        assert set(blacklist) == {'f1', 'f2', 'f3'}
    
    def test_create_blacklist_empty_dataframe_raises_error(self):
        """Test that empty DataFrame raises ValueError"""
        selector = FeatureSelector()
        
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="importance_df cannot be empty"):
            selector.create_blacklist(empty_df)
    
    def test_create_blacklist_missing_feature_column_raises_error(self):
        """Test that missing 'feature' column raises ValueError"""
        selector = FeatureSelector()
        
        df = pd.DataFrame({
            'name': ['f1', 'f2'],
            'importance': [0.1, 0.2]
        })
        
        with pytest.raises(ValueError, match="must contain 'feature' column"):
            selector.create_blacklist(df)
    
    def test_create_blacklist_missing_importance_column_raises_error(self):
        """Test that missing 'importance' column raises ValueError"""
        selector = FeatureSelector()
        
        df = pd.DataFrame({
            'feature': ['f1', 'f2'],
            'score': [0.1, 0.2]
        })
        
        with pytest.raises(ValueError, match="must contain 'importance' column"):
            selector.create_blacklist(df)
    
    def test_create_blacklist_exact_threshold_not_blacklisted(self):
        """Test that features exactly at threshold are not blacklisted"""
        selector = FeatureSelector(threshold=0.01)
        
        importance_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3'],
            'importance': [0.01, 0.009, 0.011]
        })
        
        blacklist = selector.create_blacklist(importance_df)
        
        # Only f2 (0.009) should be blacklisted
        assert len(blacklist) == 1
        assert 'f2' in blacklist
        assert 'f1' not in blacklist  # Exactly at threshold
        assert 'f3' not in blacklist


class TestSaveLoadBlacklist:
    """Test blacklist persistence functionality"""
    
    def test_save_and_load_blacklist(self):
        """Test saving and loading blacklist round-trip"""
        selector = FeatureSelector()
        
        blacklist = ['feature1', 'feature2', 'feature3']
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test_blacklist.json')
            
            # Save
            selector.save_blacklist(blacklist, path)
            
            # Verify file exists
            assert os.path.exists(path)
            
            # Load
            loaded_blacklist = selector.load_blacklist(path)
            
            # Verify content
            assert loaded_blacklist == blacklist
    
    def test_save_empty_blacklist(self):
        """Test saving empty blacklist"""
        selector = FeatureSelector()
        
        blacklist = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'empty_blacklist.json')
            
            selector.save_blacklist(blacklist, path)
            loaded_blacklist = selector.load_blacklist(path)
            
            assert loaded_blacklist == []
    
    def test_save_blacklist_creates_directories(self):
        """Test that save_blacklist creates parent directories"""
        selector = FeatureSelector()
        
        blacklist = ['f1', 'f2']
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'subdir1', 'subdir2', 'blacklist.json')
            
            # Directory doesn't exist yet
            assert not os.path.exists(os.path.dirname(path))
            
            # Save should create directories
            selector.save_blacklist(blacklist, path)
            
            # Verify directories and file were created
            assert os.path.exists(path)
            loaded_blacklist = selector.load_blacklist(path)
            assert loaded_blacklist == blacklist
    
    def test_save_blacklist_none_raises_error(self):
        """Test that saving None blacklist raises ValueError"""
        selector = FeatureSelector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'blacklist.json')
            
            with pytest.raises(ValueError, match="blacklist cannot be None"):
                selector.save_blacklist(None, path)
    
    def test_load_nonexistent_file_raises_error(self):
        """Test that loading non-existent file raises FileNotFoundError"""
        selector = FeatureSelector()
        
        with pytest.raises(FileNotFoundError, match="Blacklist file not found"):
            selector.load_blacklist('/nonexistent/path/blacklist.json')
    
    def test_load_invalid_json_raises_error(self):
        """Test that loading invalid JSON raises ValueError"""
        selector = FeatureSelector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'invalid.json')
            
            # Write invalid JSON
            with open(path, 'w') as f:
                f.write('{ invalid json }')
            
            with pytest.raises(ValueError, match="Invalid JSON"):
                selector.load_blacklist(path)
    
    def test_load_wrong_format_raises_error(self):
        """Test that loading wrong format (not a list) raises ValueError"""
        selector = FeatureSelector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'wrong_format.json')
            
            # Write JSON object instead of list
            with open(path, 'w') as f:
                json.dump({'features': ['f1', 'f2']}, f)
            
            with pytest.raises(ValueError, match="must contain a list"):
                selector.load_blacklist(path)


class TestValidateBlacklist:
    """Test blacklist validation functionality"""
    
    def test_validate_blacklist_within_limit(self):
        """Test validation passes when blacklist is within 80% limit"""
        selector = FeatureSelector()
        
        blacklist = ['f1', 'f2', 'f3']  # 3 out of 10 = 30%
        total_features = 10
        
        result = selector.validate_blacklist(blacklist, total_features)
        assert result is True
    
    def test_validate_blacklist_at_80_percent(self):
        """Test validation passes when blacklist is exactly at 80%"""
        selector = FeatureSelector()
        
        blacklist = ['f' + str(i) for i in range(8)]  # 8 out of 10 = 80%
        total_features = 10
        
        result = selector.validate_blacklist(blacklist, total_features)
        assert result is True
    
    def test_validate_blacklist_exceeds_limit(self):
        """Test validation fails when blacklist exceeds 80% limit"""
        selector = FeatureSelector()
        
        blacklist = ['f' + str(i) for i in range(9)]  # 9 out of 10 = 90%
        total_features = 10
        
        result = selector.validate_blacklist(blacklist, total_features)
        assert result is False
    
    def test_validate_empty_blacklist(self):
        """Test validation passes for empty blacklist"""
        selector = FeatureSelector()
        
        blacklist = []
        total_features = 10
        
        result = selector.validate_blacklist(blacklist, total_features)
        assert result is True
    
    def test_validate_all_features_blacklisted(self):
        """Test validation fails when all features are blacklisted"""
        selector = FeatureSelector()
        
        blacklist = ['f' + str(i) for i in range(10)]  # 10 out of 10 = 100%
        total_features = 10
        
        result = selector.validate_blacklist(blacklist, total_features)
        assert result is False
    
    def test_validate_blacklist_zero_total_features_raises_error(self):
        """Test that zero total_features raises ValueError"""
        selector = FeatureSelector()
        
        blacklist = ['f1']
        
        with pytest.raises(ValueError, match="total_features must be positive"):
            selector.validate_blacklist(blacklist, 0)
    
    def test_validate_blacklist_negative_total_features_raises_error(self):
        """Test that negative total_features raises ValueError"""
        selector = FeatureSelector()
        
        blacklist = ['f1']
        
        with pytest.raises(ValueError, match="total_features must be positive"):
            selector.validate_blacklist(blacklist, -5)
    
    def test_validate_blacklist_none_raises_error(self):
        """Test that None blacklist raises ValueError"""
        selector = FeatureSelector()
        
        with pytest.raises(ValueError, match="blacklist cannot be None"):
            selector.validate_blacklist(None, 10)


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_workflow(self):
        """Test complete workflow: create, save, load, validate"""
        selector = FeatureSelector(threshold=0.01)
        
        # Create importance DataFrame
        importance_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3', 'f4', 'f5'],
            'importance': [0.1, 0.005, 0.02, 0.008, 0.15]
        })
        
        # Create blacklist
        blacklist = selector.create_blacklist(importance_df)
        assert len(blacklist) == 2
        
        # Validate blacklist
        is_valid = selector.validate_blacklist(blacklist, len(importance_df))
        assert is_valid is True  # 2 out of 5 = 40%
        
        # Save and load
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'blacklist.json')
            
            selector.save_blacklist(blacklist, path)
            loaded_blacklist = selector.load_blacklist(path)
            
            assert loaded_blacklist == blacklist
    
    def test_workflow_with_excessive_blacklist(self):
        """Test workflow when blacklist exceeds 80% limit"""
        selector = FeatureSelector(threshold=0.5)  # High threshold
        
        # Most features have low importance
        importance_df = pd.DataFrame({
            'feature': ['f' + str(i) for i in range(10)],
            'importance': [0.1, 0.05, 0.02, 0.01, 0.03, 0.04, 0.06, 0.08, 0.09, 0.6]
        })
        
        # Create blacklist
        blacklist = selector.create_blacklist(importance_df)
        assert len(blacklist) == 9  # All except f9 (0.6)
        
        # Validate should fail
        is_valid = selector.validate_blacklist(blacklist, len(importance_df))
        assert is_valid is False  # 9 out of 10 = 90%
