
import numpy as np
import pandas as pd

from utils.logging_config import get_logger

log = get_logger(__name__)

class KellyPositionSizer:
    def __init__(self, initial_fraction=0.25, max_fraction=0.50):
        self.initial_fraction = initial_fraction  # Fractional Kelly (Tam Kelly çok riskli olabilir)
        self.max_fraction = max_fraction          # Tek işlemde sermayenin maksimum ne kadarı riske edilecek
        self.trade_history = []                   # [{'pnl': 0.05}, {'pnl': -0.02}, ...]
        
    def add_trade(self, pnl_pct):
        """Yeni bir trade sonucunu geçmişe ekler."""
        self.trade_history.append({'pnl': pnl_pct})
        
    def calculate_kelly(self):
        """Geçmiş trade'lerden Kelly oranını hesaplar."""
        if not self.trade_history:
            return self.initial_fraction # Yeterli veri yoksa varsayılan
            
        wins = [t['pnl'] for t in self.trade_history if t['pnl'] > 0]
        losses = [t['pnl'] for t in self.trade_history if t['pnl'] <= 0]
        
        # En az 5 win ve 5 loss olmadan Kelly hesaplama, varsayılanı kullan
        if len(wins) < 5 or len(losses) < 5:
            return self.initial_fraction
        
        p = len(wins) / len(self.trade_history)  # Win rate
        
        avg_win = np.mean(wins)
        avg_loss = abs(np.mean(losses)) if losses else 1.0
        
        if avg_loss == 0: return self.max_fraction
        
        b = avg_win / avg_loss  # Win/Loss ratio (Profit Factor'a benzer ama ortlama üzerinden)
        
        # Kelly Criterion: f = (p * b - q) / b  where q = 1 - p
        q = 1 - p
        kelly = (p * b - q) / b
        
        # Negatif Kelly (Beklenti negatif) -> İşlem yapma (0)
        if kelly <= 0:
            return 0.0
            
        # Fractional Kelly (Risk yönetimi için güvenli liman)
        kelly_fraction = kelly * self.initial_fraction
        
        # Güvenlik Limiti (Asla sermayenin %50'sinden fazlasını tek işleme koyma)
        return np.clip(kelly_fraction, 0.05, self.max_fraction)
    
    def get_position_size(self, capital, confidence=1.0):
        """
        capital: Mevcut sermaye (Cash + Equity değil, allocate edilebilir miktar)
        confidence: Model'in tahmin güveni (0.0 - 1.0 arası). Eğer model güven vermiyorsa 1.0 varsay.
        """
        kelly_pct = self.calculate_kelly()
        
        # Model güveni ile Kelly'yi ölçekle
        # Eğer model %60 eminse, Kelly'nin %60'ını kullan
        adjusted_kelly = kelly_pct * confidence
        
        # Pozisyon büyüklüğü (TL)
        position_size = capital * adjusted_kelly
        
        return position_size

if __name__ == "__main__":
    # Test
    sizer = KellyPositionSizer()
    # Simüle edilmiş trade geçmişi
    import random

    random.seed(42)
    for _ in range(50):
        # %60 win rate, 1.5 risk/reward
        if random.random() < 0.6:
            sizer.add_trade(0.03) # %3 kazan
        else:
            sizer.add_trade(-0.02) # %2 kaybet
            
    log.info(f"Calculated Kelly Fraction: {sizer.calculate_kelly():.4f}")
