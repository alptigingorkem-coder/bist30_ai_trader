"""
Unit tests for Feature Importance Analysis CLI

Tests the command-line interface functionality including argument parsing,
validation, and configuration creation.

Requirements: 5.1, 5.2, 5.3, 5.5, 9.1, 9.2
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.analysis.run_feature_importance import (
    parse_arguments,
    validate_arguments,
    create_analysis_config,
    load_config_module
)


class TestCLIArgumentParsing(unittest.TestCase):
    """Test CLI argument parsing functionality."""
    
    def test_default_arguments(self):
        """Test that default arguments are set correctly."""
        with patch('sys.argv', ['run_feature_importance.py']):
            args = parse_arguments()
            
            self.assertEqual(args.config, 'config')
            self.assertEqual(args.threshold, 0.001)
            self.assertEqual(args.sample_size, 1000)
            self.assertIsNone(args.start_date)
            self.assertIsNone(args.end_date)
            self.assertIsNone(args.tickers)
            self.assertEqual(args.output_dir, 'reports/feature_importance')
            self.assertFalse(args.save_models)
            self.assertEqual(args.log_level, 'INFO')
            self.assertFalse(args.quiet)
    
    def test_custom_arguments(self):
        """Test parsing custom arguments."""
        with patch('sys.argv', [
            'run_feature_importance.py',
            '--threshold', '0.005',
            '--sample-size', '2000',
            '--start-date', '2023-01-01',
            '--end-date', '2023-12-31',
            '--tickers', 'THYAO,AKBNK',
            '--output-dir', 'custom_output',
            '--save-models',
            '--log-level', 'DEBUG'
        ]):
            args = parse_arguments()
            
            self.assertEqual(args.threshold, 0.005)
            self.assertEqual(args.sample_size, 2000)
            self.assertEqual(args.start_date, '2023-01-01')
            self.assertEqual(args.end_date, '2023-12-31')
            self.assertEqual(args.tickers, 'THYAO,AKBNK')
            self.assertEqual(args.output_dir, 'custom_output')
            self.assertTrue(args.save_models)
            self.assertEqual(args.log_level, 'DEBUG')


class TestCLIArgumentValidation(unittest.TestCase):
    """Test CLI argument validation functionality."""
    
    def test_valid_arguments(self):
        """Test that valid arguments pass validation."""
        args = MagicMock()
        args.threshold = 0.001
        args.sample_size = 1000
        args.start_date = '2023-01-01'
        args.end_date = '2023-12-31'
        
        # Should not raise any exception
        validate_arguments(args)
    
    def test_invalid_threshold_negative(self):
        """Test that negative threshold raises ValueError."""
        args = MagicMock()
        args.threshold = -0.5
        args.sample_size = 1000
        args.start_date = None
        args.end_date = None
        
        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        
        self.assertIn('Threshold must be between 0 and 1', str(context.exception))
    
    def test_invalid_threshold_too_large(self):
        """Test that threshold > 1 raises ValueError."""
        args = MagicMock()
        args.threshold = 1.5
        args.sample_size = 1000
        args.start_date = None
        args.end_date = None
        
        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        
        self.assertIn('Threshold must be between 0 and 1', str(context.exception))
    
    def test_invalid_sample_size(self):
        """Test that non-positive sample size raises ValueError."""
        args = MagicMock()
        args.threshold = 0.001
        args.sample_size = -100
        args.start_date = None
        args.end_date = None
        
        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        
        self.assertIn('Sample size must be positive', str(context.exception))
    
    def test_invalid_start_date_format(self):
        """Test that invalid start date format raises ValueError."""
        args = MagicMock()
        args.threshold = 0.001
        args.sample_size = 1000
        args.start_date = '2023/01/01'
        args.end_date = None
        
        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        
        self.assertIn('Invalid start date format', str(context.exception))
    
    def test_invalid_end_date_format(self):
        """Test that invalid end date format raises ValueError."""
        args = MagicMock()
        args.threshold = 0.001
        args.sample_size = 1000
        args.start_date = None
        args.end_date = '31-12-2023'
        
        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        
        self.assertIn('Invalid end date format', str(context.exception))
    
    def test_invalid_date_order(self):
        """Test that start date after end date raises ValueError."""
        args = MagicMock()
        args.threshold = 0.001
        args.sample_size = 1000
        args.start_date = '2023-12-31'
        args.end_date = '2023-01-01'
        
        with self.assertRaises(ValueError) as context:
            validate_arguments(args)
        
        self.assertIn('Start date', str(context.exception))
        self.assertIn('must be before end date', str(context.exception))


class TestConfigCreation(unittest.TestCase):
    """Test analysis configuration creation from CLI arguments."""
    
    def test_minimal_config(self):
        """Test creating config with minimal arguments."""
        args = MagicMock()
        args.sample_size = 1000
        args.threshold = 0.001
        args.output_dir = 'reports/feature_importance'
        args.save_models = False
        args.start_date = None
        args.end_date = None
        args.tickers = None
        
        config = create_analysis_config(args)
        
        self.assertEqual(config['sample_size'], 1000)
        self.assertEqual(config['importance_threshold'], 0.001)
        self.assertEqual(config['output_dir'], 'reports/feature_importance')
        self.assertFalse(config['save_models'])
        self.assertNotIn('start_date', config)
        self.assertNotIn('end_date', config)
        self.assertNotIn('tickers', config)
    
    def test_full_config(self):
        """Test creating config with all arguments."""
        args = MagicMock()
        args.sample_size = 2000
        args.threshold = 0.005
        args.output_dir = 'custom_output'
        args.save_models = True
        args.start_date = '2023-01-01'
        args.end_date = '2023-12-31'
        args.tickers = 'THYAO,AKBNK,EREGL'
        
        config = create_analysis_config(args)
        
        self.assertEqual(config['sample_size'], 2000)
        self.assertEqual(config['importance_threshold'], 0.005)
        self.assertEqual(config['output_dir'], 'custom_output')
        self.assertTrue(config['save_models'])
        self.assertEqual(config['start_date'], '2023-01-01')
        self.assertEqual(config['end_date'], '2023-12-31')
        self.assertEqual(config['tickers'], ['THYAO', 'AKBNK', 'EREGL'])
    
    def test_ticker_parsing(self):
        """Test that tickers are correctly parsed from comma-separated string."""
        args = MagicMock()
        args.sample_size = 1000
        args.threshold = 0.001
        args.output_dir = 'reports/feature_importance'
        args.save_models = False
        args.start_date = None
        args.end_date = None
        args.tickers = 'THYAO, AKBNK , EREGL'  # With spaces
        
        config = create_analysis_config(args)
        
        self.assertEqual(config['tickers'], ['THYAO', 'AKBNK', 'EREGL'])


class TestConfigModuleLoading(unittest.TestCase):
    """Test configuration module loading."""
    
    def test_load_valid_config(self):
        """Test loading a valid config module."""
        # This should work if config.py exists
        try:
            config_module = load_config_module('config')
            self.assertIsNotNone(config_module)
        except ImportError:
            self.skipTest("config module not available")
    
    def test_load_invalid_config(self):
        """Test that loading invalid config raises ImportError."""
        with self.assertRaises(ImportError) as context:
            load_config_module('nonexistent_config_module')
        
        self.assertIn('not found', str(context.exception))


if __name__ == '__main__':
    unittest.main()
