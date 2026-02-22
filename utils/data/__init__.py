"""
Data utilities package.

This package contains specialized components for data handling:
- DataRepository: Data fetching from multiple sources
- DataCache: Caching layer for data
- DataValidator: Data quality validation
- DataTransformer: Data transformation and feature engineering
"""

from utils.data.data_repository import DataRepository

__all__ = ['DataRepository']
