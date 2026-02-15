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

    def simulate_slippage(self, price):
        """
        Küçük yatırımcı için Spread ve Slippage maliyetini simüle eder.
        Kapanış Fiyatı (Close) genellikle "Orta Nokta" gibidir.
        Alırken biraz daha pahalıya (Ask), satarken ucuza (Bid) satarız.
        
        Varsayım: %0.1 (Binde 1) Spread/Slippage maliyeti.
        """
        spread_impact = 0.001 
        # Alış simülasyonu için fiyatı artır (Kötümser senaryo)
        executed_price = price * (1 + spread_impact)
        return executed_price
