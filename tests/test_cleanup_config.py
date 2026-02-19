"""Unit tests for CleanupConfig class.

Tests configuration loading, default values, validation, and error handling.
"""

import pytest
import tempfile
from pathlib import Path
from scripts.maintenance.core.config import CleanupConfig


class TestCleanupConfigDefaults:
    """Test default configuration values."""
    
    def test_defaults_when_no_config_file(self):
        """Test that defaults are used when config file doesn't exist."""
        config = CleanupConfig(config_path='nonexistent_config.yaml')
        
        assert config.small_file_threshold == 100
        assert config.large_file_threshold == 500
        assert config.log_retention_days == 30
        assert config.duplicate_similarity == 0.85
        assert '.venv' in config.excluded_dirs
        assert '__pycache__' in config.excluded_dirs
        assert 'test_*.py' in config.excluded_patterns
    
    def test_defaults_with_empty_yaml(self):
        """Test that defaults are used with empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('')
            temp_path = f.name
        
        try:
            config = CleanupConfig(config_path=temp_path)
            assert config.small_file_threshold == 100
            assert config.large_file_threshold == 500
        finally:
            Path(temp_path).unlink()


class TestCleanupConfigLoading:
    """Test configuration loading from YAML files."""
    
    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        yaml_content = """
thresholds:
  small_file_lines: 50
  large_file_lines: 1000
  log_retention_days: 60
  duplicate_similarity: 0.9

exclusions:
  directories:
    - .venv
    - custom_dir
  patterns:
    - "*.tmp"

script_categories:
  production:
    - main.py
  analysis_keywords:
    - analyze
  maintenance_keywords:
    - clean
  test_keywords:
    - test
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = CleanupConfig(config_path=temp_path)
            
            assert config.small_file_threshold == 50
            assert config.large_file_threshold == 1000
            assert config.log_retention_days == 60
            assert config.duplicate_similarity == 0.9
            assert config.excluded_dirs == ['.venv', 'custom_dir']
            assert config.excluded_patterns == ['*.tmp']
            assert config.production_scripts == ['main.py']
            assert config.analysis_keywords == ['analyze']
        finally:
            Path(temp_path).unlink()
    
    def test_partial_config_uses_defaults(self):
        """Test that missing values use defaults."""
        yaml_content = """
thresholds:
  small_file_lines: 75
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = CleanupConfig(config_path=temp_path)
            
            assert config.small_file_threshold == 75
            assert config.large_file_threshold == 500  # default
            assert config.log_retention_days == 30  # default
        finally:
            Path(temp_path).unlink()


class TestCleanupConfigValidation:
    """Test configuration validation."""
    
    def test_invalid_yaml_syntax(self):
        """Test handling of invalid YAML syntax."""
        yaml_content = """
thresholds:
  small_file_lines: [invalid yaml
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = CleanupConfig(config_path=temp_path)
            is_valid, errors = config.validate()
            
            # Should use defaults and report error
            assert not is_valid
            assert any('YAML' in error for error in errors)
            assert config.small_file_threshold == 100  # default
        finally:
            Path(temp_path).unlink()
    
    def test_invalid_threshold_values(self):
        """Test validation of invalid threshold values."""
        yaml_content = """
thresholds:
  small_file_lines: -10
  large_file_lines: 0
  log_retention_days: -5
  duplicate_similarity: 1.5
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = CleanupConfig(config_path=temp_path)
            is_valid, errors = config.validate()
            
            # Should use defaults for invalid values
            assert not is_valid
            assert len(errors) > 0
            assert config.small_file_threshold == 100  # default
            assert config.large_file_threshold == 500  # default
            assert config.log_retention_days == 30  # default
            assert config.duplicate_similarity == 0.85  # default
        finally:
            Path(temp_path).unlink()
    
    def test_small_threshold_greater_than_large(self):
        """Test validation when small threshold >= large threshold."""
        yaml_content = """
thresholds:
  small_file_lines: 600
  large_file_lines: 500
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = CleanupConfig(config_path=temp_path)
            is_valid, errors = config.validate()
            
            assert not is_valid
            assert any('must be less than' in error for error in errors)
        finally:
            Path(temp_path).unlink()
    
    def test_valid_config_passes_validation(self):
        """Test that a valid configuration passes validation."""
        yaml_content = """
thresholds:
  small_file_lines: 100
  large_file_lines: 500
  log_retention_days: 30
  duplicate_similarity: 0.85
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = CleanupConfig(config_path=temp_path)
            is_valid, errors = config.validate()
            
            assert is_valid
            assert len(errors) == 0
        finally:
            Path(temp_path).unlink()


class TestCleanupConfigEdgeCases:
    """Test edge cases and error handling."""
    
    def test_non_list_exclusions(self):
        """Test handling of non-list exclusion values."""
        yaml_content = """
exclusions:
  directories: "not a list"
  patterns: 123
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = CleanupConfig(config_path=temp_path)
            is_valid, errors = config.validate()
            
            # Should use defaults for invalid values
            assert not is_valid
            assert isinstance(config.excluded_dirs, list)
            assert isinstance(config.excluded_patterns, list)
        finally:
            Path(temp_path).unlink()
    
    def test_missing_script_categories(self):
        """Test handling of missing script categories."""
        yaml_content = """
thresholds:
  small_file_lines: 100
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = CleanupConfig(config_path=temp_path)
            
            # Should return empty lists for missing categories
            assert config.production_scripts == []
            assert config.analysis_keywords == []
            assert config.maintenance_keywords == []
            assert config.test_keywords == []
        finally:
            Path(temp_path).unlink()
    
    def test_duplicate_similarity_boundary_values(self):
        """Test duplicate similarity at boundary values."""
        yaml_content = """
thresholds:
  duplicate_similarity: 0.0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = CleanupConfig(config_path=temp_path)
            assert config.duplicate_similarity == 0.0
            
            is_valid, errors = config.validate()
            assert is_valid
        finally:
            Path(temp_path).unlink()
        
        yaml_content = """
thresholds:
  duplicate_similarity: 1.0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = CleanupConfig(config_path=temp_path)
            assert config.duplicate_similarity == 1.0
            
            is_valid, errors = config.validate()
            assert is_valid
        finally:
            Path(temp_path).unlink()
