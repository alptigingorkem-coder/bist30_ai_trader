"""
Portfolio validation logic.

This module handles validation of portfolio operations against risk limits
and trading constraints. Follows the Single Responsibility Principle by
separating validation concerns from business logic.
"""

from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class PortfolioValidator:
    """
    Validates portfolio operations against risk limits.
    
    Responsibilities:
    - Validate position opening constraints
    - Check exposure limits
    - Validate stress limits (daily loss, consecutive losses)
    - Return clear validation results (bool, reason)
    
    This class follows the Validator pattern, returning validation results
    instead of raising exceptions, allowing calling code to handle failures
    gracefully.
    """
    
    def __init__(
        self,
        max_positions: int = 10,
        max_single_exposure: float = 0.10,
        max_total_exposure: float = 0.80,
        daily_max_loss_pct: float = 0.03,
        consecutive_loss_limit: int = 3
    ):
        """
        Initialize validator with risk limits.
        
        Args:
            max_positions: Maximum number of concurrent positions
            max_single_exposure: Maximum exposure for a single position (as fraction)
            max_total_exposure: Maximum total portfolio exposure (as fraction)
            daily_max_loss_pct: Maximum daily loss percentage (as fraction)
            consecutive_loss_limit: Maximum consecutive losing trades before halt
        """
        self.max_positions = max_positions
        self.max_single_exposure = max_single_exposure
        self.max_total_exposure = max_total_exposure
        self.daily_max_loss_pct = daily_max_loss_pct
        self.consecutive_loss_limit = consecutive_loss_limit
        
        logger.info(
            f"PortfolioValidator initialized: max_positions={max_positions}, "
            f"max_single_exposure={max_single_exposure}, "
            f"max_total_exposure={max_total_exposure}"
        )
    
    def can_open_position(
        self,
        symbol: str,
        size_pct: float,
        current_positions: Dict,
        cash: float,
        total_exposure: float,
        total_value: float
    ) -> Tuple[bool, str]:
        """
        Check if a new position can be opened.
        
        Args:
            symbol: Stock symbol to check
            size_pct: Desired position size as fraction of portfolio
            current_positions: Dictionary of current positions
            cash: Available cash
            total_exposure: Current total exposure
            total_value: Total portfolio value
            
        Returns:
            Tuple of (can_open, reason)
            - can_open: True if position can be opened, False otherwise
            - reason: Explanation string ("OK" if can open, error code otherwise)
        """
        # Check 0: Valid size percentage
        if size_pct <= 0:
            logger.debug(f"Cannot open {symbol}: INVALID_SIZE_PCT ({size_pct})")
            return False, "INVALID_SIZE_PCT"
        
        # Check 1: Already has position?
        if symbol in current_positions:
            logger.debug(f"Cannot open {symbol}: ALREADY_HAS_POSITION")
            return False, "ALREADY_HAS_POSITION"
        
        # Check 2: Max positions reached?
        if len(current_positions) >= self.max_positions:
            logger.debug(
                f"Cannot open {symbol}: MAX_POSITIONS_REACHED "
                f"({len(current_positions)}/{self.max_positions})"
            )
            return False, "MAX_POSITIONS_REACHED"
        
        # Check 3: Single exposure limit
        if size_pct > self.max_single_exposure:
            logger.debug(
                f"Cannot open {symbol}: EXCEEDS_SINGLE_EXPOSURE "
                f"({size_pct:.2%} > {self.max_single_exposure:.2%})"
            )
            return False, "EXCEEDS_SINGLE_EXPOSURE"
        
        # Check 4: Total exposure limit
        current_exposure_ratio = total_exposure / total_value if total_value > 0 else 0
        new_exposure_ratio = current_exposure_ratio + size_pct
        
        if new_exposure_ratio > self.max_total_exposure:
            logger.debug(
                f"Cannot open {symbol}: EXCEEDS_TOTAL_EXPOSURE "
                f"({new_exposure_ratio:.2%} > {self.max_total_exposure:.2%})"
            )
            return False, "EXCEEDS_TOTAL_EXPOSURE"
        
        # Check 5: Sufficient cash?
        required_cash = total_value * size_pct
        if required_cash > cash:
            logger.debug(
                f"Cannot open {symbol}: INSUFFICIENT_CASH "
                f"(need {required_cash:.2f}, have {cash:.2f})"
            )
            return False, "INSUFFICIENT_CASH"
        
        logger.debug(f"Can open {symbol}: All validation checks passed")
        return True, "OK"
    
    def check_stress_limits(
        self,
        daily_pnl: float,
        consecutive_losses: int,
        initial_capital: float
    ) -> Tuple[bool, str]:
        """
        Check if trading should be halted due to stress limits.
        
        Args:
            daily_pnl: Current day's profit/loss
            consecutive_losses: Number of consecutive losing trades
            initial_capital: Initial portfolio capital
            
        Returns:
            Tuple of (can_trade, reason)
            - can_trade: True if trading can continue, False if halted
            - reason: Explanation string ("OK" if can trade, halt reason otherwise)
        """
        # Check 1: Daily max loss
        if daily_pnl < 0:
            # Handle zero capital edge case
            if initial_capital <= 0:
                logger.warning("Cannot check stress limits: initial capital is zero or negative")
                return False, "INVALID_CAPITAL"
            
            daily_loss_pct = abs(daily_pnl) / initial_capital
            if daily_loss_pct >= self.daily_max_loss_pct:
                reason = (
                    f"DAILY_MAX_LOSS ({daily_loss_pct*100:.1f}% >= "
                    f"{self.daily_max_loss_pct*100:.1f}%)"
                )
                logger.warning(f"Trading halted: {reason}")
                return False, reason
        
        # Check 2: Consecutive losses
        if consecutive_losses >= self.consecutive_loss_limit:
            reason = (
                f"CONSECUTIVE_LOSSES ({consecutive_losses} >= "
                f"{self.consecutive_loss_limit})"
            )
            logger.warning(f"Trading halted: {reason}")
            return False, reason
        
        return True, "OK"
    
    def validate_trade_size(
        self,
        symbol: str,
        quantity: float,
        price: float,
        cash: float
    ) -> Tuple[bool, str]:
        """
        Validate that a trade size is valid.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            price: Price per share
            cash: Available cash
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check 1: Positive quantity
        if quantity <= 0:
            logger.debug(f"Invalid trade size for {symbol}: quantity must be positive")
            return False, "INVALID_QUANTITY"
        
        # Check 2: Positive price
        if price <= 0:
            logger.debug(f"Invalid trade size for {symbol}: price must be positive")
            return False, "INVALID_PRICE"
        
        # Check 3: Sufficient cash
        required_cash = quantity * price
        if required_cash > cash:
            logger.debug(
                f"Invalid trade size for {symbol}: insufficient cash "
                f"(need {required_cash:.2f}, have {cash:.2f})"
            )
            return False, "INSUFFICIENT_CASH"
        
        return True, "OK"
    
    def validate_position_close(
        self,
        symbol: str,
        current_positions: Dict
    ) -> Tuple[bool, str]:
        """
        Validate that a position can be closed.
        
        Args:
            symbol: Stock symbol
            current_positions: Dictionary of current positions
            
        Returns:
            Tuple of (can_close, reason)
        """
        if symbol not in current_positions:
            logger.debug(f"Cannot close {symbol}: NO_POSITION")
            return False, "NO_POSITION"
        
        return True, "OK"
