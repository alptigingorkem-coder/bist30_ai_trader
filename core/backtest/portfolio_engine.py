
"""
Vectorized Portfolio Backtester (O(1) Matrix Engine)
Architecture: Shared Capital, Matrix Operations, Dynamic Slippage.
Designed for BIST100 Scalability.
"""

import pandas as pd
import numpy as np
import config
from core.risk_manager import RiskManager
from utils.constants import (
    INITIAL_CAPITAL_PAPER,
    COMMISSION_RATE,
    CACHE_ROLLING_WINDOW,
    BASE_SLIPPAGE,
    IMPACT_SLIPPAGE_FACTOR,
    MAX_SLIPPAGE,
    DEFAULT_SLIPPAGE
)
import logging

logger = logging.getLogger(__name__)

class PortfolioBacktester:
    def __init__(self, initial_capital: float = INITIAL_CAPITAL_PAPER, commission: float = COMMISSION_RATE):
        self.initial_capital = initial_capital
        self.commission = commission
        self.risk_manager = RiskManager()
        
    def run_backtest(self, prices: pd.DataFrame, signals: pd.DataFrame, volumes: pd.DataFrame = None) -> pd.DataFrame:
        """
        Run vectorized backtest on a portfolio of assets.

        Args:
            prices (pd.DataFrame): Close prices (Index=Date, Cols=Tickers)
            signals (pd.DataFrame): Target Weights (0.0 - 1.0) or Signals (Index=Date, Cols=Tickers)
            volumes (pd.DataFrame): Volume data for slippage/liquidity check.

        Returns:
            pd.DataFrame: Portfolio Level Metrics (Equity, Drawdown, etc.)
        """
        # Align and prepare data
        P, W_vals, V_vals, V_TL_vals, Avg_V_vals, dates = self._prepare_data(prices, signals, volumes)

        n_days, n_assets = P.shape

        # Initialize portfolio state
        cash, holdings_qty, equity_curve = self._initialize_portfolio_state(n_days, n_assets)

        # Run backtest loop
        cash, holdings_qty, equity_curve = self._run_backtest_loop(
            P, W_vals, V_vals, Avg_V_vals, cash, holdings_qty, equity_curve
        )

        # Calculate and return metrics
        return self._calculate_metrics(dates, equity_curve)

    def _prepare_data(self, prices: pd.DataFrame, signals: pd.DataFrame, volumes: pd.DataFrame = None):
        """Align and prepare data for backtest."""
        # Align Data
        common_index = prices.index.intersection(signals.index)
        P = prices.loc[common_index].copy()
        W_target = signals.loc[common_index].copy().fillna(0.0)

        # Process volumes
        V, V_TL = self._process_volumes(P, volumes, common_index)

        # Convert to numpy arrays
        P_vals = P.values
        W_vals = W_target.values.copy()
        V_vals = V.values if V is not None else np.zeros(P.shape)
        V_TL_vals = V_TL.values if V_TL is not None else np.zeros(P.shape)

        # Calculate average volume
        Avg_V_vals = self._calculate_avg_volume(V, P.shape)

        # Apply liquidity filter
        W_vals = self._apply_liquidity_filter(W_vals, V_TL, P.shape)

        return P_vals, W_vals, V_vals, V_TL_vals, Avg_V_vals, P.index

    def _process_volumes(self, P: pd.DataFrame, volumes: pd.DataFrame, common_index):
        """Process volume data and calculate volume in TL."""
        if volumes is not None:
            V = volumes.loc[common_index].copy().fillna(0.0)
            V_TL = P * V
        else:
            V = None
            V_TL = None
        return V, V_TL

    def _calculate_avg_volume(self, V: pd.DataFrame, shape: tuple):
        """Calculate 20-day average volume."""
        if V is not None:
            Avg_V = V.rolling(window=CACHE_ROLLING_WINDOW, min_periods=1).mean()
            return Avg_V.values
        else:
            return np.ones(shape)

    def _apply_liquidity_filter(self, W_vals: np.ndarray, V_TL: pd.DataFrame, shape: tuple):
        """Apply liquidity filter to weights."""
        min_liq = getattr(config, 'MIN_LIQUIDITY_THRESHOLD', 0)
        if min_liq > 0 and V_TL is not None:
            Rolling_V_TL = V_TL.rolling(window=CACHE_ROLLING_WINDOW, min_periods=1).mean()
            Liq_Mask = (Rolling_V_TL < min_liq).values
            W_vals[Liq_Mask] = 0.0
        return W_vals

    def _initialize_portfolio_state(self, n_days: int, n_assets: int):
        """Initialize portfolio state arrays."""
        cash = self.initial_capital
        holdings_qty = np.zeros(n_assets)
        equity_curve = np.zeros(n_days)
        return cash, holdings_qty, equity_curve

    def _run_backtest_loop(self, P_vals, W_vals, V_vals, Avg_V_vals, cash, holdings_qty, equity_curve):
        """Execute main backtest loop over all days."""
        n_days = P_vals.shape[0]

        for t in range(n_days):
            cash, holdings_qty = self._process_day(
                t, P_vals, W_vals, V_vals, Avg_V_vals, cash, holdings_qty
            )

            # Record end-of-day equity
            equity_curve[t] = self._calculate_equity(cash, holdings_qty, P_vals[t])

        return cash, holdings_qty, equity_curve

    def _process_day(self, t: int, P_vals, W_vals, V_vals, Avg_V_vals, cash, holdings_qty):
        """Process a single trading day."""
        current_prices = P_vals[t]
        target_weights = W_vals[t]

        # Calculate current equity
        current_equity = self._calculate_equity(cash, holdings_qty, current_prices)

        if current_equity <= 0:
            return cash, holdings_qty

        # Calculate target quantities
        target_qty = self._calculate_target_quantities(current_equity, target_weights, current_prices)

        # Calculate trades
        trade_qty = target_qty - holdings_qty

        # Execute trades if needed
        if np.any(np.abs(trade_qty) > 1e-6):
            cash = self._execute_trades(
                cash, holdings_qty, trade_qty, current_prices,
                Avg_V_vals[t] if V_vals is not None else None
            )
            holdings_qty += trade_qty

        return cash, holdings_qty

    def _calculate_equity(self, cash: float, holdings_qty: np.ndarray, prices: np.ndarray) -> float:
        """Calculate total portfolio equity."""
        holdings_val = np.sum(holdings_qty * prices)
        return cash + holdings_val

    def _calculate_target_quantities(self, equity: float, weights: np.ndarray, prices: np.ndarray):
        """Calculate target quantities based on weights."""
        target_holdings_val = equity * weights
        target_qty = target_holdings_val / prices
        return np.nan_to_num(target_qty)

    def _execute_trades(self, cash: float, holdings_qty: np.ndarray, trade_qty: np.ndarray,
                       current_prices: np.ndarray, avg_vol: np.ndarray):
        """Execute trades and update cash."""
        # Calculate slippage
        slippage_rates = self._calculate_slippage(trade_qty, avg_vol)

        # Calculate transaction costs
        transaction_price = current_prices * (1 + np.sign(trade_qty) * slippage_rates)
        transaction_cost = trade_qty * transaction_price
        commission_cost = np.abs(transaction_cost) * self.commission

        # Update cash
        total_cash_change = -np.sum(transaction_cost) - np.sum(commission_cost)
        return cash + total_cash_change

    def _calculate_slippage(self, trade_qty: np.ndarray, avg_vol: np.ndarray):
        """Calculate slippage rates based on trade size and volume."""
        if avg_vol is not None:
            inv_avg_vol = np.where(avg_vol > 0, 1.0/avg_vol, 0.0)
            participation = np.abs(trade_qty) * inv_avg_vol

            base_slip = BASE_SLIPPAGE
            impact_slip = participation * IMPACT_SLIPPAGE_FACTOR
            return np.minimum(base_slip + impact_slip, MAX_SLIPPAGE)
        else:
            return np.full(len(trade_qty), DEFAULT_SLIPPAGE)

    def _calculate_metrics(self, dates, equity_curve: np.ndarray) -> pd.DataFrame:
        """Calculate portfolio metrics."""
        res = pd.DataFrame(index=dates)
        res['Equity'] = equity_curve
        res['Drawdown'] = (res['Equity'] - res['Equity'].cummax()) / res['Equity'].cummax()
        res['Returns'] = res['Equity'].pct_change().fillna(0)
        return res

