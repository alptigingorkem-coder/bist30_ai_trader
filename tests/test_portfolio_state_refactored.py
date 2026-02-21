"""
Integration tests for refactored PortfolioState.

Tests that the refactored PortfolioState maintains backward compatibility
and correctly delegates to specialized components.
"""

import pytest
import os
import tempfile
from paper_trading.portfolio_state import PortfolioState


class TestPortfolioStateRefactored:
    """Test refactored PortfolioState integration."""
    
    def test_initialization(self):
        """Test PortfolioState initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(
                initial_capital=100000,
                max_positions=10,
                state_file=state_file
            )
            
            assert portfolio.cash == 100000
            assert portfolio.initial_capital == 100000
            assert portfolio.position_count() == 0
            assert portfolio.total_portfolio_value() == 100000
    
    def test_open_and_close_position(self):
        """Test opening and closing a position."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(initial_capital=100000, state_file=state_file)
            
            # Open position
            decision = {
                "action": "OPEN_POSITION",
                "symbol": "ASELS",
                "price": 45.50,
                "quantity": 100,
                "side": "LONG"
            }
            
            result = portfolio.apply_trade_decision(decision)
            
            assert result["success"] is True
            assert portfolio.has_position("ASELS")
            assert portfolio.position_count() == 1
            assert portfolio.cash == 100000 - (45.50 * 100)
            
            # Close position
            decision2 = {
                "action": "CLOSE_POSITION",
                "symbol": "ASELS",
                "price": 50.0
            }
            
            result2 = portfolio.apply_trade_decision(decision2)
            
            assert result2["success"] is True
            assert not portfolio.has_position("ASELS")
            assert portfolio.position_count() == 0
            assert len(portfolio.closed_trades) == 1
    
    def test_validation_delegates_correctly(self):
        """Test that validation delegates to PortfolioValidator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(
                initial_capital=10000,
                max_positions=2,
                state_file=state_file
            )
            
            # Should be able to open first position (5% of capital = 500)
            can_open, reason = portfolio.can_open_new_position("ASELS", 0.05)
            assert can_open is True
            
            # Open first position: 10 shares @ 45.0 = 450 (4.5% of capital, within 10% limit)
            result = portfolio._open_position("ASELS", 45.0, 10, "LONG")
            assert result["success"] is True
            
            # Should not be able to open same symbol again
            can_open, reason = portfolio.can_open_new_position("ASELS", 0.05)
            assert can_open is False
            assert reason == "ALREADY_HAS_POSITION"
    
    def test_trade_statistics_delegates_correctly(self):
        """Test that statistics delegate to PortfolioMetrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(initial_capital=100000, state_file=state_file)
            
            # Add some closed trades
            portfolio.closed_trades = [
                {
                    "symbol": "ASELS",
                    "pnl": 500.0,
                    "return_pct": 0.10,
                    "entry_price": 40.0,
                    "exit_price": 45.0,
                    "quantity": 100,
                    "entry_time": "2026-02-22T10:00:00",
                    "exit_time": "2026-02-22T15:00:00",
                    "holding_minutes": 300
                }
            ]
            
            stats = portfolio.get_trade_statistics()
            
            assert stats["total_trades"] == 1
            assert stats["winning_trades"] == 1
            assert stats["win_rate"] == 100.0
    
    def test_formatting_delegates_correctly(self):
        """Test that formatting delegates to PortfolioFormatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(initial_capital=100000, state_file=state_file)
            
            # Add closed trade
            portfolio.closed_trades = [
                {
                    "symbol": "ASELS",
                    "pnl": 500.0,
                    "return_pct": 0.10,
                    "entry_price": 40.0,
                    "exit_price": 45.0,
                    "quantity": 100,
                    "entry_time": "2026-02-22T10:00:00",
                    "exit_time": "2026-02-22T15:00:00",
                    "holding_minutes": 300
                }
            ]
            
            ledger = portfolio.get_trade_ledger()
            
            assert len(ledger) == 1
            assert ledger[0]["symbol"] == "ASELS"
            assert "trade_id" in ledger[0]
            assert "commission" in ledger[0]
    
    def test_persistence_delegates_correctly(self):
        """Test that persistence delegates to PortfolioRepository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            # Create and save state
            portfolio1 = PortfolioState(initial_capital=100000, state_file=state_file)
            portfolio1._open_position("ASELS", 45.0, 100, "LONG")
            portfolio1._save_state()
            
            # Load state in new instance
            portfolio2 = PortfolioState(initial_capital=100000, state_file=state_file)
            
            assert portfolio2.has_position("ASELS")
            assert portfolio2.positions["ASELS"]["quantity"] == 100
    
    def test_stress_controls_work(self):
        """Test that stress controls work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(
                initial_capital=100000,
                daily_max_loss_pct=0.03,
                consecutive_loss_limit=3,
                state_file=state_file
            )
            
            # Simulate losses
            portfolio.daily_pnl = -3500  # More than 3% loss
            
            can_trade, reason = portfolio.check_stress_limits()
            
            assert can_trade is False
            assert "DAILY_MAX_LOSS" in reason
    
    def test_backward_compatibility_methods(self):
        """Test backward compatibility helper methods."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            portfolio = PortfolioState(initial_capital=100000, state_file=state_file)
            
            # Test helper methods
            portfolio.open_or_add("ASELS", 100, 45.0)
            assert portfolio.has_position("ASELS")
            
            symbols = portfolio.get_open_symbols()
            assert "ASELS" in symbols
            
            price = portfolio.get_last_price("ASELS")
            assert price == 45.0
            
            weight = portfolio.current_weight("ASELS")
            assert weight > 0
            
            # Test reduce and close
            portfolio.reduce_position("ASELS", 0.5, 50.0)
            assert portfolio.positions["ASELS"]["quantity"] == 50
            
            portfolio.close_position("ASELS", 50.0)
            assert not portfolio.has_position("ASELS")
    
    def test_classmethod_load(self):
        """Test classmethod load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            # Create and save
            portfolio1 = PortfolioState(initial_capital=100000, state_file=state_file)
            portfolio1._open_position("ASELS", 45.0, 100, "LONG")
            portfolio1.save()
            
            # Load using classmethod
            portfolio2 = PortfolioState.load(state_file)
            
            assert portfolio2.has_position("ASELS")
