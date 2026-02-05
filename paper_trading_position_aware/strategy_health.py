"""
Strategy Health & Kill-Switch Module
Model-bağımsız strateji sağlık izleme ve otomatik durdurma sistemi

FAZ 5 - 2026-02-03
Enhanced with: Max DD tracking, dynamic confidence threshold, persistence
"""

from enum import Enum
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import numpy as np
import json
import os


class StrategyState(Enum):
    """Strateji durumu"""
    ACTIVE = "ACTIVE"          # Tam operasyonel
    DEGRADED = "DEGRADED"      # Uyarı, izleme altında
    PAUSED = "PAUSED"          # Geçici durdurma
    DISABLED = "DISABLED"      # Tamamen devre dışı
    PAPER_ONLY = "PAPER_ONLY"  # Max DD new low - sadece paper trade


class StrategyHealth:
    """
    Strategy Health Monitor - Model bağımsız performans izleme.
    
    Features:
    - Rolling performance windows (30/50/100 trades)
    - Regime-specific performance tracking
    - Hard invalidation rules (auto kill-switch)
    - Strategy state machine
    - Max DD tracking with paper-only mode
    - Dynamic confidence threshold adjustment
    - State persistence (save/load)
    """
    
    # Invalidation thresholds
    EXPECTANCY_MIN = 0.0                    # Son 50 trade expectancy min
    HIGH_CONF_WINRATE_MIN = 0.45            # %45 minimum high-conf win rate
    MAX_CONSECUTIVE_LOSSES = 7              # Art arda max kayıp
    ROLLING_SHARPE_MIN = -0.5               # Min rolling sharpe
    MAX_DD_PAPER_ONLY_THRESHOLD = -0.25     # %25 DD → paper-only mode
    
    # Default confidence threshold
    DEFAULT_CONFIDENCE_THRESHOLD = 0.60
    CONFIDENCE_STEP = 0.05                  # Her degradation'da +%5
    
    def __init__(self, closed_trades: List[dict] = None, equity_curve: List[float] = None):
        self.trades = closed_trades or []
        self.equity_curve = equity_curve or []
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
        
    def update_trades(self, trades: List[dict]):
        """Trade listesini güncelle"""
        self.trades = trades
        self._evaluate_state()
    
    # ─────────────────────────────────────────────────────────────
    # ROLLING PERFORMANCE WINDOWS
    # ─────────────────────────────────────────────────────────────
    
    def get_rolling_metrics(self, window: int = 50) -> dict:
        """
        Son N trade için rolling metrikler.
        Windows: 30, 50, 100
        """
        if len(self.trades) < window:
            recent = self.trades
        else:
            recent = self.trades[-window:]
        
        if not recent:
            return self._empty_metrics()
        
        returns = [t.get("return_pct", 0) for t in recent]
        pnls = [t.get("pnl", 0) for t in recent]
        
        # Win rate
        winners = [t for t in recent if t.get("pnl", 0) > 0]
        win_rate = len(winners) / len(recent) if recent else 0
        
        # Average win/loss
        avg_win = np.mean([t["pnl"] for t in winners]) if winners else 0
        losers = [t for t in recent if t.get("pnl", 0) <= 0]
        avg_loss = abs(np.mean([t["pnl"] for t in losers])) if losers else 0
        
        # Expectancy
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        # Rolling Sharpe (approximation)
        returns_arr = np.array(returns)
        if len(returns_arr) > 1 and np.std(returns_arr) > 0:
            rolling_sharpe = (np.mean(returns_arr) / np.std(returns_arr)) * np.sqrt(252)
        else:
            rolling_sharpe = 0
        
        # Profit factor
        gross_profit = sum(t["pnl"] for t in winners) if winners else 0
        gross_loss = abs(sum(t["pnl"] for t in losers)) if losers else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            "window": window,
            "trades": len(recent),
            "win_rate": round(win_rate * 100, 1),
            "expectancy": round(expectancy, 2),
            "rolling_sharpe": round(rolling_sharpe, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "∞",
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "total_pnl": round(sum(pnls), 2)
        }
    
    def get_all_rolling_windows(self) -> dict:
        """30, 50, 100 trade window metrikleri"""
        return {
            "window_30": self.get_rolling_metrics(30),
            "window_50": self.get_rolling_metrics(50),
            "window_100": self.get_rolling_metrics(100)
        }
    
    # ─────────────────────────────────────────────────────────────
    # REGIME-SPECIFIC PERFORMANCE
    # ─────────────────────────────────────────────────────────────
    
    def calculate_regime_performance(self) -> dict:
        """
        Rejim bazlı performans analizi.
        Trade'lerde 'regime' alanı olmalı.
        """
        regimes = {}
        
        for trade in self.trades:
            regime = trade.get("regime", "Unknown")
            if regime not in regimes:
                regimes[regime] = []
            regimes[regime].append(trade)
        
        performance = {}
        for regime, trades in regimes.items():
            winners = [t for t in trades if t.get("pnl", 0) > 0]
            win_rate = len(winners) / len(trades) if trades else 0
            total_pnl = sum(t.get("pnl", 0) for t in trades)
            avg_return = np.mean([t.get("return_pct", 0) for t in trades]) if trades else 0
            
            performance[regime] = {
                "trades": len(trades),
                "win_rate": round(win_rate * 100, 1),
                "total_pnl": round(total_pnl, 2),
                "avg_return_pct": round(avg_return * 100, 2),
                "edge": "✅" if total_pnl > 0 and win_rate > 0.50 else "⚠️" if total_pnl > 0 else "❌"
            }
        
        self.regime_performance = performance
        return performance
    
    def should_skip_regime(self, current_regime: str, min_trades: int = 10, min_win_rate: float = 40.0) -> Tuple[bool, str]:
        """
        Bu rejimde trade yapılmalı mı?
        
        Args:
            current_regime: Mevcut piyasa rejimi
            min_trades: Minimum trade sayısı (istatistiksel anlamlılık için)
            min_win_rate: Minimum win rate %
            
        Returns:
            (should_skip, reason)
        """
        perf = self.calculate_regime_performance()
        
        if current_regime not in perf:
            # Yeni rejim, yeterli veri yok
            return False, f"Yeni rejim: {current_regime}"
        
        stats = perf[current_regime]
        
        # Yeterli trade yoksa skip etme
        if stats["trades"] < min_trades:
            return False, f"Yetersiz veri: {stats['trades']} < {min_trades} trade"
        
        # Win rate çok düşükse skip et
        if stats["win_rate"] < min_win_rate:
            return True, f"Düşük WR: {stats['win_rate']:.1f}% < {min_win_rate}% (rejim: {current_regime})"
        
        # PnL negatifse skip et
        if stats["total_pnl"] < 0:
            return True, f"Negatif PnL: {stats['total_pnl']:.2f} TL (rejim: {current_regime})"
        
        return False, f"Rejim OK: {current_regime}"
    
    def get_regime_recommendation(self, current_regime: str) -> dict:
        """
        Belirli bir rejim için trading tavsiyesi.
        """
        should_skip, reason = self.should_skip_regime(current_regime)
        perf = self.regime_performance.get(current_regime, {})
        
        return {
            "regime": current_regime,
            "should_skip": should_skip,
            "reason": reason,
            "historical_trades": perf.get("trades", 0),
            "historical_win_rate": perf.get("win_rate", 0),
            "historical_pnl": perf.get("total_pnl", 0)
        }
    
    # ─────────────────────────────────────────────────────────────
    # HARD INVALIDATION RULES
    # ─────────────────────────────────────────────────────────────
    
    def check_invalidation_rules(self) -> Tuple[StrategyState, str]:
        """
        Hard invalidation kurallarını kontrol et.
        Returns: (new_state, reason)
        """
        metrics_50 = self.get_rolling_metrics(50)
        
        # Rule 1: Expectancy < 0 for last 50 trades → DISABLED
        if metrics_50["trades"] >= 50 and metrics_50["expectancy"] < self.EXPECTANCY_MIN:
            return StrategyState.DISABLED, f"Expectancy < 0 (son 50: {metrics_50['expectancy']})"
        
        # Rule 2: High-conf win rate < 45% → DEGRADED (threshold artır)
        high_conf_stats = self._get_high_confidence_stats()
        if high_conf_stats["count"] >= 20 and high_conf_stats["win_rate"] < self.HIGH_CONF_WINRATE_MIN * 100:
            return StrategyState.DEGRADED, f"High-conf win rate < %45 ({high_conf_stats['win_rate']:.1f}%)"
        
        # Rule 3: Consecutive losses >= 7 → PAUSED
        consecutive = self._get_consecutive_losses()
        if consecutive >= self.MAX_CONSECUTIVE_LOSSES:
            return StrategyState.PAUSED, f"Ardışık {consecutive} kayıp"
        
        # Rule 4: Rolling Sharpe < -0.5 → DEGRADED
        if metrics_50["trades"] >= 30 and metrics_50["rolling_sharpe"] < self.ROLLING_SHARPE_MIN:
            return StrategyState.DEGRADED, f"Rolling Sharpe < -0.5 ({metrics_50['rolling_sharpe']})"
        
        # Rule 5: Max DD new low beyond threshold → PAPER_ONLY
        if self.max_drawdown < self.MAX_DD_PAPER_ONLY_THRESHOLD:
            self.paper_only_mode = True
            return StrategyState.PAPER_ONLY, f"Max DD new low: {self.max_drawdown*100:.1f}%"
        
        return StrategyState.ACTIVE, "Tüm kurallar geçti"
    
    def _get_high_confidence_stats(self) -> dict:
        """High confidence (>0.70) trade istatistikleri"""
        high_conf = [t for t in self.trades if t.get("entry_confidence", 0) >= 0.70]
        if not high_conf:
            return {"count": 0, "win_rate": 0}
        
        winners = [t for t in high_conf if t.get("pnl", 0) > 0]
        return {
            "count": len(high_conf),
            "win_rate": len(winners) / len(high_conf) * 100
        }
    
    def _get_consecutive_losses(self) -> int:
        """Son kaç trade art arda kayıp"""
        if not self.trades:
            return 0
        
        consecutive = 0
        for trade in reversed(self.trades):
            if trade.get("pnl", 0) <= 0:
                consecutive += 1
            else:
                break
        return consecutive
    
    # ─────────────────────────────────────────────────────────────
    # STRATEGY STATE MACHINE
    # ─────────────────────────────────────────────────────────────
    
    def _evaluate_state(self):
        """Strateji durumunu değerlendir ve güncelle"""
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
    
    def get_state(self) -> Tuple[StrategyState, str]:
        """Mevcut strateji durumu"""
        return self.state, self.state_reason
    
    def force_state(self, new_state: StrategyState, reason: str):
        """Manuel olarak durum değiştir"""
        self.state_history.append({
            "from": self.state.value,
            "to": new_state.value,
            "reason": f"MANUAL: {reason}",
            "timestamp": datetime.now().isoformat()
        })
        self.state = new_state
        self.state_reason = reason
    
    def can_trade(self) -> bool:
        """Trade yapılabilir mi? (Not: PAPER_ONLY durumunda paper trade'e izin verir)"""
        return self.state in [StrategyState.ACTIVE, StrategyState.DEGRADED, StrategyState.PAPER_ONLY]
    
    def can_live_trade(self) -> bool:
        """Live trade yapılabilir mi? (PAPER_ONLY'de False)"""
        return self.state in [StrategyState.ACTIVE, StrategyState.DEGRADED]
    
    def is_paper_only_mode(self) -> bool:
        """Sadece paper trade modunda mı?"""
        return self.state == StrategyState.PAPER_ONLY or self.paper_only_mode
    
    def should_reduce_size(self) -> bool:
        """Pozisyon boyutu küçültülmeli mi?"""
        return self.state in [StrategyState.DEGRADED, StrategyState.PAPER_ONLY]
    
    # ─────────────────────────────────────────────────────────────
    # REPORTING
    # ─────────────────────────────────────────────────────────────
    
    def print_health_report(self):
        """Sağlık raporu yazdır"""
        print("\n" + "="*70)
        print("🏥 STRATEGY HEALTH REPORT")
        print("="*70)
        
        # State
        state_icons = {
            StrategyState.ACTIVE: "🟢",
            StrategyState.DEGRADED: "🟡",
            StrategyState.PAUSED: "🟠",
            StrategyState.DISABLED: "🔴"
        }
        icon = state_icons.get(self.state, "⚪")
        print(f"\n{icon} State: {self.state.value}")
        if self.state_reason:
            print(f"   Reason: {self.state_reason}")
        
        # Rolling Windows
        print("\n📊 Rolling Performance:")
        for window in [30, 50, 100]:
            m = self.get_rolling_metrics(window)
            print(f"   [{window:>3}] WR: {m['win_rate']:>5.1f}% | Exp: {m['expectancy']:>7.2f} | Sharpe: {m['rolling_sharpe']:>5.2f} | PnL: {m['total_pnl']:>10.2f}")
        
        # Regime Performance
        print("\n🌡️ Regime Performance:")
        regime_perf = self.calculate_regime_performance()
        if regime_perf:
            for regime, stats in regime_perf.items():
                print(f"   {regime:<12} {stats['edge']} WR: {stats['win_rate']:>5.1f}% | PnL: {stats['total_pnl']:>10.2f} ({stats['trades']} trades)")
        else:
            print("   No regime data available")
        
        # Invalidation Check
        print("\n⚠️ Invalidation Rules:")
        new_state, reason = self.check_invalidation_rules()
        if new_state == StrategyState.ACTIVE:
            print("   ✅ All rules passed")
        else:
            print(f"   ❌ {reason}")
        
        # Consecutive Losses
        consec = self._get_consecutive_losses()
        print(f"\n🔥 Consecutive Losses: {consec} / {self.MAX_CONSECUTIVE_LOSSES}")
        
        print("="*70)
    
    def get_health_summary(self) -> dict:
        """Sağlık özeti dict olarak"""
        metrics_50 = self.get_rolling_metrics(50)
        
        return {
            "state": self.state.value,
            "state_reason": self.state_reason,
            "can_trade": self.can_trade(),
            "should_reduce_size": self.should_reduce_size(),
            "rolling_50": metrics_50,
            "consecutive_losses": self._get_consecutive_losses(),
            "high_conf_stats": self._get_high_confidence_stats(),
            "total_trades": len(self.trades),
            # New fields
            "max_drawdown": round(self.max_drawdown * 100, 2),
            "paper_only_mode": self.paper_only_mode,
            "confidence_threshold": self.current_confidence_threshold
        }
    
    # ─────────────────────────────────────────────────────────────
    # MAX DRAWDOWN TRACKING
    # ─────────────────────────────────────────────────────────────
    
    def update_equity(self, current_equity: float):
        """
        Update equity curve and recalculate max drawdown.
        Call this with each new portfolio value.
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
    
    def _calculate_max_drawdown(self):
        """Calculate max drawdown from equity curve"""
        if not self.equity_curve:
            return
        
        peak = self.equity_curve[0]
        max_dd = 0.0
        
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            if peak > 0:
                dd = (equity - peak) / peak
                if dd < max_dd:
                    max_dd = dd
        
        self.max_drawdown = max_dd
        self.equity_high_water_mark = peak
    
    def reset_max_dd_tracking(self):
        """Reset max DD tracking (e.g., start of new evaluation period)"""
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
        high_conf_stats = self._get_high_confidence_stats()
        
        # If not enough data, return default
        if high_conf_stats["count"] < 20:
            return self.DEFAULT_CONFIDENCE_THRESHOLD
        
        # Calculate how much below target we are
        target_winrate = self.HIGH_CONF_WINRATE_MIN * 100  # 45%
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
        """Update confidence threshold based on performance"""
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
        Returns filepath.
        """
        if filepath is None:
            filepath = "paper_trading_position_aware/logs/strategy_health_state.json"
        
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
        """
        if filepath is None:
            filepath = "paper_trading_position_aware/logs/strategy_health_state.json"
        
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
    
    def _empty_metrics(self) -> dict:
        return {
            "window": 0, "trades": 0, "win_rate": 0, "expectancy": 0,
            "rolling_sharpe": 0, "profit_factor": 0, "avg_win": 0,
            "avg_loss": 0, "total_pnl": 0
        }


# ─────────────────────────────────────────────────────────────
# INTEGRATION HELPER
# ─────────────────────────────────────────────────────────────

def check_strategy_health(portfolio_state, equity_curve: List[float] = None) -> Tuple[bool, str, dict]:
    """
    PortfolioState ile entegre kullanım.
    
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
        "consecutive_losses": health._get_consecutive_losses()
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
    """
    return StrategyHealth(portfolio_state.closed_trades, equity_curve)


if __name__ == "__main__":
    # Demo with sample trades
    print("\n" + "="*70)
    print("🧪 STRATEGY HEALTH DEMO")
    print("="*70)
    
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
    print("\n📊 New Features Demo:")
    print("-" * 50)
    
    # Max DD
    print(f"Max Drawdown: {health.max_drawdown*100:.2f}%")
    print(f"High Water Mark: {health.equity_high_water_mark:,.2f}")
    
    # Confidence threshold
    recommended_conf = health.get_recommended_confidence_threshold()
    print(f"Current Confidence Threshold: {health.current_confidence_threshold}")
    print(f"Recommended Threshold: {recommended_conf}")
    
    # State methods
    print(f"\nCan Trade: {health.can_trade()}")
    print(f"Can Live Trade: {health.can_live_trade()}")
    print(f"Paper Only Mode: {health.is_paper_only_mode()}")
    
    # Save/Load test
    filepath = health.save_state()
    print(f"\nState saved to: {filepath}")
    
    health2 = StrategyHealth()
    loaded = health2.load_state()
    print(f"State loaded: {loaded}")
    print(f"Restored state: {health2.state.value}")
    
    print("="*70)

