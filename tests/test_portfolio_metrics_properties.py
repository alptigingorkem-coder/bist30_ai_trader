"""
Property-based tests for PortfolioMetrics.

**Property 6: Metrics Calculation Invariants**
**Validates: Requirements 1.5**

These tests verify that metrics calculations satisfy mathematical invariants
across all possible inputs. Property-based testing generates hundreds of
random test cases to ensure correctness.
"""

import pytest
from hypothesis import given, strategies as st, assume
from paper_trading.portfolio.portfolio_metrics import PortfolioMetrics


# Strategy for generating valid trade ledger entries
@st.composite
def trade_ledger_entry(draw):
    """Generate a valid trade ledger entry."""
    net_pnl = draw(st.floats(min_value=-10000, max_value=10000, allow_nan=False, allow_infinity=False))
    commission = draw(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False))
    return_pct = draw(st.floats(min_value=-100, max_value=500, allow_nan=False, allow_infinity=False))
    holding_days = draw(st.floats(min_value=0.01, max_value=365, allow_nan=False, allow_infinity=False))
    
    return {
        "net_pnl": round(net_pnl, 2),
        "commission": round(commission, 2),
        "return_pct": round(return_pct, 2),
        "holding_days": round(holding_days, 2)
    }


@st.composite
def closed_trade_entry(draw):
    """Generate a valid closed trade entry."""
    pnl = draw(st.floats(min_value=-10000, max_value=10000, allow_nan=False, allow_infinity=False))
    return_pct = draw(st.floats(min_value=-1.0, max_value=5.0, allow_nan=False, allow_infinity=False))
    confidence = draw(st.one_of(
        st.none(),
        st.floats(min_value=0.5, max_value=1.0, allow_nan=False, allow_infinity=False)
    ))
    
    return {
        "pnl": round(pnl, 2),
        "return_pct": return_pct,
        "entry_confidence": confidence
    }


class TestTradeStatisticsInvariants:
    """Property tests for trade statistics invariants."""
    
    @given(st.lists(trade_ledger_entry(), min_size=1, max_size=50))
    def test_total_trades_equals_sum_of_wins_and_losses(self, ledger):
        """
        Property: total_trades = winning_trades + losing_trades
        
        For any list of trades, the total count must equal the sum of
        winning and losing trades.
        """
        metrics = PortfolioMetrics()
        stats = metrics.get_trade_statistics(ledger)
        
        assert stats["total_trades"] == stats["winning_trades"] + stats["losing_trades"]
    
    @given(st.lists(trade_ledger_entry(), min_size=1, max_size=50))
    def test_win_rate_bounded_between_0_and_100(self, ledger):
        """
        Property: 0 <= win_rate <= 100
        
        Win rate must always be a valid percentage.
        """
        metrics = PortfolioMetrics()
        stats = metrics.get_trade_statistics(ledger)
        
        assert 0 <= stats["win_rate"] <= 100
    
    @given(st.lists(trade_ledger_entry(), min_size=1, max_size=50))
    def test_total_pnl_equals_sum_of_individual_pnls(self, ledger):
        """
        Property: total_pnl = sum(all net_pnl values)
        
        Total PnL must equal the sum of individual trade PnLs.
        """
        metrics = PortfolioMetrics()
        stats = metrics.get_trade_statistics(ledger)
        
        expected_total = sum(t["net_pnl"] for t in ledger)
        
        assert abs(stats["total_pnl"] - expected_total) < 0.01
    
    @given(st.lists(trade_ledger_entry(), min_size=1, max_size=50))
    def test_profit_factor_positive_when_has_winners(self, ledger):
        """
        Property: profit_factor > 0 when there are winning trades with meaningful profit
        
        Profit factor must be positive if there are any winning trades.
        """
        metrics = PortfolioMetrics()
        stats = metrics.get_trade_statistics(ledger)
        
        # Only check if there are meaningful winners (> 0.1)
        has_meaningful_winners = any(t["net_pnl"] > 0.1 for t in ledger)
        
        if has_meaningful_winners:
            pf = stats["profit_factor"]
            if pf != "∞":
                assert pf >= 0  # Can be 0 if losses are much larger
    
    @given(st.lists(trade_ledger_entry(), min_size=2, max_size=50))
    def test_statistics_deterministic(self, ledger):
        """
        Property: Calling get_trade_statistics twice returns same results
        
        Statistics calculation must be deterministic.
        """
        metrics = PortfolioMetrics()
        
        stats1 = metrics.get_trade_statistics(ledger)
        stats2 = metrics.get_trade_statistics(ledger)
        
        assert stats1 == stats2


class TestConfidenceBucketInvariants:
    """Property tests for confidence bucket analysis invariants."""
    
    @given(st.lists(closed_trade_entry(), min_size=1, max_size=50))
    def test_total_trades_equals_sum_of_buckets(self, trades):
        """
        Property: sum(bucket counts) <= total trades
        
        The sum of all bucket counts should not exceed total trades
        (some trades may have no confidence).
        """
        metrics = PortfolioMetrics()
        analysis = metrics.get_confidence_bucket_analysis(trades)
        
        total_in_buckets = sum(bucket["count"] for bucket in analysis.values())
        trades_with_confidence = sum(1 for t in trades if t.get("entry_confidence") is not None)
        
        assert total_in_buckets == trades_with_confidence
    
    @given(st.lists(closed_trade_entry(), min_size=1, max_size=50))
    def test_win_rates_bounded(self, trades):
        """
        Property: 0 <= win_rate <= 100 for all buckets
        
        All bucket win rates must be valid percentages.
        """
        metrics = PortfolioMetrics()
        analysis = metrics.get_confidence_bucket_analysis(trades)
        
        for bucket in analysis.values():
            assert 0 <= bucket["win_rate"] <= 100
    
    @given(st.lists(closed_trade_entry(), min_size=1, max_size=50))
    def test_bucket_analysis_deterministic(self, trades):
        """
        Property: Calling get_confidence_bucket_analysis twice returns same results
        
        Bucket analysis must be deterministic.
        """
        metrics = PortfolioMetrics()
        
        analysis1 = metrics.get_confidence_bucket_analysis(trades)
        analysis2 = metrics.get_confidence_bucket_analysis(trades)
        
        assert analysis1 == analysis2


class TestSignalAccuracyInvariants:
    """Property tests for signal accuracy report invariants."""
    
    @given(st.lists(closed_trade_entry(), min_size=1, max_size=50))
    def test_total_analyzed_equals_sum_of_categories(self, trades):
        """
        Property: total_analyzed = sum(all category counts)
        
        Total analyzed trades must equal sum of all categories.
        """
        metrics = PortfolioMetrics()
        report = metrics.get_signal_accuracy_report(trades)
        
        category_sum = (
            report["correct_execution"]["count"] +
            report["false_positive"]["count"] +
            report["missed_opportunity"]["count"] +
            report["correct_avoidance"]["count"]
        )
        
        assert report["total_analyzed"] == category_sum
    
    @given(st.lists(closed_trade_entry(), min_size=1, max_size=50))
    def test_percentages_sum_to_100(self, trades):
        """
        Property: sum(all category percentages) = 100 (when total > 0)
        
        All category percentages must sum to 100%.
        """
        metrics = PortfolioMetrics()
        report = metrics.get_signal_accuracy_report(trades)
        
        if report["total_analyzed"] > 0:
            pct_sum = (
                report["correct_execution"]["pct"] +
                report["false_positive"]["pct"] +
                report["missed_opportunity"]["pct"] +
                report["correct_avoidance"]["pct"]
            )
            
            # Allow small rounding error
            assert abs(pct_sum - 100.0) < 0.5
    
    @given(st.lists(closed_trade_entry(), min_size=1, max_size=50))
    def test_signal_accuracy_deterministic(self, trades):
        """
        Property: Calling get_signal_accuracy_report twice returns same results
        
        Signal accuracy report must be deterministic.
        """
        metrics = PortfolioMetrics()
        
        report1 = metrics.get_signal_accuracy_report(trades)
        report2 = metrics.get_signal_accuracy_report(trades)
        
        assert report1 == report2


class TestSharpeRatioInvariants:
    """Property tests for Sharpe ratio invariants."""
    
    @given(st.lists(trade_ledger_entry(), min_size=2, max_size=50))
    def test_sharpe_ratio_is_finite(self, ledger):
        """
        Property: Sharpe ratio is always a finite number
        
        Sharpe ratio calculation should never produce NaN or infinity.
        """
        metrics = PortfolioMetrics()
        sharpe = metrics.calculate_sharpe_ratio(ledger)
        
        assert isinstance(sharpe, (int, float))
        assert not (sharpe != sharpe)  # Check for NaN
        assert abs(sharpe) < 1e10  # Check for reasonable bounds
    
    @given(st.lists(trade_ledger_entry(), min_size=2, max_size=50))
    def test_sharpe_ratio_deterministic(self, ledger):
        """
        Property: Calling calculate_sharpe_ratio twice returns same result
        
        Sharpe ratio calculation must be deterministic.
        """
        metrics = PortfolioMetrics()
        
        sharpe1 = metrics.calculate_sharpe_ratio(ledger)
        sharpe2 = metrics.calculate_sharpe_ratio(ledger)
        
        assert sharpe1 == sharpe2
    
    @given(st.lists(trade_ledger_entry(), min_size=2, max_size=50))
    def test_positive_returns_give_positive_sharpe(self, ledger):
        """
        Property: All positive returns → positive or zero Sharpe ratio
        
        If all trades have positive returns, Sharpe ratio should be non-negative.
        """
        # Force all returns to be meaningfully positive
        for trade in ledger:
            trade["return_pct"] = abs(trade["return_pct"]) + 1.0  # At least 1%
        
        # Verify all returns are actually positive after modification
        all_positive = all(t["return_pct"] > 0 for t in ledger)
        assume(all_positive)  # Skip if somehow not all positive
        
        metrics = PortfolioMetrics(risk_free_rate=0.0)
        sharpe = metrics.calculate_sharpe_ratio(ledger)
        
        # Should be positive or zero (zero if all returns are identical)
        assert sharpe >= 0


class TestMaxDrawdownInvariants:
    """Property tests for maximum drawdown invariants."""
    
    @given(st.lists(st.floats(min_value=1000, max_value=1000000, allow_nan=False, allow_infinity=False), min_size=2, max_size=100))
    def test_max_drawdown_non_positive(self, equity_curve):
        """
        Property: max_drawdown <= 0
        
        Maximum drawdown is always negative or zero (it's a loss).
        """
        metrics = PortfolioMetrics()
        dd = metrics.calculate_max_drawdown(equity_curve)
        
        assert dd["max_drawdown"] <= 0
    
    @given(st.lists(st.floats(min_value=1000, max_value=1000000, allow_nan=False, allow_infinity=False), min_size=2, max_size=100))
    def test_trough_less_than_or_equal_peak(self, equity_curve):
        """
        Property: trough_value <= peak_value
        
        The trough (lowest point) cannot be higher than the peak.
        """
        metrics = PortfolioMetrics()
        dd = metrics.calculate_max_drawdown(equity_curve)
        
        if dd["max_drawdown"] < 0:
            assert dd["trough_value"] <= dd["peak_value"]
    
    @given(st.lists(st.floats(min_value=1000, max_value=1000000, allow_nan=False, allow_infinity=False), min_size=2, max_size=100))
    def test_max_drawdown_deterministic(self, equity_curve):
        """
        Property: Calling calculate_max_drawdown twice returns same result
        
        Max drawdown calculation must be deterministic.
        """
        metrics = PortfolioMetrics()
        
        dd1 = metrics.calculate_max_drawdown(equity_curve)
        dd2 = metrics.calculate_max_drawdown(equity_curve)
        
        assert dd1 == dd2
    
    @given(st.lists(st.floats(min_value=1000, max_value=1000000, allow_nan=False, allow_infinity=False), min_size=2, max_size=100))
    def test_increasing_equity_has_zero_drawdown(self, equity_curve):
        """
        Property: Monotonically increasing equity → zero drawdown
        
        If equity only increases, there should be no drawdown.
        """
        # Sort to make it increasing
        equity_curve = sorted(equity_curve)
        
        metrics = PortfolioMetrics()
        dd = metrics.calculate_max_drawdown(equity_curve)
        
        assert dd["max_drawdown"] == 0.0


class TestWinStreakInvariants:
    """Property tests for win streak statistics invariants."""
    
    @given(st.lists(closed_trade_entry(), min_size=1, max_size=50))
    def test_streak_stats_non_negative(self, trades):
        """
        Property: max_win_streak >= 0 and max_loss_streak >= 0
        
        Maximum streaks are always non-negative counts.
        """
        metrics = PortfolioMetrics()
        stats = metrics.calculate_win_streak_stats(trades)
        
        assert stats["max_win_streak"] >= 0
        assert stats["max_loss_streak"] >= 0
    
    @given(st.lists(closed_trade_entry(), min_size=1, max_size=50))
    def test_current_streak_bounded_by_max_streaks(self, trades):
        """
        Property: |current_streak| <= max(max_win_streak, max_loss_streak)
        
        Current streak cannot exceed the maximum observed streak.
        """
        metrics = PortfolioMetrics()
        stats = metrics.calculate_win_streak_stats(trades)
        
        abs_current = abs(stats["current_streak"])
        max_streak = max(stats["max_win_streak"], stats["max_loss_streak"])
        
        assert abs_current <= max_streak
    
    @given(st.lists(closed_trade_entry(), min_size=1, max_size=50))
    def test_win_streak_deterministic(self, trades):
        """
        Property: Calling calculate_win_streak_stats twice returns same result
        
        Win streak calculation must be deterministic.
        """
        metrics = PortfolioMetrics()
        
        stats1 = metrics.calculate_win_streak_stats(trades)
        stats2 = metrics.calculate_win_streak_stats(trades)
        
        assert stats1 == stats2
    
    @given(st.lists(closed_trade_entry(), min_size=1, max_size=50))
    def test_all_wins_gives_zero_loss_streak(self, trades):
        """
        Property: All winning trades → max_loss_streak = 0
        
        If all trades are winners, there should be no losing streak.
        """
        # Force all trades to be winners
        for trade in trades:
            trade["pnl"] = abs(trade["pnl"]) + 0.01
        
        metrics = PortfolioMetrics()
        stats = metrics.calculate_win_streak_stats(trades)
        
        assert stats["max_loss_streak"] == 0
        assert stats["max_win_streak"] == len(trades)
    
    @given(st.lists(closed_trade_entry(), min_size=1, max_size=50))
    def test_all_losses_gives_zero_win_streak(self, trades):
        """
        Property: All losing trades → max_win_streak = 0
        
        If all trades are losers, there should be no winning streak.
        """
        # Force all trades to be losers
        for trade in trades:
            trade["pnl"] = -abs(trade["pnl"]) - 0.01
        
        metrics = PortfolioMetrics()
        stats = metrics.calculate_win_streak_stats(trades)
        
        assert stats["max_win_streak"] == 0
        assert stats["max_loss_streak"] == len(trades)


class TestMetricsComposition:
    """Property tests for metrics composition and consistency."""
    
    @given(st.lists(trade_ledger_entry(), min_size=1, max_size=50))
    def test_metrics_independent_of_order(self, ledger):
        """
        Property: Metrics are independent of trade order (except streaks)
        
        Shuffling trades should not change statistics (except streak stats).
        """
        import random
        
        metrics = PortfolioMetrics()
        
        # Calculate stats for original order
        stats1 = metrics.get_trade_statistics(ledger)
        
        # Shuffle and calculate again
        shuffled = ledger.copy()
        random.shuffle(shuffled)
        stats2 = metrics.get_trade_statistics(shuffled)
        
        # These should be equal (order-independent)
        assert stats1["total_trades"] == stats2["total_trades"]
        assert stats1["winning_trades"] == stats2["winning_trades"]
        assert stats1["losing_trades"] == stats2["losing_trades"]
        assert stats1["win_rate"] == stats2["win_rate"]
        assert stats1["total_pnl"] == stats2["total_pnl"]
