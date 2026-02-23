"""
BacktestStrategy: Strategy pattern implementation for backtest execution.

This module implements the Strategy pattern to simplify the run_backtest() function
by extracting signal validation, trading checks, trade execution, and result aggregation
into separate methods with guard clauses.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, List, Any
from dataclasses import dataclass
from enum import Enum
from utils.constants import (
    DEFAULT_INITIAL_CAPITAL,
    COMMISSION_RATE,
    MAX_DRAWDOWN_LIMIT,
    RISK_PER_TRADE,
    MAX_SINGLE_POS_WEIGHT,
    CASH_USAGE_PCT,
    REBALANCE_THRESHOLD
)


class Urgency(Enum):
    """Order urgency levels for smart order routing."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""
    initial_capital: float = DEFAULT_INITIAL_CAPITAL
    commission: float = COMMISSION_RATE
    max_drawdown_limit: float = MAX_DRAWDOWN_LIMIT
    enable_risk_sizing: bool = False
    enable_kelly: bool = True
    risk_per_trade: float = RISK_PER_TRADE
    max_single_pos_weight: float = MAX_SINGLE_POS_WEIGHT
    min_holding_days: int = 0


class BacktestStrategy:
    """
    Executes backtest strategy with simplified logic using guard clauses.
    
    This class refactors the complex run_backtest() function by:
    - Extracting signal validation into _is_valid_signal()
    - Extracting trading checks into _can_trade()
    - Extracting trade execution into _execute_trade()
    - Extracting result aggregation into _aggregate_results()
    - Using guard clauses to eliminate nested conditionals
    """
    
    def __init__(self, config: Optional[BacktestConfig] = None):
        """Initialize backtest strategy with configuration."""
        self.config = config or BacktestConfig()
        
    def run(
        self,
        data: pd.DataFrame,
        signals_or_weights: Optional[pd.Series] = None,
        risk_manager: Any = None,
        regime_detector: Any = None,
        position_sizer: Any = None,
        execution_manager: Any = None,
        router: Any = None
    ) -> pd.DataFrame:
        """
        Run backtest with guard clauses for simplified logic.
        
        Args:
            data: Market data DataFrame with OHLCV columns
            signals_or_weights: Trading signals (binary) or weights (0-1)
            risk_manager: Risk management instance
            regime_detector: Market regime detection instance
            position_sizer: Position sizing instance
            execution_manager: Execution management instance
            router: Smart order routing instance
            
        Returns:
            DataFrame with backtest results including positions, trades, equity
        """
        # Initialize components
        df = data.copy()
        
        # Align signals with data
        if signals_or_weights is not None:
            common_index = df.index.intersection(signals_or_weights.index)
            df = df.loc[common_index].copy()
            inputs = signals_or_weights.loc[common_index]
        else:
            inputs = pd.Series(0, index=df.index)
        
        # Determine input type (binary signal vs weighted)
        is_weighted = self._is_weighted_input(inputs)
        
        # Prepare data columns
        df = self._prepare_data_columns(df)
        
        # Initialize result arrays
        results = self._initialize_results(len(df))
        
        # Initialize state
        state = self._initialize_state(df, inputs, is_weighted)
        
        # Main backtest loop
        for i in range(1, len(df)):
            # Update current market data
            current = self._get_current_data(df, i, state)
            
            # Guard clause: Circuit breaker check
            if self._check_circuit_breaker(current, state, results, i):
                continue
            
            # Detect current regime
            current_regime = self._detect_regime(df, i, regime_detector)
            results['regimes'][i] = current_regime
            
            # Adjust risk for regime
            if risk_manager and hasattr(risk_manager, 'adjust_for_regime'):
                risk_manager.adjust_for_regime(current_regime)
            
            # Determine trading action
            action, exit_reason, urgency = self._determine_action(
                current, state, is_weighted, risk_manager, regime_detector, current_regime
            )
            
            # Execute action
            self._execute_action(
                action, exit_reason, urgency, current, state, results, i,
                execution_manager, router
            )
            
            # Update state
            self._update_state(current, state, results, i)
        
        # Aggregate results into DataFrame
        return self._aggregate_results(df, results, state)

    
    def _is_weighted_input(self, inputs: pd.Series) -> bool:
        """Check if inputs are weighted (0-1) vs binary (0/1)."""
        if inputs.dtype != float:
            return False
        return inputs.max() <= 1.0 and inputs.min() >= 0.0
    
    def _prepare_data_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure required columns exist in data."""
        if 'ATR' not in df.columns:
            df['ATR'] = np.nan
        if 'Regime' not in df.columns:
            df['Regime'] = 'Trend_Up'
        if 'ATR_MA_60' not in df.columns and 'ATR' in df.columns:
            df['ATR_MA_60'] = df['ATR'].rolling(60).mean().bfill()
        if 'Log_Return' not in df.columns:
            df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
        if 'Volatility_20' not in df.columns:
            df['Volatility_20'] = df['Log_Return'].rolling(20).std().fillna(0)
        return df
    
    def _initialize_results(self, length: int) -> Dict[str, List]:
        """Initialize result storage arrays."""
        return {
            'positions': np.zeros(length),
            'current_weights': np.zeros(length),
            'trades': np.zeros(length),
            'exit_reasons': [None] * length,
            'equities': np.zeros(length),
            'regimes': [None] * length,
            'order_types': [None] * length,
            'execution_notes': [None] * length
        }
    
    def _initialize_state(
        self, df: pd.DataFrame, inputs: pd.Series, is_weighted: bool
    ) -> Dict[str, Any]:
        """Initialize backtest state variables."""
        state = {
            'equity': self.config.initial_capital,
            'cash': self.config.initial_capital,
            'holdings_value': 0.0,
            'holdings_qty': 0.0,
            'in_position': False,
            'entry_price': 0.0,
            'entry_date': None,
            'peak_price': 0.0,
            'days_held': 0,
            'peak_equity': self.config.initial_capital,
            'circuit_breaker_triggered': False,
            'is_weighted': is_weighted,
            'prices': df['Close'].values,
            'opens': df['Open'].values,
            'highs': df['High'].values,
            'lows': df['Low'].values,
            'atrs': df['ATR'].values,
            'dates': df.index,
            'input_values': inputs.values,
            'volumes': df['Volume'].values if 'Volume' in df.columns else np.zeros(len(df)),
            'avg_volumes': df['Volume'].rolling(20).mean().bfill().values if 'Volume' in df.columns else np.zeros(len(df))
        }
        state['equities'] = np.zeros(len(df))
        state['equities'][0] = self.config.initial_capital
        return state

    
    def _get_current_data(self, df: pd.DataFrame, i: int, state: Dict) -> Dict[str, Any]:
        """Extract current market data for index i."""
        idx_val = state['dates'][i]
        if isinstance(idx_val, tuple):
            current_date = idx_val[0]
        else:
            current_date = idx_val
        
        return {
            'i': i,
            'close': state['prices'][i],
            'open': state['opens'][i],
            'high': state['highs'][i],
            'low': state['lows'][i],
            'atr': state['atrs'][i],
            'date': current_date,
            'input_val': state['input_values'][i],
            'volume': state['volumes'][i],
            'avg_volume': state['avg_volumes'][i]
        }
    
    def _check_circuit_breaker(
            self, current: Dict, state: Dict, results: Dict, i: int
        ) -> bool:
        """
        Check and handle circuit breaker condition.

        Returns True if circuit breaker is active (skip trading).
        """
        # Update portfolio valuation
        self._update_portfolio_valuation(current, state)

        # Calculate drawdown
        dd = self._calculate_drawdown(state)

        # Check if circuit breaker should trigger
        if self._should_trigger_circuit_breaker(dd, state):
            self._trigger_circuit_breaker(current, state, results, i, dd)
            return True

        # If already triggered, skip trading
        if state['circuit_breaker_triggered']:
            self._handle_triggered_circuit_breaker(state, results, i)
            return True

        return False

    def _update_portfolio_valuation(self, current: Dict, state: Dict):
        """Update portfolio holdings value and equity."""
        if state['holdings_qty'] > 0:
            state['holdings_value'] = state['holdings_qty'] * current['close']
            state['in_position'] = True
        else:
            state['holdings_value'] = 0.0
            state['in_position'] = False

        state['equity'] = state['cash'] + state['holdings_value']

        if state['equity'] > state['peak_equity']:
            state['peak_equity'] = state['equity']

    def _calculate_drawdown(self, state: Dict) -> float:
        """Calculate current drawdown from peak equity."""
        if state['peak_equity'] > 0:
            return (state['equity'] - state['peak_equity']) / state['peak_equity']
        return 0

    def _should_trigger_circuit_breaker(self, dd: float, state: Dict) -> bool:
        """Check if circuit breaker should be triggered."""
        return dd < -self.config.max_drawdown_limit and not state['circuit_breaker_triggered']

    def _trigger_circuit_breaker(self, current: Dict, state: Dict, results: Dict, i: int, dd: float):
        """Trigger circuit breaker and force close positions."""
        print(f"!!! CIRCUIT BREAKER TRIGGERED ({current['date'].date()}) !!! Drawdown: {dd:.2%}. Trading stopped.")

        # Force close position if open
        if state['holdings_qty'] > 0:
            self._force_close_position(current, state, results, i)

        state['circuit_breaker_triggered'] = True
        self._update_results_for_circuit_breaker(state, results, i)

    def _force_close_position(self, current: Dict, state: Dict, results: Dict, i: int):
        """Force close open position due to circuit breaker."""
        results['trades'][i] = 1
        results['exit_reasons'][i] = 'CIRCUIT_BREAKER'

        # Sell at open with high urgency
        sell_price = current['open']
        state['cash'] += state['holdings_qty'] * sell_price * (1 - self.config.commission)
        state['holdings_qty'] = 0
        state['holdings_value'] = 0

    def _handle_triggered_circuit_breaker(self, state: Dict, results: Dict, i: int):
        """Handle state when circuit breaker is already triggered."""
        self._update_results_for_circuit_breaker(state, results, i)

    def _update_results_for_circuit_breaker(self, state: Dict, results: Dict, i: int):
        """Update results arrays when circuit breaker is active."""
        results['positions'][i] = 0
        results['current_weights'][i] = 0
        results['equities'][i] = state['cash']


    
    def _detect_regime(
        self, df: pd.DataFrame, i: int, regime_detector: Any
    ) -> str:
        """Detect current market regime."""
        if regime_detector is None:
            return 'Trend_Up'
        
        current_slice = df.iloc[[i]].copy()
        market_data = self._get_market_indicators(current_slice)
        return regime_detector.detect_regime(market_data)
    
    def _get_market_indicators(self, data_slice: pd.DataFrame) -> Dict[str, Any]:
        """Extract market indicators for regime detection."""
        # Return the DataFrame directly for regime detector
        return data_slice
    
    def _determine_action(
        self,
        current: Dict,
        state: Dict,
        is_weighted: bool,
        risk_manager: Any,
        regime_detector: Any,
        current_regime: str
    ) -> Tuple[str, Optional[str], Urgency]:
        """
        Determine trading action based on current state and signals.
        
        Returns: (action, exit_reason, urgency)
        """
        action = 'HOLD'
        exit_reason = None
        urgency = Urgency.NORMAL
        
        # Check regime-based restrictions
        if regime_detector:
            regime_action = regime_detector.get_trading_action(current_regime)
            force_exit = regime_action.get('force_exit', False)
            should_trade = regime_action.get('trade', True)
            
            # Guard clause: Force exit due to crisis regime
            if force_exit and state['in_position']:
                return 'SELL', f'CRISIS_{current_regime}', Urgency.HIGH
            
            # Guard clause: Don't trade in volatile regime
            if not should_trade and state['in_position']:
                return 'SELL', f'REGIME_{current_regime}', Urgency.NORMAL
        
        # Check risk manager exit conditions
        if state['in_position'] and risk_manager:
            state['days_held'] = (current['date'] - state['entry_date']).days
            if current['high'] > state['peak_price']:
                state['peak_price'] = current['high']
            
            check_res, reason = risk_manager.check_exit_conditions(
                current['close'], state['entry_price'], state['peak_price'],
                current['atr'], state['days_held']
            )
            
            # Guard clause: Risk manager says sell
            if check_res == 'SELL':
                urgency = Urgency.HIGH if 'STOP' in reason else Urgency.NORMAL
                return 'SELL', reason, urgency
        
        # Check signal/weight for trading decision
        if is_weighted:
            return self._determine_weighted_action(current, state, regime_detector, current_regime, risk_manager)
        else:
            return self._determine_binary_action(current, state, risk_manager)

    
    def _determine_weighted_action(
        self,
        current: Dict,
        state: Dict,
        regime_detector: Any,
        current_regime: str,
        risk_manager: Any
    ) -> Tuple[str, Optional[str], Urgency]:
        """Determine action for weighted (continuous) signals."""
        base_weight = current['input_val']
        
        # Apply regime multiplier
        pos_mult = 1.0
        if regime_detector:
            regime_action = regime_detector.get_trading_action(current_regime)
            pos_mult = regime_action.get('position_multiplier', 1.0)
        
        # Calculate target weight based on sizing method
        target_weight = base_weight * pos_mult
        target_weight = max(0, min(1, target_weight))  # Clamp to [0, 1]
        
        # Calculate target quantity
        target_value = state['equity'] * target_weight
        target_qty = target_value / current['close']
        
        # Calculate rebalance threshold
        qty_diff_pct = 0
        if state['holdings_qty'] > 0:
            qty_diff_pct = abs(target_qty - state['holdings_qty']) / state['holdings_qty']
        else:
            qty_diff_pct = 1.0 if target_qty > 0 else 0
        
        # Guard clause: No significant change needed
        if qty_diff_pct <= REBALANCE_THRESHOLD:
            return 'HOLD', None, Urgency.NORMAL
        
        # Determine buy or sell
        if target_qty > state['holdings_qty']:
            return 'BUY', None, Urgency.NORMAL
        elif target_qty < state['holdings_qty']:
            # Check minimum holding period
            if state['days_held'] >= self.config.min_holding_days:
                if target_qty < (state['holdings_qty'] * 0.1):
                    return 'SELL', 'WEIGHT_ZERO', Urgency.LOW
                else:
                    return 'REBALANCE_SELL', None, Urgency.LOW
        
        return 'HOLD', None, Urgency.NORMAL
    
    def _determine_binary_action(
        self,
        current: Dict,
        state: Dict,
        risk_manager: Any
    ) -> Tuple[str, Optional[str], Urgency]:
        """Determine action for binary (0/1) signals."""
        # Guard clause: Buy signal and not in position
        if current['input_val'] == 1 and not state['in_position']:
            return 'BUY', None, Urgency.NORMAL
        
        # Guard clause: Sell signal and in position
        if current['input_val'] == 0 and state['in_position']:
            min_holding = risk_manager.min_holding_periods if risk_manager else 0
            if state['days_held'] >= min_holding:
                return 'SELL', 'SIGNAL_LOST', Urgency.NORMAL
        
        return 'HOLD', None, Urgency.NORMAL

    
    def _execute_action(
        self,
        action: str,
        exit_reason: Optional[str],
        urgency: Urgency,
        current: Dict,
        state: Dict,
        results: Dict,
        i: int,
        execution_manager: Any,
        router: Any
    ) -> None:
        """Execute the determined trading action."""
        if action == 'HOLD':
            return
        
        if action == 'BUY':
            self._execute_buy(current, state, results, i, execution_manager, router, urgency)
        elif action == 'SELL':
            self._execute_sell(current, state, results, i, exit_reason, execution_manager, router, urgency)
        elif action == 'REBALANCE_SELL':
            self._execute_rebalance_sell(current, state, results, i, execution_manager, router, urgency)
    
    def _execute_buy(
            self,
            current: Dict,
            state: Dict,
            results: Dict,
            i: int,
            execution_manager: Any,
            router: Any,
            urgency: Urgency
        ) -> None:
        """Execute buy order."""
        # Calculate quantity to buy
        diff_qty = self._calculate_buy_quantity(current, state)

        # Guard clause: No quantity to buy
        if diff_qty <= 0:
            return

        # Get execution price
        executed_price = self._get_execution_price(current, router, diff_qty, urgency, results, i)

        # Calculate costs
        total_cost = self._calculate_buy_cost(diff_qty, executed_price, current)

        # Guard clause: Insufficient funds
        if state['cash'] < total_cost:
            return

        # Execute trade
        self._execute_buy_trade(diff_qty, executed_price, total_cost, current, state, results, i)

    def _calculate_buy_quantity(self, current: Dict, state: Dict) -> float:
        """Calculate quantity to buy based on strategy type."""
        if state['is_weighted']:
            # For weighted, calculate based on target weight
            target_weight = current['input_val']
            target_value = state['equity'] * target_weight
            target_qty = target_value / current['close']
            return target_qty - state['holdings_qty']
        else:
            # For binary, use 99% of cash
            return (state['cash'] * CASH_USAGE_PCT) / current['close']

    def _get_execution_price(self, current: Dict, router: Any, qty: float,
                            urgency: Urgency, results: Dict, i: int) -> float:
        """Get execution price from router or use current close."""
        executed_price = current['close']

        if router:
            order = router.generate_order("BACKTEST", "BUY", current['close'], abs(qty), urgency)
            executed_price = order.get('price', current['close'])

            if 'type' in order:
                results['order_types'][i] = order['type'].value
            if 'note' in order:
                results['execution_notes'][i] = order['note']

        return executed_price

    def _calculate_buy_cost(self, qty: float, price: float, current: Dict) -> float:
        """Calculate total cost including slippage and commission."""
        slippage = self._calculate_slippage(current['volume'], current['avg_volume'], qty)
        cost = qty * price * (1 + slippage)
        return cost * (1 + self.config.commission)

    def _execute_buy_trade(self, qty: float, price: float, total_cost: float,
                          current: Dict, state: Dict, results: Dict, i: int):
        """Execute the buy trade and update state."""
        state['cash'] -= total_cost
        state['holdings_qty'] += qty
        results['trades'][i] = 1

        # Update entry price (weighted average for scale-in)
        if state['in_position'] and state['holdings_qty'] > 0:
            old_qty = state['holdings_qty'] - qty
            state['entry_price'] = (state['entry_price'] * old_qty + price * qty) / state['holdings_qty']
        else:
            state['entry_price'] = price
            state['entry_date'] = current['date']
            state['peak_price'] = current['close']
            state['in_position'] = True


    
    def _execute_sell(
        self,
        current: Dict,
        state: Dict,
        results: Dict,
        i: int,
        exit_reason: Optional[str],
        execution_manager: Any,
        router: Any,
        urgency: Urgency
    ) -> None:
        """Execute full sell order."""
        # Guard clause: No holdings to sell
        if state['holdings_qty'] <= 0:
            return
        
        sell_qty = state['holdings_qty']
        
        # Get execution price from router
        executed_price = current['close']
        if router:
            order = router.generate_order("BACKTEST", "SELL", current['close'], sell_qty, urgency)
            executed_price = order.get('price', current['close'])
            if 'type' in order:
                results['order_types'][i] = order['type'].value
            if 'note' in order:
                results['execution_notes'][i] = order['note']
        
        # Calculate slippage
        slippage = self._calculate_slippage(current['volume'], current['avg_volume'], sell_qty)
        
        # Calculate proceeds
        proceeds = sell_qty * executed_price * (1 - slippage)
        net_proceeds = proceeds * (1 - self.config.commission)
        
        # Execute trade
        state['cash'] += net_proceeds
        state['holdings_qty'] = 0
        state['in_position'] = False
        results['trades'][i] = 1
        results['exit_reasons'][i] = exit_reason
        
        # Record PnL for position sizer (if available)
        if state['entry_price'] > 0:
            pnl_pct = (executed_price - state['entry_price']) / state['entry_price']
            # Position sizer update would go here if available
    
    def _execute_rebalance_sell(
        self,
        current: Dict,
        state: Dict,
        results: Dict,
        i: int,
        execution_manager: Any,
        router: Any,
        urgency: Urgency
    ) -> None:
        """Execute partial sell order (rebalancing)."""
        # Calculate target quantity
        target_weight = current['input_val']
        target_value = state['equity'] * target_weight
        target_qty = target_value / current['close']
        
        sell_qty = state['holdings_qty'] - target_qty
        
        # Guard clause: No quantity to sell
        if sell_qty <= 0:
            return
        
        # Get execution price from router
        executed_price = current['close']
        if router:
            order = router.generate_order("BACKTEST", "SELL", current['close'], sell_qty, urgency)
            executed_price = order.get('price', current['close'])
            if 'type' in order:
                results['order_types'][i] = order['type'].value
            if 'note' in order:
                results['execution_notes'][i] = order['note']
        
        # Calculate slippage
        slippage = self._calculate_slippage(current['volume'], current['avg_volume'], sell_qty)
        
        # Calculate proceeds
        proceeds = sell_qty * executed_price * (1 - slippage)
        net_proceeds = proceeds * (1 - self.config.commission)
        
        # Execute trade
        state['cash'] += net_proceeds
        state['holdings_qty'] -= sell_qty
        results['trades'][i] = 1
        
        # Check if position is effectively closed
        if state['holdings_qty'] < 1e-6:
            state['holdings_qty'] = 0
            state['in_position'] = False
            results['exit_reasons'][i] = 'REBALANCE'

    
    def _calculate_slippage(
        self, current_volume: float, avg_volume: float, quantity: float
    ) -> float:
        """
        Calculate slippage based on liquidity impact.
        
        Simple model: slippage increases with order size relative to average volume.
        """
        if avg_volume <= 0:
            return 0.0
        
        volume_ratio = quantity / avg_volume
        # Simple linear model: 0.1% slippage per 1% of average volume
        slippage = volume_ratio * 0.001
        return min(slippage, 0.05)  # Cap at 5%
    
    def _update_state(
        self, current: Dict, state: Dict, results: Dict, i: int
    ) -> None:
        """Update state after action execution."""
        # Update position indicator
        results['positions'][i] = 1 if state['holdings_qty'] > 0 else 0
        
        # Update holdings value
        if state['holdings_qty'] > 0:
            state['holdings_value'] = state['holdings_qty'] * current['close']
        else:
            state['holdings_value'] = 0.0
        
        # Update equity
        state['equity'] = state['cash'] + state['holdings_value']
        results['equities'][i] = state['equity']
        
        # Update weight
        if state['equity'] > 0:
            results['current_weights'][i] = (state['holdings_qty'] * current['close']) / state['equity']
        else:
            results['current_weights'][i] = 0
    
    def _aggregate_results(
        self, df: pd.DataFrame, results: Dict, state: Dict
    ) -> pd.DataFrame:
        """Aggregate results into output DataFrame."""
        # Add result columns to DataFrame
        df['Regime'] = results['regimes']
        df['Position'] = results['positions']
        df['Actual_Weight'] = results['current_weights']
        df['Trades'] = results['trades']
        df['ExitReason'] = results['exit_reasons']
        df['OrderType'] = results['order_types']
        df['ExecutionNote'] = results['execution_notes']
        df['Equity'] = results['equities']
        
        # Calculate strategy returns
        df['Strategy_Return_Gross'] = df['Actual_Weight'].shift(1).fillna(0) * df['Log_Return']
        
        # Calculate net returns
        df['Net_Strategy_Return'] = df['Equity'].pct_change().fillna(0)
        df['Cumulative_Strategy_Return'] = df['Equity'] / self.config.initial_capital
        
        return df
