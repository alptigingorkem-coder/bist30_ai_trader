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
# Emtia döngüleri uzun sürer, volatilite toleransı daha yüksektir.
REGIME_THRESHOLDS = {
    "volatility_low": 0.28,      # Düşük volatilite
    "volatility_high": 0.65,     # Yüksek volatilite (Çok yüksek olmadıkça trend bozulmaz)
    "try_change_high": 0.015,    # Kur şoklarına dayanıklılıkları yüksektir
    "min_regime_days": 6         # Trend değişim onayı için 6 gün
}

# --- MODEL AĞIRLIKLARI (HİBRİT YAPI) ---
# Alpha (Ayrışma) Modeli daha baskın. Endeks düşse bile emtia artarsa yükselirler.
BETA_ALPHA_RATIO = {
    'beta': 0.40,  # %40 Piyasa Takibi
    'alpha': 0.60  # %60 Spesifik Hikaye (Emtia/İhracat)
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.012  # Haftalık %1.2 altı getiriye işlem açma (Risk primi yüksek)
KELLY_FRACTION = 0.45         # Orta-Düşük Kelly (Emtia volatilitesi sert olabilir)
STOP_LOSS_ATR = 2.0           # Standart Stop
TAKE_PROFIT_ATR = 3.5         # İyi trend yakalarsa tut

# Özel Risk Kuralları Eşikleri
COMMODITY_VOLATILITY_CAP = 0.05 # Haftalık emtia değişim volatilitesi bu değeri aşarsa riskli

# Loglama için önek
LOG_PREFIX = "[INDUSTRIAL_STRATEGY]"
