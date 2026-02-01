from config import *

# --- GROWTH SINIFI ÖZEL AYARLARI ---
# Bu ayarlar ana config.py dosyasındaki değerleri ezer.

# Hisseler (Büyüme, Teknoloji, Havacılık, Enerji)
TICKERS = ["THYAO.IS", "ASELS.IS", "PGSUS.IS", "TCELL.IS", "ODAS.IS", "KONTR.IS", "SASA.IS", "TTKOM.IS", "ASTOR.IS", "HEKTS.IS"]
SECTOR_NAME = "GROWTH"

# --- ÖZELLİK MÜHENDİSLİĞİ ODAK NOKTALARI ---
# Büyüme hisseleri trend ve momentuma duyarlıdır.
FEATURE_FOCUS = [
    'Return_Lag_4w',           # Kısa Vadeli Momentum
    'Return_Lag_12w',          # Orta Vadeli Momentum
    'RSI',                     # Güç Göstergesi
    'MACD',                    # Trend Takibi
    'Close_to_SMA200',         # Ana Trendin Neresindeyiz? (Uzaklaşma oranı)
    'BB_Width',                # Volatilite Patlaması Sinyali (Bollinger Band Genişliği)
    'Momentum_Trend'           # Özel momentum skoru
]

# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Volatiliteye en toleranslı grup. Yüksek volatilite genellikle ralli işaretidir.
REGIME_THRESHOLDS = {
    "volatility_low": 0.30,      # Düşük
    "volatility_high": 0.70,     # Çok Yüksek (Bu seviyeye kadar trend bozulmaz)
    "try_change_high": 0.010,    # Kur hassasiyeti (Orta seviye)
    "min_regime_days": 4         # Hızlı rejim değişimi
}

# --- MODEL AĞIRLIKLARI (HİBRİT YAPI) ---
# Beta (Trend) çok baskın.
BETA_ALPHA_RATIO = {
    'beta': 0.80,  # %80 Trend Takibi
    'alpha': 0.20  # %20 Hisse Özel Hikayesi
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.015  # Haftalık %1.5 altı getiri yetersiz (Yüksek beta için değmez)
KELLY_FRACTION = 0.65         # Agresif Kelly (Trend varsa tam gaz)
STOP_LOSS_ATR = 2.5           # Geniş Stop (Silkelenmemek için)
TAKE_PROFIT_ATR = 5.0         # Çok Geniş Hedef (Trendi sonuna kadar sür)

# Özel Risk Kuralları Eşikleri
MOMENTUM_BOOST_THRESHOLD = 0.10 # Eğer 4 haftalık getiri %10 üzerindeyse pozisyonu artır

# Loglama için önek
LOG_PREFIX = "[GROWTH_STRATEGY]"
