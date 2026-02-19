"""Shared utility functions for analysis scripts.

This module contains common financial metrics and helper functions
used across multiple analysis scripts.
"""

import numpy as np
import pandas as pd


def calculate_max_drawdown(cumulative_returns):
    """Calculate maximum drawdown from cumulative returns.
    
    Args:
        cumulative_returns: Series of cumulative returns
        
    Returns:
        float: Maximum drawdown (negative value)
    """
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min()


def calculate_sharpe_ratio(returns):
    """Calculate annualized Sharpe ratio.
    
    Args:
        returns: Series of returns
        
    Returns:
        float: Annualized Sharpe ratio
    """
    if returns.std() == 0:
        return 0
    return np.sqrt(252) * returns.mean() / returns.std()
