"""
Refactored Portfolio State - Coordinator Pattern.

This module provides a simplified PortfolioState that delegates responsibilities
to specialized components following the Single Responsibility Principle (SRP).

Components:
- PortfolioRepository: Data persistence
- PortfolioValidator: Validation logic
- PortfolioService: Business logic (trade execution)
- PortfolioFormatter: Presentation and reporting
- PortfolioMetrics: Statistical analysis
"""

import os
import logging
from typing import Dict, List, Tuple
from datetime import datetime

from paper_trading.portfolio.portfolio_repository import PortfolioRepository
from paper_trading.portfolio.portfolio_validator import PortfolioValidator
from paper_trading.portfolio.portfolio_service import PortfolioService
from paper_trading.portfolio.portfolio_formatter import PortfolioFormatter
from paper_trading.portfolio.portfolio_metrics import PortfolioMetrics

log = logging.getLogger(__name__)


class PortfolioState:
    """
    Refactored portfolio state manager following the Coordinator pattern.
    
    This class now acts as a thin coordinator that delegates responsibilities
    to specialized components. It maintains backward compatibility with the
    original API while providing a cleaner, more maintainable architecture.
    
    Responsibilities:
    - Initialize and coordinate specialized components
    - Maintain portfolio state (positions, cash, PnL)
    - Provide backward-compatible API
    - Manage stress controls (FAZ 3)
    
    Delegates to:
    - PortfolioRepository: Load/save state
    - PortfolioValidator: Validate trades
    - PortfolioService: Execute trades
    - PortfolioFormatter: Format reports
    - PortfolioMetrics: Calculate statistics
    """
    
    def __init__(
        self,
        initial_capital: float = 100000,
        max_positions: int = 10,
        max_single_exposure: float = 0.10,
        max_total_exposure: float = 0.80,
        state_file: str = "logs/paper_trading/portfolio_state.json",
        # FAZ 3: Live Stress Parameters
        daily_max_loss_pct: float = 0.03,
        consecutive_loss_limit: int = 3,
        exposure_decay_rate: float = 0.20,
    ):
        """Initialize portfolio state and components."""
        # Configuration
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.max_single_exposure = max_single_exposure
        self.max_total_exposure = max_total_exposure
        self.state_file = state_file
        
        # FAZ 3: Live Stress Controls
        self.daily_max_loss_pct = daily_max_loss_pct
        self.consecutive_loss_limit = consecutive_loss_limit
        self.exposure_decay_rate = exposure_decay_rate
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.current_exposure_multiplier = 1.0
        self.trading_halted = False
        self.halt_reason = ""
        
        # State
        self.positions: Dict[str, dict] = {}
        self.cash = initial_capital
        self.realized_pnl = 0.0
        self.trade_history: List[dict] = []
        self.closed_trades: List[dict] = []
        self.peak_equity = initial_capital
        
        # Initialize components
        self.repository = PortfolioRepository(state_file)
        self.validator = PortfolioValidator(
            max_positions=max_positions,
            max_single_exposure=max_single_exposure,
            max_total_exposure=max_total_exposure,
            daily_max_loss_pct=daily_max_loss_pct,
            consecutive_loss_limit=consecutive_loss_limit
        )
        self.service = PortfolioService(self, self.validator)
        self.formatter = PortfolioFormatter()
        self.metrics = PortfolioMetrics()
        
        # Load existing state
        self._load_state()
        
        log.info(f"PortfolioState initialized: capital={initial_capital}, max_pos={max_positions}")
    
    # ─────────────────────────────────────────────────────────────
    # POSITION QUERIES
    # ─────────────────────────────────────────────────────────────
    
    def has_position(self, symbol: str) -> bool:
        """Check if position exists for symbol."""
        return symbol in self.positions and self.positions[symbol]["quantity"] > 0
    
    def position_count(self) -> int:
        """Return number of open positions."""
        return len(self.positions)
    
    # ─────────────────────────────────────────────────────────────
    # EXPOSURE
    # ─────────────────────────────────────────────────────────────
    
    def current_total_exposure(self) -> float:
        """Calculate total exposure across all positions."""
        return sum(
            pos["quantity"] * pos.get("current_price", pos["entry_price"])
            for pos in self.positions.values()
        )
    
    def exposure_ratio(self) -> float:
        """Calculate exposure ratio (exposure / total value)."""
        total = self.total_portfolio_value()
        return self.current_total_exposure() / total if total > 0 else 0.0
    
    def total_portfolio_value(self) -> float:
        """Calculate total portfolio value (cash + positions)."""
        return self.cash + self.current_total_exposure()
    
    @property
    def total_equity(self) -> float:
        """Alias for total_portfolio_value."""
        return self.total_portfolio_value()
    
    # ─────────────────────────────────────────────────────────────
    # VALIDATION (Delegates to PortfolioValidator)
    # ─────────────────────────────────────────────────────────────
    
    def can_open_new_position(self, symbol: str, size_pct: float) -> Tuple[bool, str]:
        """
        Check if new position can be opened.
        Delegates to PortfolioValidator.
        """
        return self.validator.can_open_position(
            symbol=symbol,
            size_pct=size_pct,
            current_positions=self.positions,
            cash=self.cash,
            total_exposure=self.current_total_exposure(),
            total_value=self.total_portfolio_value()
        )
    
    # ─────────────────────────────────────────────────────────────
    # TRADE EXECUTION (Delegates to PortfolioService)
    # ─────────────────────────────────────────────────────────────
    
    def apply_trade_decision(self, decision: dict) -> dict:
        """
        Execute trade decision.
        Delegates to PortfolioService, then saves state.
        """
        result = self.service.apply_trade_decision(decision)
        
        if result["success"]:
            self._save_state()
        
        return result
    
    # Internal trade methods (for backward compatibility)
    def _open_position(self, symbol, price, quantity, side, confidence=None, regime=None):
        """Open position (backward compatibility)."""
        return self.service.open_position(symbol, price, quantity, side, confidence, regime)
    
    def _close_position(self, symbol, price):
        """Close position (backward compatibility)."""
        return self.service.close_position(symbol, price)
    
    def _scale_in(self, symbol, price, quantity):
        """Scale in (backward compatibility)."""
        return self.service.scale_in(symbol, price, quantity)
    
    def _scale_out(self, symbol, price, pct):
        """Scale out (backward compatibility)."""
        return self.service.scale_out(symbol, price, pct)
    
    # ─────────────────────────────────────────────────────────────
    # HELPER METHODS (for PositionEngine compatibility)
    # ─────────────────────────────────────────────────────────────
    
    def current_weight(self, symbol: str) -> float:
        """Return current portfolio weight of a symbol."""
        if symbol not in self.positions:
            return 0.0
        pos = self.positions[symbol]
        position_value = pos["quantity"] * pos.get("current_price", pos["entry_price"])
        total_value = self.total_portfolio_value()
        return position_value / total_value if total_value > 0 else 0.0
    
    def open_or_add(self, symbol: str, quantity: float, price: float):
        """Open new position or add to existing."""
        if symbol in self.positions:
            self._scale_in(symbol, price, quantity)
        else:
            self._open_position(symbol, price, quantity, "LONG")
    
    def reduce_position(self, symbol: str, reduce_pct: float, price: float):
        """Reduce position by percentage."""
        self._scale_out(symbol, price, reduce_pct)
    
    def close_position(self, symbol: str, price: float):
        """Close position completely."""
        self._close_position(symbol, price)
    
    def get_open_symbols(self) -> list:
        """Return list of symbols with open positions."""
        return list(self.positions.keys())
    
    def get_last_price(self, symbol: str) -> float:
        """Get last known price for symbol."""
        if symbol in self.positions:
            return self.positions[symbol].get("current_price", self.positions[symbol]["entry_price"])
        return 0.0
    
    @classmethod
    def load(cls, state_file: str = "logs/paper_trading/portfolio_state.json"):
        """Load portfolio state from file."""
        instance = cls(state_file=state_file)
        return instance
    
    def save(self):
        """Save portfolio state to file."""
        self._save_state()
    
    # ─────────────────────────────────────────────────────────────
    # PERSISTENCE (Delegates to PortfolioRepository)
    # ─────────────────────────────────────────────────────────────
    
    def _load_state(self):
        """Load state from file using repository."""
        state = self.repository.load()
        
        # Handle case where state file doesn't exist (returns None)
        if state is None:
            state = {}
        
        self.positions = state.get("positions", {})
        self.cash = state.get("cash", self.initial_capital)
        self.realized_pnl = state.get("realized_pnl", 0.0)
        self.trade_history = state.get("trade_history", [])
        self.closed_trades = state.get("closed_trades", [])
        self.peak_equity = state.get("peak_equity", self.initial_capital)
    
    def _save_state(self):
        """Save state to file using repository."""
        state = {
            "positions": self.positions,
            "cash": self.cash,
            "realized_pnl": self.realized_pnl,
            "trade_history": self.trade_history,
            "closed_trades": self.closed_trades,
            "peak_equity": self.peak_equity,
        }
        self.repository.save(state)
    
    # ─────────────────────────────────────────────────────────────
    # TRADE LEDGER & STATISTICS (Delegates to Formatter & Metrics)
    # ─────────────────────────────────────────────────────────────
    
    def get_trade_ledger(self) -> List[dict]:
        """Get normalized trade ledger. Delegates to PortfolioFormatter."""
        return self.formatter.get_trade_ledger(self.closed_trades)
    
    def export_trade_ledger_csv(self, filepath: str = None) -> str:
        """Export trade ledger to CSV. Delegates to PortfolioFormatter."""
        return self.formatter.export_trade_ledger_csv(self.closed_trades, filepath)
    
    def get_trade_statistics(self) -> dict:
        """Get trade statistics. Delegates to PortfolioMetrics."""
        ledger = self.get_trade_ledger()
        return self.metrics.get_trade_statistics(ledger)
    
    # ─────────────────────────────────────────────────────────────
    # CONFIDENCE ANALYSIS (Delegates to PortfolioMetrics)
    # ─────────────────────────────────────────────────────────────
    
    def get_confidence_bucket_analysis(self) -> dict:
        """Get confidence bucket analysis. Delegates to PortfolioMetrics."""
        return self.metrics.get_confidence_bucket_analysis(self.closed_trades)
    
    def get_signal_accuracy_report(self) -> dict:
        """Get signal accuracy report. Delegates to PortfolioMetrics."""
        return self.metrics.get_signal_accuracy_report(self.closed_trades)
    
    def print_confidence_analysis(self):
        """Print confidence analysis. Delegates to PortfolioFormatter."""
        bucket_analysis = self.get_confidence_bucket_analysis()
        signal_report = self.get_signal_accuracy_report()
        
        formatted = self.formatter.format_confidence_analysis(bucket_analysis, signal_report)
        for line in formatted.split("\n"):
            log.info(line)
    
    # ─────────────────────────────────────────────────────────────
    # LIVE STRESS SIMULATION (FAZ 3)
    # ─────────────────────────────────────────────────────────────
    
    def check_stress_limits(self) -> Tuple[bool, str]:
        """
        Check if trading should be halted due to stress limits.
        Delegates to PortfolioValidator.
        """
        return self.validator.check_stress_limits(
            daily_pnl=self.daily_pnl,
            consecutive_losses=self.consecutive_losses,
            initial_capital=self.initial_capital
        )
    
    def update_stress_state(self, trade_pnl: float):
        """Update stress tracking after each closed trade."""
        self.daily_pnl += trade_pnl
        
        if trade_pnl < 0:
            self.consecutive_losses += 1
            self._apply_exposure_decay()
        else:
            self.consecutive_losses = 0
            self._restore_exposure()
        
        can_trade, reason = self.check_stress_limits()
        if not can_trade:
            self.trading_halted = True
            self.halt_reason = reason
    
    def _apply_exposure_decay(self):
        """Reduce exposure multiplier after each loss."""
        new_multiplier = self.current_exposure_multiplier * (1 - self.exposure_decay_rate)
        self.current_exposure_multiplier = max(0.20, new_multiplier)
    
    def _restore_exposure(self):
        """Gradually restore exposure after wins."""
        new_multiplier = self.current_exposure_multiplier + 0.10
        self.current_exposure_multiplier = min(1.0, new_multiplier)
    
    def get_effective_max_exposure(self) -> float:
        """Get current max exposure after decay adjustment."""
        return self.max_total_exposure * self.current_exposure_multiplier
    
    def reset_daily_stress(self):
        """Reset daily stress counters."""
        self.daily_pnl = 0.0
        self.trading_halted = False
        self.halt_reason = ""
    
    def reset_all_stress(self):
        """Full stress reset."""
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.current_exposure_multiplier = 1.0
        self.trading_halted = False
        self.halt_reason = ""
    
    def get_stress_status(self) -> dict:
        """Get current stress status summary."""
        return {
            "trading_halted": self.trading_halted,
            "halt_reason": self.halt_reason,
            "daily_pnl": round(self.daily_pnl, 2),
            "daily_pnl_pct": round(self.daily_pnl / self.initial_capital * 100, 2),
            "consecutive_losses": self.consecutive_losses,
            "exposure_multiplier": round(self.current_exposure_multiplier, 2),
            "effective_max_exposure": round(self.get_effective_max_exposure() * 100, 1),
            "daily_max_loss_remaining": round((self.daily_max_loss_pct * self.initial_capital + self.daily_pnl), 2)
        }
    
    def print_stress_status(self):
        """Print stress status. Delegates to PortfolioFormatter."""
        status = self.get_stress_status()
        formatted = self.formatter.format_stress_status(status)
        for line in formatted.split("\n"):
            log.info(line)
