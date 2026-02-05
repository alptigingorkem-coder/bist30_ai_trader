from config import *

# --- RETAIL SINIFI ÖZEL AYARLARI ---
# Perakende: Enflasyon (Gıda), Asgari Ücret ve Tüketici Talebi.

# Hisseler (BİM, Migros, Şok, Mavi)
TICKERS = ["BIMAS.IS", "MGROS.IS", "SOKM.IS", "MAVI.IS"]
SECTOR_NAME = "RETAIL"

# --- ÖZELLİK MÜHENDİSLİĞİ ODAK NOKTALARI ---
FEATURE_FOCUS = [
    'Inflation',               # Gıda enflasyonu (Ciro artışı)
    'Consumer_Confidence',     # Talep
    'Minimum_Wage',            # Personel giderleri
    'RSI',
    'MACD',
    'Return_Lag_4w'
]

# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Defansif sektör, düşük volatilite beklenir.
REGIME_THRESHOLDS = {
    "volatility_low": 0.18,      
    "volatility_high": 0.40,     # Çok düşük tolerans
    "try_change_high": 0.015,    # Kura dayanıklı
    "min_regime_days": 7
}

# --- MODEL AĞIRLIKLARI ---
# Alpha (Yönetim kalitesi/Marjlar) daha önemli.
BETA_ALPHA_RATIO = {
    'beta': 0.40,  
    'alpha': 0.60 
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.008
KELLY_FRACTION = 0.40         # Güvenli liman
STOP_LOSS_ATR = 1.5           # Sıkı stop (Defansif olduğu için)
TAKE_PROFIT_ATR = 2.5
LOG_PREFIX = "[RETAIL_STRATEGY]"
