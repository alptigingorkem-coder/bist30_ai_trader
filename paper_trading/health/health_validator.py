"""
Health Validator.

This module handles validation logic for strategy health monitoring.
Follows the Single Responsibility Principle by separating validation
from calculation, analysis, and reporting.
"""

from typing import Tuple, Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StrategyState(Enum):
    """Strategy state enumeration."""
    ACTIVE = "ACTIVE"          # Fully operational
    DEGRADED = "DEGRADED"      # Warning, under monitoring
    PAUSED = "PAUSED"          # Temporarily stopped
    DISABLED = "DISABLED"      # Completely disabled
    PAPER_ONLY = "PAPER_ONLY"  # Max DD new low - paper trade only


class HealthValidator:
    """
    Validates strategy health against thresholds.
    
    Responsibilities:
    - Check if strategy meets health thresholds
    - Validate invalidation rules
    - Determine if regime should be skipped
    - Manage strategy state transitions
    
    This class contains validation logic without side effects.
    """
    
    # Default invalidation thresholds
    DEFAULT_EXPECTANCY_MIN = 0.0
    DEFAULT_HIGH_CONF_WINRATE_MIN = 0.45
    DEFAULT_MAX_CONSECUTIVE_LOSSES = 7
    DEFAULT_ROLLING_SHARPE_MIN = -0.5
    DEFAULT_MAX_DD_PAPER_ONLY_THRESHOLD = -0.25
    
    def __init__(self, thresholds: Dict = None):
        """
        Initialize HealthValidator with thresholds.
        
        Args:
            thresholds: Dictionary with validation thresholds:
                - expectancy_min: Minimum expectancy (default: 0.0)
                - high_conf_winrate_min: Minimum high-conf win rate (default: 0.45)
                - max_consecutive_losses: Max consecutive losses (default: 7)
                - rolling_sharpe_min: Minimum rolling Sharpe (default: -0.5)
                - max_dd_paper_only: Max DD for paper-only mode (default: -0.25)
                - min_win_rate: Minimum win rate for regime (default: 40.0)
                - min_trades: Minimum trades for regime (default: 10)
        """
        thresholds = thresholds or {}
        
        self.expectancy_min = thresholds.get('expectancy_min', self.DEFAULT_EXPECTANCY_MIN)
        self.high_conf_winrate_min = thresholds.get('high_conf_winrate_min', self.DEFAULT_HIGH_CONF_WINRATE_MIN)
        self.max_consecutive_losses = thresholds.get('max_consecutive_losses', self.DEFAULT_MAX_CONSECUTIVE_LOSSES)
        self.rolling_sharpe_min = thresholds.get('rolling_sharpe_min', self.DEFAULT_ROLLING_SHARPE_MIN)
        self.max_dd_paper_only = thresholds.get('max_dd_paper_only', self.DEFAULT_MAX_DD_PAPER_ONLY_THRESHOLD)
        self.min_win_rate = thresholds.get('min_win_rate', 40.0)
        self.min_trades = thresholds.get('min_trades', 10)
        
        logger.info(
            f"HealthValidator initialized: expectancy_min={self.expectancy_min}, "
            f"high_conf_winrate_min={self.high_conf_winrate_min}, "
            f"max_consecutive_losses={self.max_consecutive_losses}"
        )
    
    def is_healthy(self, metrics: Dict) -> bool:
        """
        Check if strategy meets health thresholds.
        
        Args:
            metrics: Dictionary with health metrics:
                - health_score: Overall health score (0-100)
                
        Returns:
            True if strategy is healthy, False otherwise
        """
        health_score = metrics.get('health_score', 0)
        return health_score > 50
    
    def check_invalidation_rules(self, metrics: Dict) -> Tuple[StrategyState, str]:
        """
        Check if strategy should be invalidated based on hard rules.
        
        Args:
            metrics: Dictionary with metrics:
                - rolling_50: Rolling 50 metrics (expectancy, rolling_sharpe, trades)
                - high_conf_stats: High confidence stats (count, win_rate)
                - consecutive_losses: Number of consecutive losses
                - max_drawdown: Maximum drawdown percentage
                
        Returns:
            Tuple of (new_state, reason)
        """
        rolling_50 = metrics.get('rolling_50', {})
        high_conf_stats = metrics.get('high_conf_stats', {})
        consecutive_losses = metrics.get('consecutive_losses', 0)
        max_drawdown = metrics.get('max_drawdown', 0)
        
        # Rule 1: Expectancy < 0 for last 50 trades → DISABLED
        if rolling_50.get('trades', 0) >= 50:
            expectancy = rolling_50.get('expectancy', 0)
            if expectancy < self.expectancy_min:
                return StrategyState.DISABLED, f"Expectancy < 0 (son 50: {expectancy})"
        
        # Rule 2: High-conf win rate < 45% → DEGRADED
        if high_conf_stats.get('count', 0) >= 20:
            high_conf_wr = high_conf_stats.get('win_rate', 0)
            if high_conf_wr < self.high_conf_winrate_min * 100:
                return StrategyState.DEGRADED, f"High-conf win rate < 45% ({high_conf_wr:.1f}%)"
        
        # Rule 3: Consecutive losses >= 7 → PAUSED
        if consecutive_losses >= self.max_consecutive_losses:
            return StrategyState.PAUSED, f"Ardışık {consecutive_losses} kayıp"
        
        # Rule 4: Rolling Sharpe < -0.5 → DEGRADED
        if rolling_50.get('trades', 0) >= 30:
            rolling_sharpe = rolling_50.get('rolling_sharpe', 0)
            if rolling_sharpe < self.rolling_sharpe_min:
                return StrategyState.DEGRADED, f"Rolling Sharpe < -0.5 ({rolling_sharpe})"
        
        # Rule 5: Max DD new low beyond threshold → PAPER_ONLY
        if max_drawdown < self.max_dd_paper_only * 100:  # Convert to percentage
            return StrategyState.PAPER_ONLY, f"Max DD new low: {max_drawdown:.1f}%"
        
        return StrategyState.ACTIVE, "Tüm kurallar geçti"
    
    def should_skip_regime(self, regime_stats: Dict) -> Tuple[bool, str]:
        """
        Determine if regime should be skipped based on performance.
        
        Args:
            regime_stats: Dictionary with regime statistics:
                - trades: Number of trades
                - win_rate: Win rate percentage
                - total_pnl: Total PnL
                
        Returns:
            Tuple of (should_skip, reason)
        """
        if not regime_stats:
            return False, "No regime data available"
        
        trades = regime_stats.get('trades', 0)
        win_rate = regime_stats.get('win_rate', 0)
        total_pnl = regime_stats.get('total_pnl', 0)
        
        # Not enough data
        if trades < self.min_trades:
            return False, f"Insufficient data: {trades} < {self.min_trades} trades"
        
        # Low win rate
        if win_rate < self.min_win_rate:
            return True, f"Low win rate: {win_rate:.1f}% < {self.min_win_rate}%"
        
        # Negative PnL
        if total_pnl < 0:
            return True, f"Negative PnL: {total_pnl:.2f} TL"
        
        return False, "Regime OK"
    
    def can_trade(self, state: StrategyState) -> bool:
        """
        Check if trading is allowed in current state.
        
        Args:
            state: Current strategy state
            
        Returns:
            True if trading is allowed, False otherwise
        """
        return state in [StrategyState.ACTIVE, StrategyState.DEGRADED, StrategyState.PAPER_ONLY]
    
    def can_live_trade(self, state: StrategyState) -> bool:
        """
        Check if live trading is allowed in current state.
        
        Args:
            state: Current strategy state
            
        Returns:
            True if live trading is allowed, False otherwise
        """
        return state in [StrategyState.ACTIVE, StrategyState.DEGRADED]
    
    def should_reduce_size(self, state: StrategyState) -> bool:
        """
        Check if position size should be reduced.
        
        Args:
            state: Current strategy state
            
        Returns:
            True if size should be reduced, False otherwise
        """
        return state in [StrategyState.DEGRADED, StrategyState.PAPER_ONLY]
