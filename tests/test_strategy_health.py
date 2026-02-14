"""
Test suite for Strategy Health & Kill-Switch Module
"""

import unittest
import os
import json
import tempfile
from paper_trading.strategy_health import (
    StrategyHealth, 
    StrategyState, 
    check_strategy_health,
    get_strategy_health_monitor
)


class TestRollingMetrics(unittest.TestCase):
    """Test rolling performance windows"""
    
    def test_rolling_metrics_empty(self):
        health = StrategyHealth([])
        metrics = health.get_rolling_metrics(50)
        self.assertEqual(metrics["trades"], 0)
        self.assertEqual(metrics["win_rate"], 0)
    
    def test_rolling_metrics_basic(self):
        trades = [
            {"pnl": 100, "return_pct": 0.01},
            {"pnl": -50, "return_pct": -0.005},
            {"pnl": 200, "return_pct": 0.02},
        ]
        health = StrategyHealth(trades)
        metrics = health.get_rolling_metrics(50)
        
        self.assertEqual(metrics["trades"], 3)
        self.assertAlmostEqual(metrics["win_rate"], 66.7, delta=0.1)
        self.assertEqual(metrics["total_pnl"], 250)
    
    def test_all_rolling_windows(self):
        trades = [{"pnl": 100, "return_pct": 0.01}] * 100
        health = StrategyHealth(trades)
        
        windows = health.get_all_rolling_windows()
        self.assertIn("window_30", windows)
        self.assertIn("window_50", windows)
        self.assertIn("window_100", windows)
        self.assertEqual(windows["window_30"]["trades"], 30)
        self.assertEqual(windows["window_50"]["trades"], 50)
        self.assertEqual(windows["window_100"]["trades"], 100)


class TestInvalidationRules(unittest.TestCase):
    """Test hard invalidation rules"""
    
    def test_expectancy_disabled(self):
        # Create 50 losing trades
        trades = [{"pnl": -100, "return_pct": -0.01}] * 50
        health = StrategyHealth(trades)
        
        state, reason = health.check_invalidation_rules()
        self.assertEqual(state, StrategyState.DISABLED)
        self.assertIn("Expectancy", reason)
    
    def test_consecutive_losses_paused(self):
        # Create 7 consecutive losing trades
        trades = [{"pnl": -100, "return_pct": -0.01}] * 7
        health = StrategyHealth(trades)
        
        state, reason = health.check_invalidation_rules()
        self.assertEqual(state, StrategyState.PAUSED)
        self.assertIn("Ardışık", reason)
    
    def test_high_conf_winrate_degraded(self):
        # Create 20 high-confidence losing trades
        trades = [{"pnl": -100, "return_pct": -0.01, "entry_confidence": 0.85}] * 20
        health = StrategyHealth(trades)
        
        state, reason = health.check_invalidation_rules()
        self.assertEqual(state, StrategyState.DEGRADED)
        self.assertIn("High-conf", reason)
    
    def test_max_dd_paper_only(self):
        # Create equity curve with big drawdown
        equity = [100000]
        for _ in range(30):
            equity.append(equity[-1] * 0.98)  # 2% loss each day = -45% total
        
        health = StrategyHealth([], equity)
        
        state, reason = health.check_invalidation_rules()
        self.assertEqual(state, StrategyState.PAPER_ONLY)
        self.assertIn("Max DD", reason)
        self.assertTrue(health.paper_only_mode)
    
    def test_active_state(self):
        # Create good trades
        trades = [{"pnl": 100, "return_pct": 0.01, "entry_confidence": 0.75}] * 50
        health = StrategyHealth(trades)
        
        state, reason = health.check_invalidation_rules()
        self.assertEqual(state, StrategyState.ACTIVE)
        self.assertIn("Tüm kurallar geçti", reason)


class TestStateTransitions(unittest.TestCase):
    """Test strategy state machine"""
    
    def test_initial_state(self):
        health = StrategyHealth([])
        self.assertEqual(health.state, StrategyState.ACTIVE)
    
    def test_state_history_tracking(self):
        health = StrategyHealth([])
        health.force_state(StrategyState.DEGRADED, "Test reason")
        
        self.assertEqual(health.state, StrategyState.DEGRADED)
        self.assertEqual(len(health.state_history), 1)
        self.assertEqual(health.state_history[0]["from"], "ACTIVE")
        self.assertEqual(health.state_history[0]["to"], "DEGRADED")
    
    def test_can_trade_states(self):
        health = StrategyHealth([])
        
        health.state = StrategyState.ACTIVE
        self.assertTrue(health.can_trade())
        self.assertTrue(health.can_live_trade())
        
        health.state = StrategyState.DEGRADED
        self.assertTrue(health.can_trade())
        self.assertTrue(health.can_live_trade())
        
        health.state = StrategyState.PAPER_ONLY
        self.assertTrue(health.can_trade())
        self.assertFalse(health.can_live_trade())
        
        health.state = StrategyState.PAUSED
        self.assertFalse(health.can_trade())
        
        health.state = StrategyState.DISABLED
        self.assertFalse(health.can_trade())


class TestMaxDrawdownTracking(unittest.TestCase):
    """Test max drawdown tracking"""
    
    def test_max_dd_calculation(self):
        equity = [100, 110, 105, 115, 100, 120]  # Peak 115, trough 100
        health = StrategyHealth([], equity)
        
        expected_dd = (100 - 115) / 115  # -13%
        self.assertAlmostEqual(health.max_drawdown, expected_dd, delta=0.01)
    
    def test_update_equity(self):
        health = StrategyHealth([], [100000])
        
        health.update_equity(110000)  # New high
        self.assertEqual(health.equity_high_water_mark, 110000)
        
        health.update_equity(100000)  # Drawdown
        expected_dd = (100000 - 110000) / 110000
        self.assertEqual(health.max_drawdown, expected_dd)
    
    def test_reset_max_dd(self):
        health = StrategyHealth([], [100000, 90000])
        self.assertTrue(health.max_drawdown < 0)
        
        health.reset_max_dd_tracking()
        self.assertEqual(health.max_drawdown, 0.0)
        self.assertFalse(health.paper_only_mode)


class TestDynamicConfidenceThreshold(unittest.TestCase):
    """Test dynamic confidence threshold adjustment"""
    
    def test_default_threshold(self):
        health = StrategyHealth([])
        self.assertEqual(health.current_confidence_threshold, 0.60)
    
    def test_threshold_increase_on_poor_performance(self):
        # Poor high-conf performance: all losses
        trades = [{"pnl": -100, "return_pct": -0.01, "entry_confidence": 0.80}] * 25
        health = StrategyHealth(trades)
        
        recommended = health.get_recommended_confidence_threshold()
        self.assertGreater(recommended, health.DEFAULT_CONFIDENCE_THRESHOLD)
    
    def test_threshold_stable_on_good_performance(self):
        # Good high-conf performance: all wins
        trades = [{"pnl": 100, "return_pct": 0.01, "entry_confidence": 0.80}] * 30
        health = StrategyHealth(trades)
        
        recommended = health.get_recommended_confidence_threshold()
        self.assertEqual(recommended, health.DEFAULT_CONFIDENCE_THRESHOLD)


class TestStatePersistence(unittest.TestCase):
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
            
            self.assertTrue(loaded)
            self.assertEqual(health2.state, StrategyState.DEGRADED)
            self.assertEqual(health2.current_confidence_threshold, 0.75)
        finally:
            os.unlink(filepath)
    
    def test_load_nonexistent_file(self):
        health = StrategyHealth([])
        loaded = health.load_state("nonexistent_file.json")
        self.assertFalse(loaded)


class TestIntegrationHelper(unittest.TestCase):
    """Test integration helper functions"""
    
    def test_check_strategy_health_returns_tuple(self):
        class MockPortfolio:
            closed_trades = []
            
            def calculate_equity_curve(self):
                return [100]
        
        can_trade, message, recommendations = check_strategy_health(MockPortfolio())
        
        self.assertIsInstance(can_trade, bool)
        self.assertIsInstance(message, str)
        self.assertIsInstance(recommendations, dict)
        self.assertIn("confidence_threshold", recommendations)
        self.assertIn("position_size_multiplier", recommendations)


if __name__ == "__main__":
    unittest.main()
