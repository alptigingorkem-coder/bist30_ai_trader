from config import *

# --- TELECOM SINIFI ÖZEL AYARLARI ---
# Telekom: Abone sayısı, ARPU ve Altyapı yatırımları (Döviz).

# Hisseler (Turkcell, Türk Telekom)
TICKERS = ["TCELL.IS", "TTKOM.IS"]
SECTOR_NAME = "TELECOM"

# --- ÖZELLİK MÜHENDİSLİĞİ ODAK NOKTALARI ---
FEATURE_FOCUS = [
    'ARPU_Growth',             # (Varsa)
    'USDTRY_Change',           # Yatırımlar döviz, gelirler TL (Risk)
    'Inflation',               # Tarife zamları enflasyonu yenebiliyor mu?
    'RSI',
    'MACD'
]

# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Orta volatilite.
REGIME_THRESHOLDS = {
    "volatility_low": 0.22,
    "volatility_high": 0.50,
    "try_change_high": 0.009,    # Kur şokuna çok duyarlı (Borçluluk)
    "min_regime_days": 5
}

# --- MODEL AĞIRLIKLARI ---
BETA_ALPHA_RATIO = {
    'beta': 0.60,  
    'alpha': 0.40 
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.012
KELLY_FRACTION = 0.45
STOP_LOSS_ATR = 2.0
TAKE_PROFIT_ATR = 3.5
LOG_PREFIX = "[TELECOM_STRATEGY]"
