from datetime import datetime
from paper_trading.portfolio_state import PortfolioState
from core.risk_manager import RiskManager
from utils.constants import MIN_WEIGHT_CHANGE

class PositionEngine:
    """
    Target-weight aware Position Engine
    """

    HOLD = "HOLD"
    OPEN = "OPEN"
    SCALE_IN = "SCALE_IN"
    SCALE_OUT = "SCALE_OUT"
    CLOSE = "CLOSE"

    def __init__(
        self,
        portfolio_state: PortfolioState,
        risk_manager: RiskManager,
        min_weight_change: float = MIN_WEIGHT_CHANGE
    ):
        self.portfolio = portfolio_state
        self.risk = risk_manager
        self.min_weight_change = min_weight_change

    def process_signal(
            self,
            symbol: str,
            target_weight: float,
            confidence: float,
            price: float,
            win_rate: float = None,
            win_loss_ratio: float = None
        ) -> dict:
        """
        Compare target weight with current portfolio state
        """
        current_weight = self.portfolio.current_weight(symbol)
        weight_diff = target_weight - current_weight

        decision = self._create_base_decision(symbol, price, current_weight, target_weight, confidence)

        # Check for close action
        if self._should_close_position(target_weight, current_weight):
            return self._execute_close(decision, symbol, price)

        # Check for hold action
        if self._should_hold(weight_diff):
            decision["reason"] = "Weight difference below threshold"
            return decision

        # Check for scale in action
        if self._should_scale_in(weight_diff):
            return self._execute_scale_in(decision, symbol, price, weight_diff, current_weight)

        # Check for scale out action
        if self._should_scale_out(weight_diff):
            return self._execute_scale_out(decision, symbol, price, weight_diff, current_weight)

        return decision

    def _create_base_decision(self, symbol: str, price: float, current_weight: float,
                             target_weight: float, confidence: float) -> dict:
        """Create base decision dictionary."""
        return {
            "symbol": symbol,
            "price": price,
            "current_weight": current_weight,
            "target_weight": target_weight,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "action": self.HOLD,
            "quantity": 0,
            "reason": ""
        }

    def _should_close_position(self, target_weight: float, current_weight: float) -> bool:
        """Check if position should be closed."""
        return target_weight == 0 and current_weight > 0

    def _should_hold(self, weight_diff: float) -> bool:
        """Check if position should be held."""
        return abs(weight_diff) < self.min_weight_change

    def _should_scale_in(self, weight_diff: float) -> bool:
        """Check if position should be scaled in."""
        return weight_diff > 0

    def _should_scale_out(self, weight_diff: float) -> bool:
        """Check if position should be scaled out."""
        return weight_diff < 0

    def _execute_close(self, decision: dict, symbol: str, price: float) -> dict:
        """Execute close position action."""
        decision["action"] = self.CLOSE
        decision["reason"] = "Target weight is zero"
        self.portfolio.close_position(symbol, price)
        return decision

    def _execute_scale_in(self, decision: dict, symbol: str, price: float,
                         weight_diff: float, current_weight: float) -> dict:
        """Execute scale in action."""
        add_value = self.portfolio.total_portfolio_value() * weight_diff
        qty = add_value / price

        decision["action"] = self.OPEN if current_weight == 0 else self.SCALE_IN
        decision["quantity"] = qty
        decision["reason"] = "Increasing position towards target weight"

        self.portfolio.open_or_add(symbol, qty, price)
        return decision

    def _execute_scale_out(self, decision: dict, symbol: str, price: float,
                          weight_diff: float, current_weight: float) -> dict:
        """Execute scale out action."""
        reduce_pct = abs(weight_diff) / current_weight if current_weight > 0 else 0

        decision["action"] = self.SCALE_OUT
        decision["quantity"] = reduce_pct
        decision["reason"] = "Reducing position towards target weight"

        self.portfolio.reduce_position(symbol, reduce_pct, price)
        return decision


    def close_unwanted_positions(self, allowed_symbols):
        for symbol in self.portfolio.get_open_symbols():
            if symbol not in allowed_symbols:
                self.portfolio.close_position(symbol, self.portfolio.get_last_price(symbol))
