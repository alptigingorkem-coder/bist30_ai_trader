from config import *

# --- AUTOMOTIVE SINIFI ÖZEL AYARLARI ---
# Otomotiv: İhracat (Euro/Dolar), Faiz oranları (Kredi) ve İç talep.

# Hisseler (Ford, Tofaş, Türk Traktör, Otokar)
TICKERS = ["FROTO.IS", "TOASO.IS", "TTRAK.IS", "OTKAR.IS"]
SECTOR_NAME = "AUTOMOTIVE"

# --- ÖZELLİK MÜHENDİSLİĞİ ODAK NOKTALARI ---
FEATURE_FOCUS = [
    'EURTRY_Change',           # İhracat genellikle Euro bölgesine
    'Credit_Rates',            # (Varsa) Taşıt kredisi faizleri
    'Consumer_Confidence',     # Tüketici güveni (Satışlar için)
    'Dividends',               # Temettü verimi (FROTO/TOASO için kritik)
    'RSI',
    'MACD',
    'Excess_Return_Lag_12w'    # Çeyreklik performans
]

# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Döngüsel sektör, faiz artışlarına duyarlı.
REGIME_THRESHOLDS = {
    "volatility_low": 0.22,      
    "volatility_high": 0.50,     # Düşük tolerans (Durgunluk korkusu)
    "try_change_high": 0.010,    
    "min_regime_days": 5
}

# --- MODEL AĞIRLIKLARI ---
# Alpha (Temettü/İhracat performansı) önemlidir.
BETA_ALPHA_RATIO = {
    'beta': 0.50,  
    'alpha': 0.50 
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.010
KELLY_FRACTION = 0.50
STOP_LOSS_ATR = 2.0
TAKE_PROFIT_ATR = 3.5
LOG_PREFIX = "[AUTOMOTIVE_STRATEGY]"
