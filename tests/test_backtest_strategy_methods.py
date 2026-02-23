"""
Tests for BacktestStrategy extracted methods.

This module tests the private methods extracted during Task 11.1 refactoring.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.backtest.backtest_strategy import BacktestStrategy, BacktestConfig, Urgency
from utils.constants import (
    DEFAULT_INITIAL_CAPITAL,
    INITIAL_CAPITAL_PAPER,
    COMMISSION_RATE,
    MAX_DRAWDOWN_LIMIT,
    CASH_USAGE_PCT
)


class TestBacktestStrategyCircuitBreakerMethods(unittest.TestCase):
    """Test circuit breaker related extracted methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = BacktestConfig(
            initial_capital=INITIAL_CAPITAL_PAPER,
            max_drawdown_limit=MAX_DRAWDOWN_LIMIT
        )
        self.strategy = BacktestStrategy(self.config)
        
        self.current = {
            'close': 100.0,
            'open': 99.0,
            'date': datetime(2024, 1, 1)
        }
        
        self.state = {
            'holdings_qty': 50,
            'cash': 5000.0,
            'equity': INITIAL_CAPITAL_PAPER,
            'peak_equity': 12000.0,
            'circuit_breaker_triggered': False,
            'in_position': True,
            'holdings_value': 5000.0
        }
        
        self.results = {
            'trades': np.zeros(10),
            'exit_reasons': [''] * 10,
            'positions': np.zeros(10),
            'current_weights': np.zeros(10),
            'equities': np.zeros(10)
        }
    
    def test_update_portfolio_valuation(self):
        """Test _update_portfolio_valuation updates state correctly."""
        self.strategy._update_portfolio_valuation(self.current, self.state)
        
        # Holdings value should be updated
        expected_holdings = 50 * 100.0
        self.assertEqual(self.state['holdings_value'], expected_holdings)
        
        # Equity should be updated
        expected_equity = 5000.0 + expected_holdings
        self.assertEqual(self.state['equity'], expected_equity)
        
        # Peak equity should be updated if current is higher
        self.assertEqual(self.state['peak_equity'], 12000.0)  # Unchanged
    
    def test_update_portfolio_valuation_no_holdings(self):
        """Test _update_portfolio_valuation with no holdings."""
        self.state['holdings_qty'] = 0
        
        self.strategy._update_portfolio_valuation(self.current, self.state)
        
        self.assertEqual(self.state['holdings_value'], 0.0)
        self.assertFalse(self.state['in_position'])
    
    def test_calculate_drawdown(self):
        """Test _calculate_drawdown calculation."""
        self.state['equity'] = 8000.0
        self.state['peak_equity'] = INITIAL_CAPITAL_PAPER
        
        dd = self.strategy._calculate_drawdown(self.state)
        
        # (8000 - 10000) / 10000 = -0.2
        self.assertAlmostEqual(dd, -0.2, places=4)
    
    def test_calculate_drawdown_zero_peak(self):
        """Test _calculate_drawdown with zero peak."""
        self.state['equity'] = 5000.0
        self.state['peak_equity'] = 0
        
        dd = self.strategy._calculate_drawdown(self.state)
        
        self.assertEqual(dd, 0)
    
    def test_should_trigger_circuit_breaker_true(self):
        """Test _should_trigger_circuit_breaker returns True."""
        dd = -0.35  # Below -0.30 threshold
        
        should_trigger = self.strategy._should_trigger_circuit_breaker(dd, self.state)
        
        self.assertTrue(should_trigger)
    
    def test_should_trigger_circuit_breaker_false(self):
        """Test _should_trigger_circuit_breaker returns False."""
        dd = -0.20  # Above -0.30 threshold
        
        should_trigger = self.strategy._should_trigger_circuit_breaker(dd, self.state)
        
        self.assertFalse(should_trigger)
    
    def test_should_trigger_circuit_breaker_already_triggered(self):
        """Test _should_trigger_circuit_breaker when already triggered."""
        dd = -0.35
        self.state['circuit_breaker_triggered'] = True
        
        should_trigger = self.strategy._should_trigger_circuit_breaker(dd, self.state)
        
        self.assertFalse(should_trigger)  # Already triggered
    
    def test_force_close_position(self):
        """Test _force_close_position closes position."""
        i = 5
        
        self.strategy._force_close_position(self.current, self.state, self.results, i)
        
        # Check trade recorded
        self.assertEqual(self.results['trades'][i], 1)
        self.assertEqual(self.results['exit_reasons'][i], 'CIRCUIT_BREAKER')
        
        # Check position closed
        self.assertEqual(self.state['holdings_qty'], 0)
        self.assertEqual(self.state['holdings_value'], 0)
        
        # Check cash updated (50 shares * 99 open price * (1 - commission))
        expected_cash = 5000.0 + (50 * 99.0 * (1 - COMMISSION_RATE))
        self.assertAlmostEqual(self.state['cash'], expected_cash, places=2)
    
    def test_update_results_for_circuit_breaker(self):
        """Test _update_results_for_circuit_breaker updates results."""
        i = 5
        self.state['cash'] = 8000.0
        
        self.strategy._update_results_for_circuit_breaker(self.state, self.results, i)
        
        self.assertEqual(self.results['positions'][i], 0)
        self.assertEqual(self.results['current_weights'][i], 0)
        self.assertEqual(self.results['equities'][i], 8000.0)


class TestBacktestStrategyBuyMethods(unittest.TestCase):
    """Test buy execution related extracted methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = BacktestConfig(initial_capital=INITIAL_CAPITAL_PAPER)
        self.strategy = BacktestStrategy(self.config)
        
        self.current = {
            'close': 100.0,
            'input_val': 0.5,
            'volume': 100000,
            'avg_volume': 100000
        }
        
        self.state = {
            'is_weighted': True,
            'equity': INITIAL_CAPITAL_PAPER,
            'cash': INITIAL_CAPITAL_PAPER,
            'holdings_qty': 0,
            'in_position': False
        }
        
        self.results = {
            'trades': np.zeros(10),
            'order_types': [''] * 10,
            'execution_notes': [''] * 10
        }
    
    def test_calculate_buy_quantity_weighted(self):
        """Test _calculate_buy_quantity for weighted strategy."""
        qty = self.strategy._calculate_buy_quantity(self.current, self.state)
        
        # Target: 10000 * 0.5 / 100 = 50 shares
        # Current: 0 shares
        # Diff: 50 shares
        self.assertAlmostEqual(qty, 50.0, places=2)
    
    def test_calculate_buy_quantity_binary(self):
        """Test _calculate_buy_quantity for binary strategy."""
        self.state['is_weighted'] = False
        
        qty = self.strategy._calculate_buy_quantity(self.current, self.state)
        
        # 99% of cash: INITIAL_CAPITAL_PAPER * CASH_USAGE_PCT / 100 = 99 shares
        expected_qty = INITIAL_CAPITAL_PAPER * CASH_USAGE_PCT / 100
        self.assertAlmostEqual(qty, expected_qty, places=2)
    
    def test_get_execution_price_no_router(self):
        """Test _get_execution_price without router."""
        i = 5
        
        price = self.strategy._get_execution_price(
            self.current, None, 50, Urgency.NORMAL, self.results, i
        )
        
        self.assertEqual(price, 100.0)  # Should return close price
    
    def test_calculate_buy_cost(self):
        """Test _calculate_buy_cost calculation."""
        qty = 50
        price = 100.0
        
        cost = self.strategy._calculate_buy_cost(qty, price, self.current)
        
        # Base cost: 50 * 100 = 5000
        # Slippage: small amount
        # Commission: 0.2%
        # Total should be slightly more than 5000
        self.assertGreater(cost, 5000.0)
        self.assertLess(cost, 5100.0)  # Reasonable upper bound
    
    def test_execute_buy_trade_new_position(self):
        """Test _execute_buy_trade for new position."""
        i = 5
        qty = 50
        price = 100.0
        total_cost = 5010.0
        
        self.current['date'] = datetime(2024, 1, 1)
        
        self.strategy._execute_buy_trade(
            qty, price, total_cost, self.current, self.state, self.results, i
        )
        
        # Check cash deducted
        self.assertAlmostEqual(self.state['cash'], INITIAL_CAPITAL_PAPER - 5010.0, places=2)
        
        # Check holdings updated
        self.assertEqual(self.state['holdings_qty'], 50)
        
        # Check trade recorded
        self.assertEqual(self.results['trades'][i], 1)
        
        # Check entry price set
        self.assertEqual(self.state['entry_price'], 100.0)
        self.assertTrue(self.state['in_position'])
    
    def test_execute_buy_trade_scale_in(self):
        """Test _execute_buy_trade for scaling in."""
        i = 5
        qty = 25
        price = 110.0
        total_cost = 2752.5
        
        # Existing position
        self.state['holdings_qty'] = 50
        self.state['entry_price'] = 100.0
        self.state['in_position'] = True
        
        self.current['date'] = datetime(2024, 1, 1)
        
        self.strategy._execute_buy_trade(
            qty, price, total_cost, self.current, self.state, self.results, i
        )
        
        # Check holdings updated
        self.assertEqual(self.state['holdings_qty'], 75)
        
        # Check weighted average entry price
        # (50 * 100 + 25 * 110) / 75 = (5000 + 2750) / 75 = 103.33
        expected_entry = (50 * 100.0 + 25 * 110.0) / 75
        self.assertAlmostEqual(self.state['entry_price'], expected_entry, places=2)


class TestBacktestStrategyIntegration(unittest.TestCase):
    """Integration tests for BacktestStrategy methods."""
    
    def test_circuit_breaker_flow(self):
        """Test complete circuit breaker flow."""
        config = BacktestConfig(max_drawdown_limit=0.25)
        strategy = BacktestStrategy(config)
        
        current = {
            'close': 70.0,
            'open': 69.0,
            'date': datetime(2024, 1, 1)
        }
        
        state = {
            'holdings_qty': 100,
            'cash': 0.0,
            'equity': 7000.0,
            'peak_equity': INITIAL_CAPITAL_PAPER,
            'circuit_breaker_triggered': False,
            'in_position': True,
            'holdings_value': 7000.0
        }
        
        results = {
            'trades': np.zeros(10),
            'exit_reasons': [''] * 10,
            'positions': np.zeros(10),
            'current_weights': np.zeros(10),
            'equities': np.zeros(10)
        }
        
        # Should trigger circuit breaker (30% drawdown)
        triggered = strategy._check_circuit_breaker(current, state, results, 5)
        
        self.assertTrue(triggered)
        self.assertTrue(state['circuit_breaker_triggered'])
        self.assertEqual(state['holdings_qty'], 0)  # Position closed


if __name__ == '__main__':
    unittest.main()
