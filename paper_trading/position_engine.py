from datetime import datetime
from paper_trading.portfolio_state import PortfolioState
from core.risk_manager import RiskManager

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
        min_weight_change: float = 0.03
    ):
        self.portfolio = portfolio_state
        self.risk = risk_manager
        self.min_weight_change = min_weight_change

    def process_signal(
        self,
        symbol: str,
        target_weight: float,
        confidence: float,
        price: float
    ) -> dict:
        """
        Compare target weight with current portfolio state
        """

        current_weight = self.portfolio.current_weight(symbol)
        weight_diff = target_weight - current_weight

        decision = {
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

        # CLOSE
        if target_weight == 0 and current_weight > 0:
            decision["action"] = self.CLOSE
            decision["reason"] = "Target weight is zero"
            self.portfolio.close_position(symbol, price)
            return decision

        # HOLD
        if abs(weight_diff) < self.min_weight_change:
            decision["reason"] = "Weight difference below threshold"
            return decision

        # SCALE IN
        if weight_diff > 0:
            add_value = self.portfolio.total_portfolio_value() * weight_diff
            qty = add_value / price

            decision["action"] = self.OPEN if current_weight == 0 else self.SCALE_IN
            decision["quantity"] = qty
            decision["reason"] = "Increasing position towards target weight"

            self.portfolio.open_or_add(symbol, qty, price)
            return decision

        # SCALE OUT
        if weight_diff < 0:
            reduce_pct = abs(weight_diff) / current_weight if current_weight > 0 else 0

            decision["action"] = self.SCALE_OUT
            decision["quantity"] = reduce_pct
            decision["reason"] = "Reducing position towards target weight"

            self.portfolio.reduce_position(symbol, reduce_pct, price)
            return decision

        return decision

    def close_unwanted_positions(self, allowed_symbols):
        for symbol in self.portfolio.get_open_symbols():
            if symbol not in allowed_symbols:
                self.portfolio.close_position(symbol, self.portfolio.get_last_price(symbol))
