"""
Position-Aware Paper Trading - Portfolio State Module
Professional-grade portfolio & trade lifecycle tracking
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, Tuple, List


class PortfolioState:
    """
    Stateful portföy yönetimi.
    - Açık pozisyonlar
    - Exposure & risk
    - Event log (trade_history)
    - Backtest trade log (closed_trades)
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        max_positions: int = 10,
        max_single_exposure: float = 0.10,
        max_total_exposure: float = 0.80,
        state_file: str = "paper_trading_position_aware/logs/portfolio_state.json",
        # FAZ 3: Live Stress Parameters
        daily_max_loss_pct: float = 0.03,  # %3 günlük max kayıp
        consecutive_loss_limit: int = 3,   # 3 ardışık kayıp sonrası dur
        exposure_decay_rate: float = 0.20, # Her kayıpta %20 exposure azalt
    ):
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
        self.current_exposure_multiplier = 1.0  # 1.0 = full, 0.5 = half
        self.trading_halted = False
        self.halt_reason = ""

        self.positions: Dict[str, dict] = {}
        self.cash = initial_capital
        self.realized_pnl = 0.0

        # EVENT LOG (decision-level)
        self.trade_history: List[dict] = []

        # BACKTEST LOG (completed trades)
        self.closed_trades: List[dict] = []

        self._load_state()

    # ─────────────────────────────────────────────────────────────
    # POSITION QUERIES
    # ─────────────────────────────────────────────────────────────

    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions and self.positions[symbol]["quantity"] > 0

    def position_count(self) -> int:
        return len(self.positions)

    # ─────────────────────────────────────────────────────────────
    # EXPOSURE
    # ─────────────────────────────────────────────────────────────

    def current_total_exposure(self) -> float:
        return sum(
            pos["quantity"] * pos.get("current_price", pos["entry_price"])
            for pos in self.positions.values()
        )

    def exposure_ratio(self) -> float:
        total = self.cash + self.current_total_exposure()
        return self.current_total_exposure() / total if total > 0 else 0.0

    # ─────────────────────────────────────────────────────────────
    # VALIDATION
    # ─────────────────────────────────────────────────────────────

    def can_open_new_position(self, symbol: str, size_pct: float) -> Tuple[bool, str]:
        if self.has_position(symbol):
            return False, "ALREADY_HAS_POSITION"
        if self.position_count() >= self.max_positions:
            return False, "MAX_POSITIONS_REACHED"
        if size_pct > self.max_single_exposure:
            return False, "EXCEEDS_SINGLE_EXPOSURE"
        if self.exposure_ratio() + size_pct > self.max_total_exposure:
            return False, "EXCEEDS_TOTAL_EXPOSURE"
        if (self.cash + self.current_total_exposure()) * size_pct > self.cash:
            return False, "INSUFFICIENT_CASH"
        return True, "OK"

    # ─────────────────────────────────────────────────────────────
    # TRADE EXECUTION
    # ─────────────────────────────────────────────────────────────

    def apply_trade_decision(self, decision: dict) -> dict:
        action = decision.get("action")
        symbol = decision.get("symbol")
        price = decision.get("price", 0.0)
        quantity = decision.get("quantity", 0.0)

        result = {"success": False, "action": action, "symbol": symbol}

        if action == "OPEN_POSITION":
            result = self._open_position(symbol, price, quantity, decision.get("side", "LONG"))

        elif action == "CLOSE_POSITION":
            result = self._close_position(symbol, price)

        elif action == "SCALE_IN":
            result = self._scale_in(symbol, price, quantity)

        elif action == "SCALE_OUT":
            result = self._scale_out(symbol, price, decision.get("scale_pct", 0.5))

        elif action in ["HOLD_EXISTING", "IGNORE_SIGNAL"]:
            result["success"] = True

        if result["success"]:
            self.trade_history.append(
                {
                    **decision,
                    "timestamp": datetime.now().isoformat(),
                    "execution": result,
                }
            )
            self._save_state()

        return result

    # ─────────────────────────────────────────────────────────────
    # INTERNAL TRADE OPS
    # ─────────────────────────────────────────────────────────────

    def _open_position(self, symbol, price, quantity, side, confidence=None, regime=None):
        cost = price * quantity
        if cost > self.cash:
            return {"success": False, "reason": "INSUFFICIENT_CASH"}

        self.positions[symbol] = {
            "side": side,
            "entry_price": price,
            "quantity": quantity,
            "entry_time": datetime.now().isoformat(),
            "current_price": price,
            "entry_confidence": confidence,  # FAZ 2: Signal confidence at entry
            "entry_regime": regime,  # FAZ 5: Market regime at entry
        }
        self.cash -= cost
        return {"success": True}

    def _close_position(self, symbol, price):
        if symbol not in self.positions:
            return {"success": False, "reason": "NO_POSITION"}

        pos = self.positions[symbol]
        qty = pos["quantity"]
        entry_price = pos["entry_price"]

        pnl = (price - entry_price) * qty if pos["side"] == "LONG" else (entry_price - price) * qty

        self.cash += price * qty
        self.realized_pnl += pnl

        # 🔥 PROFESSIONAL BACKTEST RECORD
        self.closed_trades.append(
            {
                "symbol": symbol,
                "side": pos["side"],
                "entry_price": entry_price,
                "exit_price": price,
                "quantity": qty,
                "pnl": pnl,
                "return_pct": pnl / (entry_price * qty),
                "entry_time": pos["entry_time"],
                "exit_time": datetime.now().isoformat(),
                "holding_minutes": (
                    datetime.now() - datetime.fromisoformat(pos["entry_time"])
                ).total_seconds()
                / 60,
                "entry_confidence": pos.get("entry_confidence"),  # FAZ 2
                "regime": pos.get("entry_regime"),  # FAZ 5: Market regime
            }
        )

        del self.positions[symbol]
        return {"success": True, "realized_pnl": pnl}

    def _scale_in(self, symbol, price, quantity):
        pos = self.positions[symbol]
        total_cost = pos["entry_price"] * pos["quantity"] + price * quantity
        pos["quantity"] += quantity
        pos["entry_price"] = total_cost / pos["quantity"]
        self.cash -= price * quantity
        return {"success": True}

    def _scale_out(self, symbol, price, pct):
        pos = self.positions[symbol]
        qty = pos["quantity"] * pct
        pnl = (price - pos["entry_price"]) * qty
        self.cash += price * qty
        self.realized_pnl += pnl
        pos["quantity"] -= qty
        if pos["quantity"] <= 0:
            del self.positions[symbol]
        return {"success": True, "realized_pnl": pnl}

    # ─────────────────────────────────────────────────────────────
    # HELPER METHODS (for PositionEngine compatibility)
    # ─────────────────────────────────────────────────────────────

    def current_weight(self, symbol: str) -> float:
        """Return current portfolio weight of a symbol"""
        if symbol not in self.positions:
            return 0.0
        pos = self.positions[symbol]
        position_value = pos["quantity"] * pos.get("current_price", pos["entry_price"])
        total_value = self.total_portfolio_value()
        return position_value / total_value if total_value > 0 else 0.0

    def total_portfolio_value(self) -> float:
        """Total portfolio value (cash + positions)"""
        return self.cash + self.current_total_exposure()

    @property
    def total_equity(self) -> float:
        """Alias for total_portfolio_value"""
        return self.total_portfolio_value()

    def open_or_add(self, symbol: str, quantity: float, price: float):
        """Open new position or add to existing"""
        if symbol in self.positions:
            self._scale_in(symbol, price, quantity)
        else:
            self._open_position(symbol, price, quantity, "LONG")

    def reduce_position(self, symbol: str, reduce_pct: float, price: float):
        """Reduce position by percentage"""
        self._scale_out(symbol, price, reduce_pct)

    def close_position(self, symbol: str, price: float):
        """Close position completely"""
        self._close_position(symbol, price)

    def get_open_symbols(self) -> list:
        """Return list of symbols with open positions"""
        return list(self.positions.keys())

    def get_last_price(self, symbol: str) -> float:
        """Get last known price for symbol"""
        if symbol in self.positions:
            return self.positions[symbol].get("current_price", self.positions[symbol]["entry_price"])
        return 0.0

    @classmethod
    def load(cls, state_file: str = "paper_trading_position_aware/logs/portfolio_state.json"):
        """Load portfolio state from file"""
        instance = cls(state_file=state_file)
        return instance

    def save(self):
        """Save portfolio state to file"""
        self._save_state()

    # ─────────────────────────────────────────────────────────────
    # PERSISTENCE
    # ─────────────────────────────────────────────────────────────

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                self.positions = state.get("positions", {})
                self.cash = state.get("cash", self.initial_capital)
                self.realized_pnl = state.get("realized_pnl", 0.0)
                self.trade_history = state.get("trade_history", [])
                self.closed_trades = state.get("closed_trades", [])

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "positions": self.positions,
                    "cash": self.cash,
                    "realized_pnl": self.realized_pnl,
                    "trade_history": self.trade_history,
                    "closed_trades": self.closed_trades,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    # ─────────────────────────────────────────────────────────────
    # TRADE LEDGER (FAZ 1)
    # ─────────────────────────────────────────────────────────────

    def get_trade_ledger(self) -> List[dict]:
        """
        Return normalized trade ledger with consistent schema.
        Each trade includes: trade_id, symbol, side, entry_price, exit_price,
        quantity, gross_pnl, commission, net_pnl, return_pct, entry_time,
        exit_time, holding_days
        """
        import hashlib
        
        ledger = []
        for i, trade in enumerate(self.closed_trades):
            # Generate unique trade ID
            trade_str = f"{trade.get('symbol', '')}_{trade.get('entry_time', '')}_{trade.get('exit_time', '')}"
            trade_id = hashlib.md5(trade_str.encode()).hexdigest()[:8].upper()
            
            # Calculate holding days
            entry_time = trade.get("entry_time", "")
            exit_time = trade.get("exit_time", "")
            holding_minutes = trade.get("holding_minutes", 0)
            holding_days = holding_minutes / 1440  # 1440 minutes = 1 day
            
            # Commission (estimated)
            entry_price = trade.get("entry_price", 0)
            exit_price = trade.get("exit_price", 0)
            quantity = trade.get("quantity", 0)
            commission_rate = 0.0025  # %0.25
            commission = (entry_price + exit_price) * quantity * commission_rate
            
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
                "entry_time": entry_time,
                "exit_time": exit_time,
                "holding_days": round(holding_days, 2)
            })
        
        return ledger

    def export_trade_ledger_csv(self, filepath: str = None) -> str:
        """
        Export trade ledger to CSV file.
        Returns the filepath of the exported CSV.
        """
        import csv
        
        if filepath is None:
            filepath = "paper_trading_position_aware/logs/trade_ledger.csv"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        ledger = self.get_trade_ledger()
        
        if not ledger:
            print("⚠️ No closed trades to export")
            return filepath
        
        fieldnames = [
            "trade_id", "symbol", "side", "entry_price", "exit_price",
            "quantity", "gross_pnl", "commission", "net_pnl", "return_pct",
            "entry_time", "exit_time", "holding_days"
        ]
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(ledger)
        
        print(f"✅ Trade ledger exported: {filepath} ({len(ledger)} trades)")
        return filepath

    def get_trade_statistics(self) -> dict:
        """
        Return summary statistics from trade ledger.
        """
        ledger = self.get_trade_ledger()
        
        if not ledger:
            return {"total_trades": 0}
        
        total_trades = len(ledger)
        winning_trades = [t for t in ledger if t["net_pnl"] > 0]
        losing_trades = [t for t in ledger if t["net_pnl"] <= 0]
        
        total_pnl = sum(t["net_pnl"] for t in ledger)
        total_commission = sum(t["commission"] for t in ledger)
        avg_return = sum(t["return_pct"] for t in ledger) / total_trades
        avg_holding = sum(t["holding_days"] for t in ledger) / total_trades
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        avg_win = sum(t["net_pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t["net_pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        profit_factor = abs(sum(t["net_pnl"] for t in winning_trades) / sum(t["net_pnl"] for t in losing_trades)) if losing_trades and sum(t["net_pnl"] for t in losing_trades) != 0 else float('inf')
        
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

    # ─────────────────────────────────────────────────────────────
    # EXECUTION VS SIGNAL ANALYSIS (FAZ 2)
    # ─────────────────────────────────────────────────────────────

    def get_confidence_bucket_analysis(self) -> dict:
        """
        Analyze trade performance by confidence bucket.
        Buckets: 0.50-0.60, 0.60-0.70, 0.70-0.80, 0.80-0.90, 0.90-1.00
        
        Returns per-bucket: trade count, win rate, avg return, total PnL
        """
        buckets = {
            "0.50-0.60": {"trades": [], "label": "Low"},
            "0.60-0.70": {"trades": [], "label": "Medium-Low"},
            "0.70-0.80": {"trades": [], "label": "Medium"},
            "0.80-0.90": {"trades": [], "label": "High"},
            "0.90-1.00": {"trades": [], "label": "Very High"},
        }
        
        for trade in self.closed_trades:
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

    def get_signal_accuracy_report(self) -> dict:
        """
        Analyze if model signals were correct but execution was wrong.
        
        Categories:
        - correct_execution: High confidence + profitable
        - false_positive: High confidence + loss (model wrong)
        - missed_opportunity: Low confidence + profitable (should have higher confidence)
        - correct_avoidance: Low confidence + loss (correctly low confidence)
        """
        high_conf_threshold = 0.70
        
        categories = {
            "correct_execution": [],
            "false_positive": [],
            "missed_opportunity": [],
            "correct_avoidance": []
        }
        
        for trade in self.closed_trades:
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

    def print_confidence_analysis(self):
        """Pretty print confidence bucket analysis"""
        bucket_analysis = self.get_confidence_bucket_analysis()
        signal_report = self.get_signal_accuracy_report()
        
        print("\n" + "="*60)
        print("📊 CONFIDENCE BUCKET ANALYSIS (FAZ 2)")
        print("="*60)
        
        print("\n🎯 Performance by Confidence Level:")
        print(f"{'Bucket':<12} {'Count':>6} {'Win%':>8} {'Avg Ret%':>10} {'Total PnL':>12}")
        print("-" * 50)
        
        for bucket, data in bucket_analysis.items():
            print(f"{bucket:<12} {data['count']:>6} {data['win_rate']:>7.1f}% {data['avg_return_pct']:>9.2f}% {data['total_pnl']:>11.2f}")
        
        print("\n🔍 Signal Accuracy Report:")
        print("-" * 50)
        for key, val in signal_report.items():
            if key == "total_analyzed":
                print(f"Total Analyzed: {val}")
                continue
            print(f"  {key}: {val['count']} ({val['pct']}%) - {val['description']}")
        
        print("="*60)

    # ─────────────────────────────────────────────────────────────
    # LIVE STRESS SIMULATION (FAZ 3)
    # ─────────────────────────────────────────────────────────────

    def check_stress_limits(self) -> Tuple[bool, str]:
        """
        Check if trading should be halted due to stress limits.
        Returns: (can_trade, halt_reason)
        """
        portfolio_value = self.total_portfolio_value()
        
        # 1. Daily Max Loss Check
        daily_loss_pct = abs(self.daily_pnl) / self.initial_capital if self.daily_pnl < 0 else 0
        if daily_loss_pct >= self.daily_max_loss_pct:
            self.trading_halted = True
            self.halt_reason = f"DAILY_MAX_LOSS ({daily_loss_pct*100:.1f}% > {self.daily_max_loss_pct*100:.1f}%)"
            return False, self.halt_reason
        
        # 2. Consecutive Loss Check
        if self.consecutive_losses >= self.consecutive_loss_limit:
            self.trading_halted = True
            self.halt_reason = f"CONSECUTIVE_LOSSES ({self.consecutive_losses} >= {self.consecutive_loss_limit})"
            return False, self.halt_reason
        
        return True, "OK"

    def update_stress_state(self, trade_pnl: float):
        """
        Update stress tracking after each closed trade.
        Call this after every trade closes.
        """
        # Update daily PnL
        self.daily_pnl += trade_pnl
        
        # Update consecutive loss counter
        if trade_pnl < 0:
            self.consecutive_losses += 1
            # Apply exposure decay
            self._apply_exposure_decay()
        else:
            # Reset consecutive losses on win
            self.consecutive_losses = 0
            # Gradually restore exposure
            self._restore_exposure()
        
        # Check limits
        self.check_stress_limits()

    def _apply_exposure_decay(self):
        """Reduce exposure multiplier after each loss"""
        new_multiplier = self.current_exposure_multiplier * (1 - self.exposure_decay_rate)
        self.current_exposure_multiplier = max(0.20, new_multiplier)  # Minimum %20
        
    def _restore_exposure(self):
        """Gradually restore exposure after wins"""
        new_multiplier = self.current_exposure_multiplier + 0.10  # +%10 per win
        self.current_exposure_multiplier = min(1.0, new_multiplier)  # Max %100

    def get_effective_max_exposure(self) -> float:
        """Get current max exposure after decay adjustment"""
        return self.max_total_exposure * self.current_exposure_multiplier

    def reset_daily_stress(self):
        """Reset daily stress counters (call at start of new trading day)"""
        self.daily_pnl = 0.0
        self.trading_halted = False
        self.halt_reason = ""
        # Note: consecutive_losses and exposure_multiplier persist across days

    def reset_all_stress(self):
        """Full stress reset (e.g., start of new week)"""
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.current_exposure_multiplier = 1.0
        self.trading_halted = False
        self.halt_reason = ""

    def get_stress_status(self) -> dict:
        """Get current stress status summary"""
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
        """Pretty print stress status"""
        status = self.get_stress_status()
        
        print("\n" + "="*60)
        print("🔥 LIVE STRESS STATUS (FAZ 3)")
        print("="*60)
        
        halt_icon = "🛑" if status["trading_halted"] else "✅"
        print(f"\nTrading Status: {halt_icon} {'HALTED - ' + status['halt_reason'] if status['trading_halted'] else 'ACTIVE'}")
        
        print(f"\n📊 Daily Stats:")
        print(f"   Daily PnL      : {status['daily_pnl']:>10.2f} TL ({status['daily_pnl_pct']:+.2f}%)")
        print(f"   Max Loss Left  : {status['daily_max_loss_remaining']:>10.2f} TL")
        
        print(f"\n⚡ Stress Indicators:")
        print(f"   Consecutive L  : {status['consecutive_losses']} / {self.consecutive_loss_limit}")
        print(f"   Exposure Mult  : {status['exposure_multiplier']*100:.0f}%")
        print(f"   Effective Exp  : {status['effective_max_exposure']:.0f}%")
        
        print("="*60)

