"""Configuration management for post-development cleanup system.

This module provides the CleanupConfig class that loads configuration from YAML files
and provides default values for all cleanup operations.
"""

from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import yaml


class CleanupConfig:
    """Configuration for cleanup operations.
    
    Loads configuration from a YAML file or uses default values if the file
    is missing or invalid. Provides validation and access to all configuration
    parameters used by the cleanup system.
    
    Attributes:
        config_path: Path to the configuration YAML file
        _config: Internal dictionary storing the loaded configuration
        _validation_errors: List of validation errors encountered
    """
    
    # Default configuration values
    DEFAULT_SMALL_FILE_THRESHOLD = 100
    DEFAULT_LARGE_FILE_THRESHOLD = 500
    DEFAULT_LOG_RETENTION_DAYS = 30
    DEFAULT_DUPLICATE_SIMILARITY = 0.85
    
    DEFAULT_EXCLUDED_DIRS = [
        '.venv', '__pycache__', '.git', 'node_modules', '.pytest_cache',
        '.mypy_cache', '.tox', 'build', 'dist', '.vscode', '.idea',
        'htmlcov', '.coverage'
    ]
    
    DEFAULT_EXCLUDED_PATTERNS = [
        'test_*.py', '*_test.py', '__init__.py', '__main__.py',
        'setup.py', 'conftest.py'
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from YAML file or use defaults.
        
        Args:
            config_path: Path to YAML configuration file. If None, looks for
                        'cleanup_config.yaml' in the current directory.
        """
        self.config_path = Path(config_path) if config_path else Path('cleanup_config.yaml')
        self._config: Dict[str, Any] = {}
        self._validation_errors: List[str] = []
        
        # Load configuration
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file or use defaults."""
        if not self.config_path.exists():
            # Use all defaults if config file doesn't exist
            self._config = self._get_default_config()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
                
            if loaded_config is None:
                # Empty YAML file
                self._config = self._get_default_config()
                return
            
            # Merge loaded config with defaults
            self._config = self._merge_with_defaults(loaded_config)
            
        except yaml.YAMLError as e:
            # Invalid YAML syntax - use defaults
            self._validation_errors.append(f"Invalid YAML syntax: {e}")
            self._config = self._get_default_config()
        except Exception as e:
            # Other errors - use defaults
            self._validation_errors.append(f"Error loading config: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration dictionary."""
        return {
            'thresholds': {
                'small_file_lines': self.DEFAULT_SMALL_FILE_THRESHOLD,
                'large_file_lines': self.DEFAULT_LARGE_FILE_THRESHOLD,
                'log_retention_days': self.DEFAULT_LOG_RETENTION_DAYS,
                'duplicate_similarity': self.DEFAULT_DUPLICATE_SIMILARITY,
            },
            'exclusions': {
                'directories': self.DEFAULT_EXCLUDED_DIRS.copy(),
                'patterns': self.DEFAULT_EXCLUDED_PATTERNS.copy(),
            },
            'script_categories': {
                'production': [],
                'analysis_keywords': [],
                'maintenance_keywords': [],
                'test_keywords': [],
            }
        }
    
    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded configuration with defaults.
        
        Args:
            loaded_config: Configuration loaded from YAML file
            
        Returns:
            Merged configuration with defaults for missing values
        """
        defaults = self._get_default_config()
        
        # Merge thresholds
        if 'thresholds' in loaded_config:
            defaults['thresholds'].update(loaded_config['thresholds'])
        
        # Merge exclusions
        if 'exclusions' in loaded_config:
            if 'directories' in loaded_config['exclusions']:
                defaults['exclusions']['directories'] = loaded_config['exclusions']['directories']
            if 'patterns' in loaded_config['exclusions']:
                defaults['exclusions']['patterns'] = loaded_config['exclusions']['patterns']
        
        # Merge script categories
        if 'script_categories' in loaded_config:
            defaults['script_categories'].update(loaded_config['script_categories'])
        
        return defaults
    
    @property
    def small_file_threshold(self) -> int:
        """Threshold for small files (default: 100 lines)."""
        value = self._config['thresholds']['small_file_lines']
        if not isinstance(value, int) or value <= 0:
            self._validation_errors.append(
                f"Invalid small_file_lines: {value}. Using default."
            )
            return self.DEFAULT_SMALL_FILE_THRESHOLD
        return value
    
    @property
    def large_file_threshold(self) -> int:
        """Threshold for large files (default: 500 lines)."""
        value = self._config['thresholds']['large_file_lines']
        if not isinstance(value, int) or value <= 0:
            self._validation_errors.append(
                f"Invalid large_file_lines: {value}. Using default."
            )
            return self.DEFAULT_LARGE_FILE_THRESHOLD
        return value
    
    @property
    def log_retention_days(self) -> int:
        """Days to retain log files (default: 30)."""
        value = self._config['thresholds']['log_retention_days']
        if not isinstance(value, int) or value < 0:
            self._validation_errors.append(
                f"Invalid log_retention_days: {value}. Using default."
            )
            return self.DEFAULT_LOG_RETENTION_DAYS
        return value
    
    @property
    def duplicate_similarity(self) -> float:
        """Minimum similarity score for duplicate detection (default: 0.85)."""
        value = self._config['thresholds']['duplicate_similarity']
        if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
            self._validation_errors.append(
                f"Invalid duplicate_similarity: {value}. Using default."
            )
            return self.DEFAULT_DUPLICATE_SIMILARITY
        return float(value)
    
    @property
    def excluded_dirs(self) -> List[str]:
        """Directories to exclude from analysis."""
        dirs = self._config['exclusions']['directories']
        if not isinstance(dirs, list):
            self._validation_errors.append(
                f"Invalid excluded directories: {dirs}. Using defaults."
            )
            return self.DEFAULT_EXCLUDED_DIRS.copy()
        return dirs
    
    @property
    def excluded_patterns(self) -> List[str]:
        """File patterns to exclude."""
        patterns = self._config['exclusions']['patterns']
        if not isinstance(patterns, list):
            self._validation_errors.append(
                f"Invalid excluded patterns: {patterns}. Using defaults."
            )
            return self.DEFAULT_EXCLUDED_PATTERNS.copy()
        return patterns
    
    @property
    def production_scripts(self) -> List[str]:
        """List of production scripts."""
        scripts = self._config['script_categories'].get('production', [])
        if not isinstance(scripts, list):
            return []
        return scripts
    
    @property
    def analysis_keywords(self) -> List[str]:
        """Keywords that indicate analysis scripts."""
        keywords = self._config['script_categories'].get('analysis_keywords', [])
        if not isinstance(keywords, list):
            return []
        return keywords
    
    @property
    def maintenance_keywords(self) -> List[str]:
        """Keywords that indicate maintenance scripts."""
        keywords = self._config['script_categories'].get('maintenance_keywords', [])
        if not isinstance(keywords, list):
            return []
        return keywords
    
    @property
    def test_keywords(self) -> List[str]:
        """Keywords that indicate test scripts."""
        keywords = self._config['script_categories'].get('test_keywords', [])
        if not isinstance(keywords, list):
            return []
        return keywords
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate configuration and return errors.
        
        Returns:
            Tuple of (is_valid, error_list) where is_valid is True if no
            validation errors were encountered.
        """
        # Clear previous validation errors from property access
        errors = self._validation_errors.copy()
        self._validation_errors.clear()
        
        # Perform validation by accessing all properties
        _ = self.small_file_threshold
        _ = self.large_file_threshold
        _ = self.log_retention_days
        _ = self.duplicate_similarity
        _ = self.excluded_dirs
        _ = self.excluded_patterns
        
        # Add any new validation errors
        errors.extend(self._validation_errors)
        
        # Additional validation: small threshold should be less than large threshold
        if self.small_file_threshold >= self.large_file_threshold:
            errors.append(
                f"small_file_threshold ({self.small_file_threshold}) must be less than "
                f"large_file_threshold ({self.large_file_threshold})"
            )
        
        return (len(errors) == 0, errors)
