"""
Unit tests for HealthAnalyzer class.

Tests analysis logic for strategy health monitoring.
"""

import pytest
from paper_trading.health.health_analyzer import HealthAnalyzer
from paper_trading.health.health_metrics import HealthMetrics


class TestCalculateHealthScore:
    """Test health score calculation."""
    
    def test_perfect_health(self):
        """Test health score with perfect conditions."""
        analyzer = HealthAnalyzer()
        
        score = analyzer.calculate_health_score(
            trades=[],
            equity_curve=[100000, 105000, 110000],
            regime_changes_today=0,
            current_regime="Trend_Up",
            trading_allowed=True
        )
        
        assert score == 100
    
    def test_regime_instability_penalty(self):
        """Test penalty for regime instability."""
        analyzer = HealthAnalyzer()
        
        score = analyzer.calculate_health_score(
            trades=[],
            equity_curve=[100000],
            regime_changes_today=5,
            current_regime="Trend_Up",
            trading_allowed=True
        )
        
        assert score == 80  # -20 for instability
    
    def test_crisis_regime_penalty(self):
        """Test penalty for crisis regime."""
        analyzer = HealthAnalyzer()
        
        score = analyzer.calculate_health_score(
            trades=[],
            equity_curve=[100000],
            regime_changes_today=0,
            current_regime="CRISIS",
            trading_allowed=True
        )
        
        assert score == 70  # -30 for crisis
    
    def test_trading_disabled_penalty(self):
        """Test penalty when trading is disabled."""
        analyzer = HealthAnalyzer()
        
        score = analyzer.calculate_health_score(
            trades=[],
            equity_curve=[100000],
            regime_changes_today=0,
            current_regime="Trend_Up",
            trading_allowed=False
        )
        
        assert score == 80  # -20 for disabled
    
    def test_drawdown_penalty(self):
        """Test penalty for drawdown."""
        analyzer = HealthAnalyzer()
        
        # 20% drawdown
        equity = [100000, 120000, 96000]
        
        score = analyzer.calculate_health_score(
            trades=[],
            equity_curve=equity,
            regime_changes_today=0,
            current_regime="Trend_Up",
            trading_allowed=True
        )
        
        assert score < 100  # Should have penalty
        assert score >= 80  # ~20% DD = ~20 point penalty


class TestAnalyzeRegimePerformance:
    """Test regime performance analysis."""
    
    def test_empty_trades(self):
        """Test regime analysis with no trades."""
        analyzer = HealthAnalyzer()
        result = analyzer.analyze_regime_performance([])
        
        assert result == {}
    
    def test_single_regime(self):
        """Test regime analysis with single regime."""
        analyzer = HealthAnalyzer()
        trades = [
            {"pnl": 100, "return_pct": 0.01, "regime": "Trend_Up"},
            {"pnl": -50, "return_pct": -0.005, "regime": "Trend_Up"},
            {"pnl": 200, "return_pct": 0.02, "regime": "Trend_Up"}
        ]
        
        result = analyzer.analyze_regime_performance(trades)
        
        assert "Trend_Up" in result
        assert result["Trend_Up"]["trades"] == 3
        assert result["Trend_Up"]["win_rate"] > 60
        assert result["Trend_Up"]["total_pnl"] == 250
    
    def test_multiple_regimes(self):
        """Test regime analysis with multiple regimes."""
        analyzer = HealthAnalyzer()
        trades = [
            {"pnl": 100, "return_pct": 0.01, "regime": "Trend_Up"},
            {"pnl": -50, "return_pct": -0.005, "regime": "Sideways"},
            {"pnl": 200, "return_pct": 0.02, "regime": "Trend_Up"}
        ]
        
        result = analyzer.analyze_regime_performance(trades)
        
        assert "Trend_Up" in result
        assert "Sideways" in result
        assert result["Trend_Up"]["trades"] == 2
        assert result["Sideways"]["trades"] == 1
    
    def test_edge_indicators(self):
        """Test edge indicator assignment."""
        analyzer = HealthAnalyzer()
        
        # Good edge: positive PnL + >50% WR
        good_trades = [
            {"pnl": 100, "return_pct": 0.01, "regime": "Good"},
            {"pnl": 200, "return_pct": 0.02, "regime": "Good"}
        ]
        
        # Warning: positive PnL but <50% WR
        warning_trades = [
            {"pnl": 300, "return_pct": 0.03, "regime": "Warning"},
            {"pnl": -50, "return_pct": -0.005, "regime": "Warning"},
            {"pnl": -100, "return_pct": -0.01, "regime": "Warning"}
        ]
        
        # Bad: negative PnL
        bad_trades = [
            {"pnl": -100, "return_pct": -0.01, "regime": "Bad"},
            {"pnl": -50, "return_pct": -0.005, "regime": "Bad"}
        ]
        
        all_trades = good_trades + warning_trades + bad_trades
        result = analyzer.analyze_regime_performance(all_trades)
        
        assert result["Good"]["edge"] == "✅"
        assert result["Warning"]["edge"] == "⚠️"
        assert result["Bad"]["edge"] == "❌"


class TestDetectDegradation:
    """Test strategy degradation detection."""
    
    def test_insufficient_data(self):
        """Test degradation detection with insufficient data."""
        analyzer = HealthAnalyzer()
        
        recent = [{"pnl": 100, "return_pct": 0.01}] * 10
        historical = [{"pnl": 100, "return_pct": 0.01}] * 50
        
        is_degrading, reason = analyzer.detect_degradation(recent, historical)
        
        assert is_degrading is False
        assert "Insufficient" in reason
    
    def test_no_degradation(self):
        """Test when strategy is not degrading."""
        analyzer = HealthAnalyzer()
        
        # Similar performance
        recent = [{"pnl": 100, "return_pct": 0.01}] * 30
        historical = [{"pnl": 100, "return_pct": 0.01}] * 100
        
        is_degrading, reason = analyzer.detect_degradation(recent, historical)
        
        assert is_degrading is False
    
    def test_win_rate_degradation(self):
        """Test detection of win rate degradation."""
        analyzer = HealthAnalyzer()
        
        # Historical: 80% WR
        historical = [{"pnl": 100, "return_pct": 0.01}] * 80 + \
                    [{"pnl": -50, "return_pct": -0.005}] * 20
        
        # Recent: 50% WR (30% drop)
        recent = [{"pnl": 100, "return_pct": 0.01}] * 15 + \
                [{"pnl": -50, "return_pct": -0.005}] * 15
        
        is_degrading, reason = analyzer.detect_degradation(recent, historical)
        
        assert is_degrading is True
        assert "Win rate drop" in reason


class TestGetRegimeRecommendation:
    """Test regime recommendation logic."""
    
    def test_new_regime(self):
        """Test recommendation for new regime with no data."""
        analyzer = HealthAnalyzer()
        
        result = analyzer.get_regime_recommendation("NewRegime", {})
        
        assert result["should_skip"] is False
        assert "New regime" in result["reason"]
    
    def test_insufficient_trades(self):
        """Test recommendation with insufficient trades."""
        analyzer = HealthAnalyzer()
        
        stats = {
            "trades": 5,
            "win_rate": 60.0,
            "total_pnl": 100
        }
        
        result = analyzer.get_regime_recommendation("TestRegime", stats, min_trades=10)
        
        assert result["should_skip"] is False
        assert "Insufficient data" in result["reason"]
    
    def test_low_win_rate(self):
        """Test recommendation with low win rate."""
        analyzer = HealthAnalyzer()
        
        stats = {
            "trades": 20,
            "win_rate": 30.0,
            "total_pnl": 100
        }
        
        result = analyzer.get_regime_recommendation("TestRegime", stats, min_win_rate=40.0)
        
        assert result["should_skip"] is True
        assert "Low win rate" in result["reason"]
    
    def test_negative_pnl(self):
        """Test recommendation with negative PnL."""
        analyzer = HealthAnalyzer()
        
        stats = {
            "trades": 20,
            "win_rate": 50.0,
            "total_pnl": -500
        }
        
        result = analyzer.get_regime_recommendation("TestRegime", stats)
        
        assert result["should_skip"] is True
        assert "Negative PnL" in result["reason"]
    
    def test_good_regime(self):
        """Test recommendation for good regime."""
        analyzer = HealthAnalyzer()
        
        stats = {
            "trades": 20,
            "win_rate": 60.0,
            "total_pnl": 1000
        }
        
        result = analyzer.get_regime_recommendation("TestRegime", stats)
        
        assert result["should_skip"] is False
        assert "Regime OK" in result["reason"]


class TestShouldSkipRegime:
    """Test should_skip_regime method."""
    
    def test_skip_bad_regime(self):
        """Test skipping bad regime."""
        analyzer = HealthAnalyzer()
        
        regime_performance = {
            "BadRegime": {
                "trades": 20,
                "win_rate": 30.0,
                "total_pnl": -500
            }
        }
        
        should_skip, reason = analyzer.should_skip_regime("BadRegime", regime_performance)
        
        assert should_skip is True
    
    def test_trade_good_regime(self):
        """Test trading in good regime."""
        analyzer = HealthAnalyzer()
        
        regime_performance = {
            "GoodRegime": {
                "trades": 20,
                "win_rate": 60.0,
                "total_pnl": 1000
            }
        }
        
        should_skip, reason = analyzer.should_skip_regime("GoodRegime", regime_performance)
        
        assert should_skip is False
