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
            self.trailing_stop_mult = 1.0 # 1.5 -> 1.0 (Daha sıkı)
            self.take_profit_mult = 5.0 
            
        elif regime == 'Sideways': # Yatay
            self.stop_loss_mult = 2.0
            self.trailing_stop_mult = 2.0 # 2.5 -> 2.0 (Daha sıkı takip)
            self.take_profit_mult = 3.0
            
        elif regime == 'Trend_Up': # Ralli
            self.stop_loss_mult = config.ATR_STOP_LOSS_MULTIPLIER 
            self.trailing_stop_mult = config.ATR_TRAILING_STOP_MULTIPLIER
            self.take_profit_mult = config.ATR_TAKE_PROFIT_MULTIPLIER
        
        else:
            # Bilinmeyen rejim fallback (Trend_Up Say)
             self.stop_loss_mult = config.ATR_STOP_LOSS_MULTIPLIER
             self.trailing_stop_mult = config.ATR_TRAILING_STOP_MULTIPLIER
             self.take_profit_mult = config.ATR_TAKE_PROFIT_MULTIPLIER

    def get_stop_distance(self, price, atr):
        """
        Stop mesafesini yüzde olarak döndürür.
        Pozisyon büyüklüğü hesaplamak için kullanılır.
        """
        if np.isnan(atr) or atr == 0:
            return config.MAX_STOP_LOSS_PCT # Fallback
            
        dynamic_dist = (atr * self.stop_loss_mult) / price
        # Max stop loss ile sınırla (Sigorta)
        return min(dynamic_dist, config.MAX_STOP_LOSS_PCT)

    def check_exit_conditions(self, current_price, entry_price, peak_price, atr, days_held):
        """
        Çıkış koşullarını kontrol eder (Sıkılaştırılmış Trailing Stop).
        Döner: 'SELL' veya 'HOLD'
        """
        # 1. Analiz
        current_atr = atr if not np.isnan(atr) else entry_price * 0.05
        
        # Başlangıç Stopu (Entry day)
        initial_stop_dist = current_atr * self.stop_loss_mult
        initial_stop_price = entry_price - initial_stop_dist
        
        # Hard Stop (Yüzdesel Sigorta)
        hard_stop_price = entry_price * (1 - self.max_stop_loss_pct)
        
        # 2. Stop Loss Kontrolü
        # Eğer fiyat en baştan belirlenen stopun altına indiyse ÇIK
        effective_initial_stop = max(initial_stop_price, hard_stop_price)
        
        if current_price < effective_initial_stop:
            return 'SELL', 'STOP_LOSS'

        # 3. Trailing Stop (Sıkılaştırılmış)
        if self.trailing_active:
             # Trailing stop mesafesi normal stopun %80'i kadar olabilir (Daha sıkı takip)
             tight_multiplier = self.trailing_stop_mult
             
             trailing_stop_price = peak_price - (current_atr * tight_multiplier)
             
             # Trailing stop kârdayken aktifleşsin gibi bir kısıt koymuyoruz (User isteği: Sıkılaştır)
             if current_price < trailing_stop_price:
                 # Sadece kâra geçtikten sonra trailing stop devreye girerse 'Profit Protection' olur.
                 # Ama biz her türlü geri çekilmede koruma istiyoruz.
                 return 'SELL', 'TRAILING_STOP'

        # 4. Take Profit (Kar Al)
        # Trend_Up'da TP çok yüksek ama var (Trend dönüşlerini/aşırı alımı kaçırmamak için)
        take_profit_price = entry_price + (current_atr * self.take_profit_mult)
        if current_price >= take_profit_price:
            return 'SELL', 'TAKE_PROFIT'
            
        return 'HOLD', None

    def calculate_position_size(self, capital, price, atr, win_rate=0.55, win_loss_ratio=2.0):
        """
        Kelly Criterion (Half-Kelly) ile pozisyon büyüklüğü hesaplar.
        f = (p * b - q) / b
        p: Win Rate
        b: Win/Loss Ratio
        q: Loss Rate (1-p)
        """
        if atr <= 0 or price <= 0: return 0.0
        
        # 1. Kelly Oranı Hesapla
        p = win_rate
        b = win_loss_ratio
        q = 1 - p
        
        kelly_fraction = (p * b - q) / b
        
        # 2. Negatif Kelly (Beklenti < 0) -> İşlem Yapma
        if kelly_fraction <= 0:
            return 0.0
            
        # 3. Half-Kelly (Güvenlik Payı)
        # Tam Kelly çok risklidir ve volatilite yaratır. Yarısı kadar risk alıyoruz.
        safe_fraction = kelly_fraction * 0.5
        
        # 4. Maksimum Risk Sınırı (Portföyün %20'sinden fazlasını tek hisseye bağlama)
        # Bu config'den de gelebilir ama buraya hardcoded güvenlik ekliyoruz.
        MAX_ALLOCATION = 0.20
        allocation = min(safe_fraction, MAX_ALLOCATION)
        
        # 5. Volatilite Bazlı Düzeltme (Risk Parity benzeri)
        # Eğer hisse çok volatilse (ATR yüksekse), pozisyonu küçült.
        # Stop mesafesi portföyün %2'sini geçmemeli.
        max_risk_per_trade = capital * 0.02 # %2 Risk Kuralı
        stop_distance = atr * self.stop_loss_mult
        
        if stop_distance > 0:
            vol_based_size = max_risk_per_trade / stop_distance
            # Fiyat bazlı lot sayısı
            # vol_based_lot = vol_based_size  (Bu nakit karşılığı değil, lot sayısı olurdu ama burada capital üzerinden gidiyoruz)
            
            # Tutar olarak hesaplayalım:
            # Risk = (Entry - Stop) * Lot
            # MaxRisk = StopDist * Lot
            # Lot = MaxRisk / StopDist
            # PositionValue = Lot * Price
            
            lot_size = int(max_risk_per_trade / stop_distance)
            position_value_vol = lot_size * price
            
            # Kelly Alloc vs Volatility Alloc -> Min olanı al
            position_value_kelly = capital * allocation
            
            final_position_value = min(position_value_kelly, position_value_vol)
            
            # Lot sayısına çevir
            final_lots = int(final_position_value / price)
            return final_lots
            
        return 0
