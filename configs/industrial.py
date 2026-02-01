from config import *

# --- INDUSTRIAL SINIFI ÖZEL AYARLARI ---
# Bu ayarlar ana config.py dosyasındaki değerleri ezer.

# Hisseler (Sanayi, Demir-Çelik, Petrokimya, Otomotiv)
TICKERS = ["EREGL.IS", "TUPRS.IS", "FROTO.IS", "KRDMD.IS", "PETKM.IS", "OYAKC.IS", "TOASO.IS", "TTRAK.IS", "OTKAR.IS"]
SECTOR_NAME = "INDUSTRIAL"

# --- ÖZELLİK MÜHENDİSLİĞİ ODAK NOKTALARI ---
# Sanayi hisseleri küresel emtia fiyatlarına (Altın, Petrol, Demir vb.) ve döviz kuruna duyarlıdır.
FEATURE_FOCUS = [
    'Gold_TRY_Momentum',       # Gram Altın Momentumu (KRDMD/EREGL için)
    'Oil_TRY_Momentum',        # Petrol TL Momentumu (TUPRS/PETKM için)
    'USDTRY_Change',           # İhracatçı oldukları için Kur Hassasiyeti
    'Volatility_Ratio',        # Hisse Volatilitesi / Endeks Volatilitesi Oranı
    'RSI',                     # Teknik
    'MACD',                    # Teknik
    'Excess_Return_Lag_4w'     # Endeksten ayrışma momentumu (Alpha Sinyali)
]

# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Emtia döngüleri sert olabilir, volatility tolerance düşürüldü (FIX: TUPRS Crash tespiti için)
REGIME_THRESHOLDS = {
    "volatility_low": 0.25,      # 0.28 -> 0.25
    "volatility_high": 0.55,     # 0.65 -> 0.55 (Daha çabuk Crash/Bear moduna geçsin)
    "try_change_high": 0.015,
    "min_regime_days": 3         # 6 -> 3 (Trend değişimine daha hızlı tepki)
}

# --- MODEL AĞIRLIKLARI (HİBRİT YAPI) ---
# Alpha (Ayrışma) Modeli daha baskın. Endeks düşse bile emtia artarsa yükselirler.
BETA_ALPHA_RATIO = {
    'beta': 0.30,  # %30 Piyasa (Beta azaltıldı)
    'alpha': 0.70  # %70 Spesifik Hikaye (Emtia/İhracat arttırıldı)
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.012  # Haftalık %1.2 altı getiriye işlem açma (Risk primi yüksek)
KELLY_FRACTION = 0.45         # Orta-Düşük Kelly
STOP_LOSS_ATR = 1.8           # 2.0 -> 1.8 (Daha sıkı stop)
TAKE_PROFIT_ATR = 3.0         # 3.5 -> 3.0 (Karı daha erken al)

# Özel Risk Kuralları Eşikleri
COMMODITY_VOLATILITY_CAP = 0.05 # Haftalık emtia değişim volatilitesi bu değeri aşarsa riskli

# Loglama için önek
LOG_PREFIX = "[INDUSTRIAL_STRATEGY]"
