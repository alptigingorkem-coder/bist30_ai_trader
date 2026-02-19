import config
import pandas as pd
import numpy as np
import logging
from models.regime_detector import RegimeDetector

logger = logging.getLogger(__name__)

class ConfigWrapper:
    def __init__(self, module): self.module = module
    def get(self, name, default=None): return getattr(self.module, name, default)

class RiskManager:
    def __init__(self):
        self.stop_loss_mult = config.ATR_STOP_LOSS_MULTIPLIER
        self.take_profit_mult = config.ATR_TAKE_PROFIT_MULTIPLIER
        self.trailing_stop_mult = config.ATR_TRAILING_STOP_MULTIPLIER
        self.min_holding_periods = config.MIN_HOLDING_PERIODS
        self.max_stop_loss_pct = config.MAX_STOP_LOSS_PCT
        self.trailing_active = config.TRAILING_STOP_ACTIVE
        self.current_regime = None 
        
        # Initialize RegimeDetector
        try:
            self.regime_detector = RegimeDetector(ConfigWrapper(config))
            logger.info("✅ RegimeDetector entegre edildi (RiskManager)")
        except Exception as e:
            logger.warning(f"⚠️ RegimeDetector başlatılamadı: {e}")
            self.regime_detector = None

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
             self.stop_loss_mult = config.ATR_STOP_LOSS_MULTIPLIER
             self.trailing_stop_mult = config.ATR_TRAILING_STOP_MULTIPLIER
             self.take_profit_mult = config.ATR_TAKE_PROFIT_MULTIPLIER

    def calculate_stop_loss(self, entry_price, atr, regime="NORMAL"):
        """
        Rejime göre dinamik stop-loss.
        
        Args:
            entry_price: Giriş fiyatı
            atr: Average True Range
            regime: Piyasa rejimi ('CRISIS', 'VOLATILE', 'TREND_UP', vb.)
        
        Returns:
            float: Stop-loss seviyesi
        """
        base_mult = getattr(config, 'ATR_STOP_LOSS_MULTIPLIER', 1.5)
        
        # Rejim çarpanı
        # Rejim çarpanı (RegimeDetector üzerinden)
        regime_mult = 1.0
        if self.regime_detector and regime:
            regime_mult = self.regime_detector.get_stop_loss_multiplier(regime)
        else:
            # Fallback to config lookup manually if detector fails or not init
            regime_actions = getattr(config, 'REGIME_ACTIONS', {})
            action = regime_actions.get(regime, {})
            regime_mult = action.get('stop_loss_mult', 1.5)
        
        # Final çarpan
        final_mult = base_mult * regime_mult
        
        # Stop hesapla
        stop = entry_price - (final_mult * atr)
        
        logger.debug(f"Stop-loss: Entry={entry_price:.2f}, ATR={atr:.4f}, "
                    f"Regime={regime}, Mult={final_mult:.2f}, Stop={stop:.2f}")
        
        return stop


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
        current_atr = atr if not np.isnan(atr) else entry_price * 0.03
        
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

        # YENİ: Regime Force Exit (RegimeDetector üzerinden)
        # Not: check_exit_conditions metodunun parametrelerine 'regime' eklenmeliydi ama
        # mevcut imzayı bozmamak için self.current_regime kullanıyoruz.
        if self.regime_detector and self.current_regime:
            action = self.regime_detector.get_trading_action(self.current_regime)
            if action.get('force_exit', False):
                return 'SELL', f"FORCE_EXIT_{self.current_regime}"

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

    def calculate_position_size(self, capital, price, atr, win_rate=None, win_loss_ratio=None):
        """
        Kelly Criterion (Half-Kelly) ile pozisyon büyüklüğü hesaplar.
        f = (p * b - q) / b
        p: Win Rate (Dinamik veya Varsayılan)
        b: Win/Loss Ratio (Dinamik veya Varsayılan)
        q: Loss Rate (1-p)
        """
        if atr <= 0 or price <= 0: return 0.0
        
        # Varsayılanlar (Eğer dinamik veri yoksa)
        if win_rate is None:
            win_rate = 0.55 # Muhafazakar başlangıç
        if win_loss_ratio is None:
            win_loss_ratio = 2.0 # Hedeflenen
            
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

    def check_portfolio_drawdown(self, current_equity, peak_equity):
        """
        Portföy bazlı Drawdown kontrolü (Circuit Breaker).
        
        Returns:
            action (str): 'CONTINUE', 'REDUCE_EXPOSURE', 'STOP_TRADING'
            drawdown (float): Calculated drawdown
        """
        if peak_equity <= 0: return 'CONTINUE', 0.0
        
        drawdown = (current_equity - peak_equity) / peak_equity
        limit = config.MAX_DRAWDOWN_LIMIT # Örn: -0.20
        
        # Drawdown negatif bir değerdir, limit pozitif tanımlanmış olabilir config'de (0.25)
        # Config'deki 0.25 aslında %25 kayıp demek.
        # Bu yüzden karşılaştırmayı mutlak değer veya işaretle dikkatli yapmalıyız.
        # Config'de 0.20 -> %20 kayıp.
        # Drawdown -0.21 -> Limit aşıldı.
        
        limit_val = -abs(limit) # -0.20
        
        if drawdown < limit_val:
            return 'STOP_TRADING', drawdown
            
        # Warning Zone: Limitin yarısına gelindiğinde (-0.10)
        warning_val = limit_val / 2
        if drawdown < warning_val:
            return 'REDUCE_EXPOSURE', drawdown
            
        return 'CONTINUE', drawdown

    def check_order_timeout(self, order_type, time_in_force_minutes=5):
        """
        Passive orders (LIMIT) timeout check.
        In backtesting, this is a placeholder or used if we had minute-level data loop.
        In Live Trading, this would cancel the order.
        """
        # Audit Requirement: 5 min timeout
        if order_type == "LIMIT":
            return True # Timeout active
        return False

    def check_liquidity(self, ticker: str, volume: float) -> bool:
        """
        Check if the stock has sufficient liquidity to be tradeable.
        Uses config.MIN_LIQUIDITY_THRESHOLD (Default: 20M TL).
        NOTE: 'volume' here assumes Volume * Price (TL Volume).
        If passing Lot Volume, ensure to multiply by price before calling, 
        OR better, call this with TL Volume.
        """
        threshold = getattr(config, 'MIN_LIQUIDITY_THRESHOLD', 20_000_000)
        
        if volume < threshold:
            logger.debug(f"{ticker}: Low Liquidity ({volume:,.0f} < {threshold:,.0f}). Trade Rejected.")
            return False
        return True

    def calculate_dynamic_slippage(self, target_size_qty: float, avg_volume_qty: float) -> float:
        """
        Calculate slippage based on volume participation.
        Formula: Base + (Participation * Impact_Factor)
        Base: 0.05% (5bps)
        """
        if avg_volume_qty <= 0: return 0.01 # High slippage penalty for no volume
        
        participation = target_size_qty / avg_volume_qty
        
        base_slippage = 0.0005 # 5 basis points
        
        # Impact Factor increases with size
        # 1% participation -> ~0 impact
        # 10% participation -> Significant impact
        impact_factor = 0.1 # Sensitivity
        
        impact_cost = participation * impact_factor
        
        total_slippage = base_slippage + impact_cost
        
        # Max Cap to prevent unrealistic backtest crash
        return min(total_slippage, 0.03) # Max 3% slippage
