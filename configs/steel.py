from config import *

# --- STEEL (METAL) SINIFI ÖZEL AYARLARI ---
# Demir-Çelik: Küresel emtia fiyatları (HRC), Çin talebi.

# Hisseler (Ereğli, Kardemir, İskenderun Demir)
TICKERS = ["EREGL.IS", "KRDMD.IS", "ISDMR.IS"]
SECTOR_NAME = "STEEL"

# --- ÖZELLİK MÜHENDİSLİĞİ ODAK NOKTALARI ---
FEATURE_FOCUS = [
    'Steel_Price',             # (Varsa) HRC fiyatları
    'USDTRY_Change',           # İhracat/Satışlar döviz endeksli
    'Dividends',               # Ereğli temettü etkisi
    'RSI',
    'MACD',
    'Close_to_SMA200'          # Döngüsel trend takibi
]

# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Döngüsel ve ağır hisseler.
REGIME_THRESHOLDS = {
    "volatility_low": 0.20,
    "volatility_high": 0.45,     
    "try_change_high": 0.010,
    "min_regime_days": 7         # Yavaş trend değişimi
}

# --- MODEL AĞIRLIKLARI ---
BETA_ALPHA_RATIO = {
    'beta': 0.40,  
    'alpha': 0.60  # Emtia fiyatları endeksten daha belirleyici
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.010
KELLY_FRACTION = 0.40         # Muhafazakar
STOP_LOSS_ATR = 1.8
TAKE_PROFIT_ATR = 3.0
LOG_PREFIX = "[STEEL_STRATEGY]"
