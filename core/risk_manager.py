import config
import pandas as pd
import numpy as np

class RiskManager:
    def __init__(self):
        self.stop_loss_mult = config.ATR_STOP_LOSS_MULTIPLIER
        self.take_profit_mult = config.ATR_TAKE_PROFIT_MULTIPLIER
        self.trailing_stop_mult = config.ATR_TRAILING_STOP_MULTIPLIER
        self.min_holding_periods = config.MIN_HOLDING_PERIODS
        self.max_stop_loss_pct = config.MAX_STOP_LOSS_PCT
        self.trailing_active = config.TRAILING_STOP_ACTIVE
        self.current_regime = None # Initialize current_regime

    def adjust_for_regime(self, regime):
        """
        Piyasa rejimine göre risk parametrelerini dinamik olarak ayarlar.
        Regimler: Sideways, Crash_Bear, Trend_Up
        """
        self.current_regime = regime 
        
        if regime == 'Crash_Bear': # Kriz/Ayı
            self.stop_loss_mult = 1.5 
            self.trailing_stop_mult = 1.5
            self.take_profit_mult = 5.0 
            
        elif regime == 'Sideways': # Yatay
            self.stop_loss_mult = 2.0
            self.trailing_stop_mult = 2.5
            self.take_profit_mult = 3.0
            
        elif regime == 'Trend_Up': # Ralli
            self.stop_loss_mult = 3.0 
            self.trailing_stop_mult = 3.5
            self.take_profit_mult = 999.0 # Kar Al Devre Dışı
        
        else:
            # Bilinmeyen rejim fallback (Sideways varsay)
             self.stop_loss_mult = 2.0
             self.trailing_stop_mult = 2.5
             self.take_profit_mult = 3.0

    def check_exit_conditions(self, current_price, entry_price, peak_price, atr, days_held):
        """
        Çıkış koşullarını kontrol eder.
        Döner: 'SELL' veya 'HOLD'
        """
        # 1. Dinamik Stop (ATR Bazlı) - Başlangıç Stopu
        current_atr = atr if not np.isnan(atr) else entry_price * 0.05
        
        dynamic_stop_price = entry_price - (current_atr * self.stop_loss_mult)
        
        # Hard Stop (Sigorta) - Max % kayıp
        hard_stop_price = entry_price * (1 - self.max_stop_loss_pct)
        
        effective_stop = max(dynamic_stop_price, hard_stop_price)
        
        if current_price < effective_stop:
            return 'SELL', 'STOP_LOSS'

        # 2. Trailing Stop (İzleyen Stop)
        if self.trailing_active and current_price > entry_price:
            trailing_stop_price = peak_price - (current_atr * self.trailing_stop_mult)
            if current_price < trailing_stop_price:
                return 'SELL', 'TRAILING_STOP'

        # 3. Take Profit (Kar Al) - Ralli Modunda İPTAL
        # Eğer 'Trend_Up' modundaysak, hedef fiyattan çıkma, trendi sür.
        # Sadece diğer rejimlerde hedef karı al.
        if self.current_regime != 'Trend_Up':
            take_profit_price = entry_price + (current_atr * self.take_profit_mult)
            if current_price >= take_profit_price:
                return 'SELL', 'TAKE_PROFIT'
            
        return 'HOLD', None
