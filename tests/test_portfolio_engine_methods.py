"""
Tests for PortfolioBacktester extracted methods.

This module tests the private methods extracted during Task 11.1 refactoring.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.backtest.portfolio_engine import PortfolioBacktester
from utils.constants import (
    INITIAL_CAPITAL_PAPER,
    COMMISSION_RATE
)


class TestPortfolioBacktesterMethods(unittest.TestCase):
    """Test extracted methods from PortfolioBacktester."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backtester = PortfolioBacktester(
            initial_capital=INITIAL_CAPITAL_PAPER, 
            commission=COMMISSION_RATE
        )
        
        # Create sample data
        dates = pd.date_range(start="2024-01-01", periods=50)
        tickers = ['A', 'B', 'C']
        
        self.prices = pd.DataFrame(
            100 + np.random.randn(50, 3).cumsum(axis=0),
            index=dates,
            columns=tickers
        )
        
        self.signals = pd.DataFrame(
            0.33,
            index=dates,
            columns=tickers
        )
        
        self.volumes = pd.DataFrame(
            500000,
            index=dates,
            columns=tickers
        )
    
    def test_process_volumes_with_volumes(self):
        """Test _process_volumes with volume data."""
        common_index = self.prices.index
        V, V_TL = self.backtester._process_volumes(
            self.prices, self.volumes, common_index
        )
        
        self.assertIsNotNone(V)
        self.assertIsNotNone(V_TL)
        self.assertEqual(V.shape, self.volumes.shape)
        self.assertEqual(V_TL.shape, self.prices.shape)
    
    def test_process_volumes_without_volumes(self):
        """Test _process_volumes without volume data."""
        common_index = self.prices.index
        V, V_TL = self.backtester._process_volumes(
            self.prices, None, common_index
        )
        
        self.assertIsNone(V)
        self.assertIsNone(V_TL)
    
    def test_calculate_avg_volume(self):
        """Test _calculate_avg_volume calculation."""
        avg_vol = self.backtester._calculate_avg_volume(
            self.volumes, self.volumes.shape
        )
        
        self.assertEqual(avg_vol.shape, self.volumes.shape)
        # First 19 values should be less than full average
        self.assertTrue(np.all(avg_vol[0] <= self.volumes.iloc[0].values))
    
    def test_calculate_avg_volume_none(self):
        """Test _calculate_avg_volume with None."""
        shape = (50, 3)
        avg_vol = self.backtester._calculate_avg_volume(None, shape)
        
        self.assertEqual(avg_vol.shape, shape)
        self.assertTrue(np.all(avg_vol == 1.0))
    
    def test_initialize_portfolio_state(self):
        """Test _initialize_portfolio_state initialization."""
        n_days, n_assets = 50, 3
        cash, holdings_qty, equity_curve = self.backtester._initialize_portfolio_state(
            n_days, n_assets
        )
        
        self.assertEqual(cash, INITIAL_CAPITAL_PAPER)
        self.assertEqual(holdings_qty.shape, (n_assets,))
        self.assertEqual(equity_curve.shape, (n_days,))
        self.assertTrue(np.all(holdings_qty == 0))
        self.assertTrue(np.all(equity_curve == 0))
    
    def test_calculate_equity(self):
        """Test _calculate_equity calculation."""
        cash = 5000.0
        holdings_qty = np.array([10, 20, 30])
        prices = np.array([100, 50, 25])
        
        equity = self.backtester._calculate_equity(cash, holdings_qty, prices)
        
        # 5000 + (10*100 + 20*50 + 30*25) = 5000 + 2750 = 7750
        expected = 5000 + (10*100 + 20*50 + 30*25)
        self.assertEqual(equity, expected)
    
    def test_calculate_target_quantities(self):
        """Test _calculate_target_quantities calculation."""
        equity = 10000.0
        weights = np.array([0.3, 0.4, 0.3])
        prices = np.array([100, 50, 25])
        
        target_qty = self.backtester._calculate_target_quantities(
            equity, weights, prices
        )
        
        # Expected: [3000/100, 4000/50, 3000/25] = [30, 80, 120]
        expected = np.array([30, 80, 120])
        np.testing.assert_array_almost_equal(target_qty, expected)
    
    def test_calculate_target_quantities_with_nan(self):
        """Test _calculate_target_quantities handles NaN."""
        equity = 10000.0
        weights = np.array([0.5, 0.5, 0.0])
        prices = np.array([100, 0, 25])  # Zero price
        
        target_qty = self.backtester._calculate_target_quantities(
            equity, weights, prices
        )
        
        # Should handle division by zero
        self.assertFalse(np.any(np.isnan(target_qty)))
        self.assertFalse(np.any(np.isinf(target_qty)))
    
    def test_calculate_slippage_with_volume(self):
        """Test _calculate_slippage with volume data."""
        trade_qty = np.array([100, 200, 300])
        avg_vol = np.array([10000, 20000, 30000])
        
        slippage = self.backtester._calculate_slippage(trade_qty, avg_vol)
        
        self.assertEqual(slippage.shape, trade_qty.shape)
        # Slippage should be positive
        self.assertTrue(np.all(slippage >= 0))
        # Slippage should not exceed max
        self.assertTrue(np.all(slippage <= 0.03))
    
    def test_calculate_slippage_without_volume(self):
        """Test _calculate_slippage without volume data."""
        trade_qty = np.array([100, 200, 300])
        
        slippage = self.backtester._calculate_slippage(trade_qty, None)
        
        self.assertEqual(slippage.shape, trade_qty.shape)
        # Should return default slippage
        self.assertTrue(np.all(slippage == 0.001))
    
    def test_calculate_metrics(self):
        """Test _calculate_metrics calculation."""
        dates = pd.date_range(start="2024-01-01", periods=10)
        equity_curve = np.array([10000, 10100, 10050, 10200, 10150, 
                                10300, 10250, 10400, 10350, 10500])
        
        metrics = self.backtester._calculate_metrics(dates, equity_curve)
        
        self.assertIsInstance(metrics, pd.DataFrame)
        self.assertIn('Equity', metrics.columns)
        self.assertIn('Drawdown', metrics.columns)
        self.assertIn('Returns', metrics.columns)
        self.assertEqual(len(metrics), len(dates))
        
        # Check equity values
        np.testing.assert_array_equal(metrics['Equity'].values, equity_curve)
        
        # Check returns calculation
        self.assertEqual(metrics['Returns'].iloc[0], 0)  # First return is 0
        self.assertAlmostEqual(metrics['Returns'].iloc[1], 0.01, places=4)  # 1% return


class TestPortfolioBacktesterIntegration(unittest.TestCase):
    """Integration tests for complete backtest flow."""
    
    def test_complete_backtest_flow(self):
        """Test complete backtest with all components."""
        backtester = PortfolioBacktester(initial_capital=INITIAL_CAPITAL_PAPER)
        
        # Create test data
        dates = pd.date_range(start="2024-01-01", periods=30)
        tickers = ['A', 'B']
        
        prices = pd.DataFrame(
            [[100, 50], [101, 51], [102, 52]] * 10,
            index=dates,
            columns=tickers
        )
        
        signals = pd.DataFrame(
            [[0.5, 0.5]] * 30,
            index=dates,
            columns=tickers
        )
        
        volumes = pd.DataFrame(
            [[100000, 100000]] * 30,
            index=dates,
            columns=tickers
        )
        
        result = backtester.run_backtest(prices, signals, volumes)
        
        # Verify result structure
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 30)
        self.assertIn('Equity', result.columns)
        self.assertIn('Drawdown', result.columns)
        self.assertIn('Returns', result.columns)
        
        # Verify equity is positive
        self.assertTrue(all(result['Equity'] > 0))
        
        # Verify drawdown is negative or zero
        self.assertTrue(all(result['Drawdown'] <= 0))


if __name__ == '__main__':
    unittest.main()
