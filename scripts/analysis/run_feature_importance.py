#!/usr/bin/env python3
"""
Feature Importance Analysis CLI

This script provides a command-line interface for running LightGBM feature
importance analysis with SHAP values. It allows customization of analysis
parameters and generates comprehensive reports with visualizations.

Usage:
    python scripts/analysis/run_feature_importance.py [options]

Examples:
    # Run with default settings
    python scripts/analysis/run_feature_importance.py

    # Run with custom threshold and sample size
    python scripts/analysis/run_feature_importance.py --threshold 0.005 --sample-size 2000

    # Run for specific tickers and date range
    python scripts/analysis/run_feature_importance.py --tickers THYAO,AKBNK --start-date 2023-01-01

    # Run with custom config file
    python scripts/analysis/run_feature_importance.py --config my_config.py

Requirements: 5.1, 5.2, 5.3, 9.1, 9.2, 9.5
"""

import argparse
import sys
import os
import logging
from datetime import datetime
from typing import Optional, List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.analysis.feature_importance_analyzer import FeatureImportanceAnalyzer
from scripts.analysis.feature_importance_config import AnalysisConfig
from utils.logging_config import get_logger

log = get_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    
    Requirements: 5.1, 5.2, 5.3
    """
    parser = argparse.ArgumentParser(
        description='LightGBM Feature Importance Analysis with SHAP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  %(prog)s

  # Custom threshold and sample size
  %(prog)s --threshold 0.005 --sample-size 2000

  # Specific tickers and date range
  %(prog)s --tickers THYAO,AKBNK,EREGL --start-date 2023-01-01 --end-date 2023-12-31

  # Custom output directory
  %(prog)s --output-dir reports/my_analysis

  # Save trained models
  %(prog)s --save-models

For more information, see docs/feature_importance_analysis.md
        """
    )
    
    # Configuration file
    parser.add_argument(
        '--config',
        type=str,
        default='config',
        help='Configuration module name (default: config). Can be "config" or sector-specific config.'
    )
    
    # Analysis parameters
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.001,
        help='Feature importance threshold for blacklisting (default: 0.001). '
             'Features with importance below this value will be blacklisted.'
    )
    
    parser.add_argument(
        '--sample-size',
        type=int,
        default=1000,
        help='Sample size for SHAP calculation (default: 1000). '
             'Larger values are more accurate but slower.'
    )
    
    # Date range
    parser.add_argument(
        '--start-date',
        type=str,
        default=None,
        help='Analysis start date in YYYY-MM-DD format (default: from config). '
             'Example: 2023-01-01'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        help='Analysis end date in YYYY-MM-DD format (default: from config). '
             'Example: 2023-12-31'
    )
    
    # Tickers
    parser.add_argument(
        '--tickers',
        type=str,
        default=None,
        help='Comma-separated list of tickers to analyze (default: from config). '
             'Example: THYAO,AKBNK,EREGL'
    )
    
    # Output
    parser.add_argument(
        '--output-dir',
        type=str,
        default='reports/feature_importance',
        help='Output directory for reports and visualizations (default: reports/feature_importance)'
    )
    
    parser.add_argument(
        '--save-models',
        action='store_true',
        help='Save baseline and optimized models to disk'
    )
    
    # Logging
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages (only show errors)'
    )
    
    return parser.parse_args()


def load_config_module(config_name: str):
    """
    Load configuration module dynamically.
    
    Args:
        config_name: Name of the config module (e.g., 'config', 'sector_config')
    
    Returns:
        Loaded configuration module
    
    Raises:
        ImportError: If config module cannot be loaded
    
    Requirements: 5.1
    """
    try:
        # Try to import the config module
        config_module = __import__(config_name)
        log.info(f"Configuration module '{config_name}' loaded successfully")
        return config_module
    except ImportError as e:
        log.error(f"Failed to load configuration module '{config_name}': {str(e)}")
        raise ImportError(
            f"Configuration module '{config_name}' not found. "
            f"Please ensure the module exists and is in the Python path."
        )


def validate_arguments(args: argparse.Namespace) -> None:
    """
    Validate command-line arguments.
    
    Args:
        args: Parsed arguments
    
    Raises:
        ValueError: If arguments are invalid
    
    Requirements: 5.5
    """
    # Validate threshold
    if args.threshold < 0 or args.threshold > 1:
        raise ValueError(
            f"Threshold must be between 0 and 1, got {args.threshold}"
        )
    
    # Validate sample size
    if args.sample_size <= 0:
        raise ValueError(
            f"Sample size must be positive, got {args.sample_size}"
        )
    
    # Validate dates if provided
    if args.start_date:
        try:
            datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Invalid start date format: {args.start_date}. "
                f"Expected YYYY-MM-DD"
            )
    
    if args.end_date:
        try:
            datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Invalid end date format: {args.end_date}. "
                f"Expected YYYY-MM-DD"
            )
    
    # Validate date order
    if args.start_date and args.end_date:
        start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(args.end_date, "%Y-%m-%d")
        if start_dt > end_dt:
            raise ValueError(
                f"Start date ({args.start_date}) must be before end date ({args.end_date})"
            )


def create_analysis_config(args: argparse.Namespace) -> dict:
    """
    Create analysis configuration from command-line arguments.
    
    Args:
        args: Parsed arguments
    
    Returns:
        Dictionary with analysis configuration
    
    Requirements: 5.1, 5.2, 5.3
    """
    config = {
        'sample_size': args.sample_size,
        'importance_threshold': args.threshold,
        'output_dir': args.output_dir,
        'save_models': args.save_models
    }
    
    # Add optional parameters if provided
    if args.start_date:
        config['start_date'] = args.start_date
    
    if args.end_date:
        config['end_date'] = args.end_date
    
    if args.tickers:
        # Parse comma-separated tickers
        tickers = [t.strip() for t in args.tickers.split(',')]
        config['tickers'] = tickers
    
    return config


def print_analysis_summary(result) -> None:
    """
    Print analysis results summary to console.
    
    Args:
        result: AnalysisResult object
    
    Requirements: 9.5
    """
    print("\n" + "=" * 80)
    print("FEATURE IMPORTANCE ANALYSIS RESULTS")
    print("=" * 80)
    print(f"\nTimestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {result.analysis_duration:.2f} seconds")
    
    print("\n" + "-" * 80)
    print("DATA SUMMARY")
    print("-" * 80)
    print(f"Tickers analyzed: {len(result.tickers_analyzed)}")
    print(f"Data points: {result.data_size:,}")
    if len(result.tickers_analyzed) <= 10:
        print(f"Tickers: {', '.join(result.tickers_analyzed)}")
    
    print("\n" + "-" * 80)
    print("FEATURE ANALYSIS")
    print("-" * 80)
    print(f"Total features: {result.total_features}")
    print(f"Blacklisted: {result.blacklisted_features} "
          f"({result.blacklisted_features/result.total_features*100:.1f}%)")
    print(f"Remaining: {result.remaining_features} "
          f"({result.remaining_features/result.total_features*100:.1f}%)")
    
    print("\n" + "-" * 80)
    print("MODEL PERFORMANCE")
    print("-" * 80)
    print(f"Baseline NDCG@3:  {result.baseline_ndcg3:.4f}")
    print(f"Optimized NDCG@3: {result.optimized_ndcg3:.4f}")
    
    improvement_sign = "+" if result.improvement_pct >= 0 else ""
    print(f"Improvement:      {improvement_sign}{result.improvement_pct:.2f}%")
    
    if result.improvement_pct < 0:
        print("\n⚠️  WARNING: Optimized model performs worse than baseline!")
        print("   Consider adjusting the importance threshold.")
    elif result.improvement_pct > 0:
        print("\n✓ Success: Feature selection improved model performance!")
    else:
        print("\n→ No change in model performance.")
    
    print("\n" + "-" * 80)
    print("TOP 10 MOST IMPORTANT FEATURES")
    print("-" * 80)
    for i, row in result.importance_df.head(10).iterrows():
        print(f"{i+1:2d}. {row['feature']:40s} {row['importance']:.6f}")
    
    print("\n" + "-" * 80)
    print("OUTPUT FILES")
    print("-" * 80)
    print(f"Blacklist: models/saved/feature_blacklist.json")
    print(f"Reports: {result.config['output_dir']}/")
    print(f"  - analysis_report_*.md")
    print(f"  - top_features.png")
    print(f"  - model_comparison.png")
    print(f"  - analysis_metadata_*.json")
    
    print("\n" + "=" * 80)


def main() -> int:
    """
    Main execution function.
    
    Returns:
        Exit code (0 for success, 1 for error)
    
    Requirements: 9.1, 9.2, 9.5
    """
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Configure logging
        if args.quiet:
            log_level = logging.ERROR
        else:
            log_level = getattr(logging, args.log_level)
        
        logging.getLogger().setLevel(log_level)
        
        # Print header
        if not args.quiet:
            print("\n" + "=" * 80)
            print("LightGBM Feature Importance Analysis")
            print("=" * 80)
            print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Validate arguments
        log.info("Validating arguments...")
        validate_arguments(args)
        
        # Load configuration module
        log.info(f"Loading configuration module: {args.config}")
        config_module = load_config_module(args.config)
        
        # Create analysis configuration
        log.info("Creating analysis configuration...")
        analysis_config = create_analysis_config(args)
        
        if not args.quiet:
            print(f"\nConfiguration:")
            print(f"  Config module: {args.config}")
            print(f"  Sample size: {analysis_config['sample_size']}")
            print(f"  Importance threshold: {analysis_config['importance_threshold']}")
            print(f"  Output directory: {analysis_config['output_dir']}")
            if 'start_date' in analysis_config:
                print(f"  Start date: {analysis_config['start_date']}")
            if 'end_date' in analysis_config:
                print(f"  End date: {analysis_config['end_date']}")
            if 'tickers' in analysis_config:
                print(f"  Tickers: {', '.join(analysis_config['tickers'][:5])}"
                      f"{'...' if len(analysis_config['tickers']) > 5 else ''}")
            print()
        
        # Create analyzer
        log.info("Initializing Feature Importance Analyzer...")
        analyzer = FeatureImportanceAnalyzer(
            config_module=config_module,
            analysis_config=analysis_config
        )
        
        # Run analysis
        log.info("Starting analysis...")
        if not args.quiet:
            print("Running analysis (this may take several minutes)...\n")
        
        result = analyzer.run_analysis()
        
        # Print results
        if not args.quiet:
            print_analysis_summary(result)
        
        log.info("Analysis completed successfully")
        return 0
    
    except KeyboardInterrupt:
        log.warning("Analysis interrupted by user")
        print("\n\n⚠️  Analysis interrupted by user (Ctrl+C)")
        return 130
    
    except ValueError as e:
        log.error(f"Invalid configuration: {str(e)}")
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        print("\nUse --help for usage information.", file=sys.stderr)
        return 1
    
    except ImportError as e:
        log.error(f"Import error: {str(e)}")
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        return 1
    
    except Exception as e:
        log.error(f"Analysis failed: {str(e)}", exc_info=True)
        print(f"\n❌ Analysis failed: {str(e)}", file=sys.stderr)
        print("\nCheck logs for detailed error information.", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
