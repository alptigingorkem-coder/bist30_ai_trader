
"""
Vectorized Portfolio Backtester (O(1) Matrix Engine)
Architecture: Shared Capital, Matrix Operations, Dynamic Slippage.
Designed for BIST100 Scalability.
"""

import pandas as pd
import numpy as np
import config
from core.risk_manager import RiskManager
import logging

logger = logging.getLogger(__name__)

class PortfolioBacktester:
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.002):
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
        # Align Data
        common_index = prices.index.intersection(signals.index)
        P = prices.loc[common_index].copy()
        W_target = signals.loc[common_index].copy().fillna(0.0)
        
        if volumes is not None:
            V = volumes.loc[common_index].copy().fillna(0.0)
            # Calculate Volume in TL (Price * Volume) for liquidity check
            # Assuming V is Lot count. If V is TL, adjust accordingly.
            # Standard: V is Lot.
            V_TL = P * V
        else:
            V = None
            V_TL = None

        # Dimensions
        n_days, n_assets = P.shape
        tickers = P.columns
        
        # Portfolio State Arrays (Vectorized where possible, looped for path dependence)
        # Note: True vectorization of path-dependent equity with rebalancing costs 
        # is hard without loop. We will use a fast loop over days (O(T)), but 
        # vector operations over assets (O(1)*N). This is semi-vectorized.
        
        cash = self.initial_capital
        holdings_qty = np.zeros(n_assets) # Current shares per ticker
        equity_curve = np.zeros(n_days)
        
        # Pre-calculate Returns (for validation)
        # R = P.pct_change().fillna(0)
        
        # Convert DataFrames to Numpy for speed
        P_vals = P.values
        W_vals = W_target.values.copy()
        V_vals = V.values if V is not None else np.zeros((n_days, n_assets))
        V_TL_vals = V_TL.values if V_TL is not None else np.zeros((n_days, n_assets))
        dates = P.index
        
        # 20-day Avg Volume for Slippage (Rolling Mean is fast in Pandas)
        if V is not None:
            Avg_V = V.rolling(window=20, min_periods=1).mean()
            Avg_V_vals = Avg_V.values
        else:
            Avg_V_vals = np.ones((n_days, n_assets)) # Avoid div/0
            
        # Liquidity Filter Mask (Global)
        # If Volume < Threshold -> Weight = 0
        min_liq = getattr(config, 'MIN_LIQUIDITY_THRESHOLD', 0)
        if min_liq > 0 and V_TL is not None:
           # Mask where rolling avg volume is low
           # Use DataFrame for rolling, then convert to numpy
           # min_periods=1 allows trading from day 1 if volume confirms
           Rolling_V_TL = V_TL.rolling(window=20, min_periods=1).mean()
           Liq_Mask = (Rolling_V_TL < min_liq).values
           # Apply mask to Weights (Force 0 allocation)
           W_vals[Liq_Mask] = 0.0
        
        # --- FAST LOOP (Days) ---
        for t in range(n_days):
            current_prices = P_vals[t]
            target_weights = W_vals[t]
            
            # 1. Calculate Current Equity (Pre-Trade) for Sizing
            current_holdings_val = np.sum(holdings_qty * current_prices)
            current_equity = cash + current_holdings_val
            
            # 2. Determine Target Portfolio Value
            # Rebalance Logic:
            # Target Value_i = Equity * Weight_i
            # Target Qty_i = Target Value_i / Price_i
            
            # Prevent rebalancing if equity is broken
            if current_equity <= 0:
                continue
                
            target_holdings_val = current_equity * target_weights
            target_qty = target_holdings_val / current_prices
            # Fix inf/nan
            target_qty = np.nan_to_num(target_qty)
            
            # 3. Calculate Trade Sizes
            trade_qty = target_qty - holdings_qty
            
            # Filter small trades (Buffer) to save commission
            # trade_val = trade_qty * current_prices
            # mask_small = np.abs(trade_val) < (current_equity * 0.005) # 0.5% buffer
            # trade_qty[mask_small] = 0
            
            # 4. Execute Trades & Calculate Costs
            if np.any(np.abs(trade_qty) > 1e-6):
                # Slippage Calculation (Vectorized over assets)
                # impact = base + (trade / avg_vol)*scale
                if V is not None:
                     current_avg_vol = Avg_V_vals[t]
                     # Safe divide
                     inv_avg_vol = np.where(current_avg_vol > 0, 1.0/current_avg_vol, 0.0)
                     participation = np.abs(trade_qty) * inv_avg_vol
                     
                     base_slip = 0.0005
                     impact_slip = participation * 0.1
                     slippage_rates = np.minimum(base_slip + impact_slip, 0.03)
                else:
                    slippage_rates = np.full(n_assets, 0.001)

                transaction_price = current_prices * (1 + np.sign(trade_qty) * slippage_rates)
                transaction_cost = trade_qty * transaction_price
                
                commission_cost = np.abs(transaction_cost) * self.commission
                
                # Net Cash Flow
                # Buy (Qty > 0): -Cost - Comm
                # Sell (Qty < 0): -Cost - Comm (Cost is negative for sell, so -(-Cost) = +Cash)
                # Formula: Cash change = - (TradeQty * Price) - Commission
                # Check sign: Buy 10 @ 10 = -100. Sell 10 @ 10 = +100. Correct.
                
                total_cash_change = -np.sum(transaction_cost) - np.sum(commission_cost)
                
                cash += total_cash_change
                holdings_qty += trade_qty
                
            # 5. Record End-of-Day Equity
            eod_holdings_val = np.sum(holdings_qty * current_prices)
            equity_curve[t] = cash + eod_holdings_val
                
        # --- END LOOP ---
        
        # Metrics DataFrame
        res = pd.DataFrame(index=dates)
        res['Equity'] = equity_curve
        res['Drawdown'] = (res['Equity'] - res['Equity'].cummax()) / res['Equity'].cummax()
        res['Returns'] = res['Equity'].pct_change().fillna(0)
        
        return res
