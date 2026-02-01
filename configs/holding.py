from config import *

# --- HOLDING SINIFI ÖZEL AYARLARI ---
# Bu ayarlar ana config.py dosyasındaki değerleri ezer.

# Hisseler (Holdingler ve Büyük Perakende/Hizmet)
TICKERS = ["KCHOL.IS", "SAHOL.IS", "BIMAS.IS", "SISE.IS", "AGHOL.IS", "MGROS.IS", "DOHOL.IS", "TEKFEN.IS", "ALARK.IS", "ENKAI.IS"]
SECTOR_NAME = "HOLDING"

# --- ÖZELLİK MÜHENDİSLİĞİ ODAK NOKTALARI ---
# Holdingler temel analize (bilanço) ve endeks korelasyonuna duyarlıdır.
FEATURE_FOCUS = [
    'Forward_PE_Change',       # F/K Oranı Değişimi (Gelecek Beklentisi)
    'EBITDA_Margin_Change',    # FAVÖK Marjı Değişimi (Operasyonel Karlılık)
    'PB_Ratio',                # PD/DD (Değerleme)
    'RSI',                     # Teknik - Aşırı Alım/Satım
    'MACD',                    # Teknik - Trend
    'Return_Lag_4w',           # Momentum
    'Close_to_SMA200',         # Uzun Vadeli Trend (200 Günlük Ortalama)
    'NAV_Discount'             # (Opsiyonel) Net Aktif Değer İskontosu
]

# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Holdingler endekse paralel hareket eder, orta seviye volatilite eşikleri.
REGIME_THRESHOLDS = {
    "volatility_low": 0.25,      # Düşük volatilite
    "volatility_high": 0.60,     # Yüksek volatilite
    "try_change_high": 0.012,    # Kur hassasiyeti (Banking'den az, Industrial'dan çok)
    "min_regime_days": 5         # Rejim değişimi onayı için 5 gün
}

# --- MODEL AĞIRLIKLARI (HİBRİT YAPI) ---
# Hem Beta (Endeks) hem Alpha (Bilanço) dengeli.
BETA_ALPHA_RATIO = {
    'beta': 0.60,  # %60 Ana Model (Piyasa)
    'alpha': 0.40  # %40 Yan Model (Temel Analiz/Ayrışma)
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.010  # Haftalık %1.0 altı getiri tahminine işlem açma (Daha güvenli liman)
KELLY_FRACTION = 0.5          # %50 Kelly (Daha muhafazakar)
STOP_LOSS_ATR = 2.0           # Standart Stop
TAKE_PROFIT_ATR = 4.0         # Geniş Hedef (Holdingler trendi uzun sürer)

# Özel Risk Kuralları Eşikleri
VOLATILITY_CAP = 0.07         # Haftalık volatilite %7 üzerindeyse pozisyonu küçült

# Loglama için önek
LOG_PREFIX = "[HOLDING_STRATEGY]"
