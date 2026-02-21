"""
Property-based tests for PortfolioState API Contract Preservation.

**Property 1: API Contract Preservation**
**Validates: Requirements 1.5**

For any public method that existed in the original PortfolioState,
calling that method with the same arguments on the refactored class
should produce the same result.
"""

import pytest
import tempfile
import os
from hypothesis import given, strategies as st, assume, settings
from paper_trading.portfolio_state import PortfolioState


class TestAPIContractPreservation:
    """
    Test that refactored PortfolioState maintains API compatibility.
    
    Since we've refactored PortfolioState to delegate to specialized components,
    we need to ensure all public methods still work correctly and maintain
    the same behavior.
    """
    
    @given(
        initial_capital=st.floats(min_value=1000, max_value=1000000),
        max_positions=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=50)
    def test_initialization_api_preserved(self, initial_capital, max_positions):
        """
        For any valid initialization parameters, PortfolioState should initialize correctly.
        
        **Validates: Requirements 1.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(
                initial_capital=initial_capital,
                max_positions=max_positions,
                state_file=state_file
            )
            
            # API contract: initialization should set these attributes
            assert portfolio.initial_capital == initial_capital
            assert portfolio.max_positions == max_positions
            assert portfolio.cash == initial_capital
            assert portfolio.position_count() == 0
            assert portfolio.total_portfolio_value() == initial_capital
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu',))),
        size_pct=st.floats(min_value=0.01, max_value=0.20)
    )
    @settings(max_examples=50)
    def test_can_open_position_api_preserved(self, symbol, size_pct):
        """
        For any symbol and size, can_open_new_position should return (bool, str).
        
        **Validates: Requirements 1.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(
                initial_capital=100000,
                max_positions=10,
                state_file=state_file
            )
            
            # API contract: should return tuple of (bool, str)
            result = portfolio.can_open_new_position(symbol, size_pct)
            
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], bool)
            assert isinstance(result[1], str)
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu',))),
        price=st.floats(min_value=1.0, max_value=1000.0),
        quantity=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=50)
    def test_open_position_api_preserved(self, symbol, price, quantity):
        """
        For any valid trade parameters, _open_position should return dict with success field.
        
        **Validates: Requirements 1.5**
        """
        # Ensure we have enough cash
        required_cash = price * quantity
        assume(required_cash < 50000)  # Half of initial capital
        
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(
                initial_capital=100000,
                max_positions=10,
                state_file=state_file
            )
            
            # API contract: should return dict with 'success' key
            result = portfolio._open_position(symbol, price, quantity, "LONG")
            
            assert isinstance(result, dict)
            assert "success" in result
            assert isinstance(result["success"], bool)
            
            if result["success"]:
                # If successful, position should exist
                assert portfolio.has_position(symbol)
                assert portfolio.positions[symbol]["quantity"] == quantity
                assert portfolio.positions[symbol]["entry_price"] == price
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu',))),
        entry_price=st.floats(min_value=10.0, max_value=100.0),
        exit_price=st.floats(min_value=10.0, max_value=100.0),
        quantity=st.integers(min_value=10, max_value=100)
    )
    @settings(max_examples=50)
    def test_close_position_api_preserved(self, symbol, entry_price, exit_price, quantity):
        """
        For any position, _close_position should return dict and update state correctly.
        
        **Validates: Requirements 1.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(
                initial_capital=100000,
                max_positions=10,
                state_file=state_file
            )
            
            # Open position first
            open_result = portfolio._open_position(symbol, entry_price, quantity, "LONG")
            assume(open_result["success"])
            
            # API contract: close should return dict with 'success' key
            close_result = portfolio._close_position(symbol, exit_price)
            
            assert isinstance(close_result, dict)
            assert "success" in close_result
            assert isinstance(close_result["success"], bool)
            
            if close_result["success"]:
                # Position should be removed
                assert not portfolio.has_position(symbol)
                # Closed trade should be recorded
                assert len(portfolio.closed_trades) == 1
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu',)))
    )
    @settings(max_examples=50)
    def test_has_position_api_preserved(self, symbol):
        """
        For any symbol, has_position should return bool.
        
        **Validates: Requirements 1.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(
                initial_capital=100000,
                state_file=state_file
            )
            
            # API contract: should return bool
            result = portfolio.has_position(symbol)
            assert isinstance(result, bool)
            assert result is False  # No positions initially
    
    @settings(max_examples=50)
    @given(st.data())
    def test_position_count_api_preserved(self, data):
        """
        For any number of positions, position_count should return correct integer.
        
        **Validates: Requirements 1.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(
                initial_capital=100000,
                max_positions=10,
                state_file=state_file
            )
            
            # API contract: should return int
            count = portfolio.position_count()
            assert isinstance(count, int)
            assert count == 0
            
            # Open some positions
            num_positions = data.draw(st.integers(min_value=1, max_value=5))
            for i in range(num_positions):
                symbol = f"SYM{i}"
                portfolio._open_position(symbol, 50.0, 10, "LONG")
            
            # Count should match
            count = portfolio.position_count()
            assert isinstance(count, int)
            assert count == num_positions
    
    @settings(max_examples=50)
    @given(st.data())
    def test_total_portfolio_value_api_preserved(self, data):
        """
        For any portfolio state, total_portfolio_value should return float >= 0.
        
        **Validates: Requirements 1.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            initial_capital = data.draw(st.floats(min_value=10000, max_value=1000000))
            
            portfolio = PortfolioState(
                initial_capital=initial_capital,
                state_file=state_file
            )
            
            # API contract: should return float
            value = portfolio.total_portfolio_value()
            assert isinstance(value, float)
            assert value >= 0
            assert value == initial_capital  # Initially equals capital
    
    @settings(max_examples=50)
    @given(st.data())
    def test_get_trade_statistics_api_preserved(self, data):
        """
        For any closed trades, get_trade_statistics should return dict with expected keys.
        
        **Validates: Requirements 1.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(
                initial_capital=100000,
                state_file=state_file
            )
            
            # Add some closed trades
            num_trades = data.draw(st.integers(min_value=0, max_value=10))
            for i in range(num_trades):
                pnl = data.draw(st.floats(min_value=-1000, max_value=1000))
                portfolio.closed_trades.append({
                    "symbol": f"SYM{i}",
                    "pnl": pnl,
                    "return_pct": pnl / 5000,
                    "entry_price": 50.0,
                    "exit_price": 50.0 + pnl / 100,
                    "quantity": 100,
                    "entry_time": "2026-02-22T10:00:00",
                    "exit_time": "2026-02-22T15:00:00",
                    "holding_minutes": 300
                })
            
            # API contract: should return dict with specific keys
            stats = portfolio.get_trade_statistics()
            
            assert isinstance(stats, dict)
            assert "total_trades" in stats
            
            # If there are trades, should have all keys
            if num_trades > 0:
                assert "winning_trades" in stats
                assert "losing_trades" in stats
                assert "win_rate" in stats
                assert "total_pnl" in stats
            else:
                # Empty trades should only have total_trades
                assert stats == {"total_trades": 0}
    
    @settings(max_examples=50)
    @given(st.data())
    def test_save_load_api_preserved(self, data):
        """
        For any portfolio state, save and load should preserve state.
        
        **Validates: Requirements 1.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            initial_capital = data.draw(st.floats(min_value=10000, max_value=1000000))
            
            # Create and modify portfolio
            portfolio1 = PortfolioState(
                initial_capital=initial_capital,
                state_file=state_file
            )
            
            # Open some positions
            num_positions = data.draw(st.integers(min_value=0, max_value=3))
            for i in range(num_positions):
                symbol = f"SYM{i}"
                price = data.draw(st.floats(min_value=10.0, max_value=100.0))
                quantity = data.draw(st.integers(min_value=1, max_value=50))
                portfolio1._open_position(symbol, price, quantity, "LONG")
            
            # Save
            portfolio1.save()
            
            # Load in new instance
            portfolio2 = PortfolioState.load(state_file)
            
            # API contract: state should be preserved
            assert portfolio2.position_count() == portfolio1.position_count()
            assert abs(portfolio2.cash - portfolio1.cash) < 0.01
            assert portfolio2.realized_pnl == portfolio1.realized_pnl
    
    @settings(max_examples=50)
    @given(
        daily_pnl=st.floats(min_value=-10000, max_value=10000),
        consecutive_losses=st.integers(min_value=0, max_value=10)
    )
    def test_check_stress_limits_api_preserved(self, daily_pnl, consecutive_losses):
        """
        For any stress state, check_stress_limits should return (bool, str).
        
        **Validates: Requirements 1.5**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(
                initial_capital=100000,
                daily_max_loss_pct=0.03,
                consecutive_loss_limit=3,
                state_file=state_file
            )
            
            # Set stress state
            portfolio.daily_pnl = daily_pnl
            portfolio.consecutive_losses = consecutive_losses
            
            # API contract: should return tuple of (bool, str)
            result = portfolio.check_stress_limits()
            
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], bool)
            assert isinstance(result[1], str)
