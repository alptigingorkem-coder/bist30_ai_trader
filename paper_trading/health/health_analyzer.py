"""
Health Analyzer.

This module handles analysis logic for strategy health monitoring.
Follows the Single Responsibility Principle by separating analysis
from calculation, validation, and reporting.
"""

from typing import List, Dict, Tuple
import logging

from paper_trading.health.health_metrics import HealthMetrics

logger = logging.getLogger(__name__)


class HealthAnalyzer:
    """
    Analyzes strategy health and trends.
    
    Responsibilities:
    - Calculate overall health score
    - Analyze regime-specific performance
    - Detect strategy degradation
    - Provide regime recommendations
    
    This class uses HealthMetrics for calculations and adds
    higher-level analysis logic.
    """
    
    def __init__(self, metrics: HealthMetrics = None):
        """
        Initialize HealthAnalyzer.
        
        Args:
            metrics: HealthMetrics instance (creates new if None)
        """
        self.metrics = metrics or HealthMetrics()
        logger.info("HealthAnalyzer initialized")
    
    def calculate_health_score(self, trades: List[dict], 
                              equity_curve: List[float],
                              regime_changes_today: int = 0,
                              current_regime: str = "UNKNOWN",
                              trading_allowed: bool = True) -> float:
        """
        Calculate overall health score (0-100).
        
        Args:
            trades: List of trade dictionaries
            equity_curve: Equity curve values
            regime_changes_today: Number of regime changes today
            current_regime: Current market regime
            trading_allowed: Whether trading is currently allowed
            
        Returns:
            Health score from 0 to 100
        """
        score = 100
        
        # Regime instability penalty
        if regime_changes_today > 3:
            score -= 20
            logger.debug(f"Regime instability penalty: {regime_changes_today} changes")
        
        # Crisis/Volatile regime penalty
        crisis_regimes = ['CRISIS', 'VOLATILE', 'Crash_Bear']
        if current_regime in crisis_regimes:
            score -= 30
            logger.debug(f"Crisis regime penalty: {current_regime}")
        
        # Trading disabled penalty
        if not trading_allowed:
            score -= 20
            logger.debug("Trading disabled penalty")
        
        # Drawdown penalty
        if equity_curve:
            max_dd = self.metrics.calculate_max_drawdown(equity_curve)
            if abs(max_dd) > 0.10:
                dd_penalty = int(abs(max_dd) * 100)
                score -= dd_penalty
                logger.debug(f"Drawdown penalty: {dd_penalty} (DD: {max_dd*100:.1f}%)")
        
        # Performance penalty (if enough trades)
        if len(trades) >= 20:
            recent_metrics = self.metrics.calculate_rolling_metrics(trades, 20)
            if recent_metrics["win_rate"] < 40:
                score -= 15
                logger.debug(f"Low win rate penalty: {recent_metrics['win_rate']:.1f}%")
        
        return max(0, score)
    
    def analyze_regime_performance(self, trades: List[dict]) -> Dict[str, dict]:
        """
        Analyze performance by market regime.
        
        Args:
            trades: List of trade dictionaries with 'regime' field
            
        Returns:
            Dictionary mapping regime to performance stats:
                - trades: Number of trades
                - win_rate: Win rate percentage
                - total_pnl: Total PnL
                - avg_return_pct: Average return percentage
                - edge: Visual indicator (✅/⚠️/❌)
        """
        regimes = {}
        
        # Group trades by regime
        for trade in trades:
            regime = trade.get("regime", "Unknown")
            if regime not in regimes:
                regimes[regime] = []
            regimes[regime].append(trade)
        
        # Calculate performance for each regime
        performance = {}
        for regime, regime_trades in regimes.items():
            win_rate = self.metrics.calculate_win_rate(regime_trades)
            total_pnl = sum(t.get("pnl", 0) for t in regime_trades)
            
            returns = [t.get("return_pct", 0) for t in regime_trades]
            avg_return = sum(returns) / len(returns) if returns else 0
            
            # Determine edge indicator
            if total_pnl > 0 and win_rate > 0.50:
                edge = "✅"
            elif total_pnl > 0:
                edge = "⚠️"
            else:
                edge = "❌"
            
            performance[regime] = {
                "trades": len(regime_trades),
                "win_rate": round(win_rate * 100, 1),
                "total_pnl": round(total_pnl, 2),
                "avg_return_pct": round(avg_return * 100, 2),
                "edge": edge
            }
        
        return performance
    
    def detect_degradation(self, recent_trades: List[dict], 
                          historical_trades: List[dict],
                          recent_window: int = 30,
                          historical_window: int = 100) -> Tuple[bool, str]:
        """
        Detect if strategy is degrading by comparing recent vs historical performance.
        
        Args:
            recent_trades: Recent trades to analyze
            historical_trades: Historical trades for comparison
            recent_window: Window size for recent performance
            historical_window: Window size for historical performance
            
        Returns:
            Tuple of (is_degrading, reason)
        """
        if len(recent_trades) < recent_window:
            return False, f"Insufficient recent data ({len(recent_trades)} < {recent_window})"
        
        if len(historical_trades) < historical_window:
            return False, f"Insufficient historical data ({len(historical_trades)} < {historical_window})"
        
        # Calculate recent metrics
        recent_metrics = self.metrics.calculate_rolling_metrics(recent_trades, recent_window)
        
        # Calculate historical metrics
        historical_metrics = self.metrics.calculate_rolling_metrics(historical_trades, historical_window)
        
        # Check for degradation signals
        degradation_signals = []
        
        # Win rate degradation (>10% drop)
        wr_drop = historical_metrics["win_rate"] - recent_metrics["win_rate"]
        if wr_drop > 10:
            degradation_signals.append(f"Win rate drop: {wr_drop:.1f}%")
        
        # Expectancy degradation (negative recent expectancy)
        if recent_metrics["expectancy"] < 0 and historical_metrics["expectancy"] > 0:
            degradation_signals.append(f"Expectancy turned negative: {recent_metrics['expectancy']:.2f}")
        
        # Sharpe degradation (>0.5 drop)
        sharpe_drop = historical_metrics["rolling_sharpe"] - recent_metrics["rolling_sharpe"]
        if sharpe_drop > 0.5:
            degradation_signals.append(f"Sharpe drop: {sharpe_drop:.2f}")
        
        # Profit factor degradation (<1.0 recent)
        if isinstance(recent_metrics["profit_factor"], (int, float)):
            if recent_metrics["profit_factor"] < 1.0 and historical_metrics["profit_factor"] != "∞":
                if isinstance(historical_metrics["profit_factor"], (int, float)):
                    if historical_metrics["profit_factor"] > 1.0:
                        degradation_signals.append(f"Profit factor < 1.0: {recent_metrics['profit_factor']:.2f}")
        
        if degradation_signals:
            reason = "; ".join(degradation_signals)
            logger.warning(f"Strategy degradation detected: {reason}")
            return True, reason
        
        return False, "No degradation detected"
    
    def get_regime_recommendation(self, current_regime: str, 
                                 regime_stats: dict,
                                 min_trades: int = 10,
                                 min_win_rate: float = 40.0) -> dict:
        """
        Recommend whether to trade in current regime.
        
        Args:
            current_regime: Current market regime
            regime_stats: Performance statistics for the regime
            min_trades: Minimum trades required for statistical significance
            min_win_rate: Minimum win rate percentage required
            
        Returns:
            Dictionary with:
                - regime: Regime name
                - should_skip: Whether to skip trading
                - reason: Explanation
                - historical_trades: Number of historical trades
                - historical_win_rate: Historical win rate
                - historical_pnl: Historical PnL
        """
        if not regime_stats:
            return {
                "regime": current_regime,
                "should_skip": False,
                "reason": f"New regime: {current_regime} (no historical data)",
                "historical_trades": 0,
                "historical_win_rate": 0,
                "historical_pnl": 0
            }
        
        trades = regime_stats.get("trades", 0)
        win_rate = regime_stats.get("win_rate", 0)
        total_pnl = regime_stats.get("total_pnl", 0)
        
        # Not enough data
        if trades < min_trades:
            return {
                "regime": current_regime,
                "should_skip": False,
                "reason": f"Insufficient data: {trades} < {min_trades} trades",
                "historical_trades": trades,
                "historical_win_rate": win_rate,
                "historical_pnl": total_pnl
            }
        
        # Low win rate
        if win_rate < min_win_rate:
            return {
                "regime": current_regime,
                "should_skip": True,
                "reason": f"Low win rate: {win_rate:.1f}% < {min_win_rate}%",
                "historical_trades": trades,
                "historical_win_rate": win_rate,
                "historical_pnl": total_pnl
            }
        
        # Negative PnL
        if total_pnl < 0:
            return {
                "regime": current_regime,
                "should_skip": True,
                "reason": f"Negative PnL: {total_pnl:.2f} TL",
                "historical_trades": trades,
                "historical_win_rate": win_rate,
                "historical_pnl": total_pnl
            }
        
        # All checks passed
        return {
            "regime": current_regime,
            "should_skip": False,
            "reason": f"Regime OK: {current_regime}",
            "historical_trades": trades,
            "historical_win_rate": win_rate,
            "historical_pnl": total_pnl
        }
    
    def should_skip_regime(self, current_regime: str, 
                          regime_performance: Dict[str, dict],
                          min_trades: int = 10,
                          min_win_rate: float = 40.0) -> Tuple[bool, str]:
        """
        Determine if trading should be skipped in current regime.
        
        Args:
            current_regime: Current market regime
            regime_performance: Performance stats by regime
            min_trades: Minimum trades for statistical significance
            min_win_rate: Minimum win rate percentage
            
        Returns:
            Tuple of (should_skip, reason)
        """
        recommendation = self.get_regime_recommendation(
            current_regime,
            regime_performance.get(current_regime, {}),
            min_trades,
            min_win_rate
        )
        
        return recommendation["should_skip"], recommendation["reason"]
