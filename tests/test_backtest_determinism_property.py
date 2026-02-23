"""
Property-based tests for backtest determinism.

Feature: code-quality-refactoring, Property 2: Backtest Determinism
Validates: Requirements 6.4

For any backtest configuration, results should be identical before and after refactoring.
"""

import pytest
import numpy as np
import pandas as pd
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta

from core.backtest.backtest_strategy import BacktestStrategy, BacktestConfig


# ─────────────────────────────────────────────────────────────
# HYPOTHESIS STRATEGIES
# ─────────────────────────────────────────────────────────────

@st.composite
def market_data_strategy(draw):
    """Generate realistic market data for testing."""
    length = draw(st.integers(min_value=50, max_value=200))
    start_date = datetime(2023, 1, 1)
    dates = pd.date_range(start=start_date, periods=length, freq='D')
    
    # Generate price data with realistic constraints
    base_price = draw(st.floats(min_value=50, max_value=200))
    returns = draw(st.lists(
        st.floats(min_value=-0.05, max_value=0.05),
        min_size=length,
        max_size=length
    ))
    
    prices = [base_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    data = pd.DataFrame({
        'Open': [p * draw(st.floats(min_value=0.98, max_value=1.02)) for p in prices],
        'High': [p * draw(st.floats(min_value=1.0, max_value=1.05)) for p in prices],
        'Low': [p * draw(st.floats(min_value=0.95, max_value=1.0)) for p in prices],
        'Close': prices,
        'Volume': draw(st.lists(
            st.floats(min_value=100000, max_value=10000000),
            min_size=length,
            max_size=length
        )),
        'ATR': draw(st.lists(
            st.floats(min_value=0.5, max_value=5.0),
            min_size=length,
            max_size=length
        ))
    }, index=dates)
    
    # Ensure High >= Close >= Low
    data['High'] = data[['High', 'Close']].max(axis=1)
    data['Low'] = data[['Low', 'Close']].min(axis=1)
    
    return data


@st.composite
def backtest_config_strategy(draw):
    """Generate random but valid backtest configurations."""
    return BacktestConfig(
        initial_capital=draw(st.floats(min_value=10000, max_value=1000000)),
        commission=draw(st.floats(min_value=0.0001, max_value=0.01)),
        max_drawdown_limit=draw(st.floats(min_value=0.1, max_value=0.5)),
        enable_risk_sizing=draw(st.booleans()),
        enable_kelly=draw(st.booleans()),
        risk_per_trade=draw(st.floats(min_value=0.01, max_value=0.05)),
        max_single_pos_weight=draw(st.floats(min_value=0.1, max_value=0.5)),
        min_holding_days=draw(st.integers(min_value=0, max_value=5))
    )



# ─────────────────────────────────────────────────────────────
# PROPERTY TESTS
# ─────────────────────────────────────────────────────────────

# Feature: code-quality-refactoring, Property 2: Backtest Determinism
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
)
@given(
    data=market_data_strategy(),
    config=backtest_config_strategy()
)
def test_backtest_determinism_same_config(data, config):
    """
    Property 2: Backtest Determinism
    
    For any backtest configuration and data, running the backtest multiple times
    with the same inputs should produce identical results.
    
    This validates that the backtest is deterministic and has no hidden state
    or randomness that could cause different results.
    """
    strategy = BacktestStrategy(config)
    
    # Run backtest twice with same inputs
    result1 = strategy.run(
        data=data.copy(),
        signals_or_weights=None,
        risk_manager=None,
        regime_detector=None,
        position_sizer=None,
        execution_manager=None,
        router=None
    )
    
    result2 = strategy.run(
        data=data.copy(),
        signals_or_weights=None,
        risk_manager=None,
        regime_detector=None,
        position_sizer=None,
        execution_manager=None,
        router=None
    )
    
    # Results should be identical
    assert len(result1) == len(result2), "Result lengths should match"
    
    # Check equity curves are identical
    pd.testing.assert_series_equal(
        result1['Equity'],
        result2['Equity'],
        check_names=False,
        rtol=1e-10
    )
    
    # Check positions are identical
    pd.testing.assert_series_equal(
        result1['Position'],
        result2['Position'],
        check_names=False
    )
    
    # Check trades are identical
    pd.testing.assert_series_equal(
        result1['Trades'],
        result2['Trades'],
        check_names=False
    )


# Feature: code-quality-refactoring, Property 2: Backtest Determinism
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
)
@given(
    data=market_data_strategy(),
    config=backtest_config_strategy()
)
def test_backtest_determinism_with_signals(data, config):
    """
    Property 2: Backtest Determinism (with signals)
    
    For any backtest configuration, data, and signals, running the backtest
    multiple times should produce identical results.
    """
    strategy = BacktestStrategy(config)
    
    # Generate random binary signals
    signals = pd.Series(
        np.random.choice([0, 1], size=len(data)),
        index=data.index
    )
    
    # Run backtest twice with same inputs
    result1 = strategy.run(
        data=data.copy(),
        signals_or_weights=signals.copy(),
        risk_manager=None,
        regime_detector=None,
        position_sizer=None,
        execution_manager=None,
        router=None
    )
    
    result2 = strategy.run(
        data=data.copy(),
        signals_or_weights=signals.copy(),
        risk_manager=None,
        regime_detector=None,
        position_sizer=None,
        execution_manager=None,
        router=None
    )
    
    # Results should be identical
    pd.testing.assert_series_equal(
        result1['Equity'],
        result2['Equity'],
        check_names=False,
        rtol=1e-10
    )
    
    pd.testing.assert_series_equal(
        result1['Position'],
        result2['Position'],
        check_names=False
    )



# Feature: code-quality-refactoring, Property 2: Backtest Determinism
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
)
@given(
    data=market_data_strategy(),
    config=backtest_config_strategy()
)
def test_backtest_final_equity_determinism(data, config):
    """
    Property 2: Backtest Determinism (final equity)
    
    The final equity value should be identical across multiple runs
    with the same configuration.
    """
    strategy = BacktestStrategy(config)
    
    # Generate weighted signals
    signals = pd.Series(
        np.random.uniform(0, 1, size=len(data)),
        index=data.index
    )
    
    final_equities = []
    
    # Run backtest 3 times
    for _ in range(3):
        result = strategy.run(
            data=data.copy(),
            signals_or_weights=signals.copy(),
            risk_manager=None,
            regime_detector=None,
            position_sizer=None,
            execution_manager=None,
            router=None
        )
        final_equities.append(result['Equity'].iloc[-1])
    
    # All final equities should be identical
    assert len(set(final_equities)) == 1, \
        f"Final equities should be identical but got: {final_equities}"


# Feature: code-quality-refactoring, Property 2: Backtest Determinism
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
)
@given(
    data=market_data_strategy(),
    config=backtest_config_strategy()
)
def test_backtest_trade_count_determinism(data, config):
    """
    Property 2: Backtest Determinism (trade count)
    
    The number of trades executed should be identical across multiple runs.
    """
    strategy = BacktestStrategy(config)
    
    # Generate binary signals
    signals = pd.Series(
        np.random.choice([0, 1], size=len(data)),
        index=data.index
    )
    
    trade_counts = []
    
    # Run backtest 3 times
    for _ in range(3):
        result = strategy.run(
            data=data.copy(),
            signals_or_weights=signals.copy(),
            risk_manager=None,
            regime_detector=None,
            position_sizer=None,
            execution_manager=None,
            router=None
        )
        trade_counts.append(result['Trades'].sum())
    
    # All trade counts should be identical
    assert len(set(trade_counts)) == 1, \
        f"Trade counts should be identical but got: {trade_counts}"


# Feature: code-quality-refactoring, Property 2: Backtest Determinism
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large]
)
@given(
    data=market_data_strategy(),
    config=backtest_config_strategy()
)
def test_backtest_cumulative_return_determinism(data, config):
    """
    Property 2: Backtest Determinism (cumulative returns)
    
    The cumulative return curve should be identical across multiple runs.
    """
    strategy = BacktestStrategy(config)
    
    # Generate weighted signals
    signals = pd.Series(
        np.random.uniform(0, 1, size=len(data)),
        index=data.index
    )
    
    # Run backtest twice
    result1 = strategy.run(
        data=data.copy(),
        signals_or_weights=signals.copy(),
        risk_manager=None,
        regime_detector=None,
        position_sizer=None,
        execution_manager=None,
        router=None
    )
    
    result2 = strategy.run(
        data=data.copy(),
        signals_or_weights=signals.copy(),
        risk_manager=None,
        regime_detector=None,
        position_sizer=None,
        execution_manager=None,
        router=None
    )
    
    # Cumulative returns should be identical
    pd.testing.assert_series_equal(
        result1['Cumulative_Strategy_Return'],
        result2['Cumulative_Strategy_Return'],
        check_names=False,
        rtol=1e-10
    )
