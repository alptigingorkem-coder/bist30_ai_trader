"""
Backtest Engine Mixin
Event-driven backtesting motoru: run_backtest, slippage, market impact.
"""
import pandas as pd
import numpy as np
import config
from typing import Optional, Union, Dict, Any


class BacktestEngineMixin:
    """Backtest motoru metotlarını sağlayan mixin."""

    def calculate_slippage(self, volume: float, avg_volume: float, position_size_qty: float) -> float:
        """
        FIX 19: Gerçekçi slippage hesabı.
        Eğer hacim bilgisi yoksa varsayılan sabit değer döner.
        """
        if pd.isna(volume) or pd.isna(avg_volume) or avg_volume == 0:
            return 0.001

        volume_impact = position_size_qty / avg_volume

        if volume_impact < 0.01:
            return 0.0002
        elif volume_impact < 0.05:
            return 0.0005
        else:
            return 0.001

    def apply_market_impact(self, price: float, size_qty: float, avg_volume: float, is_buy: bool = True) -> float:
        """
        FIX 20: Büyük pozisyonlar fiyatı hareket ettirir.
        """
        if pd.isna(avg_volume) or avg_volume == 0:
            return price

        volume_impact = size_qty / avg_volume

        if volume_impact > 0.10:
            impact = (volume_impact - 0.10) * 0.001

            if is_buy:
                return price * (1 + impact)
            else:
                return price * (1 - impact)

        return price

    def run_backtest(
        self, 
        signals_or_weights: Optional[pd.Series] = None, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        override_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Event-driven Backtest with Risk Management.
        signals_or_weights: 
            - Series of 1/0 for Signals (All-in/All-out)
            - Series of floats (0.0-1.0) for Weights (Dynamic Sizing)
            - None (Runs on internal data, passive or stress test)
        """
        from core.risk_manager import RiskManager

        # Risk Yöneticisi
        risk_manager = RiskManager()

        # Override Data for Stress Testing
        if override_data is not None:
            self.data = override_data.copy()

        # Normalize start/end dates
        if start_date:
            start_date = pd.to_datetime(start_date)
            if isinstance(self.data.index, pd.MultiIndex):
                self.data = self.data[self.data.index.get_level_values('Date') >= start_date]
            else:
                self.data = self.data[self.data.index >= start_date]

        if end_date:
            end_date = pd.to_datetime(end_date)
            if isinstance(self.data.index, pd.MultiIndex):
                self.data = self.data[self.data.index.get_level_values('Date') <= end_date]
            else:
                self.data = self.data[self.data.index <= end_date]

        # Data Slicing
        if signals_or_weights is not None:
            common_index = self.data.index.intersection(signals_or_weights.index)
            df = self.data.loc[common_index].copy()
            inputs = signals_or_weights.loc[common_index]
        else:
            df = self.data.copy()
            inputs = pd.Series(0, index=df.index)

        # Input tipini belirle
        is_weighted = False
        if inputs.dtype == float:
            if inputs.max() <= 1.0 and inputs.min() >= 0.0:
                is_weighted = True

        # ATR verisi
        if 'ATR' not in df.columns:
            df['ATR'] = np.nan

        # Rejim Verisi
        if 'Regime' not in df.columns:
            df['Regime'] = 'Trend_Up'

        # Sonuç saklama
        positions = np.zeros(len(df))
        current_weights = np.zeros(len(df))
        trades = np.zeros(len(df))
        exit_reasons = [None] * len(df)

        equities = np.zeros(len(df))
        equities[0] = self.initial_capital

        # Durum Değişkenleri
        in_position = False
        entry_price = 0.0
        entry_date = None
        peak_price = 0.0
        days_held = 0

        prices = df['Close'].values
        opens = df['Open'].values
        highs = df['High'].values
        lows = df['Low'].values
        atrs = df['ATR'].values
        regimes = df['Regime'].values
        dates = df.index
        input_values = inputs.values

        volumes = df['Volume'].values if 'Volume' in df.columns else np.zeros(len(df))
        avg_volumes = df['Volume'].rolling(20).mean().bfill().values if 'Volume' in df.columns else np.zeros(len(df))

        equity = self.initial_capital
        cash = self.initial_capital
        holdings_value = 0.0
        holdings_qty = 0.0

        peak_equity = equity
        circuit_breaker_triggered = False

        for i in range(1, len(df)):
            current_close = prices[i]
            current_open = opens[i]
            current_high = highs[i]
            current_low = lows[i]

            idx_val = dates[i]
            if isinstance(idx_val, tuple):
                current_date = idx_val[0]
            else:
                current_date = idx_val

            current_atr = atrs[i]
            current_regime = regimes[i]
            input_val = input_values[i]

            # --- Valuation Update ---
            if holdings_qty > 0:
                holdings_value = holdings_qty * current_close
                in_position = True
            else:
                holdings_value = 0.0
                in_position = False

            equity = cash + holdings_value

            if equity > peak_equity:
                peak_equity = equity

            dd = (equity - peak_equity) / peak_equity if peak_equity > 0 else 0

            if dd < -0.30 and not circuit_breaker_triggered:
                print(f"!!! CIRCUIT BREAKER TETİKLENDİ ({current_date.date()}) !!! Drawdown: {dd:.2%}. İşlemler durduruluyor.")
                if holdings_qty > 0:
                    trades[i] = 1
                    exit_reasons[i] = 'CIRCUIT_BREAKER'
                    sell_price = current_open
                    cash += holdings_qty * sell_price * (1 - self.commission)
                    holdings_qty = 0
                    holdings_value = 0

                circuit_breaker_triggered = True
                positions[i] = 0
                current_weights[i] = 0
                equity = cash
                equities[i] = equity
                continue

            if circuit_breaker_triggered:
                positions[i] = 0
                current_weights[i] = 0
                equities[i] = cash
                continue

            # Risk Parameters Update
            risk_manager.adjust_for_regime(current_regime)

            if np.isnan(current_atr):
                current_atr = current_close * 0.03

            # --- DECISION LOGIC ---
            action = 'HOLD'
            target_qty = holdings_qty
            exit_reason = None

            # 1. RISK MANAGER CHECKS
            if in_position:
                days_held = (current_date - entry_date).days
                if current_high > peak_price:
                    peak_price = current_high

                check_res, reason = risk_manager.check_exit_conditions(current_close, entry_price, peak_price, current_atr, days_held)

                if check_res == 'SELL':
                    action = 'SELL'
                    exit_reason = reason

            # 2. SIGNAL / WEIGHT CHECK
            if action == 'HOLD':
                if is_weighted:
                    base_weight = input_val

                    if getattr(config, 'ENABLE_RISK_SIZING', False):
                        stop_dist = risk_manager.get_stop_distance(current_close, current_atr)
                        risk_weight = config.RISK_PER_TRADE / (stop_dist + 1e-6)
                        target_weight = min(base_weight, risk_weight, config.MAX_SINGLE_POS_WEIGHT)
                    elif getattr(config, 'ENABLE_KELLY', True):
                        kelly_size_tl = self.position_sizer.get_position_size(equity, confidence=input_val)
                        kelly_weight = kelly_size_tl / equity
                        target_weight = min(kelly_weight, config.MAX_SINGLE_POS_WEIGHT)
                    else:
                        target_weight = base_weight

                    if target_weight < 0:
                        target_weight = 0
                    if target_weight > 1:
                        target_weight = 1

                    target_value = equity * target_weight
                    target_qty_calc = target_value / current_close

                    qty_diff_pct = 0
                    if holdings_qty > 0:
                        qty_diff_pct = abs(target_qty_calc - holdings_qty) / holdings_qty
                    else:
                        qty_diff_pct = 1.0 if target_qty_calc > 0 else 0

                    if qty_diff_pct > 0.10:
                        if target_qty_calc > holdings_qty:
                            action = 'BUY'
                            target_qty = target_qty_calc
                        elif target_qty_calc < holdings_qty:
                            min_holding = getattr(config, 'MIN_HOLDING_DAYS', 0)
                            if days_held >= min_holding:
                                action = 'SELL' if target_qty_calc < (holdings_qty * 0.1) else 'REBALANCE_SELL'
                                target_qty = target_qty_calc
                                if action == 'SELL':
                                    exit_reason = 'WEIGHT_ZERO'
                            else:
                                action = 'HOLD'

                else:
                    # Binary Signal
                    if input_val == 1 and not in_position:
                        action = 'BUY'
                        target_qty = (cash * 0.99) / current_close
                    elif input_val == 0 and in_position:
                        if days_held >= risk_manager.min_holding_periods:
                            action = 'SELL'
                            exit_reason = 'SIGNAL_LOST'
                            target_qty = 0

            # --- EXECUTION ---
            current_volume = volumes[i]
            current_avg_vol = avg_volumes[i]

            if action == 'BUY' or action == 'REBALANCE_SELL':
                diff_qty = target_qty - holdings_qty

                if diff_qty > 0:  # BUY
                    slippage = self.calculate_slippage(current_volume, current_avg_vol, diff_qty)
                    executed_price = self.apply_market_impact(current_close, diff_qty, current_avg_vol, is_buy=True)

                    cost = diff_qty * executed_price * (1 + slippage)
                    total_cost = cost * (1 + self.commission)

                    if cash >= total_cost:
                        cash -= total_cost
                        holdings_qty += diff_qty
                        trades[i] = 1

                        if in_position and holdings_qty > 0:
                            entry_price = (entry_price * (holdings_qty - diff_qty) + executed_price * diff_qty) / holdings_qty
                        else:
                            entry_price = executed_price
                            entry_date = current_date
                            peak_price = current_close

                elif diff_qty < 0:  # SELL
                    sell_qty = abs(diff_qty)
                    slippage = self.calculate_slippage(current_volume, current_avg_vol, sell_qty)
                    executed_price = self.apply_market_impact(current_close, sell_qty, current_avg_vol, is_buy=False)

                    proceeds = sell_qty * executed_price * (1 - slippage)
                    net_proceeds = proceeds * (1 - self.commission)

                    cash += net_proceeds
                    holdings_qty -= sell_qty
                    trades[i] = 1
                    if holdings_qty < 1e-6:
                        holdings_qty = 0
                        in_position = False
                        exit_reasons[i] = exit_reason or 'REBALANCE'

            elif action == 'SELL':  # Full Sell
                if holdings_qty > 0:
                    slippage = self.calculate_slippage(current_volume, current_avg_vol, holdings_qty)
                    executed_price = self.apply_market_impact(current_close, holdings_qty, current_avg_vol, is_buy=False)

                    proceeds = holdings_qty * executed_price * (1 - slippage)
                    net_proceeds = proceeds * (1 - self.commission)

                    cash += net_proceeds
                    holdings_qty = 0
                    trades[i] = 1
                    in_position = False
                    exit_reasons[i] = exit_reason

                    if entry_price > 0:
                        pnl_pct = (executed_price - entry_price) / entry_price
                        self.position_sizer.add_trade(pnl_pct)

            # Kayıt
            positions[i] = 1 if holdings_qty > 0 else 0
            if holdings_qty > 0:
                holdings_value = holdings_qty * current_close
            else:
                holdings_value = 0.0

            equity = cash + holdings_value
            equities[i] = equity

            current_weights[i] = (holdings_qty * current_close) / equity if equity > 0 else 0

        # Sonuçları DataFrame'e yaz
        df['Position'] = positions
        df['Actual_Weight'] = current_weights
        df['Trades'] = trades
        df['ExitReason'] = exit_reasons
        df['Equity'] = equities

        df['Strategy_Return_Gross'] = df['Actual_Weight'].shift(1).fillna(0) * df['Log_Return']

        commission_cost = df['Trades'] * self.commission

        self.results = df
        return df
