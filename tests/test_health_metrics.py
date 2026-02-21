"""
Unit tests for HealthMetrics class.

Tests metric calculation methods for strategy health monitoring.
"""

import pytest
import numpy as np
from paper_trading.health.health_metrics import HealthMetrics


class TestCalculateWinRate:
    """Test win rate calculation."""
    
    def test_empty_trades(self):
        """Test win rate with no trades."""
        metrics = HealthMetrics()
        assert metrics.calculate_win_rate([]) == 0.0
    
    def test_all_winners(self):
        """Test win rate with all winning trades."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100},
            {"pnl": 200},
            {"pnl": 50}
        ]
        assert metrics.calculate_win_rate(trades) == 1.0
    
    def test_all_losers(self):
        """Test win rate with all losing trades."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": -100},
            {"pnl": -200},
            {"pnl": -50}
        ]
        assert metrics.calculate_win_rate(trades) == 0.0
    
    def test_mixed_trades(self):
        """Test win rate with mixed trades."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": 200},
            {"pnl": -100}
        ]
        assert metrics.calculate_win_rate(trades) == 0.5
    
    def test_zero_pnl_counts_as_loss(self):
        """Test that zero PnL trades count as losses."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100},
            {"pnl": 0},
            {"pnl": 200}
        ]
        win_rate = metrics.calculate_win_rate(trades)
        assert abs(win_rate - 0.6667) < 0.01


class TestCalculateProfitFactor:
    """Test profit factor calculation."""
    
    def test_empty_trades(self):
        """Test profit factor with no trades."""
        metrics = HealthMetrics()
        assert metrics.calculate_profit_factor([]) == 0.0
    
    def test_all_winners(self):
        """Test profit factor with all winners (should be inf)."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100},
            {"pnl": 200}
        ]
        assert metrics.calculate_profit_factor(trades) == float('inf')
    
    def test_all_losers(self):
        """Test profit factor with all losers (should be 0)."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": -100},
            {"pnl": -200}
        ]
        assert metrics.calculate_profit_factor(trades) == 0.0
    
    def test_mixed_trades(self):
        """Test profit factor with mixed trades."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 300},  # Gross profit = 300
            {"pnl": -100}  # Gross loss = 100
        ]
        assert metrics.calculate_profit_factor(trades) == 3.0
    
    def test_profit_factor_calculation(self):
        """Test profit factor calculation with realistic trades."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 500},
            {"pnl": 300},
            {"pnl": -200},
            {"pnl": -100}
        ]
        # Gross profit = 800, Gross loss = 300
        # Profit factor = 800 / 300 = 2.67
        pf = metrics.calculate_profit_factor(trades)
        assert abs(pf - 2.67) < 0.01


class TestCalculateSharpeRatio:
    """Test Sharpe ratio calculation."""
    
    def test_empty_equity_curve(self):
        """Test Sharpe ratio with empty equity curve."""
        metrics = HealthMetrics()
        assert metrics.calculate_sharpe_ratio([]) == 0.0
    
    def test_single_value(self):
        """Test Sharpe ratio with single equity value."""
        metrics = HealthMetrics()
        assert metrics.calculate_sharpe_ratio([100000]) == 0.0
    
    def test_zero_volatility(self):
        """Test Sharpe ratio with zero volatility (flat equity)."""
        metrics = HealthMetrics()
        equity = [100000, 100000, 100000, 100000]
        assert metrics.calculate_sharpe_ratio(equity) == 0.0
    
    def test_positive_returns(self):
        """Test Sharpe ratio with positive returns."""
        metrics = HealthMetrics()
        equity = [100000, 101000, 102000, 103000, 104000]
        sharpe = metrics.calculate_sharpe_ratio(equity)
        assert sharpe > 0
    
    def test_negative_returns(self):
        """Test Sharpe ratio with negative returns."""
        metrics = HealthMetrics()
        equity = [100000, 99000, 98000, 97000, 96000]
        sharpe = metrics.calculate_sharpe_ratio(equity)
        assert sharpe < 0


class TestCalculateMaxDrawdown:
    """Test maximum drawdown calculation."""
    
    def test_empty_equity_curve(self):
        """Test max drawdown with empty equity curve."""
        metrics = HealthMetrics()
        assert metrics.calculate_max_drawdown([]) == 0.0
    
    def test_single_value(self):
        """Test max drawdown with single equity value."""
        metrics = HealthMetrics()
        assert metrics.calculate_max_drawdown([100000]) == 0.0
    
    def test_increasing_equity(self):
        """Test max drawdown with only increasing equity (no drawdown)."""
        metrics = HealthMetrics()
        equity = [100000, 101000, 102000, 103000]
        assert metrics.calculate_max_drawdown(equity) == 0.0
    
    def test_simple_drawdown(self):
        """Test max drawdown with simple drawdown."""
        metrics = HealthMetrics()
        equity = [100000, 110000, 90000, 95000]
        # Peak = 110000, Trough = 90000
        # DD = (90000 - 110000) / 110000 = -0.1818
        dd = metrics.calculate_max_drawdown(equity)
        assert abs(dd - (-0.1818)) < 0.01
    
    def test_multiple_drawdowns(self):
        """Test max drawdown with multiple drawdowns."""
        metrics = HealthMetrics()
        equity = [100000, 110000, 95000, 105000, 90000, 100000]
        # First DD: (95000 - 110000) / 110000 = -0.1364
        # Second DD: (90000 - 110000) / 110000 = -0.1818 (from global peak)
        # Max DD should be -0.1818
        dd = metrics.calculate_max_drawdown(equity)
        assert abs(dd - (-0.1818)) < 0.01


class TestCalculateExpectancy:
    """Test expectancy calculation."""
    
    def test_empty_trades(self):
        """Test expectancy with no trades."""
        metrics = HealthMetrics()
        assert metrics.calculate_expectancy([]) == 0.0
    
    def test_positive_expectancy(self):
        """Test expectancy with positive expected value."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 300},  # Win
            {"pnl": 200},  # Win
            {"pnl": -100}  # Loss
        ]
        # Win rate = 2/3, Avg win = 250, Avg loss = 100
        # Expectancy = (2/3 * 250) - (1/3 * 100) = 166.67 - 33.33 = 133.33
        exp = metrics.calculate_expectancy(trades)
        assert abs(exp - 133.33) < 1.0
    
    def test_negative_expectancy(self):
        """Test expectancy with negative expected value."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100},  # Win
            {"pnl": -200},  # Loss
            {"pnl": -300}  # Loss
        ]
        # Win rate = 1/3, Avg win = 100, Avg loss = 250
        # Expectancy = (1/3 * 100) - (2/3 * 250) = 33.33 - 166.67 = -133.33
        exp = metrics.calculate_expectancy(trades)
        assert exp < 0


class TestCalculateRollingMetrics:
    """Test rolling metrics calculation."""
    
    def test_empty_trades(self):
        """Test rolling metrics with no trades."""
        metrics = HealthMetrics()
        result = metrics.calculate_rolling_metrics([], 50)
        
        assert result["window"] == 50
        assert result["trades"] == 0
        assert result["win_rate"] == 0.0
    
    def test_fewer_trades_than_window(self):
        """Test rolling metrics when trades < window size."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100, "return_pct": 0.01},
            {"pnl": -50, "return_pct": -0.005}
        ]
        result = metrics.calculate_rolling_metrics(trades, 50)
        
        assert result["window"] == 50
        assert result["trades"] == 2
        assert result["win_rate"] == 50.0
    
    def test_rolling_window(self):
        """Test rolling metrics with full window."""
        metrics = HealthMetrics()
        # Create 100 trades, last 50 should be used
        trades = []
        for i in range(100):
            pnl = 100 if i % 2 == 0 else -50
            trades.append({"pnl": pnl, "return_pct": pnl / 10000})
        
        result = metrics.calculate_rolling_metrics(trades, 50)
        
        assert result["window"] == 50
        assert result["trades"] == 50
        assert result["win_rate"] == 50.0
    
    def test_rolling_metrics_structure(self):
        """Test that rolling metrics returns all expected fields."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100, "return_pct": 0.01},
            {"pnl": -50, "return_pct": -0.005},
            {"pnl": 200, "return_pct": 0.02}
        ]
        result = metrics.calculate_rolling_metrics(trades, 10)
        
        assert "window" in result
        assert "trades" in result
        assert "win_rate" in result
        assert "expectancy" in result
        assert "rolling_sharpe" in result
        assert "profit_factor" in result
        assert "avg_win" in result
        assert "avg_loss" in result
        assert "total_pnl" in result


class TestCalculateConsecutiveLosses:
    """Test consecutive losses calculation."""
    
    def test_empty_trades(self):
        """Test consecutive losses with no trades."""
        metrics = HealthMetrics()
        assert metrics.calculate_consecutive_losses([]) == 0
    
    def test_no_consecutive_losses(self):
        """Test consecutive losses when last trade is a winner."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": -100},
            {"pnl": -50},
            {"pnl": 200}
        ]
        assert metrics.calculate_consecutive_losses(trades) == 0
    
    def test_all_losses(self):
        """Test consecutive losses when all trades are losses."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": -100},
            {"pnl": -50},
            {"pnl": -200}
        ]
        assert metrics.calculate_consecutive_losses(trades) == 3
    
    def test_recent_consecutive_losses(self):
        """Test consecutive losses with recent losing streak."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100},
            {"pnl": 200},
            {"pnl": -50},
            {"pnl": -100},
            {"pnl": -75}
        ]
        assert metrics.calculate_consecutive_losses(trades) == 3


class TestCalculateHighConfidenceStats:
    """Test high confidence statistics calculation."""
    
    def test_empty_trades(self):
        """Test high confidence stats with no trades."""
        metrics = HealthMetrics()
        result = metrics.calculate_high_confidence_stats([])
        
        assert result["count"] == 0
        assert result["win_rate"] == 0.0
    
    def test_no_high_confidence_trades(self):
        """Test when no trades meet confidence threshold."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100, "entry_confidence": 0.60},
            {"pnl": -50, "entry_confidence": 0.65}
        ]
        result = metrics.calculate_high_confidence_stats(trades, confidence_threshold=0.70)
        
        assert result["count"] == 0
        assert result["win_rate"] == 0.0
    
    def test_high_confidence_trades(self):
        """Test high confidence trades statistics."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100, "entry_confidence": 0.75},
            {"pnl": -50, "entry_confidence": 0.80},
            {"pnl": 200, "entry_confidence": 0.85},
            {"pnl": 50, "entry_confidence": 0.60}  # Below threshold
        ]
        result = metrics.calculate_high_confidence_stats(trades, confidence_threshold=0.70)
        
        assert result["count"] == 3
        assert abs(result["win_rate"] - 66.7) < 0.1
    
    def test_custom_threshold(self):
        """Test high confidence stats with custom threshold."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100, "entry_confidence": 0.85},
            {"pnl": -50, "entry_confidence": 0.75},
            {"pnl": 200, "entry_confidence": 0.90}
        ]
        result = metrics.calculate_high_confidence_stats(trades, confidence_threshold=0.80)
        
        assert result["count"] == 2  # Only 0.85 and 0.90
        assert result["win_rate"] == 100.0


class TestEdgeCases:
    """Test edge cases and robustness."""
    
    def test_missing_pnl_field(self):
        """Test handling of trades with missing pnl field."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 100},
            {},  # Missing pnl
            {"pnl": -50}
        ]
        # Should treat missing pnl as 0 (loss)
        win_rate = metrics.calculate_win_rate(trades)
        assert abs(win_rate - 0.333) < 0.01
    
    def test_very_large_numbers(self):
        """Test with very large PnL values."""
        metrics = HealthMetrics()
        trades = [
            {"pnl": 1000000},
            {"pnl": -500000}
        ]
        pf = metrics.calculate_profit_factor(trades)
        assert pf == 2.0
    
    def test_zero_equity_in_curve(self):
        """Test max drawdown with zero equity value."""
        metrics = HealthMetrics()
        equity = [100000, 50000, 0, 10000]
        # Should handle zero without division error
        dd = metrics.calculate_max_drawdown(equity)
        assert dd <= 0
