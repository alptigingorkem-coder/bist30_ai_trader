"""
Unit tests for PortfolioMetrics.

Tests the statistical analysis and metrics calculation for portfolio data.
"""

import pytest
import numpy as np
from paper_trading.portfolio.portfolio_metrics import PortfolioMetrics


class TestGetTradeStatistics:
    """Test cases for trade statistics calculation."""
    
    def test_empty_ledger(self):
        """Test statistics with empty ledger."""
        metrics = PortfolioMetrics()
        stats = metrics.get_trade_statistics([])
        
        assert stats == {"total_trades": 0}
    
    def test_single_winning_trade(self):
        """Test statistics with single winning trade."""
        metrics = PortfolioMetrics()
        
        ledger = [{
            "net_pnl": 500.0,
            "commission": 21.25,
            "return_pct": 12.5,
            "holding_days": 0.21
        }]
        
        stats = metrics.get_trade_statistics(ledger)
        
        assert stats["total_trades"] == 1
        assert stats["winning_trades"] == 1
        assert stats["losing_trades"] == 0
        assert stats["win_rate"] == 100.0
        assert stats["total_pnl"] == 500.0
        assert stats["avg_win"] == 500.0
        assert stats["avg_loss"] == 0.0
        assert stats["profit_factor"] == "∞"
    
    def test_mixed_trades(self):
        """Test statistics with mixed winning and losing trades."""
        metrics = PortfolioMetrics()
        
        ledger = [
            {"net_pnl": 500.0, "commission": 21.25, "return_pct": 12.5, "holding_days": 0.21},
            {"net_pnl": -250.0, "commission": 12.25, "return_pct": -5.0, "holding_days": 0.13},
            {"net_pnl": 300.0, "commission": 15.0, "return_pct": 7.5, "holding_days": 0.17}
        ]
        
        stats = metrics.get_trade_statistics(ledger)
        
        assert stats["total_trades"] == 3
        assert stats["winning_trades"] == 2
        assert stats["losing_trades"] == 1
        assert stats["win_rate"] == pytest.approx(66.67, abs=0.01)
        assert stats["total_pnl"] == 550.0
        assert stats["total_commission"] == pytest.approx(48.5)
        assert stats["avg_return_pct"] == 5.0
        assert stats["avg_win"] == 400.0
        assert stats["avg_loss"] == -250.0
        assert stats["profit_factor"] == pytest.approx(3.2)
    
    def test_all_losing_trades(self):
        """Test statistics with all losing trades."""
        metrics = PortfolioMetrics()
        
        ledger = [
            {"net_pnl": -100.0, "commission": 10.0, "return_pct": -2.0, "holding_days": 0.1},
            {"net_pnl": -200.0, "commission": 15.0, "return_pct": -4.0, "holding_days": 0.2}
        ]
        
        stats = metrics.get_trade_statistics(ledger)
        
        assert stats["total_trades"] == 2
        assert stats["winning_trades"] == 0
        assert stats["losing_trades"] == 2
        assert stats["win_rate"] == 0.0
        assert stats["total_pnl"] == -300.0
        assert stats["avg_win"] == 0.0
        assert stats["profit_factor"] == 0


class TestGetConfidenceBucketAnalysis:
    """Test cases for confidence bucket analysis."""
    
    def test_empty_trades(self):
        """Test analysis with empty trades."""
        metrics = PortfolioMetrics()
        analysis = metrics.get_confidence_bucket_analysis([])
        
        # Should return all buckets with zero counts
        assert len(analysis) == 5
        assert all(bucket["count"] == 0 for bucket in analysis.values())
    
    def test_single_bucket(self):
        """Test analysis with trades in single bucket."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"entry_confidence": 0.85, "pnl": 500.0, "return_pct": 0.125},
            {"entry_confidence": 0.87, "pnl": 300.0, "return_pct": 0.075},
            {"entry_confidence": 0.82, "pnl": -200.0, "return_pct": -0.05}
        ]
        
        analysis = metrics.get_confidence_bucket_analysis(trades)
        
        # All trades should be in 0.80-0.90 bucket
        assert analysis["0.80-0.90"]["count"] == 3
        assert analysis["0.80-0.90"]["win_rate"] == pytest.approx(66.7, abs=0.1)
        assert analysis["0.80-0.90"]["total_pnl"] == 600.0
    
    def test_multiple_buckets(self):
        """Test analysis with trades across multiple buckets."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"entry_confidence": 0.55, "pnl": 100.0, "return_pct": 0.02},
            {"entry_confidence": 0.65, "pnl": 200.0, "return_pct": 0.04},
            {"entry_confidence": 0.75, "pnl": 300.0, "return_pct": 0.06},
            {"entry_confidence": 0.85, "pnl": 400.0, "return_pct": 0.08},
            {"entry_confidence": 0.95, "pnl": 500.0, "return_pct": 0.10}
        ]
        
        analysis = metrics.get_confidence_bucket_analysis(trades)
        
        assert analysis["0.50-0.60"]["count"] == 1
        assert analysis["0.60-0.70"]["count"] == 1
        assert analysis["0.70-0.80"]["count"] == 1
        assert analysis["0.80-0.90"]["count"] == 1
        assert analysis["0.90-1.00"]["count"] == 1
    
    def test_trades_without_confidence(self):
        """Test analysis with trades missing confidence data."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"entry_confidence": 0.85, "pnl": 500.0, "return_pct": 0.125},
            {"pnl": 300.0, "return_pct": 0.075},  # No confidence
            {"entry_confidence": None, "pnl": 200.0, "return_pct": 0.05}  # None confidence
        ]
        
        analysis = metrics.get_confidence_bucket_analysis(trades)
        
        # Only one trade should be counted
        assert analysis["0.80-0.90"]["count"] == 1


class TestGetSignalAccuracyReport:
    """Test cases for signal accuracy report."""
    
    def test_empty_trades(self):
        """Test report with empty trades."""
        metrics = PortfolioMetrics()
        report = metrics.get_signal_accuracy_report([])
        
        assert report["total_analyzed"] == 0
    
    def test_correct_execution(self):
        """Test report with correct execution trades."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"entry_confidence": 0.85, "pnl": 500.0},
            {"entry_confidence": 0.90, "pnl": 300.0}
        ]
        
        report = metrics.get_signal_accuracy_report(trades)
        
        assert report["total_analyzed"] == 2
        assert report["correct_execution"]["count"] == 2
        assert report["correct_execution"]["pct"] == 100.0
    
    def test_false_positive(self):
        """Test report with false positive trades."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"entry_confidence": 0.85, "pnl": -500.0},
            {"entry_confidence": 0.90, "pnl": -300.0}
        ]
        
        report = metrics.get_signal_accuracy_report(trades)
        
        assert report["total_analyzed"] == 2
        assert report["false_positive"]["count"] == 2
        assert report["false_positive"]["pct"] == 100.0
    
    def test_missed_opportunity(self):
        """Test report with missed opportunity trades."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"entry_confidence": 0.55, "pnl": 500.0},
            {"entry_confidence": 0.60, "pnl": 300.0}
        ]
        
        report = metrics.get_signal_accuracy_report(trades)
        
        assert report["total_analyzed"] == 2
        assert report["missed_opportunity"]["count"] == 2
        assert report["missed_opportunity"]["pct"] == 100.0
    
    def test_correct_avoidance(self):
        """Test report with correct avoidance trades."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"entry_confidence": 0.55, "pnl": -500.0},
            {"entry_confidence": 0.60, "pnl": -300.0}
        ]
        
        report = metrics.get_signal_accuracy_report(trades)
        
        assert report["total_analyzed"] == 2
        assert report["correct_avoidance"]["count"] == 2
        assert report["correct_avoidance"]["pct"] == 100.0
    
    def test_mixed_categories(self):
        """Test report with mixed categories."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"entry_confidence": 0.85, "pnl": 500.0},   # correct_execution
            {"entry_confidence": 0.90, "pnl": -300.0},  # false_positive
            {"entry_confidence": 0.55, "pnl": 200.0},   # missed_opportunity
            {"entry_confidence": 0.60, "pnl": -100.0}   # correct_avoidance
        ]
        
        report = metrics.get_signal_accuracy_report(trades)
        
        assert report["total_analyzed"] == 4
        assert report["correct_execution"]["count"] == 1
        assert report["false_positive"]["count"] == 1
        assert report["missed_opportunity"]["count"] == 1
        assert report["correct_avoidance"]["count"] == 1
    
    def test_custom_threshold(self):
        """Test report with custom confidence threshold."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"entry_confidence": 0.75, "pnl": 500.0}
        ]
        
        # With default threshold (0.70), this is correct_execution
        report1 = metrics.get_signal_accuracy_report(trades, high_conf_threshold=0.70)
        assert report1["correct_execution"]["count"] == 1
        
        # With higher threshold (0.80), this is missed_opportunity
        report2 = metrics.get_signal_accuracy_report(trades, high_conf_threshold=0.80)
        assert report2["missed_opportunity"]["count"] == 1


class TestCalculateSharpeRatio:
    """Test cases for Sharpe ratio calculation."""
    
    def test_empty_ledger(self):
        """Test Sharpe ratio with empty ledger."""
        metrics = PortfolioMetrics()
        sharpe = metrics.calculate_sharpe_ratio([])
        
        assert sharpe == 0.0
    
    def test_single_trade(self):
        """Test Sharpe ratio with single trade."""
        metrics = PortfolioMetrics()
        
        ledger = [{"return_pct": 10.0}]
        
        sharpe = metrics.calculate_sharpe_ratio(ledger)
        
        assert sharpe == 0.0  # Need at least 2 trades
    
    def test_positive_returns(self):
        """Test Sharpe ratio with positive returns."""
        metrics = PortfolioMetrics(risk_free_rate=0.0)
        
        ledger = [
            {"return_pct": 5.0},
            {"return_pct": 10.0},
            {"return_pct": 7.5},
            {"return_pct": 12.0}
        ]
        
        sharpe = metrics.calculate_sharpe_ratio(ledger)
        
        assert sharpe > 0  # Should be positive
    
    def test_negative_returns(self):
        """Test Sharpe ratio with negative returns."""
        metrics = PortfolioMetrics(risk_free_rate=0.0)
        
        ledger = [
            {"return_pct": -5.0},
            {"return_pct": -10.0},
            {"return_pct": -7.5},
            {"return_pct": -12.0}
        ]
        
        sharpe = metrics.calculate_sharpe_ratio(ledger)
        
        assert sharpe < 0  # Should be negative
    
    def test_zero_volatility(self):
        """Test Sharpe ratio with zero volatility."""
        metrics = PortfolioMetrics()
        
        ledger = [
            {"return_pct": 5.0},
            {"return_pct": 5.0},
            {"return_pct": 5.0}
        ]
        
        sharpe = metrics.calculate_sharpe_ratio(ledger)
        
        assert sharpe == 0.0  # Zero std dev


class TestCalculateMaxDrawdown:
    """Test cases for maximum drawdown calculation."""
    
    def test_empty_equity_curve(self):
        """Test max drawdown with empty equity curve."""
        metrics = PortfolioMetrics()
        dd = metrics.calculate_max_drawdown([])
        
        assert dd["max_drawdown"] == 0.0
    
    def test_single_value(self):
        """Test max drawdown with single value."""
        metrics = PortfolioMetrics()
        dd = metrics.calculate_max_drawdown([100000])
        
        assert dd["max_drawdown"] == 0.0
    
    def test_increasing_equity(self):
        """Test max drawdown with only increasing equity."""
        metrics = PortfolioMetrics()
        equity = [100000, 105000, 110000, 115000]
        
        dd = metrics.calculate_max_drawdown(equity)
        
        assert dd["max_drawdown"] == 0.0
    
    def test_simple_drawdown(self):
        """Test max drawdown with simple drawdown."""
        metrics = PortfolioMetrics()
        equity = [100000, 110000, 95000, 105000]
        
        dd = metrics.calculate_max_drawdown(equity)
        
        # Peak: 110000, Trough: 95000
        # Drawdown: (95000 - 110000) / 110000 * 100 = -13.64%
        assert dd["max_drawdown"] == pytest.approx(-13.64, abs=0.01)
        assert dd["peak_value"] == 110000
        assert dd["trough_value"] == 95000
    
    def test_multiple_drawdowns(self):
        """Test max drawdown with multiple drawdowns."""
        metrics = PortfolioMetrics()
        equity = [100000, 110000, 105000, 115000, 90000, 100000]
        
        dd = metrics.calculate_max_drawdown(equity)
        
        # Peak: 115000, Trough: 90000
        # Drawdown: (90000 - 115000) / 115000 * 100 = -21.74%
        assert dd["max_drawdown"] == pytest.approx(-21.74, abs=0.01)
        assert dd["peak_value"] == 115000
        assert dd["trough_value"] == 90000


class TestCalculateWinStreakStats:
    """Test cases for win streak statistics."""
    
    def test_empty_trades(self):
        """Test streak stats with empty trades."""
        metrics = PortfolioMetrics()
        stats = metrics.calculate_win_streak_stats([])
        
        assert stats["max_win_streak"] == 0
        assert stats["max_loss_streak"] == 0
        assert stats["current_streak"] == 0
    
    def test_all_wins(self):
        """Test streak stats with all winning trades."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"pnl": 100.0},
            {"pnl": 200.0},
            {"pnl": 150.0}
        ]
        
        stats = metrics.calculate_win_streak_stats(trades)
        
        assert stats["max_win_streak"] == 3
        assert stats["max_loss_streak"] == 0
        assert stats["current_streak"] == 3
    
    def test_all_losses(self):
        """Test streak stats with all losing trades."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"pnl": -100.0},
            {"pnl": -200.0},
            {"pnl": -150.0}
        ]
        
        stats = metrics.calculate_win_streak_stats(trades)
        
        assert stats["max_win_streak"] == 0
        assert stats["max_loss_streak"] == 3
        assert stats["current_streak"] == -3
    
    def test_alternating_wins_losses(self):
        """Test streak stats with alternating wins and losses."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"pnl": 100.0},
            {"pnl": -50.0},
            {"pnl": 200.0},
            {"pnl": -100.0}
        ]
        
        stats = metrics.calculate_win_streak_stats(trades)
        
        assert stats["max_win_streak"] == 1
        assert stats["max_loss_streak"] == 1
        assert stats["current_streak"] == -1
    
    def test_long_streaks(self):
        """Test streak stats with long streaks."""
        metrics = PortfolioMetrics()
        
        trades = [
            {"pnl": 100.0},
            {"pnl": 200.0},
            {"pnl": 150.0},
            {"pnl": -50.0},
            {"pnl": -100.0},
            {"pnl": -75.0},
            {"pnl": -25.0},
            {"pnl": 300.0}
        ]
        
        stats = metrics.calculate_win_streak_stats(trades)
        
        assert stats["max_win_streak"] == 3
        assert stats["max_loss_streak"] == 4
        assert stats["current_streak"] == 1


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_pnl_trades(self):
        """Test handling trades with zero PnL."""
        metrics = PortfolioMetrics()
        
        ledger = [
            {"net_pnl": 0.0, "commission": 10.0, "return_pct": 0.0, "holding_days": 0.1}
        ]
        
        stats = metrics.get_trade_statistics(ledger)
        
        assert stats["total_trades"] == 1
        assert stats["winning_trades"] == 0
        assert stats["losing_trades"] == 1  # Zero PnL counts as loss
    
    def test_very_large_returns(self):
        """Test handling very large returns."""
        metrics = PortfolioMetrics()
        
        ledger = [
            {"return_pct": 1000.0},
            {"return_pct": 500.0}
        ]
        
        sharpe = metrics.calculate_sharpe_ratio(ledger)
        
        assert isinstance(sharpe, float)
        assert not np.isnan(sharpe)
        assert not np.isinf(sharpe)
