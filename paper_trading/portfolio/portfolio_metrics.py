"""
Portfolio metrics and statistical analysis.

This module handles portfolio performance metrics and analytics.
Follows the Metrics pattern to separate statistical calculations from business logic.
"""

import logging
from typing import List, Dict
import numpy as np

logger = logging.getLogger(__name__)


class PortfolioMetrics:
    """
    Handles portfolio performance metrics and analytics.
    
    Responsibilities:
    - Calculate trade statistics (win rate, profit factor, etc.)
    - Analyze confidence bucket performance
    - Generate signal accuracy reports
    - Calculate Sharpe ratio
    - Compute risk-adjusted returns
    
    This class follows the Metrics pattern, focusing on statistical
    calculations without modifying state or executing business logic.
    """
    
    def __init__(self, risk_free_rate: float = 0.0):
        """
        Initialize metrics calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio (default: 0%)
        """
        self.risk_free_rate = risk_free_rate
        logger.info(f"PortfolioMetrics initialized: risk_free_rate={risk_free_rate}")
    
    def get_trade_statistics(self, trade_ledger: List[dict]) -> dict:
        """
        Calculate summary statistics from trade ledger.
        
        Args:
            trade_ledger: List of normalized trade dictionaries
        
        Returns:
            Dictionary with statistics:
                - total_trades: Total number of trades
                - winning_trades: Number of winning trades
                - losing_trades: Number of losing trades
                - win_rate: Win rate percentage
                - total_pnl: Total net PnL
                - total_commission: Total commission paid
                - avg_return_pct: Average return percentage
                - avg_holding_days: Average holding period
                - avg_win: Average winning trade PnL
                - avg_loss: Average losing trade PnL
                - profit_factor: Ratio of gross profit to gross loss
        """
        if not trade_ledger:
            return {"total_trades": 0}
        
        total_trades = len(trade_ledger)
        winning_trades = [t for t in trade_ledger if t["net_pnl"] > 0]
        losing_trades = [t for t in trade_ledger if t["net_pnl"] <= 0]
        
        # Basic metrics
        total_pnl = sum(t["net_pnl"] for t in trade_ledger)
        total_commission = sum(t["commission"] for t in trade_ledger)
        avg_return = sum(t["return_pct"] for t in trade_ledger) / total_trades
        avg_holding = sum(t["holding_days"] for t in trade_ledger) / total_trades
        
        # Win rate
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        # Average win/loss
        avg_win = sum(t["net_pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t["net_pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t["net_pnl"] for t in winning_trades)
        gross_loss = abs(sum(t["net_pnl"] for t in losing_trades))
        
        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        else:
            profit_factor = float('inf') if gross_profit > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "total_commission": round(total_commission, 2),
            "avg_return_pct": round(avg_return, 2),
            "avg_holding_days": round(avg_holding, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "∞"
        }
    
    def get_confidence_bucket_analysis(self, closed_trades: List[dict]) -> dict:
        """
        Analyze trade performance by confidence bucket.
        
        Args:
            closed_trades: List of closed trade dictionaries
        
        Returns:
            Dictionary with per-bucket analysis:
                - label: Bucket label
                - count: Number of trades
                - win_rate: Win rate percentage
                - avg_return_pct: Average return percentage
                - total_pnl: Total PnL
        
        Buckets: 0.50-0.60, 0.60-0.70, 0.70-0.80, 0.80-0.90, 0.90-1.00
        """
        buckets = {
            "0.50-0.60": {"trades": [], "label": "Low"},
            "0.60-0.70": {"trades": [], "label": "Medium-Low"},
            "0.70-0.80": {"trades": [], "label": "Medium"},
            "0.80-0.90": {"trades": [], "label": "High"},
            "0.90-1.00": {"trades": [], "label": "Very High"},
        }
        
        # Categorize trades by confidence
        for trade in closed_trades:
            conf = trade.get("entry_confidence")
            if conf is None:
                continue
            
            if 0.50 <= conf < 0.60:
                buckets["0.50-0.60"]["trades"].append(trade)
            elif 0.60 <= conf < 0.70:
                buckets["0.60-0.70"]["trades"].append(trade)
            elif 0.70 <= conf < 0.80:
                buckets["0.70-0.80"]["trades"].append(trade)
            elif 0.80 <= conf < 0.90:
                buckets["0.80-0.90"]["trades"].append(trade)
            elif 0.90 <= conf <= 1.00:
                buckets["0.90-1.00"]["trades"].append(trade)
        
        # Calculate metrics for each bucket
        analysis = {}
        for bucket_name, bucket_data in buckets.items():
            trades = bucket_data["trades"]
            
            if not trades:
                analysis[bucket_name] = {
                    "label": bucket_data["label"],
                    "count": 0,
                    "win_rate": 0,
                    "avg_return_pct": 0,
                    "total_pnl": 0
                }
                continue
            
            winners = [t for t in trades if t.get("pnl", 0) > 0]
            win_rate = len(winners) / len(trades) * 100
            avg_return = sum(t.get("return_pct", 0) for t in trades) / len(trades) * 100
            total_pnl = sum(t.get("pnl", 0) for t in trades)
            
            analysis[bucket_name] = {
                "label": bucket_data["label"],
                "count": len(trades),
                "win_rate": round(win_rate, 1),
                "avg_return_pct": round(avg_return, 2),
                "total_pnl": round(total_pnl, 2)
            }
        
        return analysis
    
    def get_signal_accuracy_report(
        self,
        closed_trades: List[dict],
        high_conf_threshold: float = 0.70
    ) -> dict:
        """
        Analyze signal accuracy and execution quality.
        
        Args:
            closed_trades: List of closed trade dictionaries
            high_conf_threshold: Threshold for high confidence (default: 0.70)
        
        Returns:
            Dictionary with signal accuracy categories:
                - total_analyzed: Total trades analyzed
                - correct_execution: High confidence + profitable
                - false_positive: High confidence + loss (model wrong)
                - missed_opportunity: Low confidence + profitable
                - correct_avoidance: Low confidence + loss
        
        Categories:
        - correct_execution: High confidence + profitable (model right, execution right)
        - false_positive: High confidence + loss (model wrong)
        - missed_opportunity: Low confidence + profitable (should have higher confidence)
        - correct_avoidance: Low confidence + loss (correctly low confidence)
        """
        categories = {
            "correct_execution": [],
            "false_positive": [],
            "missed_opportunity": [],
            "correct_avoidance": []
        }
        
        # Categorize trades
        for trade in closed_trades:
            conf = trade.get("entry_confidence")
            pnl = trade.get("pnl", 0)
            
            if conf is None:
                continue
            
            is_high_conf = conf >= high_conf_threshold
            is_profitable = pnl > 0
            
            if is_high_conf and is_profitable:
                categories["correct_execution"].append(trade)
            elif is_high_conf and not is_profitable:
                categories["false_positive"].append(trade)
            elif not is_high_conf and is_profitable:
                categories["missed_opportunity"].append(trade)
            else:
                categories["correct_avoidance"].append(trade)
        
        total = sum(len(v) for v in categories.values())
        
        return {
            "total_analyzed": total,
            "correct_execution": {
                "count": len(categories["correct_execution"]),
                "pct": round(len(categories["correct_execution"]) / total * 100, 1) if total > 0 else 0,
                "description": "Model doğru, execution doğru"
            },
            "false_positive": {
                "count": len(categories["false_positive"]),
                "pct": round(len(categories["false_positive"]) / total * 100, 1) if total > 0 else 0,
                "description": "Model yanlış (yüksek güven, zarar)"
            },
            "missed_opportunity": {
                "count": len(categories["missed_opportunity"]),
                "pct": round(len(categories["missed_opportunity"]) / total * 100, 1) if total > 0 else 0,
                "description": "Model yetersiz güven vermiş ama karlı"
            },
            "correct_avoidance": {
                "count": len(categories["correct_avoidance"]),
                "pct": round(len(categories["correct_avoidance"]) / total * 100, 1) if total > 0 else 0,
                "description": "Düşük güven, düşük sonuç (doğru)"
            }
        }
    
    def calculate_sharpe_ratio(
        self,
        trade_ledger: List[dict],
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sharpe ratio from trade returns.
        
        Args:
            trade_ledger: List of normalized trade dictionaries
            periods_per_year: Number of trading periods per year (default: 252 for daily)
        
        Returns:
            Sharpe ratio (annualized)
        
        Formula: (Mean Return - Risk Free Rate) / Std Dev of Returns * sqrt(periods_per_year)
        """
        if not trade_ledger or len(trade_ledger) < 2:
            return 0.0
        
        # Extract returns as percentages (already in % in ledger)
        returns = [t["return_pct"] / 100 for t in trade_ledger]  # Convert back to decimal
        
        # Calculate mean and std dev
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)  # Sample std dev
        
        if std_return == 0 or np.isclose(std_return, 0):
            return 0.0
        
        # Annualize
        daily_risk_free = self.risk_free_rate / periods_per_year
        sharpe = (mean_return - daily_risk_free) / std_return * np.sqrt(periods_per_year)
        
        return round(sharpe, 2)
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> dict:
        """
        Calculate maximum drawdown from equity curve.
        
        Args:
            equity_curve: List of portfolio values over time
        
        Returns:
            Dictionary with:
                - max_drawdown: Maximum drawdown percentage
                - max_drawdown_value: Maximum drawdown in absolute value
                - peak_value: Peak value before drawdown
                - trough_value: Trough value at maximum drawdown
        """
        if not equity_curve or len(equity_curve) < 2:
            return {
                "max_drawdown": 0.0,
                "max_drawdown_value": 0.0,
                "peak_value": 0.0,
                "trough_value": 0.0
            }
        
        equity_array = np.array(equity_curve)
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(equity_array)
        
        # Calculate drawdown at each point
        drawdown = (equity_array - running_max) / running_max * 100
        
        # Find maximum drawdown
        max_dd_idx = np.argmin(drawdown)
        max_dd = drawdown[max_dd_idx]
        
        # Find peak before maximum drawdown
        peak_idx = np.argmax(running_max[:max_dd_idx + 1] == running_max[max_dd_idx])
        
        return {
            "max_drawdown": round(max_dd, 2),
            "max_drawdown_value": round(equity_array[max_dd_idx] - running_max[max_dd_idx], 2),
            "peak_value": round(running_max[max_dd_idx], 2),
            "trough_value": round(equity_array[max_dd_idx], 2)
        }
    
    def calculate_win_streak_stats(self, closed_trades: List[dict]) -> dict:
        """
        Calculate winning and losing streak statistics.
        
        Args:
            closed_trades: List of closed trade dictionaries
        
        Returns:
            Dictionary with:
                - max_win_streak: Maximum consecutive wins
                - max_loss_streak: Maximum consecutive losses
                - current_streak: Current streak (positive for wins, negative for losses)
        """
        if not closed_trades:
            return {
                "max_win_streak": 0,
                "max_loss_streak": 0,
                "current_streak": 0
            }
        
        max_win_streak = 0
        max_loss_streak = 0
        current_streak = 0
        
        for trade in closed_trades:
            pnl = trade.get("pnl", 0)
            
            if pnl > 0:
                if current_streak >= 0:
                    current_streak += 1
                else:
                    current_streak = 1
                max_win_streak = max(max_win_streak, current_streak)
            else:
                if current_streak <= 0:
                    current_streak -= 1
                else:
                    current_streak = -1
                max_loss_streak = max(max_loss_streak, abs(current_streak))
        
        return {
            "max_win_streak": max_win_streak,
            "max_loss_streak": max_loss_streak,
            "current_streak": current_streak
        }
