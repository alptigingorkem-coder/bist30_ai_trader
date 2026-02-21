"""
Strategy Health & Kill-Switch Module
Model-bağımsız strateji sağlık izleme ve otomatik durdurma sistemi

Refactored to use specialized components following SRP.
"""

from enum import Enum
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import os

from utils.logging_config import get_logger
import config
from models.regime_detector import RegimeDetector
from paper_trading.health.health_metrics import HealthMetrics
from paper_trading.health.health_analyzer import HealthAnalyzer
from paper_trading.health.health_reporter import HealthReporter
from paper_trading.health.health_validator import HealthValidator, StrategyState

log = get_logger(__name__)


class ConfigWrapper:
    def __init__(self, module): 
        self.module = module
    
    def get(self, name, default=None): 
        return getattr(self.module, name, default)


class StrategyHealth:
    """
    Strategy Health Monitor - Coordinator for health monitoring components.
    
    This class acts as a facade/coordinator, delegating to specialized components:
    - HealthMetrics: Pure metric calculations
    - HealthAnalyzer: Analysis and trend detection
    - HealthReporter: Formatting and reporting
    - HealthValidator: Validation and state management
    
    Features:
    - Rolling performance windows (30/50/100 trades)
    - Regime-specific performance tracking
    - Hard invalidation rules (auto kill-switch)
    - Strategy state machine
    - Max DD tracking with paper-only mode
    - Dynamic confidence threshold adjustment
    - State persistence (save/load)
    """
    
    # Default confidence threshold
    DEFAULT_CONFIDENCE_THRESHOLD = 0.60
    CONFIDENCE_STEP = 0.05  # Each degradation +5%
    
    def __init__(self, closed_trades: List[dict] = None, equity_curve: List[float] = None):
        """
        Initialize StrategyHealth with specialized components.
        
        Args:
            closed_trades: List of closed trade dictionaries
            equity_curve: List of equity values over time
        """
        self.trades = closed_trades or []
        self.equity_curve = equity_curve or []
        
        # Initialize specialized components
        self.metrics = HealthMetrics()
        self.analyzer = HealthAnalyzer(self.metrics)
        self.reporter = HealthReporter()
        self.validator = HealthValidator()
        
        # State management
        self.state = StrategyState.ACTIVE
        self.state_reason = ""
        self.state_history: List[dict] = []
        self.regime_performance: Dict[str, dict] = {}
        
        # Max DD tracking
        self.equity_high_water_mark = 0.0
        self.max_drawdown = 0.0
        self.max_dd_date = None
        self.paper_only_mode = False
        
        # Dynamic confidence threshold
        self.current_confidence_threshold = self.DEFAULT_CONFIDENCE_THRESHOLD
        
        # Calculate initial max DD if equity curve provided
        if self.equity_curve:
            self._calculate_max_drawdown()
        
        # Initialize RegimeDetector
        try:
            self.regime_detector = RegimeDetector(ConfigWrapper(config))
            log.info("✅ RegimeDetector entegre edildi (StrategyHealth)")
        except Exception as e:
            log.warning(f"⚠️ RegimeDetector başlatılamadı: {e}")
            self.regime_detector = None
        
        self.metrics_data = {
            'current_regime': 'UNKNOWN',
            'regime_changes_today': 0,
            'trading_allowed': True,
            'health_score': 100
        }
    
    # ─────────────────────────────────────────────────────────────
    # PUBLIC API - Delegates to components
    # ─────────────────────────────────────────────────────────────
    
    def update_trades(self, trades: List[dict]):
        """Update trade list and evaluate state."""
        self.trades = trades
        self._evaluate_state()
    
    def update(self, market_data):
        """
        Update strategy health with market data.
        
        Args:
            market_data: Market indicators (VIX, SMA, ATR)
        """
        if not self.regime_detector:
            return
        
        # Detect regime
        regime = self.regime_detector.detect_regime(market_data)
        
        # Regime changed?
        if regime != self.metrics_data['current_regime']:
            self.metrics_data['regime_changes_today'] += 1
            log.info(f"🔄 Regime değişti: {self.metrics_data['current_regime']} -> {regime}")
        
        self.metrics_data['current_regime'] = regime
        
        # Trading action
        action = self.regime_detector.get_trading_action(regime)
        self.metrics_data['trading_allowed'] = action['trade']
        self.metrics_data['position_multiplier'] = action['position_multiplier']
        
        # Calculate health score
        self._calculate_health_score()
    
    def is_healthy(self) -> bool:
        """Check if strategy is healthy."""
        return self.validator.is_healthy({'health_score': self.metrics_data.get('health_score', 100)})
    
    def get_rolling_metrics(self, window: int = 50) -> dict:
        """Get rolling metrics for last N trades."""
        return self.metrics.calculate_rolling_metrics(self.trades, window)
    
    def get_all_rolling_windows(self) -> dict:
        """Get metrics for 20, 30, 50, 100 trade windows."""
        return {
            "window_20": self.get_rolling_metrics(20),
            "window_30": self.get_rolling_metrics(30),
            "window_50": self.get_rolling_metrics(50),
            "window_100": self.get_rolling_metrics(100)
        }
    
    def calculate_regime_performance(self) -> dict:
        """Calculate regime-based performance analysis."""
        self.regime_performance = self.analyzer.analyze_regime_performance(self.trades)
        return self.regime_performance
    
    def should_skip_regime(self, current_regime: str, min_trades: int = 10, 
                          min_win_rate: float = 40.0) -> Tuple[bool, str]:
        """
        Check if trading should be skipped in current regime.
        
        Args:
            current_regime: Current market regime
            min_trades: Minimum trades for statistical significance
            min_win_rate: Minimum win rate percentage
            
        Returns:
            (should_skip, reason)
        """
        perf = self.calculate_regime_performance()
        
        if current_regime not in perf:
            return False, f"Yeni rejim: {current_regime}"
        
        return self.analyzer.should_skip_regime(
            current_regime, 
            perf, 
            min_trades, 
            min_win_rate
        )
    
    def get_regime_recommendation(self, current_regime: str) -> dict:
        """Get trading recommendation for specific regime."""
        perf = self.regime_performance.get(current_regime, {})
        return self.analyzer.get_regime_recommendation(current_regime, perf)
    
    def check_invalidation_rules(self) -> Tuple[StrategyState, str]:
        """
        Check hard invalidation rules.
        
        Returns:
            (new_state, reason)
        """
        metrics_50 = self.get_rolling_metrics(50)
        high_conf_stats = self.metrics.calculate_high_confidence_stats(self.trades, 0.70)
        consecutive = self.metrics.calculate_consecutive_losses(self.trades)
        
        validation_metrics = {
            'rolling_50': metrics_50,
            'high_conf_stats': high_conf_stats,
            'consecutive_losses': consecutive,
            'max_drawdown': self.max_drawdown * 100  # Convert to percentage
        }
        
        new_state, reason = self.validator.check_invalidation_rules(validation_metrics)
        
        # Update paper_only_mode flag if state is PAPER_ONLY
        if new_state == StrategyState.PAPER_ONLY:
            self.paper_only_mode = True
        
        return new_state, reason
    
    def get_state(self) -> Tuple[StrategyState, str]:
        """Get current strategy state."""
        return self.state, self.state_reason
    
    def force_state(self, new_state: StrategyState, reason: str):
        """Manually change state."""
        self.state_history.append({
            "from": self.state.value,
            "to": new_state.value,
            "reason": f"MANUAL: {reason}",
            "timestamp": datetime.now().isoformat()
        })
        self.state = new_state
        self.state_reason = reason
    
    def can_trade(self) -> bool:
        """Check if trading is allowed."""
        return self.validator.can_trade(self.state)
    
    def can_live_trade(self) -> bool:
        """Check if live trading is allowed (not PAPER_ONLY)."""
        return self.validator.can_live_trade(self.state)
    
    def is_paper_only_mode(self) -> bool:
        """Check if in paper-only mode."""
        return self.state == StrategyState.PAPER_ONLY or self.paper_only_mode
    
    def should_reduce_size(self) -> bool:
        """Check if position size should be reduced."""
        return self.validator.should_reduce_size(self.state)
    
    def print_health_report(self):
        """Print comprehensive health report."""
        health_data = self._build_health_data()
        report = self.reporter.format_health_report(health_data)
        
        for line in report.split('\n'):
            log.info(line)
    
    def get_health_summary(self) -> dict:
        """Get health summary as dictionary."""
        health_data = self._build_health_data()
        return self.reporter.get_health_summary(health_data)
    
    # ─────────────────────────────────────────────────────────────
    # MAX DRAWDOWN TRACKING
    # ─────────────────────────────────────────────────────────────
    
    def update_equity(self, current_equity: float):
        """
        Update equity curve and recalculate max drawdown.
        
        Args:
            current_equity: Current portfolio value
        """
        self.equity_curve.append(current_equity)
        
        # Update high water mark
        if current_equity > self.equity_high_water_mark:
            self.equity_high_water_mark = current_equity
        
        # Calculate current drawdown
        if self.equity_high_water_mark > 0:
            current_dd = (current_equity - self.equity_high_water_mark) / self.equity_high_water_mark
            
            # Check if new low
            if current_dd < self.max_drawdown:
                self.max_drawdown = current_dd
                self.max_dd_date = datetime.now().isoformat()
                
                # Trigger state evaluation
                self._evaluate_state()
    
    def reset_max_dd_tracking(self):
        """Reset max DD tracking (e.g., start of new evaluation period)."""
        if self.equity_curve:
            self.equity_high_water_mark = self.equity_curve[-1]
        else:
            self.equity_high_water_mark = 0.0
        self.max_drawdown = 0.0
        self.max_dd_date = None
        self.paper_only_mode = False
    
    # ─────────────────────────────────────────────────────────────
    # DYNAMIC CONFIDENCE THRESHOLD
    # ─────────────────────────────────────────────────────────────
    
    def get_recommended_confidence_threshold(self) -> float:
        """
        Get recommended confidence threshold based on recent performance.
        Increases threshold when high-conf trades are underperforming.
        """
        high_conf_stats = self.metrics.calculate_high_confidence_stats(self.trades, 0.70)
        
        # If not enough data, return default
        if high_conf_stats["count"] < 20:
            return self.DEFAULT_CONFIDENCE_THRESHOLD
        
        # Calculate how much below target we are
        target_winrate = self.validator.high_conf_winrate_min * 100  # 45%
        current_winrate = high_conf_stats["win_rate"]
        
        if current_winrate >= target_winrate:
            # Performance OK, can lower threshold gradually
            new_threshold = max(
                self.DEFAULT_CONFIDENCE_THRESHOLD,
                self.current_confidence_threshold - self.CONFIDENCE_STEP
            )
        else:
            # Performance degraded, increase threshold
            gap = (target_winrate - current_winrate) / 100  # % gap
            steps = max(1, int(gap / 0.05))  # +1 step per 5% gap
            new_threshold = min(
                0.90,  # Max threshold
                self.current_confidence_threshold + (self.CONFIDENCE_STEP * steps)
            )
        
        return round(new_threshold, 2)
    
    def update_confidence_threshold(self):
        """Update confidence threshold based on performance."""
        old_threshold = self.current_confidence_threshold
        new_threshold = self.get_recommended_confidence_threshold()
        
        if new_threshold != old_threshold:
            self.current_confidence_threshold = new_threshold
            self.state_history.append({
                "event": "CONFIDENCE_THRESHOLD_CHANGE",
                "from": old_threshold,
                "to": new_threshold,
                "timestamp": datetime.now().isoformat()
            })
        
        return new_threshold
    
    # ─────────────────────────────────────────────────────────────
    # STATE PERSISTENCE
    # ─────────────────────────────────────────────────────────────
    
    def save_state(self, filepath: str = None) -> str:
        """
        Save strategy health state to JSON file.
        
        Args:
            filepath: Path to save file (default: logs/paper_trading/strategy_health_state.json)
            
        Returns:
            Filepath where state was saved
        """
        if filepath is None:
            filepath = "logs/paper_trading/strategy_health_state.json"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        state_data = {
            "state": self.state.value,
            "state_reason": self.state_reason,
            "state_history": self.state_history,
            "regime_performance": self.regime_performance,
            "equity_high_water_mark": self.equity_high_water_mark,
            "max_drawdown": self.max_drawdown,
            "max_dd_date": self.max_dd_date,
            "paper_only_mode": self.paper_only_mode,
            "current_confidence_threshold": self.current_confidence_threshold,
            "total_trades": len(self.trades),
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_state(self, filepath: str = None):
        """
        Load strategy health state from JSON file.
        
        Args:
            filepath: Path to load file (default: logs/paper_trading/strategy_health_state.json)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if filepath is None:
            filepath = "logs/paper_trading/strategy_health_state.json"
        
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, "r", encoding="utf-8") as f:
            state_data = json.load(f)
        
        # Restore state
        state_str = state_data.get("state", "ACTIVE")
        self.state = StrategyState(state_str)
        self.state_reason = state_data.get("state_reason", "")
        self.state_history = state_data.get("state_history", [])
        self.regime_performance = state_data.get("regime_performance", {})
        self.equity_high_water_mark = state_data.get("equity_high_water_mark", 0.0)
        self.max_drawdown = state_data.get("max_drawdown", 0.0)
        self.max_dd_date = state_data.get("max_dd_date")
        self.paper_only_mode = state_data.get("paper_only_mode", False)
        self.current_confidence_threshold = state_data.get(
            "current_confidence_threshold", 
            self.DEFAULT_CONFIDENCE_THRESHOLD
        )
        
        return True
    
    # ─────────────────────────────────────────────────────────────
    # PRIVATE HELPER METHODS
    # ─────────────────────────────────────────────────────────────
    
    def _calculate_health_score(self):
        """Calculate overall health score using analyzer."""
        self.metrics_data['health_score'] = self.analyzer.calculate_health_score(
            self.trades,
            self.equity_curve,
            self.metrics_data.get('regime_changes_today', 0),
            self.metrics_data.get('current_regime', 'UNKNOWN'),
            self.metrics_data.get('trading_allowed', True)
        )
        return self.metrics_data['health_score']
    
    def _evaluate_state(self):
        """Evaluate and update strategy state."""
        new_state, reason = self.check_invalidation_rules()
        
        if new_state != self.state:
            self.state_history.append({
                "from": self.state.value,
                "to": new_state.value,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
            self.state = new_state
            self.state_reason = reason
    
    def _calculate_max_drawdown(self):
        """Calculate max drawdown from equity curve."""
        self.max_drawdown = self.metrics.calculate_max_drawdown(self.equity_curve)
        
        if self.equity_curve:
            self.equity_high_water_mark = max(self.equity_curve)
    
    def _build_health_data(self) -> dict:
        """Build health data dictionary for reporting."""
        return {
            "state": self.state.value,
            "state_reason": self.state_reason,
            "can_trade": self.can_trade(),
            "should_reduce_size": self.should_reduce_size(),
            "health_score": self.metrics_data.get('health_score', 100),
            "rolling_windows": self.get_all_rolling_windows(),
            "regime_performance": self.calculate_regime_performance(),
            "consecutive_losses": self.metrics.calculate_consecutive_losses(self.trades),
            "max_consecutive_losses": self.validator.max_consecutive_losses,
            "max_drawdown": round(self.max_drawdown * 100, 2),
            "confidence_threshold": self.current_confidence_threshold,
            "paper_only_mode": self.paper_only_mode,
            "total_trades": len(self.trades)
        }


# ─────────────────────────────────────────────────────────────
# INTEGRATION HELPER
# ─────────────────────────────────────────────────────────────

def check_strategy_health(portfolio_state, equity_curve: List[float] = None) -> Tuple[bool, str, dict]:
    """
    PortfolioState ile entegre kullanım.
    
    Args:
        portfolio_state: PortfolioState instance
        equity_curve: Optional equity curve
        
    Returns: 
        - can_trade: bool
        - message: str
        - recommendations: dict with position sizing, confidence threshold, etc.
    """
    health = StrategyHealth(portfolio_state.closed_trades, equity_curve)
    
    # Update confidence threshold if enough data
    health.update_confidence_threshold()
    
    can_trade = health.can_trade()
    can_live = health.can_live_trade()
    state, reason = health.get_state()
    
    # Build recommendations
    recommendations = {
        "can_trade": can_trade,
        "can_live_trade": can_live,
        "paper_only_mode": health.is_paper_only_mode(),
        "position_size_multiplier": 0.5 if health.should_reduce_size() else 1.0,
        "confidence_threshold": health.current_confidence_threshold,
        "state": state.value,
        "max_drawdown": round(health.max_drawdown * 100, 2),
        "consecutive_losses": health.metrics.calculate_consecutive_losses(health.trades)
    }
    
    if not can_trade:
        return False, f"Strategy {state.value}: {reason}", recommendations
    
    if health.is_paper_only_mode():
        return True, f"PAPER_ONLY: {reason} - Sadece paper trade", recommendations
    
    if health.should_reduce_size():
        return True, f"DEGRADED: Position size küçültülmeli ({reason})", recommendations
    
    return True, "Strategy ACTIVE", recommendations


def get_strategy_health_monitor(portfolio_state, equity_curve: List[float] = None) -> StrategyHealth:
    """
    StrategyHealth instance döndür - detaylı izleme için.
    
    Args:
        portfolio_state: PortfolioState instance
        equity_curve: Optional equity curve
        
    Returns:
        StrategyHealth instance
    """
    return StrategyHealth(portfolio_state.closed_trades, equity_curve)


if __name__ == "__main__":
    # Demo with sample trades
    log.info("=" * 70)
    log.info("STRATEGY HEALTH DEMO")
    log.info("=" * 70)
    
    # Create sample trades with varying performance
    sample_trades = [
        {"pnl": 500, "return_pct": 0.05, "entry_confidence": 0.75, "regime": "Trend_Up"},
        {"pnl": -200, "return_pct": -0.02, "entry_confidence": 0.68, "regime": "Trend_Up"},
        {"pnl": 300, "return_pct": 0.03, "entry_confidence": 0.72, "regime": "Sideways"},
        {"pnl": -100, "return_pct": -0.01, "entry_confidence": 0.65, "regime": "Volatile"},
        {"pnl": 800, "return_pct": 0.08, "entry_confidence": 0.85, "regime": "Trend_Up"},
    ] * 10  # 50 trades
    
    # Create sample equity curve
    equity = [100000]
    for trade in sample_trades:
        equity.append(equity[-1] + trade["pnl"])
    
    health = StrategyHealth(sample_trades, equity)
    
    # Print full health report
    health.print_health_report()
    
    # Test new features
    log.info("New Features Demo:")
    log.info("-" * 50)
    log.info("Max Drawdown: %.2f%%", health.max_drawdown * 100)
    log.info("High Water Mark: %,.2f", health.equity_high_water_mark)
    
    recommended_conf = health.get_recommended_confidence_threshold()
    log.info("Current Confidence Threshold: %s", health.current_confidence_threshold)
    log.info("Recommended Threshold: %s", recommended_conf)
    
    log.info("Can Trade: %s", health.can_trade())
    log.info("Can Live Trade: %s", health.can_live_trade())
    log.info("Paper Only Mode: %s", health.is_paper_only_mode())
    
    filepath = health.save_state()
    log.info("State saved to: %s", filepath)
    
    health2 = StrategyHealth()
    loaded = health2.load_state()
    log.info("State loaded: %s", loaded)
    log.info("Restored state: %s", health2.state.value)
    
    log.info("=" * 70)
