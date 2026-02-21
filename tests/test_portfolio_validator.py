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



class TestValidatorEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_can_open_with_zero_cash(self):
        """Test validation with zero cash available."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol="ASELS",
            size_pct=0.05,
            current_positions={},
            cash=0,  # No cash
            total_exposure=0,
            total_value=100000
        )
        
        # Assert
        assert can_open is False
        assert reason == "INSUFFICIENT_CASH"
    
    def test_can_open_with_zero_total_value(self):
        """Test validation with zero total portfolio value."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol="ASELS",
            size_pct=0.05,
            current_positions={},
            cash=0,
            total_exposure=0,
            total_value=0  # Zero value portfolio
        )
        
        # Assert
        # With zero total value, required_cash = 0 * 0.05 = 0, so cash check passes
        # But this is an edge case - in reality, zero value portfolio shouldn't trade
        assert can_open is True  # Technically passes all checks
        assert reason == "OK"
    
    def test_can_open_with_very_small_position(self):
        """Test validation with very small position size."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol="ASELS",
            size_pct=0.0001,  # 0.01% position
            current_positions={},
            cash=100000,
            total_exposure=0,
            total_value=100000
        )
        
        # Assert
        assert can_open is True
        assert reason == "OK"
    
    def test_stress_limits_with_zero_capital(self):
        """Test stress limits with zero initial capital."""
        # Setup
        validator = PortfolioValidator()
        
        # Test - should handle division by zero
        can_trade, reason = validator.check_stress_limits(
            daily_pnl=-1000,
            consecutive_losses=0,
            initial_capital=0  # Zero capital
        )
        
        # Assert - should return False with INVALID_CAPITAL
        assert can_trade is False
        assert reason == "INVALID_CAPITAL"
    
    def test_stress_limits_with_positive_pnl(self):
        """Test stress limits with positive PnL (winning day)."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_trade, reason = validator.check_stress_limits(
            daily_pnl=5000,  # Positive PnL
            consecutive_losses=2,  # Has some losses but not at limit
            initial_capital=100000
        )
        
        # Assert
        assert can_trade is True
        assert reason == "OK"
    
    def test_validate_trade_size_with_exact_cash(self):
        """Test trade size validation with exact cash amount."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        is_valid, reason = validator.validate_trade_size(
            symbol="ASELS",
            quantity=100,
            price=45.50,
            cash=4550  # Exactly enough
        )
        
        # Assert
        assert is_valid is True
        assert reason == "OK"
    
    def test_validate_trade_size_with_fractional_shares(self):
        """Test trade size validation with fractional shares."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        is_valid, reason = validator.validate_trade_size(
            symbol="ASELS",
            quantity=100.5,  # Fractional shares
            price=45.50,
            cash=10000
        )
        
        # Assert
        assert is_valid is True
        assert reason == "OK"


class TestValidatorIntegration:
    """Integration tests combining multiple validation checks."""
    
    def test_full_position_opening_workflow(self):
        """Test complete workflow of opening multiple positions."""
        # Setup
        validator = PortfolioValidator(
            max_positions=3,
            max_single_exposure=0.15,
            max_total_exposure=0.80
        )
        
        cash = 100000
        total_value = 100000
        positions = {}
        total_exposure = 0
        
        # Open first position
        can_open, reason = validator.can_open_position(
            "ASELS", 0.10, positions, cash, total_exposure, total_value
        )
        assert can_open is True
        
        # Simulate opening
        positions["ASELS"] = {"quantity": 100}
        cash -= 10000
        total_exposure += 10000
        
        # Open second position
        can_open, reason = validator.can_open_position(
            "THYAO", 0.15, positions, cash, total_exposure, total_value
        )
        assert can_open is True
        
        # Simulate opening
        positions["THYAO"] = {"quantity": 50}
        cash -= 15000
        total_exposure += 15000
        
        # Open third position
        can_open, reason = validator.can_open_position(
            "GARAN", 0.10, positions, cash, total_exposure, total_value
        )
        assert can_open is True
        
        # Simulate opening
        positions["GARAN"] = {"quantity": 75}
        cash -= 10000
        total_exposure += 10000
        
        # Try to open fourth position (should fail - max positions)
        can_open, reason = validator.can_open_position(
            "ISCTR", 0.10, positions, cash, total_exposure, total_value
        )
        assert can_open is False
        assert reason == "MAX_POSITIONS_REACHED"
    
    def test_stress_limit_progression(self):
        """Test stress limits through a series of losing trades."""
        # Setup
        validator = PortfolioValidator(
            daily_max_loss_pct=0.05,
            consecutive_loss_limit=3
        )
        
        initial_capital = 100000
        daily_pnl = 0
        consecutive_losses = 0
        
        # Loss 1
        daily_pnl -= 1000
        consecutive_losses += 1
        can_trade, reason = validator.check_stress_limits(
            daily_pnl, consecutive_losses, initial_capital
        )
        assert can_trade is True  # Still OK
        
        # Loss 2
        daily_pnl -= 1000
        consecutive_losses += 1
        can_trade, reason = validator.check_stress_limits(
            daily_pnl, consecutive_losses, initial_capital
        )
        assert can_trade is True  # Still OK
        
        # Loss 3 - hits consecutive limit
        daily_pnl -= 1000
        consecutive_losses += 1
        can_trade, reason = validator.check_stress_limits(
            daily_pnl, consecutive_losses, initial_capital
        )
        assert can_trade is False  # Halted
        assert "CONSECUTIVE_LOSSES" in reason
    
    def test_exposure_limit_with_multiple_positions(self):
        """Test exposure limits with multiple positions."""
        # Setup
        validator = PortfolioValidator(
            max_total_exposure=0.80,
            max_single_exposure=0.20  # Increase to allow 15% positions
        )
        
        # Scenario: Already have 70% exposure
        positions = {
            "ASELS": {"quantity": 100},
            "THYAO": {"quantity": 50},
            "GARAN": {"quantity": 75}
        }
        
        # Try to add 15% more (would exceed 80% limit)
        can_open, reason = validator.can_open_position(
            symbol="ISCTR",
            size_pct=0.15,
            current_positions=positions,
            cash=30000,
            total_exposure=70000,
            total_value=100000
        )
        
        # Assert
        assert can_open is False
        assert reason == "EXCEEDS_TOTAL_EXPOSURE"
        
        # Try to add 10% (would be exactly at 80%)
        can_open, reason = validator.can_open_position(
            symbol="ISCTR",
            size_pct=0.10,
            current_positions=positions,
            cash=30000,
            total_exposure=70000,
            total_value=100000
        )
        
        # Assert - exactly at limit should pass
        assert can_open is True
        assert reason == "OK"


class TestValidatorRobustness:
    """Test validator robustness with unusual inputs."""
    
    def test_can_open_with_negative_size_pct(self):
        """Test validation with negative position size."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol="ASELS",
            size_pct=-0.05,  # Negative size
            current_positions={},
            cash=100000,
            total_exposure=0,
            total_value=100000
        )
        
        # Assert - should fail with INVALID_SIZE_PCT
        assert can_open is False
        assert reason == "INVALID_SIZE_PCT"
    
    def test_can_open_with_very_large_size(self):
        """Test validation with unreasonably large position size."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol="ASELS",
            size_pct=2.0,  # 200% of portfolio
            current_positions={},
            cash=100000,
            total_exposure=0,
            total_value=100000
        )
        
        # Assert
        assert can_open is False
        assert reason == "EXCEEDS_SINGLE_EXPOSURE"
    
    def test_stress_limits_with_very_large_loss(self):
        """Test stress limits with catastrophic loss."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_trade, reason = validator.check_stress_limits(
            daily_pnl=-50000,  # 50% loss
            consecutive_losses=0,
            initial_capital=100000
        )
        
        # Assert
        assert can_trade is False
        assert "DAILY_MAX_LOSS" in reason
    
    def test_validate_position_close_with_empty_positions(self):
        """Test closing position when no positions exist."""
        # Setup
        validator = PortfolioValidator()
        
        # Test
        can_close, reason = validator.validate_position_close(
            symbol="ASELS",
            current_positions={}  # Empty
        )
        
        # Assert
        assert can_close is False
        assert reason == "NO_POSITION"
