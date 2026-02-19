#!/bin/bash
# Feature Importance Analysis - Example Usage Scripts
# This file contains example commands for running feature importance analysis

# Example 1: Quick test with minimal data
echo "Example 1: Quick test with 2 tickers"
python scripts/analysis/run_feature_importance.py \
    --tickers THYAO,AKBNK \
    --sample-size 500 \
    --start-date 2024-01-01 \
    --output-dir reports/quick_test

# Example 2: Standard analysis with default settings
echo "Example 2: Standard analysis"
python scripts/analysis/run_feature_importance.py

# Example 3: Comprehensive analysis with custom threshold
echo "Example 3: Comprehensive analysis"
python scripts/analysis/run_feature_importance.py \
    --threshold 0.005 \
    --sample-size 2000 \
    --save-models

# Example 4: Specific date range analysis
echo "Example 4: Q1 2023 analysis"
python scripts/analysis/run_feature_importance.py \
    --start-date 2023-01-01 \
    --end-date 2023-03-31 \
    --output-dir reports/q1_2023

# Example 5: Debug mode for troubleshooting
echo "Example 5: Debug mode"
python scripts/analysis/run_feature_importance.py \
    --log-level DEBUG \
    --tickers THYAO \
    --sample-size 100

# Example 6: Quiet mode (only errors)
echo "Example 6: Quiet mode"
python scripts/analysis/run_feature_importance.py --quiet

# Example 7: Custom output directory
echo "Example 7: Custom output"
python scripts/analysis/run_feature_importance.py \
    --output-dir reports/my_custom_analysis \
    --threshold 0.002

# Example 8: Multiple tickers with custom parameters
echo "Example 8: Multiple tickers"
python scripts/analysis/run_feature_importance.py \
    --tickers THYAO,AKBNK,EREGL,GARAN,ISCTR \
    --sample-size 1500 \
    --threshold 0.0015 \
    --start-date 2023-06-01
