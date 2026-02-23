"""
Shared fixtures for strategy health tests.
"""

import pytest
from datetime import datetime, timedelta


@pytest.fixture
def healthy_portfolio_stats():
    """Statistics for a healthy portfolio."""
    return {
        'win_rate': 60.0,
        'profit_factor': 2.5,
        'sharpe_ratio': 1.2,
        'total_trades': 50,
        'winning_trades': 30,
        'losing_trades': 20,
        'avg_win': 500.0,
        'avg_loss': -200.0,
        'max_drawdown': -0.15,
        'total_pnl': 10000.0
    }


@pytest.fixture
def unhealthy_portfolio_stats():
    """Statistics for an unhealthy portfolio."""
    return {
        'win_rate': 35.0,
        'profit_factor': 0.8,
        'sharpe_ratio': 0.2,
        'total_trades': 50,
        'winning_trades': 17,
        'losing_trades': 33,
        'avg_win': 300.0,
        'avg_loss': -400.0,
        'max_drawdown': -0.35,
        'total_pnl': -5000.0
    }


@pytest.fixture
def sample_trade_history():
    """Sample trade history for health calculations."""
    base_date = datetime(2024, 1, 1)
    trades = []
    
    for i in range(20):
        trade = {
            'symbol': f'STOCK{i % 5}',
            'entry_date': base_date + timedelta(days=i*2),
            'exit_date': base_date + timedelta(days=i*2 + 1),
            'pnl': 100 if i % 3 == 0 else -50,  # 33% win rate
            'confidence': 0.6 + (i % 5) * 0.05
        }
        trades.append(trade)
    
    return trades


@pytest.fixture
def health_thresholds():
    """Standard health thresholds."""
    return {
        'min_win_rate': 0.45,
        'min_profit_factor': 1.2,
        'min_sharpe_ratio': 0.5,
        'max_drawdown': 0.30,
        'min_trades': 10
    }
