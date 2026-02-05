"""
Test suite for Strategy Health & Kill-Switch Module
"""

import pytest
import os
import json
import tempfile
from paper_trading.strategy_health import (
    StrategyHealth, 
    StrategyState, 
    check_strategy_health,
    get_strategy_health_monitor
)


class TestRollingMetrics:
    """Test rolling performance windows"""
    
    def test_rolling_metrics_empty(self):
        health = StrategyHealth([])
        metrics = health.get_rolling_metrics(50)
        assert metrics["trades"] == 0
        assert metrics["win_rate"] == 0
    
    def test_rolling_metrics_basic(self):
        trades = [
            {"pnl": 100, "return_pct": 0.01},
            {"pnl": -50, "return_pct": -0.005},
            {"pnl": 200, "return_pct": 0.02},
        ]
        health = StrategyHealth(trades)
        metrics = health.get_rolling_metrics(50)
        
        assert metrics["trades"] == 3
        assert metrics["win_rate"] == pytest.approx(66.7, rel=0.1)
        assert metrics["total_pnl"] == 250
    
    def test_all_rolling_windows(self):
        trades = [{"pnl": 100, "return_pct": 0.01}] * 100
        health = StrategyHealth(trades)
        
        windows = health.get_all_rolling_windows()
        assert "window_30" in windows
        assert "window_50" in windows
        assert "window_100" in windows
        assert windows["window_30"]["trades"] == 30
        assert windows["window_50"]["trades"] == 50
        assert windows["window_100"]["trades"] == 100


class TestInvalidationRules:
    """Test hard invalidation rules"""
    
    def test_expectancy_disabled(self):
        # Create 50 losing trades
        trades = [{"pnl": -100, "return_pct": -0.01}] * 50
        health = StrategyHealth(trades)
        
        state, reason = health.check_invalidation_rules()
        assert state == StrategyState.DISABLED
        assert "Expectancy" in reason
    
    def test_consecutive_losses_paused(self):
        # Create 7 consecutive losing trades
        trades = [{"pnl": -100, "return_pct": -0.01}] * 7
        health = StrategyHealth(trades)
        
        state, reason = health.check_invalidation_rules()
        assert state == StrategyState.PAUSED
        assert "Ardışık" in reason
    
    def test_high_conf_winrate_degraded(self):
        # Create 20 high-confidence losing trades
        trades = [{"pnl": -100, "return_pct": -0.01, "entry_confidence": 0.85}] * 20
        health = StrategyHealth(trades)
        
        state, reason = health.check_invalidation_rules()
        assert state == StrategyState.DEGRADED
        assert "High-conf" in reason
    
    def test_max_dd_paper_only(self):
        # Create equity curve with big drawdown
        equity = [100000]
        for _ in range(30):
            equity.append(equity[-1] * 0.98)  # 2% loss each day = -45% total
        
        health = StrategyHealth([], equity)
        
        state, reason = health.check_invalidation_rules()
        assert state == StrategyState.PAPER_ONLY
        assert "Max DD" in reason
        assert health.paper_only_mode == True
    
    def test_active_state(self):
        # Create good trades
        trades = [{"pnl": 100, "return_pct": 0.01, "entry_confidence": 0.75}] * 50
        health = StrategyHealth(trades)
        
        state, reason = health.check_invalidation_rules()
        assert state == StrategyState.ACTIVE
        assert "Tüm kurallar geçti" in reason


class TestStateTransitions:
    """Test strategy state machine"""
    
    def test_initial_state(self):
        health = StrategyHealth([])
        assert health.state == StrategyState.ACTIVE
    
    def test_state_history_tracking(self):
        health = StrategyHealth([])
        health.force_state(StrategyState.DEGRADED, "Test reason")
        
        assert health.state == StrategyState.DEGRADED
        assert len(health.state_history) == 1
        assert health.state_history[0]["from"] == "ACTIVE"
        assert health.state_history[0]["to"] == "DEGRADED"
    
    def test_can_trade_states(self):
        health = StrategyHealth([])
        
        health.state = StrategyState.ACTIVE
        assert health.can_trade() == True
        assert health.can_live_trade() == True
        
        health.state = StrategyState.DEGRADED
        assert health.can_trade() == True
        assert health.can_live_trade() == True
        
        health.state = StrategyState.PAPER_ONLY
        assert health.can_trade() == True
        assert health.can_live_trade() == False
        
        health.state = StrategyState.PAUSED
        assert health.can_trade() == False
        
        health.state = StrategyState.DISABLED
        assert health.can_trade() == False


class TestMaxDrawdownTracking:
    """Test max drawdown tracking"""
    
    def test_max_dd_calculation(self):
        equity = [100, 110, 105, 115, 100, 120]  # Peak 115, trough 100
        health = StrategyHealth([], equity)
        
        expected_dd = (100 - 115) / 115  # -13%
        assert health.max_drawdown == pytest.approx(expected_dd, rel=0.01)
    
    def test_update_equity(self):
        health = StrategyHealth([], [100000])
        
        health.update_equity(110000)  # New high
        assert health.equity_high_water_mark == 110000
        
        health.update_equity(100000)  # Drawdown
        expected_dd = (100000 - 110000) / 110000
        assert health.max_drawdown == expected_dd
    
    def test_reset_max_dd(self):
        health = StrategyHealth([], [100000, 90000])
        assert health.max_drawdown < 0
        
        health.reset_max_dd_tracking()
        assert health.max_drawdown == 0.0
        assert health.paper_only_mode == False


class TestDynamicConfidenceThreshold:
    """Test dynamic confidence threshold adjustment"""
    
    def test_default_threshold(self):
        health = StrategyHealth([])
        assert health.current_confidence_threshold == 0.60
    
    def test_threshold_increase_on_poor_performance(self):
        # Poor high-conf performance: all losses
        trades = [{"pnl": -100, "return_pct": -0.01, "entry_confidence": 0.80}] * 25
        health = StrategyHealth(trades)
        
        recommended = health.get_recommended_confidence_threshold()
        assert recommended > health.DEFAULT_CONFIDENCE_THRESHOLD
    
    def test_threshold_stable_on_good_performance(self):
        # Good high-conf performance: all wins
        trades = [{"pnl": 100, "return_pct": 0.01, "entry_confidence": 0.80}] * 30
        health = StrategyHealth(trades)
        
        recommended = health.get_recommended_confidence_threshold()
        assert recommended == health.DEFAULT_CONFIDENCE_THRESHOLD


class TestStatePersistence:
    """Test save/load state"""
    
    def test_save_and_load(self):
        trades = [{"pnl": 100, "return_pct": 0.01}] * 10
        health = StrategyHealth(trades, [100000, 105000])
        health.current_confidence_threshold = 0.75
        health.force_state(StrategyState.DEGRADED, "Test")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            health.save_state(filepath)
            
            health2 = StrategyHealth([])
            loaded = health2.load_state(filepath)
            
            assert loaded == True
            assert health2.state == StrategyState.DEGRADED
            assert health2.current_confidence_threshold == 0.75
        finally:
            os.unlink(filepath)
    
    def test_load_nonexistent_file(self):
        health = StrategyHealth([])
        loaded = health.load_state("nonexistent_file.json")
        assert loaded == False


class TestIntegrationHelper:
    """Test integration helper functions"""
    
    def test_check_strategy_health_returns_tuple(self):
        class MockPortfolio:
            closed_trades = []
        
        can_trade, message, recommendations = check_strategy_health(MockPortfolio())
        
        assert isinstance(can_trade, bool)
        assert isinstance(message, str)
        assert isinstance(recommendations, dict)
        assert "confidence_threshold" in recommendations
        assert "position_size_multiplier" in recommendations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
