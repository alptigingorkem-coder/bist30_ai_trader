"""
Unit tests for PortfolioValidator.

Tests the validation logic for portfolio operations.
"""

import pytest
from paper_trading.portfolio.portfolio_validator import PortfolioValidator


class TestCanOpenPosition:
    """Test cases for can_open_position validation."""
    
    def test_can_open_position_success(self):
        """Test successful position opening validation."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol="ASELS",
            size_pct=0.05,
            current_positions={},
            cash=100000,
            total_exposure=0,
            total_value=100000
        )
        
        # Assert
        assert can_open is True
        assert reason == "OK"
    
    def test_cannot_open_already_has_position(self):
        """Test validation when position already exists."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol="ASELS",
            size_pct=0.05,
            current_positions={"ASELS": {"quantity": 100}},
            cash=100000,
            total_exposure=0,
            total_value=100000
        )
        
        # Assert
        assert can_open is False
        assert reason == "ALREADY_HAS_POSITION"
    
    def test_cannot_open_max_positions_reached(self):
        """Test validation when max positions limit is reached."""
        # Setup
        validator = PortfolioValidator(max_positions=3)
        current_positions = {
            "ASELS": {"quantity": 100},
            "THYAO": {"quantity": 50},
            "GARAN": {"quantity": 75}
        }
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol="ISCTR",
            size_pct=0.05,
            current_positions=current_positions,
            cash=100000,
            total_exposure=15000,
            total_value=100000
        )
        
        # Assert
        assert can_open is False
        assert reason == "MAX_POSITIONS_REACHED"
    
    def test_cannot_open_exceeds_single_exposure(self):
        """Test validation when single position exposure limit is exceeded."""
        # Setup
        validator = PortfolioValidator(max_single_exposure=0.10)
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol="ASELS",
            size_pct=0.15,  # Exceeds 10% limit
            current_positions={},
            cash=100000,
            total_exposure=0,
            total_value=100000
        )
        
        # Assert
        assert can_open is False
        assert reason == "EXCEEDS_SINGLE_EXPOSURE"
    
    def test_cannot_open_exceeds_total_exposure(self):
        """Test validation when total exposure limit is exceeded."""
        # Setup
        validator = PortfolioValidator(max_total_exposure=0.80)
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol="ASELS",
            size_pct=0.10,
            current_positions={"THYAO": {}, "GARAN": {}},
            cash=25000,
            total_exposure=75000,  # Already at 75%
            total_value=100000
        )
        
        # Assert
        assert can_open is False
        assert reason == "EXCEEDS_TOTAL_EXPOSURE"
    
    def test_cannot_open_insufficient_cash(self):
        """Test validation when insufficient cash is available."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol="ASELS",
            size_pct=0.10,
            current_positions={},
            cash=5000,  # Only 5000 available
            total_exposure=0,
            total_value=100000  # But need 10000 (10% of 100000)
        )
        
        # Assert
        assert can_open is False
        assert reason == "INSUFFICIENT_CASH"
    
    def test_can_open_at_exact_limits(self):
        """Test validation at exact limit boundaries."""
        # Setup
        validator = PortfolioValidator(
            max_positions=5,
            max_single_exposure=0.10,
            max_total_exposure=0.80
        )
        
        # Test: At max positions - 1
        can_open, reason = validator.can_open_position(
            symbol="ASELS",
            size_pct=0.10,
            current_positions={f"STOCK{i}": {} for i in range(4)},
            cash=20000,
            total_exposure=70000,
            total_value=100000
        )
        
        # Assert
        assert can_open is True
        assert reason == "OK"


class TestCheckStressLimits:
    """Test cases for stress limit validation."""
    
    def test_stress_limits_ok(self):
        """Test stress limits when all is normal."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_trade, reason = validator.check_stress_limits(
            daily_pnl=500,  # Positive PnL
            consecutive_losses=0,
            initial_capital=100000
        )
        
        # Assert
        assert can_trade is True
        assert reason == "OK"
    
    def test_stress_limits_daily_max_loss(self):
        """Test stress limits when daily max loss is exceeded."""
        # Setup
        validator = PortfolioValidator(daily_max_loss_pct=0.03)
        
        # Test
        can_trade, reason = validator.check_stress_limits(
            daily_pnl=-3500,  # 3.5% loss
            consecutive_losses=0,
            initial_capital=100000
        )
        
        # Assert
        assert can_trade is False
        assert "DAILY_MAX_LOSS" in reason
        assert "3.5%" in reason
    
    def test_stress_limits_consecutive_losses(self):
        """Test stress limits when consecutive loss limit is reached."""
        # Setup
        validator = PortfolioValidator(consecutive_loss_limit=3)
        
        # Test
        can_trade, reason = validator.check_stress_limits(
            daily_pnl=-1000,
            consecutive_losses=3,  # At limit
            initial_capital=100000
        )
        
        # Assert
        assert can_trade is False
        assert "CONSECUTIVE_LOSSES" in reason
    
    def test_stress_limits_at_exact_threshold(self):
        """Test stress limits at exact threshold."""
        # Setup
        validator = PortfolioValidator(daily_max_loss_pct=0.03)
        
        # Test: Exactly at 3% loss
        can_trade, reason = validator.check_stress_limits(
            daily_pnl=-3000,  # Exactly 3%
            consecutive_losses=0,
            initial_capital=100000
        )
        
        # Assert
        assert can_trade is False  # At or above threshold
        assert "DAILY_MAX_LOSS" in reason
    
    def test_stress_limits_just_below_threshold(self):
        """Test stress limits just below threshold."""
        # Setup
        validator = PortfolioValidator(daily_max_loss_pct=0.03)
        
        # Test: Just below 3% loss
        can_trade, reason = validator.check_stress_limits(
            daily_pnl=-2999,  # Just below 3%
            consecutive_losses=0,
            initial_capital=100000
        )
        
        # Assert
        assert can_trade is True
        assert reason == "OK"


class TestValidateTradeSize:
    """Test cases for trade size validation."""
    
    def test_validate_trade_size_success(self):
        """Test successful trade size validation."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        is_valid, reason = validator.validate_trade_size(
            symbol="ASELS",
            quantity=100,
            price=45.50,
            cash=10000
        )
        
        # Assert
        assert is_valid is True
        assert reason == "OK"
    
    def test_validate_trade_size_invalid_quantity(self):
        """Test validation with invalid quantity."""
        # Setup
        validator = PortfolioValidator()
        
        # Test: Zero quantity
        is_valid, reason = validator.validate_trade_size(
            symbol="ASELS",
            quantity=0,
            price=45.50,
            cash=10000
        )
        
        # Assert
        assert is_valid is False
        assert reason == "INVALID_QUANTITY"
        
        # Test: Negative quantity
        is_valid, reason = validator.validate_trade_size(
            symbol="ASELS",
            quantity=-100,
            price=45.50,
            cash=10000
        )
        
        assert is_valid is False
        assert reason == "INVALID_QUANTITY"
    
    def test_validate_trade_size_invalid_price(self):
        """Test validation with invalid price."""
        # Setup
        validator = PortfolioValidator()
        
        # Test: Zero price
        is_valid, reason = validator.validate_trade_size(
            symbol="ASELS",
            quantity=100,
            price=0,
            cash=10000
        )
        
        # Assert
        assert is_valid is False
        assert reason == "INVALID_PRICE"
        
        # Test: Negative price
        is_valid, reason = validator.validate_trade_size(
            symbol="ASELS",
            quantity=100,
            price=-45.50,
            cash=10000
        )
        
        assert is_valid is False
        assert reason == "INVALID_PRICE"
    
    def test_validate_trade_size_insufficient_cash(self):
        """Test validation with insufficient cash."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        is_valid, reason = validator.validate_trade_size(
            symbol="ASELS",
            quantity=100,
            price=45.50,  # Needs 4550
            cash=4000  # Only have 4000
        )
        
        # Assert
        assert is_valid is False
        assert reason == "INSUFFICIENT_CASH"


class TestValidatePositionClose:
    """Test cases for position close validation."""
    
    def test_validate_position_close_success(self):
        """Test successful position close validation."""
        # Setup
        validator = PortfolioValidator()
        current_positions = {"ASELS": {"quantity": 100}}
        
        # Test
        can_close, reason = validator.validate_position_close(
            symbol="ASELS",
            current_positions=current_positions
        )
        
        # Assert
        assert can_close is True
        assert reason == "OK"
    
    def test_validate_position_close_no_position(self):
        """Test validation when trying to close non-existent position."""
        # Setup
        validator = PortfolioValidator()
        current_positions = {"THYAO": {"quantity": 50}}
        
        # Test
        can_close, reason = validator.validate_position_close(
            symbol="ASELS",  # Not in positions
            current_positions=current_positions
        )
        
        # Assert
        assert can_close is False
        assert reason == "NO_POSITION"


class TestValidatorConfiguration:
    """Test validator configuration and initialization."""
    
    def test_default_configuration(self):
        """Test validator with default configuration."""
        # Test
        validator = PortfolioValidator()
        
        # Assert
        assert validator.max_positions == 10
        assert validator.max_single_exposure == 0.10
        assert validator.max_total_exposure == 0.80
        assert validator.daily_max_loss_pct == 0.03
        assert validator.consecutive_loss_limit == 3
    
    def test_custom_configuration(self):
        """Test validator with custom configuration."""
        # Test
        validator = PortfolioValidator(
            max_positions=5,
            max_single_exposure=0.15,
            max_total_exposure=0.90,
            daily_max_loss_pct=0.05,
            consecutive_loss_limit=5
        )
        
        # Assert
        assert validator.max_positions == 5
        assert validator.max_single_exposure == 0.15
        assert validator.max_total_exposure == 0.90
        assert validator.daily_max_loss_pct == 0.05
        assert validator.consecutive_loss_limit == 5
