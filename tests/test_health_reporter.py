"""
Unit tests for HealthReporter class.

Tests reporting and formatting for strategy health monitoring.
"""

import pytest
import tempfile
import os
from paper_trading.health.health_reporter import HealthReporter


class TestFormatHealthReport:
    """Test health report formatting."""
    
    def test_basic_report(self):
        """Test basic health report formatting."""
        reporter = HealthReporter()
        
        health_data = {
            "state": "ACTIVE",
            "state_reason": "All checks passed",
            "consecutive_losses": 2,
            "max_consecutive_losses": 7,
            "max_drawdown": -5.5,
            "confidence_threshold": 0.65
        }
        
        report = reporter.format_health_report(health_data)
        
        assert "STRATEGY HEALTH REPORT" in report
        assert "ACTIVE" in report
        assert "All checks passed" in report
        assert "2 / 7" in report
        assert "-5.50%" in report
    
    def test_report_with_rolling_windows(self):
        """Test report with rolling window metrics."""
        reporter = HealthReporter()
        
        health_data = {
            "state": "ACTIVE",
            "rolling_windows": {
                "window_50": {
                    "window": 50,
                    "win_rate": 55.5,
                    "expectancy": 125.50,
                    "rolling_sharpe": 1.25,
                    "total_pnl": 5000.00
                }
            }
        }
        
        report = reporter.format_health_report(health_data)
        
        assert "Rolling Performance" in report
        assert "55.5%" in report
        assert "125.50" in report
    
    def test_report_with_regime_performance(self):
        """Test report with regime performance."""
        reporter = HealthReporter()
        
        health_data = {
            "state": "ACTIVE",
            "regime_performance": {
                "Trend_Up": {
                    "edge": "✅",
                    "win_rate": 65.0,
                    "total_pnl": 2500.00,
                    "trades": 20
                }
            }
        }
        
        report = reporter.format_health_report(health_data)
        
        assert "Regime Performance" in report
        assert "Trend_Up" in report
        assert "✅" in report
        assert "65.0%" in report


class TestGetHealthSummary:
    """Test health summary generation."""
    
    def test_basic_summary(self):
        """Test basic health summary."""
        reporter = HealthReporter()
        
        health_data = {
            "state": "ACTIVE",
            "state_reason": "OK",
            "can_trade": True,
            "should_reduce_size": False,
            "health_score": 85,
            "consecutive_losses": 1,
            "max_drawdown": -3.5,
            "confidence_threshold": 0.60,
            "paper_only_mode": False,
            "total_trades": 100
        }
        
        summary = reporter.get_health_summary(health_data)
        
        assert summary["state"] == "ACTIVE"
        assert summary["can_trade"] is True
        assert summary["health_score"] == 85
        assert summary["consecutive_losses"] == 1
        assert summary["max_drawdown"] == -3.5
    
    def test_summary_with_rolling_50(self):
        """Test summary includes rolling 50 metrics."""
        reporter = HealthReporter()
        
        health_data = {
            "state": "ACTIVE",
            "rolling_windows": {
                "window_50": {
                    "win_rate": 55.0,
                    "expectancy": 100.0,
                    "rolling_sharpe": 1.5,
                    "total_pnl": 5000.0
                }
            }
        }
        
        summary = reporter.get_health_summary(health_data)
        
        assert summary["rolling_50"]["win_rate"] == 55.0
        assert summary["rolling_50"]["expectancy"] == 100.0
        assert summary["rolling_50"]["rolling_sharpe"] == 1.5
    
    def test_summary_with_missing_data(self):
        """Test summary handles missing data gracefully."""
        reporter = HealthReporter()
        
        health_data = {}
        
        summary = reporter.get_health_summary(health_data)
        
        assert summary["state"] == "UNKNOWN"
        assert summary["can_trade"] is False
        assert summary["health_score"] == 0


class TestExportHealthReport:
    """Test health report export."""
    
    def test_export_to_file(self):
        """Test exporting health report to file."""
        reporter = HealthReporter()
        
        health_data = {
            "state": "ACTIVE",
            "state_reason": "All good"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "health_report.txt")
            
            reporter.export_health_report(health_data, filepath)
            
            assert os.path.exists(filepath)
            
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            assert "STRATEGY HEALTH REPORT" in content
            assert "ACTIVE" in content


class TestFormatRegimeSummary:
    """Test regime summary formatting."""
    
    def test_empty_regime_performance(self):
        """Test formatting with no regime data."""
        reporter = HealthReporter()
        
        result = reporter.format_regime_summary({})
        
        assert "No regime data" in result
    
    def test_single_regime(self):
        """Test formatting with single regime."""
        reporter = HealthReporter()
        
        regime_perf = {
            "Trend_Up": {
                "edge": "✅",
                "win_rate": 60.0,
                "total_pnl": 1000.0,
                "trades": 15
            }
        }
        
        result = reporter.format_regime_summary(regime_perf)
        
        assert "Trend_Up" in result
        assert "✅" in result
        assert "60.0%" in result
    
    def test_multiple_regimes(self):
        """Test formatting with multiple regimes."""
        reporter = HealthReporter()
        
        regime_perf = {
            "Trend_Up": {"edge": "✅", "win_rate": 60.0, "total_pnl": 1000.0, "trades": 15},
            "Sideways": {"edge": "⚠️", "win_rate": 45.0, "total_pnl": 200.0, "trades": 10}
        }
        
        result = reporter.format_regime_summary(regime_perf)
        
        assert "Trend_Up" in result
        assert "Sideways" in result


class TestFormatRollingWindowsSummary:
    """Test rolling windows summary formatting."""
    
    def test_empty_rolling_windows(self):
        """Test formatting with no rolling window data."""
        reporter = HealthReporter()
        
        result = reporter.format_rolling_windows_summary({})
        
        assert "No rolling window data" in result
    
    def test_single_window(self):
        """Test formatting with single window."""
        reporter = HealthReporter()
        
        rolling_windows = {
            "window_50": {
                "window": 50,
                "trades": 50,
                "win_rate": 55.0,
                "expectancy": 100.0,
                "rolling_sharpe": 1.5,
                "total_pnl": 5000.0
            }
        }
        
        result = reporter.format_rolling_windows_summary(rolling_windows)
        
        assert "Rolling Windows Summary" in result
        assert "50" in result
        assert "55.0" in result
    
    def test_multiple_windows(self):
        """Test formatting with multiple windows."""
        reporter = HealthReporter()
        
        rolling_windows = {
            "window_30": {"window": 30, "trades": 30, "win_rate": 50.0, "expectancy": 80.0, "rolling_sharpe": 1.2, "total_pnl": 2400.0},
            "window_50": {"window": 50, "trades": 50, "win_rate": 55.0, "expectancy": 100.0, "rolling_sharpe": 1.5, "total_pnl": 5000.0}
        }
        
        result = reporter.format_rolling_windows_summary(rolling_windows)
        
        assert "30" in result
        assert "50" in result
