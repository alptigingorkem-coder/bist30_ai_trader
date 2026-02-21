"""
Portfolio business logic service.

This module handles portfolio trade execution logic. It coordinates between
validation, state management, and trade operations. Follows the Service Layer
pattern to separate business logic from data access and presentation.
"""

from typing import Dict, Optional
from datetime import datetime
import logging

from paper_trading.portfolio.portfolio_validator import PortfolioValidator

logger = logging.getLogger(__name__)


class PortfolioService:
    """
    Handles portfolio trade execution logic.
    
    Responsibilities:
    - Execute trade decisions (open, close, scale)
    - Coordinate validation before trades
    - Update portfolio state after trades
    - Track trade history
    - Calculate PnL
    
    This class follows the Service Layer pattern, orchestrating business
    operations while delegating validation to PortfolioValidator.
    """
    
    def __init__(self, portfolio_state, validator: Optional[PortfolioValidator] = None):
        """
        Initialize service with portfolio state and validator.
        
        Args:
            portfolio_state: Reference to PortfolioState instance
            validator: PortfolioValidator instance (optional, creates default if None)
        """
        self.state = portfolio_state
        self.validator = validator or PortfolioValidator()
        
        logger.info("PortfolioService initialized")
    
    def apply_trade_decision(self, decision: dict) -> dict:
        """
        Execute a trade decision.
        
        Args:
            decision: Dictionary containing trade decision
                - action: "OPEN_POSITION", "CLOSE_POSITION", "SCALE_IN", "SCALE_OUT", "HOLD_EXISTING", "IGNORE_SIGNAL"
                - symbol: Stock symbol
                - price: Current price
                - quantity: Number of shares (for open/scale_in)
                - side: "LONG" or "SHORT" (for open)
                - scale_pct: Percentage to scale out (for scale_out)
                - confidence: Signal confidence (optional)
                - regime: Market regime (optional)
        
        Returns:
            Dictionary with execution result:
                - success: bool
                - action: str
                - symbol: str
                - reason: str (if failed)
                - realized_pnl: float (if applicable)
        """
        action = decision.get("action")
        symbol = decision.get("symbol")
        price = decision.get("price", 0.0)
        quantity = decision.get("quantity", 0.0)
        
        result = {"success": False, "action": action, "symbol": symbol}
        
        try:
            if action == "OPEN_POSITION":
                result = self.open_position(
                    symbol=symbol,
                    price=price,
                    quantity=quantity,
                    side=decision.get("side", "LONG"),
                    confidence=decision.get("confidence"),
                    regime=decision.get("regime")
                )
            
            elif action == "CLOSE_POSITION":
                result = self.close_position(symbol=symbol, price=price)
            
            elif action == "SCALE_IN":
                result = self.scale_in(symbol=symbol, price=price, quantity=quantity)
            
            elif action == "SCALE_OUT":
                result = self.scale_out(
                    symbol=symbol,
                    price=price,
                    pct=decision.get("scale_pct", 0.5)
                )
            
            elif action in ["HOLD_EXISTING", "IGNORE_SIGNAL"]:
                result["success"] = True
                logger.debug(f"Action {action} for {symbol}: No trade executed")
            
            else:
                result["reason"] = f"UNKNOWN_ACTION: {action}"
                logger.warning(f"Unknown action: {action}")
            
            # Record successful trades in history
            if result["success"] and action not in ["HOLD_EXISTING", "IGNORE_SIGNAL"]:
                self.state.trade_history.append({
                    **decision,
                    "timestamp": datetime.now().isoformat(),
                    "execution": result,
                })
                logger.info(f"Trade executed: {action} {symbol} - Success")
            
        except Exception as e:
            logger.error(f"Error executing trade decision: {e}", exc_info=True)
            result["success"] = False
            result["reason"] = f"EXECUTION_ERROR: {str(e)}"
        
        return result
    
    def open_position(
        self,
        symbol: str,
        price: float,
        quantity: float,
        side: str = "LONG",
        confidence: Optional[float] = None,
        regime: Optional[str] = None
    ) -> dict:
        """
        Open a new position.
        
        Args:
            symbol: Stock symbol
            price: Entry price
            quantity: Number of shares
            side: "LONG" or "SHORT"
            confidence: Signal confidence (optional)
            regime: Market regime (optional)
        
        Returns:
            Dictionary with result:
                - success: bool
                - reason: str (if failed)
        """
        # Calculate cost
        cost = price * quantity
        
        # Validate trade size
        is_valid, reason = self.validator.validate_trade_size(
            symbol=symbol,
            quantity=quantity,
            price=price,
            cash=self.state.cash
        )
        
        if not is_valid:
            logger.debug(f"Cannot open {symbol}: {reason}")
            return {"success": False, "reason": reason}
        
        # Validate position opening
        size_pct = cost / self.state.total_portfolio_value() if self.state.total_portfolio_value() > 0 else 0
        can_open, reason = self.validator.can_open_position(
            symbol=symbol,
            size_pct=size_pct,
            current_positions=self.state.positions,
            cash=self.state.cash,
            total_exposure=self.state.current_total_exposure(),
            total_value=self.state.total_portfolio_value()
        )
        
        if not can_open:
            logger.debug(f"Cannot open {symbol}: {reason}")
            return {"success": False, "reason": reason}
        
        # Execute trade
        self.state.positions[symbol] = {
            "side": side,
            "entry_price": price,
            "quantity": quantity,
            "entry_time": datetime.now().isoformat(),
            "current_price": price,
            "entry_confidence": confidence,
            "entry_regime": regime,
        }
        self.state.cash -= cost
        
        logger.info(f"Opened position: {symbol} {quantity}@{price} ({side})")
        return {"success": True, "action": "OPEN_POSITION", "symbol": symbol}
    
    def close_position(self, symbol: str, price: float) -> dict:
        """
        Close an existing position.
        
        Args:
            symbol: Stock symbol
            price: Exit price
        
        Returns:
            Dictionary with result:
                - success: bool
                - reason: str (if failed)
                - realized_pnl: float (if successful)
        """
        # Validate position exists
        can_close, reason = self.validator.validate_position_close(
            symbol=symbol,
            current_positions=self.state.positions
        )
        
        if not can_close:
            logger.debug(f"Cannot close {symbol}: {reason}")
            return {"success": False, "reason": reason}
        
        # Get position details
        pos = self.state.positions[symbol]
        qty = pos["quantity"]
        entry_price = pos["entry_price"]
        
        # Calculate PnL
        if pos["side"] == "LONG":
            pnl = (price - entry_price) * qty
        else:  # SHORT
            pnl = (entry_price - price) * qty
        
        # Update cash and realized PnL
        self.state.cash += price * qty
        self.state.realized_pnl += pnl
        
        # Record closed trade
        entry_time = datetime.fromisoformat(pos["entry_time"])
        exit_time = datetime.now()
        holding_minutes = (exit_time - entry_time).total_seconds() / 60
        
        self.state.closed_trades.append({
            "symbol": symbol,
            "side": pos["side"],
            "entry_price": entry_price,
            "exit_price": price,
            "quantity": qty,
            "pnl": pnl,
            "return_pct": pnl / (entry_price * qty) if (entry_price * qty) > 0 else 0,
            "entry_time": pos["entry_time"],
            "exit_time": exit_time.isoformat(),
            "holding_minutes": holding_minutes,
            "entry_confidence": pos.get("entry_confidence"),
            "regime": pos.get("entry_regime"),
        })
        
        # Remove position
        del self.state.positions[symbol]
        
        logger.info(f"Closed position: {symbol} PnL={pnl:.2f}")
        return {"success": True, "realized_pnl": pnl}
    
    def scale_in(self, symbol: str, price: float, quantity: float) -> dict:
        """
        Add to an existing position (scale in).
        
        Args:
            symbol: Stock symbol
            price: Current price
            quantity: Additional shares to buy
        
        Returns:
            Dictionary with result:
                - success: bool
                - reason: str (if failed)
        """
        # Validate position exists
        if symbol not in self.state.positions:
            logger.debug(f"Cannot scale in {symbol}: NO_POSITION")
            return {"success": False, "reason": "NO_POSITION"}
        
        # Validate trade size
        is_valid, reason = self.validator.validate_trade_size(
            symbol=symbol,
            quantity=quantity,
            price=price,
            cash=self.state.cash
        )
        
        if not is_valid:
            logger.debug(f"Cannot scale in {symbol}: {reason}")
            return {"success": False, "reason": reason}
        
        # Update position (average entry price)
        pos = self.state.positions[symbol]
        total_cost = pos["entry_price"] * pos["quantity"] + price * quantity
        pos["quantity"] += quantity
        pos["entry_price"] = total_cost / pos["quantity"]
        
        # Update cash
        self.state.cash -= price * quantity
        
        logger.info(f"Scaled in: {symbol} +{quantity}@{price}")
        return {"success": True}
    
    def scale_out(self, symbol: str, price: float, pct: float) -> dict:
        """
        Reduce an existing position (scale out).
        
        Args:
            symbol: Stock symbol
            price: Current price
            pct: Percentage of position to close (0.0 to 1.0)
        
        Returns:
            Dictionary with result:
                - success: bool
                - reason: str (if failed)
                - realized_pnl: float (if successful)
        """
        # Validate position exists
        if symbol not in self.state.positions:
            logger.debug(f"Cannot scale out {symbol}: NO_POSITION")
            return {"success": False, "reason": "NO_POSITION"}
        
        # Validate percentage
        if pct <= 0 or pct > 1.0:
            logger.debug(f"Cannot scale out {symbol}: INVALID_PERCENTAGE ({pct})")
            return {"success": False, "reason": "INVALID_PERCENTAGE"}
        
        # Calculate quantities and PnL
        pos = self.state.positions[symbol]
        qty_to_sell = pos["quantity"] * pct
        
        if pos["side"] == "LONG":
            pnl = (price - pos["entry_price"]) * qty_to_sell
        else:  # SHORT
            pnl = (pos["entry_price"] - price) * qty_to_sell
        
        # Update cash and realized PnL
        self.state.cash += price * qty_to_sell
        self.state.realized_pnl += pnl
        
        # Update position
        pos["quantity"] -= qty_to_sell
        
        # Remove position if fully closed
        if pos["quantity"] <= 0:
            del self.state.positions[symbol]
            logger.info(f"Scaled out (full close): {symbol} PnL={pnl:.2f}")
        else:
            logger.info(f"Scaled out: {symbol} -{pct*100:.0f}% PnL={pnl:.2f}")
        
        return {"success": True, "realized_pnl": pnl}
