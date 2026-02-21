"""
Health Reporter.

This module handles reporting and formatting for strategy health monitoring.
Follows the Single Responsibility Principle by separating reporting
from calculation, analysis, and validation.
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class HealthReporter:
    """
    Generates strategy health reports.
    
    Responsibilities:
    - Format comprehensive health reports
    - Generate health summaries for API/UI
    - Export health reports to files
    
    This class focuses on presentation and formatting,
    delegating calculations to other components.
    """
    
    def __init__(self):
        """Initialize HealthReporter."""
        logger.info("HealthReporter initialized")
    
    def format_health_report(self, health_data: dict) -> str:
        """
        Format comprehensive health report as string.
        
        Args:
            health_data: Dictionary with health information:
                - state: Strategy state
                - state_reason: Reason for state
                - rolling_windows: Dict of rolling metrics
                - regime_performance: Dict of regime stats
                - consecutive_losses: Number of consecutive losses
                - max_drawdown: Maximum drawdown percentage
                - confidence_threshold: Current confidence threshold
                
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("STRATEGY HEALTH REPORT")
        lines.append("=" * 70)
        
        # State
        state = health_data.get("state", "UNKNOWN")
        state_reason = health_data.get("state_reason", "")
        lines.append(f"State: {state}")
        if state_reason:
            lines.append(f"   Reason: {state_reason}")
        
        # Rolling Windows
        rolling_windows = health_data.get("rolling_windows", {})
        if rolling_windows:
            lines.append("")
            lines.append("Rolling Performance:")
            for window_name, metrics in rolling_windows.items():
                window = metrics.get("window", 0)
                wr = metrics.get("win_rate", 0)
                exp = metrics.get("expectancy", 0)
                sharpe = metrics.get("rolling_sharpe", 0)
                pnl = metrics.get("total_pnl", 0)
                
                lines.append(
                    f"   [{window:3d}] WR: {wr:5.1f}% | "
                    f"Exp: {exp:7.2f} | Sharpe: {sharpe:5.2f} | "
                    f"PnL: {pnl:10.2f}"
                )
        
        # Regime Performance
        regime_perf = health_data.get("regime_performance", {})
        if regime_perf:
            lines.append("")
            lines.append("Regime Performance:")
            for regime, stats in regime_perf.items():
                edge = stats.get("edge", "")
                wr = stats.get("win_rate", 0)
                pnl = stats.get("total_pnl", 0)
                trades = stats.get("trades", 0)
                
                lines.append(
                    f"   {regime:12s} {edge} WR: {wr:5.1f}% | "
                    f"PnL: {pnl:10.2f} ({trades} trades)"
                )
        
        # Additional Metrics
        lines.append("")
        lines.append("Additional Metrics:")
        
        consec = health_data.get("consecutive_losses", 0)
        max_consec = health_data.get("max_consecutive_losses", 7)
        lines.append(f"   Consecutive Losses: {consec} / {max_consec}")
        
        max_dd = health_data.get("max_drawdown", 0)
        lines.append(f"   Max Drawdown: {max_dd:.2f}%")
        
        conf_threshold = health_data.get("confidence_threshold", 0.60)
        lines.append(f"   Confidence Threshold: {conf_threshold:.2f}")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def get_health_summary(self, health_data: dict) -> dict:
        """
        Get summary health data for API/UI.
        
        Args:
            health_data: Dictionary with health information
            
        Returns:
            Compact summary dictionary with key metrics
        """
        # Extract rolling 50 metrics if available
        rolling_50 = {}
        rolling_windows = health_data.get("rolling_windows", {})
        if "window_50" in rolling_windows:
            rolling_50 = rolling_windows["window_50"]
        
        summary = {
            "state": health_data.get("state", "UNKNOWN"),
            "state_reason": health_data.get("state_reason", ""),
            "can_trade": health_data.get("can_trade", False),
            "should_reduce_size": health_data.get("should_reduce_size", False),
            "health_score": health_data.get("health_score", 0),
            "rolling_50": {
                "win_rate": rolling_50.get("win_rate", 0),
                "expectancy": rolling_50.get("expectancy", 0),
                "rolling_sharpe": rolling_50.get("rolling_sharpe", 0),
                "total_pnl": rolling_50.get("total_pnl", 0)
            },
            "consecutive_losses": health_data.get("consecutive_losses", 0),
            "max_drawdown": health_data.get("max_drawdown", 0),
            "confidence_threshold": health_data.get("confidence_threshold", 0.60),
            "paper_only_mode": health_data.get("paper_only_mode", False),
            "total_trades": health_data.get("total_trades", 0)
        }
        
        return summary
    
    def export_health_report(self, health_data: dict, filepath: str) -> None:
        """
        Export health report to file.
        
        Args:
            health_data: Dictionary with health information
            filepath: Path to output file
        """
        report = self.format_health_report(health_data)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info(f"Health report exported to: {filepath}")
    
    def format_regime_summary(self, regime_performance: Dict[str, dict]) -> str:
        """
        Format regime performance summary.
        
        Args:
            regime_performance: Dictionary mapping regime to stats
            
        Returns:
            Formatted regime summary string
        """
        if not regime_performance:
            return "No regime data available"
        
        lines = []
        lines.append("Regime Performance Summary:")
        lines.append("-" * 60)
        
        for regime, stats in regime_performance.items():
            edge = stats.get("edge", "")
            wr = stats.get("win_rate", 0)
            pnl = stats.get("total_pnl", 0)
            trades = stats.get("trades", 0)
            
            lines.append(
                f"{regime:15s} {edge} | WR: {wr:5.1f}% | "
                f"PnL: {pnl:8.2f} | Trades: {trades:3d}"
            )
        
        return "\n".join(lines)
    
    def format_rolling_windows_summary(self, rolling_windows: Dict[str, dict]) -> str:
        """
        Format rolling windows summary.
        
        Args:
            rolling_windows: Dictionary with rolling window metrics
            
        Returns:
            Formatted rolling windows summary string
        """
        if not rolling_windows:
            return "No rolling window data available"
        
        lines = []
        lines.append("Rolling Windows Summary:")
        lines.append("-" * 70)
        lines.append(
            f"{'Window':>8s} | {'Trades':>6s} | {'WR%':>6s} | "
            f"{'Exp':>8s} | {'Sharpe':>7s} | {'PnL':>10s}"
        )
        lines.append("-" * 70)
        
        for window_name in sorted(rolling_windows.keys()):
            metrics = rolling_windows[window_name]
            window = metrics.get("window", 0)
            trades = metrics.get("trades", 0)
            wr = metrics.get("win_rate", 0)
            exp = metrics.get("expectancy", 0)
            sharpe = metrics.get("rolling_sharpe", 0)
            pnl = metrics.get("total_pnl", 0)
            
            lines.append(
                f"{window:8d} | {trades:6d} | {wr:6.1f} | "
                f"{exp:8.2f} | {sharpe:7.2f} | {pnl:10.2f}"
            )
        
        return "\n".join(lines)
