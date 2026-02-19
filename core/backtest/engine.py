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
        FIX 19: Gerçekçi slippage hesabı (Spread + Market Impact).
        Kümülatif maliyet oranını döner.
        """
        if pd.isna(volume) or pd.isna(avg_volume) or avg_volume == 0:
            return 0.001

        volume_ratio = position_size_qty / avg_volume
        
        # 1. Base Spread (Liquidity based)
        base_slippage = 0.0005
        if volume_ratio < 0.01:
            base_slippage = 0.0002
        elif volume_ratio < 0.05:
            base_slippage = 0.0005
        else:
            base_slippage = 0.001

        # 2. Market Impact (Size based)
        # Kurumsal Denetim: Double Counting'i önlemek için impact buraya dahil edildi.
        market_impact = 0.0
        if volume_ratio > 0.10:
            # Her %10 fazlalık için %5 impact (Kurumsal Düzeltme)
            # Örnek: %50 volume -> (0.5 - 0.1) * 0.05 = 0.02 (%2)
            market_impact = (volume_ratio - 0.10) * 0.05
            
        return base_slippage + market_impact



    def _get_market_indicators(self, current_slice: pd.DataFrame) -> pd.DataFrame:
        """
        Rejim tespiti için gerekli market-wide göstergeleri hazırla.
        Single-asset modunda olduğumuz için mevcut df slice'ı kullanıyoruz.
        Bu df zaten VIX, USDTRY vb. makro verileri içeriyor olmalı.
        """
        return current_slice


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

        # --- REGIME DETECTION INTEGRATION ---
        from models.regime_detector import RegimeDetector
        # HEAD OF QUANT: Execution Manager & SOR
        from core.execution import ExecutionManager, SmartOrderRouter, Urgency
        
        # Initialize SOR
        exec_manager = ExecutionManager(commission_rate=getattr(self, 'commission', 0.002))
        router = SmartOrderRouter(exec_manager)
        
        # Create a config wrapper/dict for RegimeDetector
        regime_config = {
            'REGIME_THRESHOLDS': getattr(config, 'REGIME_THRESHOLDS', {}),
            'REGIME_ACTIONS': getattr(config, 'REGIME_ACTIONS', {})
        }
        regime_detector = RegimeDetector(regime_config)
        
        print("  Regime Detection Running...")
        
        # FIX: Pre-calculate ATR Moving Average
        if 'ATR' in df.columns and 'ATR_MA_60' not in df.columns:
             df['ATR_MA_60'] = df['ATR'].rolling(60).mean().bfill() 
             
        if 'Log_Return' not in df.columns:
            df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
            
        if 'Volatility_20' not in df.columns:
            df['Volatility_20'] = df['Log_Return'].rolling(20).std().fillna(0) # Keep 0 or small number
        
        regimes = [None] * len(df)
        order_types = [None] * len(df) # NEW: Track Order Type
        execution_notes = [None] * len(df) # NEW: Track Notes

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

            # Circuit breaker eşiği config'den okunuyor (varsayılan -%30)
            circuit_breaker_threshold = -getattr(config, 'MAX_DRAWDOWN_LIMIT', 0.30)
            
            if dd < circuit_breaker_threshold and not circuit_breaker_triggered:
                print(f"!!! CIRCUIT BREAKER TETİKLENDİ ({current_date.date()}) !!! Drawdown: {dd:.2%}. İşlemler durduruluyor.")
                if holdings_qty > 0:
                    trades[i] = 1
                    exit_reasons[i] = 'CIRCUIT_BREAKER'
                    
                    # SOR: Circuit Breaker -> HIGH Urgency
                    order = router.generate_order(
                        symbol="BACKTEST", side="SELL", price=current_open, 
                        quantity=holdings_qty, urgency=Urgency.HIGH
                    )
                    sell_price = order['price']
                    order_types[i] = order['type'].value
                    execution_notes[i] = order['note']
                    
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

            # Risk & Regime Logic
            current_slice = df.iloc[[i]].copy()
            market_data = self._get_market_indicators(current_slice)
            current_regime = regime_detector.detect_regime(market_data)
            regimes[i] = current_regime
            
            if hasattr(risk_manager, 'adjust_for_regime'):
                 risk_manager.adjust_for_regime(current_regime)

            # --- DECISION LOGIC ---
            action = 'HOLD'
            target_qty = holdings_qty
            exit_reason = None
            urgency = Urgency.NORMAL # Default

            regime_action = regime_detector.get_trading_action(current_regime)
            should_trade = regime_action.get('trade', True)
            pos_mult = regime_action.get('position_multiplier', 1.0)
            force_exit = regime_action.get('force_exit', False)

            if force_exit:
                if in_position:
                    action = 'SELL'
                    exit_reason = f'CRISIS_{current_regime}'
                    urgency = Urgency.HIGH # Crisis = Panic Sell
                target_qty = 0
                
            elif not should_trade:
                if in_position:
                    action = 'SELL'
                    exit_reason = f'REGIME_{current_regime}'
                    urgency = Urgency.NORMAL # Volatility avoidance, not panic
                target_qty = 0
                
            else:
                 pass # Check Risk Manager

            # 1. RISK MANAGER CHECKS
            if in_position and action == 'HOLD':
                days_held = (current_date - entry_date).days
                if current_high > peak_price:
                    peak_price = current_high

                check_res, reason = risk_manager.check_exit_conditions(current_close, entry_price, peak_price, current_atr, days_held)

                if check_res == 'SELL':
                    action = 'SELL'
                    exit_reason = reason
                    # Stop Loss -> HIGH, Take Profit -> NORMAL/LOW
                    if 'STOP' in reason: urgency = Urgency.HIGH
                    elif 'PROFIT' in reason: urgency = Urgency.NORMAL


            # 2. SIGNAL / WEIGHT CHECK
            if action == 'HOLD':
                if is_weighted:
                    base_weight = input_val
                    # ... Sizing Logic ...
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
                    
                    target_weight *= pos_mult
                    if target_weight < 0: target_weight = 0
                    if target_weight > 1: target_weight = 1

                    target_value = equity * target_weight
                    target_qty_calc = target_value / current_close

                    qty_diff_pct = 0
                    if holdings_qty > 0:
                        qty_diff_pct = abs(target_qty_calc - holdings_qty) / holdings_qty
                    else:
                        qty_diff_pct = 1.0 if target_qty_calc > 0 else 0

                    if qty_diff_pct > 0.10: # Threshold
                        if target_qty_calc > holdings_qty:
                            action = 'BUY'
                            target_qty = target_qty_calc
                            # New Entry or Big Add -> NORMAL
                            urgency = Urgency.NORMAL
                        elif target_qty_calc < holdings_qty:
                            min_holding = getattr(config, 'MIN_HOLDING_DAYS', 0)
                            if days_held >= min_holding:
                                action = 'SELL' if target_qty_calc < (holdings_qty * 0.1) else 'REBALANCE_SELL'
                                target_qty = target_qty_calc
                                if action == 'SELL': exit_reason = 'WEIGHT_ZERO'
                                # Rebalancing is usually passive
                                urgency = Urgency.LOW
                            else:
                                action = 'HOLD'

                else:
                    # Binary Signal
                    if input_val == 1 and not in_position:
                        action = 'BUY'
                        target_qty = (cash * 0.99) / current_close
                        urgency = Urgency.NORMAL
                    elif input_val == 0 and in_position:
                        if days_held >= risk_manager.min_holding_periods:
                            action = 'SELL'
                            exit_reason = 'SIGNAL_LOST'
                            target_qty = 0
                            urgency = Urgency.NORMAL 

            # --- EXECUTION ---
            current_volume = volumes[i]
            current_avg_vol = avg_volumes[i]

            if action == 'BUY' or action == 'REBALANCE_SELL':
                diff_qty = target_qty - holdings_qty

                if diff_qty > 0:  # BUY
                    # SOR Generation
                    order = router.generate_order("BACKTEST", "BUY", current_close, abs(diff_qty), urgency)
                    executed_price = order['price']
                    order_types[i] = order['type'].value
                    execution_notes[i] = order['note']
                    
                    # Original Slippage (Liquidity Impact only)
                    slippage = self.calculate_slippage(current_volume, current_avg_vol, diff_qty)
                    # Use SOR Price + Liquidity Slippage
                    
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

                elif diff_qty < 0:  # SELL (Rebalance)
                    sell_qty = abs(diff_qty)
                    
                    # SOR Generation
                    order = router.generate_order("BACKTEST", "SELL", current_close, sell_qty, urgency)
                    executed_price = order['price']
                    order_types[i] = order['type'].value
                    execution_notes[i] = order['note']

                    slippage = self.calculate_slippage(current_volume, current_avg_vol, sell_qty)
                    
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
                    # SOR Generation
                    order = router.generate_order("BACKTEST", "SELL", current_close, holdings_qty, urgency)
                    executed_price = order['price']
                    order_types[i] = order['type'].value
                    execution_notes[i] = order['note']
                    
                    slippage = self.calculate_slippage(current_volume, current_avg_vol, holdings_qty)

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
        df['Regime'] = regimes
        df['Position'] = positions
        df['Actual_Weight'] = current_weights
        df['Trades'] = trades
        df['ExitReason'] = exit_reasons
        df['OrderType'] = order_types # NEW
        df['ExecutionNote'] = execution_notes # NEW
        df['Equity'] = equities

        df['Strategy_Return_Gross'] = df['Actual_Weight'].shift(1).fillna(0) * df['Log_Return']

        commission_cost = df['Trades'] * self.commission

        self.results = df
        
        # FIX: Calculate Missing Columns for Metrics Mixin
        df['Net_Strategy_Return'] = df['Equity'].pct_change().fillna(0)
        df['Cumulative_Strategy_Return'] = df['Equity'] / self.initial_capital
        
        return df
