"""
Shared fixtures for portfolio-related tests.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock

from paper_trading.portfolio_state import PortfolioState
from utils.constants import DEFAULT_INITIAL_CAPITAL, INITIAL_CAPITAL_PAPER


@pytest.fixture
def empty_portfolio():
    """Create an empty portfolio with default settings."""
    return PortfolioState(initial_capital=INITIAL_CAPITAL_PAPER)


@pytest.fixture
def portfolio_with_positions():
    """Create a portfolio with some open positions."""
    portfolio = PortfolioState(initial_capital=DEFAULT_INITIAL_CAPITAL)
    portfolio.open_position('THYAO', 100, 50.0, 0.7)
    portfolio.open_position('GARAN', 200, 45.0, 0.6)
    portfolio.open_position('ISCTR', 150, 30.0, 0.65)
    return portfolio


@pytest.fixture
def portfolio_at_max_positions():
    """Create a portfolio at maximum position limit."""
    portfolio = PortfolioState(
        initial_capital=DEFAULT_INITIAL_CAPITAL,
        max_positions=3
    )
    portfolio.open_position('THYAO', 100, 50.0, 0.7)
    portfolio.open_position('GARAN', 200, 45.0, 0.6)
    portfolio.open_position('ISCTR', 150, 30.0, 0.65)
    return portfolio


@pytest.fixture
def portfolio_config():
    """Standard portfolio configuration."""
    return {
        'initial_capital': DEFAULT_INITIAL_CAPITAL,
        'max_positions': 10,
        'max_single_exposure': 0.10,
        'max_total_exposure': 0.80
    }


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        'symbol': 'THYAO',
        'entry_price': 50.0,
        'exit_price': 55.0,
        'quantity': 100,
        'entry_date': datetime(2024, 1, 1),
        'exit_date': datetime(2024, 1, 10),
        'pnl': 500.0,
        'pnl_pct': 0.10,
        'confidence': 0.75
    }


@pytest.fixture
def mock_portfolio_state():
    """Mock portfolio state for testing."""
    mock = Mock(spec=PortfolioState)
    mock.cash = DEFAULT_INITIAL_CAPITAL
    mock.initial_capital = DEFAULT_INITIAL_CAPITAL
    mock.positions = {}
    mock.total_portfolio_value.return_value = DEFAULT_INITIAL_CAPITAL
    mock.current_weight.return_value = 0.0
    return mock
