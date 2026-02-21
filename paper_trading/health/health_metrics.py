"""
Health Metrics Calculator.

This module handles pure metric calculations for strategy health monitoring.
Follows the Single Responsibility Principle by separating calculation logic
from analysis, validation, and reporting.
"""

from typing import List, Dict
import numpy as np
import logging

logger = logging.getLogger(__name__)


class HealthMetrics:
    """
    Calculates strategy health metrics.
    
    Responsibilities:
    - Calculate win rate from trades
    - Calculate profit factor
    - Calculate Sharpe ratio from equity curve
    - Calculate maximum drawdown
    - Calculate rolling window metrics
    - Calculate expectancy
    
    This class contains pure calculation methods without side effects.
    All methods are stateless and deterministic.
    """
    
    def __init__(self, risk_free_rate: float = 0.0):
        """
        Initialize HealthMetrics calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculation (default: 0.0)
        """
        self.risk_free_rate = risk_free_rate
        logger.info(f"HealthMetrics initialized: risk_free_rate={risk_free_rate}")
    
    def calculate_win_rate(self, trades: List[dict]) -> float:
        """
        Calculate win rate from trades.
        
        Args:
            trades: List of trade dictionaries with 'pnl' field
            
        Returns:
            Win rate as decimal (0.0 to 1.0)
        """
        if not trades:
            return 0.0
        
        winners = [t for t in trades if t.get("pnl", 0) > 0]
        return len(winners) / len(trades)
    
    def calculate_profit_factor(self, trades: List[dict]) -> float:
        """
        Calculate profit factor (gross profit / gross loss).
        
        Args:
            trades: List of trade dictionaries with 'pnl' field
            
        Returns:
            Profit factor (float). Returns inf if no losses.
        """
        if not trades:
            return 0.0
        
        winners = [t for t in trades if t.get("pnl", 0) > 0]
        losers = [t for t in trades if t.get("pnl", 0) <= 0]
        
        gross_profit = sum(t["pnl"] for t in winners) if winners else 0
        gross_loss = abs(sum(t["pnl"] for t in losers)) if losers else 0
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def calculate_sharpe_ratio(self, equity_curve: List[float]) -> float:
        """
        Calculate Sharpe ratio from equity curve.
        
        Args:
            equity_curve: List of equity values over time
            
        Returns:
            Annualized Sharpe ratio
        """
        if len(equity_curve) < 2:
            return 0.0
        
        # Calculate returns
        returns = []
        for i in range(1, len(equity_curve)):
            if equity_curve[i-1] > 0:
                ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
                returns.append(ret)
        
        if not returns:
            return 0.0
        
        returns_arr = np.array(returns)
        
        # Handle zero volatility
        if np.std(returns_arr) == 0 or np.isclose(np.std(returns_arr), 0):
            return 0.0
        
        # Annualized Sharpe ratio (assuming daily returns)
        mean_return = np.mean(returns_arr)
        std_return = np.std(returns_arr)
        sharpe = ((mean_return - self.risk_free_rate / 252) / std_return) * np.sqrt(252)
        
        return sharpe
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """
        Calculate maximum drawdown from equity curve.
        
        Args:
            equity_curve: List of equity values over time
            
        Returns:
            Maximum drawdown as negative decimal (e.g., -0.15 for 15% drawdown)
        """
        if not equity_curve:
            return 0.0
        
        peak = equity_curve[0]
        max_dd = 0.0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            if peak > 0:
                dd = (equity - peak) / peak
                if dd < max_dd:
                    max_dd = dd
        
        return max_dd
    
    def calculate_expectancy(self, trades: List[dict]) -> float:
        """
        Calculate expectancy (average expected profit per trade).
        
        Args:
            trades: List of trade dictionaries with 'pnl' field
            
        Returns:
            Expectancy value
        """
        if not trades:
            return 0.0
        
        win_rate = self.calculate_win_rate(trades)
        
        winners = [t for t in trades if t.get("pnl", 0) > 0]
        losers = [t for t in trades if t.get("pnl", 0) <= 0]
        
        avg_win = np.mean([t["pnl"] for t in winners]) if winners else 0
        avg_loss = abs(np.mean([t["pnl"] for t in losers])) if losers else 0
        
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        return expectancy
    
    def calculate_rolling_metrics(self, trades: List[dict], window: int) -> dict:
        """
        Calculate metrics over a rolling window of trades.
        
        Args:
            trades: List of trade dictionaries
            window: Number of recent trades to analyze
            
        Returns:
            Dictionary with rolling metrics:
                - window: Window size
                - trades: Number of trades in window
                - win_rate: Win rate percentage
                - expectancy: Expectancy value
                - rolling_sharpe: Sharpe ratio (approximation from returns)
                - profit_factor: Profit factor
                - avg_win: Average winning trade
                - avg_loss: Average losing trade
                - total_pnl: Total PnL in window
        """
        if len(trades) < window:
            recent = trades
        else:
            recent = trades[-window:]
        
        if not recent:
            return self._empty_rolling_metrics(window)
        
        # Calculate metrics
        win_rate = self.calculate_win_rate(recent)
        expectancy = self.calculate_expectancy(recent)
        profit_factor = self.calculate_profit_factor(recent)
        
        # Returns for Sharpe approximation
        returns = [t.get("return_pct", 0) for t in recent]
        returns_arr = np.array(returns)
        
        if len(returns_arr) > 1 and np.std(returns_arr) > 0:
            rolling_sharpe = (np.mean(returns_arr) / np.std(returns_arr)) * np.sqrt(252)
        else:
            rolling_sharpe = 0.0
        
        # Average win/loss
        winners = [t for t in recent if t.get("pnl", 0) > 0]
        losers = [t for t in recent if t.get("pnl", 0) <= 0]
        
        avg_win = np.mean([t["pnl"] for t in winners]) if winners else 0
        avg_loss = abs(np.mean([t["pnl"] for t in losers])) if losers else 0
        
        # Total PnL
        total_pnl = sum(t.get("pnl", 0) for t in recent)
        
        return {
            "window": window,
            "trades": len(recent),
            "win_rate": round(win_rate * 100, 1),
            "expectancy": round(expectancy, 2),
            "rolling_sharpe": round(rolling_sharpe, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "∞",
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "total_pnl": round(total_pnl, 2)
        }
    
    def calculate_consecutive_losses(self, trades: List[dict]) -> int:
        """
        Calculate current consecutive losing trades.
        
        Args:
            trades: List of trade dictionaries with 'pnl' field
            
        Returns:
            Number of consecutive losses from most recent trades
        """
        if not trades:
            return 0
        
        consecutive = 0
        for trade in reversed(trades):
            if trade.get("pnl", 0) <= 0:
                consecutive += 1
            else:
                break
        
        return consecutive
    
    def calculate_high_confidence_stats(self, trades: List[dict], 
                                       confidence_threshold: float = 0.70) -> dict:
        """
        Calculate statistics for high confidence trades.
        
        Args:
            trades: List of trade dictionaries with 'entry_confidence' field
            confidence_threshold: Minimum confidence to be considered "high"
            
        Returns:
            Dictionary with:
                - count: Number of high confidence trades
                - win_rate: Win rate percentage for high confidence trades
        """
        high_conf = [t for t in trades if t.get("entry_confidence", 0) >= confidence_threshold]
        
        if not high_conf:
            return {"count": 0, "win_rate": 0.0}
        
        win_rate = self.calculate_win_rate(high_conf)
        
        return {
            "count": len(high_conf),
            "win_rate": round(win_rate * 100, 1)
        }
    
    def _empty_rolling_metrics(self, window: int) -> dict:
        """Return empty rolling metrics structure."""
        return {
            "window": window,
            "trades": 0,
            "win_rate": 0.0,
            "expectancy": 0.0,
            "rolling_sharpe": 0.0,
            "profit_factor": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "total_pnl": 0.0
        }
