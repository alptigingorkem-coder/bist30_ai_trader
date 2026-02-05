from config import *

# --- REAL ESTATE SINIFI ÖZEL AYARLARI ---
# GYO: Konut faizleri, İnşaat maliyetleri ve Değerlemeler.

# Hisseler (Emlak Konut, Torunlar, İş GYO)
TICKERS = ["EKGYO.IS", "TRGYO.IS", "ISGYO.IS"]
SECTOR_NAME = "REAL_ESTATE"

# --- ÖZELLİK MÜHENDİSLİĞİ ODAK NOKTALARI ---
FEATURE_FOCUS = [
    'Interest_Rates',          # Konut kredisi faizleri (Negatif korelasyon)
    'Construction_Cost',       # Maliyet endeksi
    'NAV_Discount',            # Net Aktif Değer İskontosu
    'RSI',
    'MACD',
    'Momentum_Trend'
]

# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Yüksek volatilite, faiz döngülerine duyarlı.
REGIME_THRESHOLDS = {
    "volatility_low": 0.30,
    "volatility_high": 0.65,
    "try_change_high": 0.015,
    "min_regime_days": 4
}

# --- MODEL AĞIRLIKLARI ---
BETA_ALPHA_RATIO = {
    'beta': 0.70,  # Endeksle ve faizle çok hareket eder
    'alpha': 0.30 
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.015
KELLY_FRACTION = 0.55
STOP_LOSS_ATR = 2.5
TAKE_PROFIT_ATR = 5.0
LOG_PREFIX = "[REAL_ESTATE_STRATEGY]"
