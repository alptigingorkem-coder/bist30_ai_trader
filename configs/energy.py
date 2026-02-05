from config import *

# --- ENERGY SINIFI ÖZEL AYARLARI ---
# Enerji: Elektrik fiyatları (PTF), Yatırımlar ve Borçluluk.

# Hisseler (Odaş, Astor, Enerjisa, Aksa, Kontrolmatik)
TICKERS = ["ODAS.IS", "ASTOR.IS", "ENJSA.IS", "AKSEN.IS", "KONTR.IS", "SMRTG.IS", "EUPWR.IS"]
SECTOR_NAME = "ENERGY"

# --- ÖZELLİK MÜHENDİSLİĞİ ODAK NOKTALARI ---
FEATURE_FOCUS = [
    'Energy_Prices',           # (Varsa) PTF
    'USDTRY_Change',           # Yatırımlar döviz bazlı
    'Debt_EBITDA',             # Borçluluk oranı
    'Momentum_Trend',          # Sektör hype'ı
    'RSI',
    'BB_Width'                 # Volatilite patlaması
]

# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Çok yüksek volatiliteye sahip, hype sektörü.
REGIME_THRESHOLDS = {
    "volatility_low": 0.35,      # Yüksek taban
    "volatility_high": 0.80,     # Çok yüksek tavan
    "try_change_high": 0.015,
    "min_regime_days": 3         # Hızlı hareket
}

# --- MODEL AĞIRLIKLARI ---
# Beta (Hype) %80, Alpha %20
BETA_ALPHA_RATIO = {
    'beta': 0.80,  
    'alpha': 0.20 
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.020  # Yüksek getiri beklentisi yoksa girme
KELLY_FRACTION = 0.70         # Risk al
STOP_LOSS_ATR = 3.0           # Çok geniş stop
TAKE_PROFIT_ATR = 6.0         # Multibagger hedefi
LOG_PREFIX = "[ENERGY_STRATEGY]"
