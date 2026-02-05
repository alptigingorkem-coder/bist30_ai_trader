from config import *

# --- AVIATION SINIFI ÖZEL AYARLARI ---
# Havacılık: Turizm, Petrol fiyatları ve Döviz kurlarına aşırı duyarlı.

# Hisseler
TICKERS = ["THYAO.IS", "PGSUS.IS", "TAVHL.IS"]
SECTOR_NAME = "AVIATION"

# --- ÖZELLİK MÜHENDİSLİĞİ ODAK NOKTALARI ---
FEATURE_FOCUS = [
    'Oil_TRY_Momentum',        # Petrolün TL maliyeti (En büyük gider kalemi)
    'USDTRY_Change',           # Gelirler döviz bazlı
    'RSI',                     # Aşırı alım/satım
    'MACD',                    # Trend
    'Return_Lag_4w',           # Momentum (Sezonsallık)
    'Volatility',              # Volatilite
    'Close_to_SMA50'           # Orta vadeli trend
]

# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Havacılık krizlere (pandemi, savaş) çok duyarlı, ancak toparlanması sert olur.
REGIME_THRESHOLDS = {
    "volatility_low": 0.28,      
    "volatility_high": 0.65,     # Yüksek tolerans
    "try_change_high": 0.012,    # Kur şoku önemli
    "min_regime_days": 4
}

# --- MODEL AĞIRLIKLARI ---
# Beta (Trend) ağırlıklı (%70), ama petrol şokları için Alpha (%30)
BETA_ALPHA_RATIO = {
    'beta': 0.70,  
    'alpha': 0.30 
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.015  # %1.5 altı riske değmez
KELLY_FRACTION = 0.60         # Agresif büyüme
STOP_LOSS_ATR = 2.5           # Geniş stop (Silkelenmemek için)
TAKE_PROFIT_ATR = 5.0         # Geniş hedef
LOG_PREFIX = "[AVIATION_STRATEGY]"
