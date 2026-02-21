"""
Unit tests for PortfolioService.

Tests the business logic for portfolio trade execution.
"""

import pytest
from datetime import datetime
from paper_trading.portfolio.portfolio_service import PortfolioService
from paper_trading.portfolio.portfolio_validator import PortfolioValidator


class MockPortfolioState:
    """Mock PortfolioState for testing PortfolioService."""
    
    def __init__(self, initial_capital=100000):
        self.cash = initial_capital
        self.initial_capital = initial_capital
        self.positions = {}
        self.closed_trades = []
        self.trade_history = []
        self.realized_pnl = 0.0
        self.max_positions = 10
        self.max_single_exposure = 0.10
        self.max_total_exposure = 0.80
    
    def total_portfolio_value(self):
        """Calculate total portfolio value."""
        position_value = sum(
            pos["quantity"] * pos["current_price"]
            for pos in self.positions.values()
        )
        return self.cash + position_value
    
    def current_total_exposure(self):
        """Calculate current total exposure."""
        return sum(
            pos["quantity"] * pos["current_price"]
            for pos in self.positions.values()
        )


class TestOpenPosition:
    """Test cases for opening positions."""
    
    def test_open_position_success(self):
        """Test successfully opening a position."""
        # Setup
        state = MockPortfolioState()
        service = PortfolioService(state)
        
        # Test
        result = service.open_position(
            symbol="ASELS",
            price=45.50,
            quantity=100,
            side="LONG"
        )
        
        # Assert
        assert result["success"] is True
        assert "ASELS" in state.positions
        assert state.positions["ASELS"]["quantity"] == 100
        assert state.positions["ASELS"]["entry_price"] == 45.50
        assert state.positions["ASELS"]["side"] == "LONG"
        assert state.cash == 100000 - (45.50 * 100)
    
    def test_open_position_with_confidence_and_regime(self):
        """Test opening position with confidence and regime data."""
        # Setup
        state = MockPortfolioState()
        service = PortfolioService(state)
        
        # Test
        result = service.open_position(
            symbol="ASELS",
            price=45.50,
            quantity=100,
            side="LONG",
            confidence=0.85,
            regime="BULL"
        )
        
        # Assert
        assert result["success"] is True
        assert state.positions["ASELS"]["entry_confidence"] == 0.85
        assert state.positions["ASELS"]["entry_regime"] == "BULL"
    
    def test_open_position_insufficient_cash(self):
        """Test opening position with insufficient cash."""
        # Setup
        state = MockPortfolioState(initial_capital=1000)
        service = PortfolioService(state)
        
        # Test
        result = service.open_position(
            symbol="ASELS",
            price=45.50,
            quantity=100,  # Needs 4550
            side="LONG"
        )
        
        # Assert
        assert result["success"] is False
        assert result["reason"] == "INSUFFICIENT_CASH"
        assert "ASELS" not in state.positions
    
    def test_open_position_already_exists(self):
        """Test opening position when it already exists."""
        # Setup
        state = MockPortfolioState()
        state.positions["ASELS"] = {"quantity": 50, "entry_price": 40.0, "current_price": 45.0}
        service = PortfolioService(state)
        
        # Test
        result = service.open_position(
            symbol="ASELS",
            price=45.50,
            quantity=100,
            side="LONG"
        )
        
        # Assert
        assert result["success"] is False
        assert result["reason"] == "ALREADY_HAS_POSITION"


class TestClosePosition:
    """Test cases for closing positions."""
    
    def test_close_position_with_profit(self):
        """Test closing a position with profit."""
        # Setup
        state = MockPortfolioState()
        state.positions["ASELS"] = {
            "side": "LONG",
            "entry_price": 40.0,
            "quantity": 100,
            "entry_time": datetime.now().isoformat(),
            "current_price": 45.0
        }
        state.cash = 96000  # After buying
        
        service = PortfolioService(state)
        
        # Test
        result = service.close_position(symbol="ASELS", price=45.0)
        
        # Assert
        assert result["success"] is True
        assert result["realized_pnl"] == 500.0  # (45-40) * 100
        assert "ASELS" not in state.positions
        assert state.cash == 96000 + (45.0 * 100)
        assert state.realized_pnl == 500.0
        assert len(state.closed_trades) == 1
    
    def test_close_position_with_loss(self):
        """Test closing a position with loss."""
        # Setup
        state = MockPortfolioState()
        state.positions["ASELS"] = {
            "side": "LONG",
            "entry_price": 50.0,
            "quantity": 100,
            "entry_time": datetime.now().isoformat(),
            "current_price": 45.0
        }
        state.cash = 95000
        
        service = PortfolioService(state)
        
        # Test
        result = service.close_position(symbol="ASELS", price=45.0)
        
        # Assert
        assert result["success"] is True
        assert result["realized_pnl"] == -500.0  # (45-50) * 100
        assert state.realized_pnl == -500.0
    
    def test_close_position_short(self):
        """Test closing a short position."""
        # Setup
        state = MockPortfolioState()
        state.positions["ASELS"] = {
            "side": "SHORT",
            "entry_price": 50.0,
            "quantity": 100,
            "entry_time": datetime.now().isoformat(),
            "current_price": 45.0
        }
        state.cash = 105000
        
        service = PortfolioService(state)
        
        # Test
        result = service.close_position(symbol="ASELS", price=45.0)
        
        # Assert
        assert result["success"] is True
        assert result["realized_pnl"] == 500.0  # (50-45) * 100 for SHORT
    
    def test_close_position_not_exists(self):
        """Test closing a position that doesn't exist."""
        # Setup
        state = MockPortfolioState()
        service = PortfolioService(state)
        
        # Test
        result = service.close_position(symbol="ASELS", price=45.0)
        
        # Assert
        assert result["success"] is False
        assert result["reason"] == "NO_POSITION"


class TestScaleIn:
    """Test cases for scaling in positions."""
    
    def test_scale_in_success(self):
        """Test successfully scaling into a position."""
        # Setup
        state = MockPortfolioState()
        state.positions["ASELS"] = {
            "side": "LONG",
            "entry_price": 40.0,
            "quantity": 100,
            "entry_time": datetime.now().isoformat(),
            "current_price": 45.0
        }
        state.cash = 96000
        
        service = PortfolioService(state)
        
        # Test: Add 50 more shares at 45.0
        result = service.scale_in(symbol="ASELS", price=45.0, quantity=50)
        
        # Assert
        assert result["success"] is True
        assert state.positions["ASELS"]["quantity"] == 150
        # Average price: (40*100 + 45*50) / 150 = 41.67
        assert abs(state.positions["ASELS"]["entry_price"] - 41.67) < 0.01
        assert state.cash == 96000 - (45.0 * 50)
    
    def test_scale_in_no_position(self):
        """Test scaling in when no position exists."""
        # Setup
        state = MockPortfolioState()
        service = PortfolioService(state)
        
        # Test
        result = service.scale_in(symbol="ASELS", price=45.0, quantity=50)
        
        # Assert
        assert result["success"] is False
        assert result["reason"] == "NO_POSITION"
    
    def test_scale_in_insufficient_cash(self):
        """Test scaling in with insufficient cash."""
        # Setup
        state = MockPortfolioState()
        state.positions["ASELS"] = {
            "side": "LONG",
            "entry_price": 40.0,
            "quantity": 100,
            "entry_time": datetime.now().isoformat(),
            "current_price": 45.0
        }
        state.cash = 1000  # Not enough
        
        service = PortfolioService(state)
        
        # Test
        result = service.scale_in(symbol="ASELS", price=45.0, quantity=100)
        
        # Assert
        assert result["success"] is False
        assert result["reason"] == "INSUFFICIENT_CASH"


class TestScaleOut:
    """Test cases for scaling out positions."""
    
    def test_scale_out_partial(self):
        """Test partially scaling out of a position."""
        # Setup
        state = MockPortfolioState()
        state.positions["ASELS"] = {
            "side": "LONG",
            "entry_price": 40.0,
            "quantity": 100,
            "entry_time": datetime.now().isoformat(),
            "current_price": 45.0
        }
        state.cash = 96000
        
        service = PortfolioService(state)
        
        # Test: Scale out 50%
        result = service.scale_out(symbol="ASELS", price=45.0, pct=0.5)
        
        # Assert
        assert result["success"] is True
        assert result["realized_pnl"] == 250.0  # (45-40) * 50
        assert state.positions["ASELS"]["quantity"] == 50
        assert state.cash == 96000 + (45.0 * 50)
        assert state.realized_pnl == 250.0
    
    def test_scale_out_full(self):
        """Test fully scaling out (100%)."""
        # Setup
        state = MockPortfolioState()
        state.positions["ASELS"] = {
            "side": "LONG",
            "entry_price": 40.0,
            "quantity": 100,
            "entry_time": datetime.now().isoformat(),
            "current_price": 45.0
        }
        state.cash = 96000
        
        service = PortfolioService(state)
        
        # Test: Scale out 100%
        result = service.scale_out(symbol="ASELS", price=45.0, pct=1.0)
        
        # Assert
        assert result["success"] is True
        assert result["realized_pnl"] == 500.0
        assert "ASELS" not in state.positions  # Position removed
    
    def test_scale_out_no_position(self):
        """Test scaling out when no position exists."""
        # Setup
        state = MockPortfolioState()
        service = PortfolioService(state)
        
        # Test
        result = service.scale_out(symbol="ASELS", price=45.0, pct=0.5)
        
        # Assert
        assert result["success"] is False
        assert result["reason"] == "NO_POSITION"
    
    def test_scale_out_invalid_percentage(self):
        """Test scaling out with invalid percentage."""
        # Setup
        state = MockPortfolioState()
        state.positions["ASELS"] = {
            "side": "LONG",
            "entry_price": 40.0,
            "quantity": 100,
            "entry_time": datetime.now().isoformat(),
            "current_price": 45.0
        }
        
        service = PortfolioService(state)
        
        # Test: Invalid percentages
        result1 = service.scale_out(symbol="ASELS", price=45.0, pct=0)
        result2 = service.scale_out(symbol="ASELS", price=45.0, pct=1.5)
        
        # Assert
        assert result1["success"] is False
        assert result1["reason"] == "INVALID_PERCENTAGE"
        assert result2["success"] is False
        assert result2["reason"] == "INVALID_PERCENTAGE"


class TestApplyTradeDecision:
    """Test cases for applying trade decisions."""
    
    def test_apply_open_position_decision(self):
        """Test applying an OPEN_POSITION decision."""
        # Setup
        state = MockPortfolioState()
        service = PortfolioService(state)
        
        decision = {
            "action": "OPEN_POSITION",
            "symbol": "ASELS",
            "price": 45.50,
            "quantity": 100,
            "side": "LONG",
            "confidence": 0.85,
            "regime": "BULL"
        }
        
        # Test
        result = service.apply_trade_decision(decision)
        
        # Assert
        assert result["success"] is True
        assert result["action"] == "OPEN_POSITION"
        assert result["symbol"] == "ASELS"
        assert len(state.trade_history) == 1
    
    def test_apply_close_position_decision(self):
        """Test applying a CLOSE_POSITION decision."""
        # Setup
        state = MockPortfolioState()
        state.positions["ASELS"] = {
            "side": "LONG",
            "entry_price": 40.0,
            "quantity": 100,
            "entry_time": datetime.now().isoformat(),
            "current_price": 45.0
        }
        
        service = PortfolioService(state)
        
        decision = {
            "action": "CLOSE_POSITION",
            "symbol": "ASELS",
            "price": 45.0
        }
        
        # Test
        result = service.apply_trade_decision(decision)
        
        # Assert
        assert result["success"] is True
        assert result["realized_pnl"] == 500.0
        assert len(state.trade_history) == 1
    
    def test_apply_hold_decision(self):
        """Test applying a HOLD_EXISTING decision."""
        # Setup
        state = MockPortfolioState()
        service = PortfolioService(state)
        
        decision = {
            "action": "HOLD_EXISTING",
            "symbol": "ASELS"
        }
        
        # Test
        result = service.apply_trade_decision(decision)
        
        # Assert
        assert result["success"] is True
        assert len(state.trade_history) == 0  # HOLD doesn't add to history
    
    def test_apply_unknown_action(self):
        """Test applying an unknown action."""
        # Setup
        state = MockPortfolioState()
        service = PortfolioService(state)
        
        decision = {
            "action": "UNKNOWN_ACTION",
            "symbol": "ASELS"
        }
        
        # Test
        result = service.apply_trade_decision(decision)
        
        # Assert
        assert result["success"] is False
        assert "UNKNOWN_ACTION" in result["reason"]


class TestServiceIntegration:
    """Integration tests for PortfolioService."""
    
    def test_complete_trade_cycle(self):
        """Test a complete trade cycle: open -> scale in -> scale out -> close."""
        # Setup
        state = MockPortfolioState()
        service = PortfolioService(state)
        
        # Open position
        result1 = service.open_position("ASELS", 40.0, 100, "LONG")
        assert result1["success"] is True
        assert state.cash == 96000
        
        # Scale in
        result2 = service.scale_in("ASELS", 45.0, 50)
        assert result2["success"] is True
        assert state.positions["ASELS"]["quantity"] == 150
        
        # Scale out 50%
        result3 = service.scale_out("ASELS", 50.0, 0.5)
        assert result3["success"] is True
        assert state.positions["ASELS"]["quantity"] == 75
        
        # Close remaining
        result4 = service.close_position("ASELS", 50.0)
        assert result4["success"] is True
        assert "ASELS" not in state.positions
        assert len(state.closed_trades) == 1
