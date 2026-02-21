"""
Unit tests for HealthValidator class.

Tests validation logic for strategy health monitoring.
"""

import pytest
from paper_trading.health.health_validator import HealthValidator, StrategyState


class TestIsHealthy:
    """Test health threshold checks."""
    
    def test_healthy_strategy(self):
        """Test strategy with good health score."""
        validator = HealthValidator()
        
        metrics = {"health_score": 75}
        
        assert validator.is_healthy(metrics) is True
    
    def test_unhealthy_strategy(self):
        """Test strategy with poor health score."""
        validator = HealthValidator()
        
        metrics = {"health_score": 30}
        
        assert validator.is_healthy(metrics) is False
    
    def test_borderline_healthy(self):
        """Test strategy at health threshold."""
        validator = HealthValidator()
        
        metrics = {"health_score": 51}
        
        assert validator.is_healthy(metrics) is True
    
    def test_borderline_unhealthy(self):
        """Test strategy just below threshold."""
        validator = HealthValidator()
        
        metrics = {"health_score": 50}
        
        assert validator.is_healthy(metrics) is False


class TestCheckInvalidationRules:
    """Test invalidation rules."""
    
    def test_all_rules_pass(self):
        """Test when all rules pass."""
        validator = HealthValidator()
        
        metrics = {
            "rolling_50": {"trades": 50, "expectancy": 100, "rolling_sharpe": 1.0},
            "high_conf_stats": {"count": 20, "win_rate": 60.0},
            "consecutive_losses": 2,
            "max_drawdown": -5.0
        }
        
        state, reason = validator.check_invalidation_rules(metrics)
        
        assert state == StrategyState.ACTIVE
        assert "geçti" in reason
    
    def test_negative_expectancy(self):
        """Test negative expectancy triggers DISABLED."""
        validator = HealthValidator()
        
        metrics = {
            "rolling_50": {"trades": 50, "expectancy": -50, "rolling_sharpe": 1.0},
            "high_conf_stats": {"count": 20, "win_rate": 60.0},
            "consecutive_losses": 2,
            "max_drawdown": -5.0
        }
        
        state, reason = validator.check_invalidation_rules(metrics)
        
        assert state == StrategyState.DISABLED
        assert "Expectancy" in reason
    
    def test_low_high_conf_winrate(self):
        """Test low high-conf win rate triggers DEGRADED."""
        validator = HealthValidator()
        
        metrics = {
            "rolling_50": {"trades": 50, "expectancy": 100, "rolling_sharpe": 1.0},
            "high_conf_stats": {"count": 20, "win_rate": 30.0},
            "consecutive_losses": 2,
            "max_drawdown": -5.0
        }
        
        state, reason = validator.check_invalidation_rules(metrics)
        
        assert state == StrategyState.DEGRADED
        assert "High-conf" in reason
    
    def test_consecutive_losses(self):
        """Test consecutive losses trigger PAUSED."""
        validator = HealthValidator()
        
        metrics = {
            "rolling_50": {"trades": 50, "expectancy": 100, "rolling_sharpe": 1.0},
            "high_conf_stats": {"count": 20, "win_rate": 60.0},
            "consecutive_losses": 8,
            "max_drawdown": -5.0
        }
        
        state, reason = validator.check_invalidation_rules(metrics)
        
        assert state == StrategyState.PAUSED
        assert "Ardışık" in reason
    
    def test_low_sharpe(self):
        """Test low Sharpe triggers DEGRADED."""
        validator = HealthValidator()
        
        metrics = {
            "rolling_50": {"trades": 50, "expectancy": 100, "rolling_sharpe": -0.8},
            "high_conf_stats": {"count": 20, "win_rate": 60.0},
            "consecutive_losses": 2,
            "max_drawdown": -5.0
        }
        
        state, reason = validator.check_invalidation_rules(metrics)
        
        assert state == StrategyState.DEGRADED
        assert "Sharpe" in reason
    
    def test_max_drawdown(self):
        """Test max drawdown triggers PAPER_ONLY."""
        validator = HealthValidator()
        
        metrics = {
            "rolling_50": {"trades": 50, "expectancy": 100, "rolling_sharpe": 1.0},
            "high_conf_stats": {"count": 20, "win_rate": 60.0},
            "consecutive_losses": 2,
            "max_drawdown": -30.0  # -30% > -25% threshold
        }
        
        state, reason = validator.check_invalidation_rules(metrics)
        
        assert state == StrategyState.PAPER_ONLY
        assert "Max DD" in reason


class TestShouldSkipRegime:
    """Test regime skip logic."""
    
    def test_no_regime_data(self):
        """Test with no regime data."""
        validator = HealthValidator()
        
        should_skip, reason = validator.should_skip_regime({})
        
        assert should_skip is False
        assert "No regime data" in reason
    
    def test_insufficient_trades(self):
        """Test with insufficient trades."""
        validator = HealthValidator()
        
        regime_stats = {
            "trades": 5,
            "win_rate": 60.0,
            "total_pnl": 100
        }
        
        should_skip, reason = validator.should_skip_regime(regime_stats)
        
        assert should_skip is False
        assert "Insufficient data" in reason
    
    def test_low_win_rate(self):
        """Test with low win rate."""
        validator = HealthValidator()
        
        regime_stats = {
            "trades": 20,
            "win_rate": 30.0,
            "total_pnl": 100
        }
        
        should_skip, reason = validator.should_skip_regime(regime_stats)
        
        assert should_skip is True
        assert "Low win rate" in reason
    
    def test_negative_pnl(self):
        """Test with negative PnL."""
        validator = HealthValidator()
        
        regime_stats = {
            "trades": 20,
            "win_rate": 50.0,
            "total_pnl": -500
        }
        
        should_skip, reason = validator.should_skip_regime(regime_stats)
        
        assert should_skip is True
        assert "Negative PnL" in reason
    
    def test_good_regime(self):
        """Test with good regime."""
        validator = HealthValidator()
        
        regime_stats = {
            "trades": 20,
            "win_rate": 60.0,
            "total_pnl": 1000
        }
        
        should_skip, reason = validator.should_skip_regime(regime_stats)
        
        assert should_skip is False
        assert "Regime OK" in reason


class TestCanTrade:
    """Test trading permission checks."""
    
    def test_active_can_trade(self):
        """Test ACTIVE state allows trading."""
        validator = HealthValidator()
        
        assert validator.can_trade(StrategyState.ACTIVE) is True
    
    def test_degraded_can_trade(self):
        """Test DEGRADED state allows trading."""
        validator = HealthValidator()
        
        assert validator.can_trade(StrategyState.DEGRADED) is True
    
    def test_paper_only_can_trade(self):
        """Test PAPER_ONLY state allows trading."""
        validator = HealthValidator()
        
        assert validator.can_trade(StrategyState.PAPER_ONLY) is True
    
    def test_paused_cannot_trade(self):
        """Test PAUSED state blocks trading."""
        validator = HealthValidator()
        
        assert validator.can_trade(StrategyState.PAUSED) is False
    
    def test_disabled_cannot_trade(self):
        """Test DISABLED state blocks trading."""
        validator = HealthValidator()
        
        assert validator.can_trade(StrategyState.DISABLED) is False


class TestCanLiveTrade:
    """Test live trading permission checks."""
    
    def test_active_can_live_trade(self):
        """Test ACTIVE state allows live trading."""
        validator = HealthValidator()
        
        assert validator.can_live_trade(StrategyState.ACTIVE) is True
    
    def test_degraded_can_live_trade(self):
        """Test DEGRADED state allows live trading."""
        validator = HealthValidator()
        
        assert validator.can_live_trade(StrategyState.DEGRADED) is True
    
    def test_paper_only_cannot_live_trade(self):
        """Test PAPER_ONLY state blocks live trading."""
        validator = HealthValidator()
        
        assert validator.can_live_trade(StrategyState.PAPER_ONLY) is False


class TestShouldReduceSize:
    """Test position size reduction checks."""
    
    def test_active_no_reduction(self):
        """Test ACTIVE state doesn't reduce size."""
        validator = HealthValidator()
        
        assert validator.should_reduce_size(StrategyState.ACTIVE) is False
    
    def test_degraded_reduces_size(self):
        """Test DEGRADED state reduces size."""
        validator = HealthValidator()
        
        assert validator.should_reduce_size(StrategyState.DEGRADED) is True
    
    def test_paper_only_reduces_size(self):
        """Test PAPER_ONLY state reduces size."""
        validator = HealthValidator()
        
        assert validator.should_reduce_size(StrategyState.PAPER_ONLY) is True


class TestCustomThresholds:
    """Test custom threshold configuration."""
    
    def test_custom_thresholds(self):
        """Test validator with custom thresholds."""
        custom_thresholds = {
            'expectancy_min': 50.0,
            'high_conf_winrate_min': 0.50,
            'max_consecutive_losses': 5,
            'min_win_rate': 50.0,
            'min_trades': 20
        }
        
        validator = HealthValidator(custom_thresholds)
        
        assert validator.expectancy_min == 50.0
        assert validator.high_conf_winrate_min == 0.50
        assert validator.max_consecutive_losses == 5
        assert validator.min_win_rate == 50.0
        assert validator.min_trades == 20
