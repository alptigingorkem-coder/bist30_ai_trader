import math
from utils.logging_config import get_logger

log = get_logger(__name__)

class ExecutionManager:
    def __init__(self, commission_rate=0.002):
        """
        Args:
            commission_rate (float): Komisyon oranı (varsayılan: on binde 20 = %0.2)
        """
        self.commission_rate = commission_rate

    def calculate_optimal_lots(self, price, allocated_cash):
        """
        Ayrılan bakiye ile alınabilecek maksimum TAM SAYI lot miktarını hesaplar.
        
        Args:
            price (float): Hissenin güncel fiyatı.
            allocated_cash (float): Bu işlem için ayrılan TL bakiyesi.
            
        Returns:
            int: Alınabilecek lot sayısı. 0 dönerse bakiye yetersizdir.
        """
        if price <= 0:
            return 0
            
        # Komisyon dahil maliyet hesabı
        # Maliyet = (Fiyat * Adet) * (1 + Komisyon)
        # Adet = Bakiye / (Fiyat * (1 + Komisyon))
        
        effective_price = price * (1 + self.commission_rate)
        lots = math.floor(allocated_cash / effective_price)
        
        return int(lots)

    def validate_order(self, symbol, quantity, price, balance):
        """
        Emrin geçerliliğini kontrol eder.
        
        Args:
            symbol (str): Hisse sembolü.
            quantity (int): Lot adedi.
            price (float): Fiyat.
            balance (float): Mevcut nakit bakiyesi.
            
        Returns:
            bool: Geçerli ise True.
        """
        if quantity <= 0:
            log.warning(f"  [{symbol}] Geçersiz Lot: {quantity} (Min 1 olmalı).")
            return False
            
        total_cost = quantity * price * (1 + self.commission_rate)
        
        if total_cost > balance:
            log.warning(f"  [{symbol}] Yetersiz Bakiye! Gerekli: {total_cost:.2f}, Mevcut: {balance:.2f}")
            return False
            
        # Minimum Tutar Kontrolü (Opsiyonel - örn. 10 TL altı işlem yapma)
        if total_cost < 10.0:
            log.info(f"  [{symbol}] İşlem tutarı çok düşük ({total_cost:.2f}), pas geçiliyor.")
            return False
            
        return True

    def simulate_slippage(self, price, order_type="MARKET"):
        """
        Küçük yatırımcı için Spread ve Slippage maliyetini simüle eder.
        """
        # MARKET emirlerde spread ödenir (%0.1)
        if order_type == "MARKET":
            spread_impact = 0.001 
            return price * (1 + spread_impact)
        
        # LIMIT emirlerde (Passive) spread kazanılır veya ödenmez
        # Ancak gerçekleşmeme riski vardır (Backtest'te bunu simüle etmek zor, 
        # o yüzden sadece fiyat avantajı veriyoruz)
        elif order_type == "LIMIT":
            return price # Spread ödenmez (Midpoint/Passive varsayımı)
            
        return price

from enum import Enum

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class Urgency(Enum):
    HIGH = "HIGH"       # Hemen al/sat (Stop Loss, Kriz)
    NORMAL = "NORMAL"   # Standart sinyal
    LOW = "LOW"         # Pasif biriktirme (Rebalance)

class SmartOrderRouter:
    """
    Head of Quant Recommendation:
    Basit Market Emirleri yerine, aciliyete göre emir tipi seçen akıllı yönlendirici.
    """
    def __init__(self, execution_manager: ExecutionManager):
        self.em = execution_manager
        
    def generate_order(self, symbol: str, side: str, price: float, quantity: int, urgency: Urgency = Urgency.NORMAL) -> dict:
        """
        Duruma uygun emir tipini ve fiyatını belirler.
        """
        order = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "original_price": price,
            "urgency": urgency.value
        }
        
        # 1. Acil Durumlar (Stop Loss, Crash Protection) -> MARKET EMİR
        if urgency == Urgency.HIGH:
            order["type"] = OrderType.MARKET
            # Market emirde fiyat garantisi yoktur, o anki fiyattan (veya daha kötüden) gerçekleşir
            # Backtest simülasyonu için slippage eklenmiş fiyatı kullanacağız
            order["price"] = self.em.simulate_slippage(price, "MARKET")
            order["note"] = "High Urgency: Market Order sent for immediate execution."
            
        # 2. Normal Sinyal (Trend Takibi) -> LIMIT EMİR (Aggressive)
        # Karşı taraftan (Ask/Bid) alarak garantiye çalışır ama Market kadar agresif değildir.
        elif urgency == Urgency.NORMAL:
            order["type"] = OrderType.LIMIT
            # Alışta Ask (Price), Satışta Bid (Price)
            # Limit emir olduğu için slippage minimumdur, ancak spread ödenir.
            order["price"] = price 
            order["note"] = "Normal Urgency: Limit Order at Market Price."
            
        # 3. Pasif (Rebalance, Accumulation) -> LIMIT EMİR (Passive)
        # Tahtaya yazılır, spread ödenmez.
        elif urgency == Urgency.LOW:
            order["type"] = OrderType.LIMIT
            # Spread avantajı (Orta nokta veya daha iyi)
            # Simülasyon: Fiyatı %0.05 iyileştir
            improvement = 0.0005
            if side == "BUY":
                order["price"] = price * (1 - improvement)
            else:
                order["price"] = price * (1 + improvement)
            order["note"] = "Low Urgency: Passive Limit Order (Midpoint)."
            
        return order
