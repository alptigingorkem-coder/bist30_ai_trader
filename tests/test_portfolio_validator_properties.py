"""
Property-based tests for PortfolioValidator.

Uses Hypothesis to test universal properties that should hold for all inputs.
These tests validate validation consistency and correctness properties.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from paper_trading.portfolio.portfolio_validator import PortfolioValidator


# ============================================================================
# HYPOTHESIS STRATEGIES
# ============================================================================

# Strategy for generating valid validator configurations
validator_config_strategy = st.fixed_dictionaries({
    "max_positions": st.integers(min_value=1, max_value=20),
    "max_single_exposure": st.floats(min_value=0.01, max_value=0.50),
    "max_total_exposure": st.floats(min_value=0.10, max_value=1.0),
    "daily_max_loss_pct": st.floats(min_value=0.01, max_value=0.20),
    "consecutive_loss_limit": st.integers(min_value=1, max_value=10),
})

# Strategy for position opening parameters
position_params_strategy = st.fixed_dictionaries({
    "symbol": st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=3, max_size=6),
    "size_pct": st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
    "cash": st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False),
    "total_exposure": st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False),
    "total_value": st.floats(min_value=1, max_value=1000000, allow_nan=False, allow_infinity=False),
})

# Strategy for stress limit parameters
stress_params_strategy = st.fixed_dictionaries({
    "daily_pnl": st.floats(min_value=-100000, max_value=100000, allow_nan=False, allow_infinity=False),
    "consecutive_losses": st.integers(min_value=0, max_value=20),
    "initial_capital": st.floats(min_value=1, max_value=1000000, allow_nan=False, allow_infinity=False),
})


# ============================================================================
# PROPERTY 5: VALIDATION CONSISTENCY
# ============================================================================

class TestValidationConsistency:
    """
    Property 5: Validation Consistency
    
    Validates: Requirements 1.5
    
    For any validation inputs, calling validator multiple times should return
    the same result. Validation is deterministic and idempotent.
    """
    
    @given(
        config=validator_config_strategy,
        params=position_params_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_can_open_position_is_deterministic(self, config, params):
        """
        Property: can_open_position(X) == can_open_position(X)
        
        Calling the same validation multiple times should return identical results.
        """
        # Setup
        validator = PortfolioValidator(**config)
        current_positions = {}
        
        # Test: Call validation multiple times
        result1 = validator.can_open_position(
            symbol=params["symbol"],
            size_pct=params["size_pct"],
            current_positions=current_positions,
            cash=params["cash"],
            total_exposure=params["total_exposure"],
            total_value=params["total_value"]
        )
        
        result2 = validator.can_open_position(
            symbol=params["symbol"],
            size_pct=params["size_pct"],
            current_positions=current_positions,
            cash=params["cash"],
            total_exposure=params["total_exposure"],
            total_value=params["total_value"]
        )
        
        result3 = validator.can_open_position(
            symbol=params["symbol"],
            size_pct=params["size_pct"],
            current_positions=current_positions,
            cash=params["cash"],
            total_exposure=params["total_exposure"],
            total_value=params["total_value"]
        )
        
        # Property: All results should be identical
        assert result1 == result2 == result3
    
    @given(
        config=validator_config_strategy,
        params=stress_params_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_check_stress_limits_is_deterministic(self, config, params):
        """
        Property: check_stress_limits(X) == check_stress_limits(X)
        
        Stress limit checks should be deterministic.
        """
        # Setup
        validator = PortfolioValidator(**config)
        
        # Test: Call validation multiple times
        result1 = validator.check_stress_limits(
            daily_pnl=params["daily_pnl"],
            consecutive_losses=params["consecutive_losses"],
            initial_capital=params["initial_capital"]
        )
        
        result2 = validator.check_stress_limits(
            daily_pnl=params["daily_pnl"],
            consecutive_losses=params["consecutive_losses"],
            initial_capital=params["initial_capital"]
        )
        
        result3 = validator.check_stress_limits(
            daily_pnl=params["daily_pnl"],
            consecutive_losses=params["consecutive_losses"],
            initial_capital=params["initial_capital"]
        )
        
        # Property: All results should be identical
        assert result1 == result2 == result3
    
    @given(
        config=validator_config_strategy,
        params=position_params_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_validation_does_not_modify_inputs(self, config, params):
        """
        Property: Validation should not modify input parameters.
        
        Validators should be side-effect free.
        """
        # Setup
        validator = PortfolioValidator(**config)
        current_positions = {"EXISTING": {"quantity": 100}}
        original_positions = current_positions.copy()
        
        # Test: Call validation
        validator.can_open_position(
            symbol=params["symbol"],
            size_pct=params["size_pct"],
            current_positions=current_positions,
            cash=params["cash"],
            total_exposure=params["total_exposure"],
            total_value=params["total_value"]
        )
        
        # Property: Input parameters should not be modified
        assert current_positions == original_positions


# ============================================================================
# PROPERTY: VALIDATION INVARIANTS
# ============================================================================

class TestValidationInvariants:
    """
    Invariants that should hold for all validation operations.
    """
    
    @given(
        config=validator_config_strategy,
        params=position_params_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_validation_returns_bool_and_string(self, config, params):
        """
        Property: Validation always returns (bool, str) tuple.
        """
        # Setup
        validator = PortfolioValidator(**config)
        
        # Test
        result = validator.can_open_position(
            symbol=params["symbol"],
            size_pct=params["size_pct"],
            current_positions={},
            cash=params["cash"],
            total_exposure=params["total_exposure"],
            total_value=params["total_value"]
        )
        
        # Property: Result should be a tuple of (bool, str)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
    
    @given(
        config=validator_config_strategy,
        params=position_params_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_ok_reason_only_when_can_open(self, config, params):
        """
        Property: Reason is "OK" if and only if can_open is True.
        """
        # Setup
        validator = PortfolioValidator(**config)
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol=params["symbol"],
            size_pct=params["size_pct"],
            current_positions={},
            cash=params["cash"],
            total_exposure=params["total_exposure"],
            total_value=params["total_value"]
        )
        
        # Property: "OK" reason iff can_open is True
        if can_open:
            assert reason == "OK"
        else:
            assert reason != "OK"
            assert len(reason) > 0  # Should have a meaningful reason
    
    @given(
        config=validator_config_strategy,
        symbol=st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=3, max_size=6),
        size_pct=st.floats(min_value=0.01, max_value=0.50, allow_nan=False, allow_infinity=False),
        cash=st.floats(min_value=1000, max_value=1000000, allow_nan=False, allow_infinity=False),
        total_value=st.floats(min_value=1000, max_value=1000000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_already_has_position_always_fails(self, config, symbol, size_pct, cash, total_value):
        """
        Property: If position already exists, validation always fails.
        """
        # Setup
        validator = PortfolioValidator(**config)
        current_positions = {symbol: {"quantity": 100}}
        
        # Test
        can_open, reason = validator.can_open_position(
            symbol=symbol,
            size_pct=size_pct,
            current_positions=current_positions,
            cash=cash,
            total_exposure=0,
            total_value=total_value
        )
        
        # Property: Should always fail with ALREADY_HAS_POSITION
        assert can_open is False
        assert reason == "ALREADY_HAS_POSITION"


# ============================================================================
# PROPERTY: MONOTONICITY
# ============================================================================

class TestValidationMonotonicity:
    """
    Test monotonicity properties of validation.
    """
    
    @given(
        config=validator_config_strategy,
        symbol=st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=3, max_size=6),
        size_pct=st.floats(min_value=0.01, max_value=0.20, allow_nan=False, allow_infinity=False),
        cash=st.floats(min_value=10000, max_value=100000, allow_nan=False, allow_infinity=False),
        total_value=st.floats(min_value=10000, max_value=100000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_more_cash_never_makes_validation_fail(self, config, symbol, size_pct, cash, total_value):
        """
        Property: If validation passes with cash X, it should pass with cash X+Y.
        
        More cash should never cause validation to fail.
        """
        # Setup
        validator = PortfolioValidator(**config)
        
        # Test with original cash
        can_open_original, _ = validator.can_open_position(
            symbol=symbol,
            size_pct=size_pct,
            current_positions={},
            cash=cash,
            total_exposure=0,
            total_value=total_value
        )
        
        # Test with more cash
        can_open_more_cash, _ = validator.can_open_position(
            symbol=symbol,
            size_pct=size_pct,
            current_positions={},
            cash=cash * 2,  # Double the cash
            total_exposure=0,
            total_value=total_value
        )
        
        # Property: If passed with less cash, should pass with more cash
        if can_open_original:
            assert can_open_more_cash is True
    
    @given(
        config=validator_config_strategy,
        daily_pnl=st.floats(min_value=-10000, max_value=-100, allow_nan=False, allow_infinity=False),
        consecutive_losses=st.integers(min_value=0, max_value=5),
        initial_capital=st.floats(min_value=10000, max_value=100000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_larger_loss_never_makes_validation_pass(self, config, daily_pnl, consecutive_losses, initial_capital):
        """
        Property: If validation fails with loss X, it should fail with loss X+Y.
        
        Larger losses should never cause validation to pass.
        """
        # Setup
        validator = PortfolioValidator(**config)
        
        # Test with original loss
        can_trade_original, _ = validator.check_stress_limits(
            daily_pnl=daily_pnl,
            consecutive_losses=consecutive_losses,
            initial_capital=initial_capital
        )
        
        # Test with larger loss
        can_trade_larger_loss, _ = validator.check_stress_limits(
            daily_pnl=daily_pnl * 2,  # Double the loss
            consecutive_losses=consecutive_losses,
            initial_capital=initial_capital
        )
        
        # Property: If failed with smaller loss, should fail with larger loss
        if not can_trade_original:
            assert can_trade_larger_loss is False


# ============================================================================
# PROPERTY: BOUNDARY CONDITIONS
# ============================================================================

class TestValidationBoundaries:
    """
    Test validation behavior at boundaries.
    """
    
    @given(
        max_positions=st.integers(min_value=1, max_value=10),
        symbol=st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=3, max_size=6)
    )
    @settings(max_examples=50, deadline=None)
    def test_max_positions_boundary(self, max_positions, symbol):
        """
        Property: Can open position when at max_positions-1, cannot when at max_positions.
        """
        # Setup
        validator = PortfolioValidator(max_positions=max_positions)
        
        # Create positions at limit - 1
        positions_below_limit = {f"STOCK{i}": {} for i in range(max_positions - 1)}
        
        # Test: Should be able to open one more
        can_open_below, _ = validator.can_open_position(
            symbol=symbol,
            size_pct=0.05,
            current_positions=positions_below_limit,
            cash=100000,
            total_exposure=0,
            total_value=100000
        )
        
        # Create positions at limit
        positions_at_limit = {f"STOCK{i}": {} for i in range(max_positions)}
        
        # Test: Should not be able to open more
        can_open_at_limit, reason = validator.can_open_position(
            symbol=symbol,
            size_pct=0.05,
            current_positions=positions_at_limit,
            cash=100000,
            total_exposure=0,
            total_value=100000
        )
        
        # Property: Can open below limit, cannot at limit
        assert can_open_below is True
        assert can_open_at_limit is False
        assert reason == "MAX_POSITIONS_REACHED"
