"""
Portfolio formatting and presentation logic.

This module handles formatting portfolio data for display and export.
Follows the Formatter pattern to separate presentation logic from business logic.
"""

import os
import csv
import hashlib
import logging
from typing import List

logger = logging.getLogger(__name__)


class PortfolioFormatter:
    """
    Handles portfolio data formatting and presentation.
    
    Responsibilities:
    - Format trade ledger for display
    - Export trade ledger to CSV
    - Format stress status for display
    - Format confidence analysis for display
    - Generate position summaries
    
    This class follows the Formatter pattern, focusing solely on
    presentation logic without business rules or data manipulation.
    """
    
    def __init__(self, commission_rate: float = 0.0025):
        """
        Initialize formatter with configuration.
        
        Args:
            commission_rate: Commission rate for trades (default: 0.25%)
        """
        self.commission_rate = commission_rate
        logger.info(f"PortfolioFormatter initialized: commission_rate={commission_rate}")
    
    def get_trade_ledger(self, closed_trades: List[dict]) -> List[dict]:
        """
        Return normalized trade ledger with consistent schema.
        
        Args:
            closed_trades: List of closed trade dictionaries
        
        Returns:
            List of normalized trade dictionaries with fields:
                - trade_id: Unique trade identifier
                - symbol: Stock symbol
                - side: "LONG" or "SHORT"
                - entry_price: Entry price
                - exit_price: Exit price
                - quantity: Number of shares
                - gross_pnl: PnL before commission
                - commission: Commission paid
                - net_pnl: PnL after commission
                - return_pct: Return percentage
                - entry_time: Entry timestamp
                - exit_time: Exit timestamp
                - holding_days: Days held
        """
        ledger = []
        
        for trade in closed_trades:
            # Generate unique trade ID
            trade_str = f"{trade.get('symbol', '')}_{trade.get('entry_time', '')}_{trade.get('exit_time', '')}"
            trade_id = hashlib.md5(trade_str.encode()).hexdigest()[:8].upper()
            
            # Calculate holding days
            holding_minutes = trade.get("holding_minutes", 0)
            holding_days = holding_minutes / 1440  # 1440 minutes = 1 day
            
            # Calculate commission
            entry_price = trade.get("entry_price", 0)
            exit_price = trade.get("exit_price", 0)
            quantity = trade.get("quantity", 0)
            commission = (entry_price + exit_price) * quantity * self.commission_rate
            
            # Calculate net PnL
            gross_pnl = trade.get("pnl", 0)
            net_pnl = gross_pnl - commission
            
            ledger.append({
                "trade_id": trade_id,
                "symbol": trade.get("symbol", ""),
                "side": trade.get("side", "LONG"),
                "entry_price": entry_price,
                "exit_price": exit_price,
                "quantity": quantity,
                "gross_pnl": gross_pnl,
                "commission": commission,
                "net_pnl": net_pnl,
                "return_pct": trade.get("return_pct", 0) * 100,  # Convert to %
                "entry_time": trade.get("entry_time", ""),
                "exit_time": trade.get("exit_time", ""),
                "holding_days": round(holding_days, 2)
            })
        
        return ledger
    
    def export_trade_ledger_csv(
        self,
        closed_trades: List[dict],
        filepath: str = None
    ) -> str:
        """
        Export trade ledger to CSV file.
        
        Args:
            closed_trades: List of closed trade dictionaries
            filepath: Output file path (default: logs/paper_trading/trade_ledger.csv)
        
        Returns:
            Path to exported CSV file
        """
        if filepath is None:
            filepath = "logs/paper_trading/trade_ledger.csv"
        
        # Create directory if needed
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Get normalized ledger
        ledger = self.get_trade_ledger(closed_trades)
        
        # Define CSV columns
        fieldnames = [
            "trade_id", "symbol", "side", "entry_price", "exit_price",
            "quantity", "gross_pnl", "commission", "net_pnl", "return_pct",
            "entry_time", "exit_time", "holding_days"
        ]
        
        # Write CSV (even if empty)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            if ledger:
                writer.writerows(ledger)
        
        if not ledger:
            logger.warning("No closed trades to export")
        else:
            logger.info(f"Trade ledger exported: {filepath} ({len(ledger)} trades)")
        
        return filepath
    
    def format_stress_status(self, stress_status: dict) -> str:
        """
        Format stress status for display.
        
        Args:
            stress_status: Dictionary with stress status data
        
        Returns:
            Formatted string for logging/display
        """
        lines = []
        lines.append("=" * 60)
        lines.append("LIVE STRESS STATUS (FAZ 3)")
        lines.append("=" * 60)
        
        # Trading status
        if stress_status.get('trading_halted', False):
            trade_status = f"HALTED - {stress_status.get('halt_reason', 'Unknown')}"
        else:
            trade_status = "ACTIVE"
        lines.append(f"Trading Status: {trade_status}")
        
        # Daily stats
        lines.append("Daily Stats:")
        lines.append(f"   Daily PnL      : {stress_status.get('daily_pnl', 0):10.2f} TL "
                    f"({stress_status.get('daily_pnl_pct', 0):+.2f}%)")
        lines.append(f"   Max Loss Left  : {stress_status.get('daily_max_loss_remaining', 0):10.2f} TL")
        
        # Stress indicators
        lines.append("Stress Indicators:")
        lines.append(f"   Consecutive L  : {stress_status.get('consecutive_losses', 0)} / "
                    f"{stress_status.get('consecutive_loss_limit', 0)}")
        lines.append(f"   Exposure Mult  : {stress_status.get('exposure_multiplier', 1.0) * 100:.0f}%")
        lines.append(f"   Effective Exp  : {stress_status.get('effective_max_exposure', 0):.0f}%")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def format_confidence_analysis(
        self,
        bucket_analysis: dict,
        signal_report: dict
    ) -> str:
        """
        Format confidence bucket analysis for display.
        
        Args:
            bucket_analysis: Dictionary with confidence bucket data
            signal_report: Dictionary with signal accuracy data
        
        Returns:
            Formatted string for logging/display
        """
        lines = []
        lines.append("=" * 60)
        lines.append("CONFIDENCE BUCKET ANALYSIS (FAZ 2)")
        lines.append("=" * 60)
        
        # Performance by confidence level
        lines.append("Performance by Confidence Level:")
        lines.append(f"{'Bucket':<12} {'Count':>6} {'Win%':>8} {'Avg Ret%':>10} {'Total PnL':>12}")
        lines.append("-" * 50)
        
        for bucket, data in bucket_analysis.items():
            lines.append(f"{bucket:<12} {data['count']:>6} {data['win_rate']:>7.1f}% "
                        f"{data['avg_return_pct']:>9.2f}% {data['total_pnl']:>11.2f}")
        
        # Signal accuracy report
        lines.append("Signal Accuracy Report:")
        lines.append("-" * 50)
        
        for key, val in signal_report.items():
            if key == "total_analyzed":
                lines.append(f"Total Analyzed: {val}")
                continue
            lines.append(f"  {key}: {val['count']} ({val['pct']}%) - {val['description']}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def format_position_summary(self, positions: dict, current_prices: dict = None) -> str:
        """
        Format current positions for display.
        
        Args:
            positions: Dictionary of current positions
            current_prices: Optional dictionary of current prices
        
        Returns:
            Formatted string for logging/display
        """
        if not positions:
            return "No open positions"
        
        lines = []
        lines.append("=" * 60)
        lines.append("CURRENT POSITIONS")
        lines.append("=" * 60)
        lines.append(f"{'Symbol':<10} {'Side':<6} {'Qty':>8} {'Entry':>10} {'Current':>10} {'PnL':>10}")
        lines.append("-" * 60)
        
        for symbol, pos in positions.items():
            current_price = current_prices.get(symbol) if current_prices else pos.get("current_price", 0)
            entry_price = pos.get("entry_price", 0)
            quantity = pos.get("quantity", 0)
            side = pos.get("side", "LONG")
            
            # Calculate unrealized PnL
            if side == "LONG":
                pnl = (current_price - entry_price) * quantity
            else:  # SHORT
                pnl = (entry_price - current_price) * quantity
            
            lines.append(f"{symbol:<10} {side:<6} {quantity:>8.0f} {entry_price:>10.2f} "
                        f"{current_price:>10.2f} {pnl:>10.2f}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
