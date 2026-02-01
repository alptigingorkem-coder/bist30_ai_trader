# Config Settings for BIST30 AI Trader - EXAMPLE CONFIG
# BU DOSYAYI 'config.py' OLARAK KOPYALAYIN VE KENDİ DEĞERLERİNİZİ GİRİN.

# --- TIER SISTEMI (SADELEŞTİRİLMİŞ) ---
# Sadece Tier 1 (Core) Aktif
# --- ABLATION STUDY CONFIG ---
# Modelin makro verileri (VIX, USDTRY vb.) doğrudan feature olarak kullanıp kullanmayacağı
ENABLE_MACRO_IN_MODEL = False  # Noise reduction için kapalı önerilir

TIERS = {
    'TIER_1': [
        "AKBNK.IS", "ALARK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS", 
        "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", 
        "GUBRF.IS", "HEKTS.IS", "ISCTR.IS", "KCHOL.IS", "KONTR.IS", 
        "KOZAL.IS", "KRDMD.IS", "ODAS.IS", "OYAKC.IS", "PETKM.IS", 
        "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TAVHL.IS", 
        "TCELL.IS", "THYAO.IS", "TOASO.IS", "TSKB.IS", "TTKOM.IS", 
        "TUPRS.IS", "YKBNK.IS"
    ],
    'TIER_2': [], # Devre dışı
    'TIER_3': []  # Devre dışı
}

# Aktif Hisseler
TICKERS = TIERS['TIER_1']

# Blacklist (Gerekli değil ama kalsın)
BLACKLIST = []

# --- SEKTÖREL SEGMENTASYON ---
# Hepsi A1 segmenti gibi işlem görebilir veya kendi karakterleri kullanılabilir.
# Core hisselerin hepsi güçlü olduğu için A1 mantığı uygundur.
SECTORS = {
    'SEGMENT_A1': TICKERS
}

# FIX 4: Sector Classification for Rotation Penalty
SECTOR_MAP = {
    # Banks
    'AKBNK.IS': 'Bank', 'GARAN.IS': 'Bank', 'ISCTR.IS': 'Bank', 
    'YKBNK.IS': 'Bank', 'TSKB.IS': 'Bank',
    # Holdings
    'KCHOL.IS': 'Holding', 'SAHOL.IS': 'Holding', 'ALARK.IS': 'Holding',
    # Construction/Real Estate
    'ENKAI.IS': 'Construction', 'TOASO.IS': 'Construction', 
    'EKGYO.IS': 'Real Estate',
    # Industrials
    'ASELS.IS': 'Defense', 'EREGL.IS': 'Steel', 'FROTO.IS': 'Auto',
    'OYAKC.IS': 'Cement', 'TUPRS.IS': 'Petrochem', 'SASA.IS': 'Chemicals',
    # Telecom/Tech
    'TTKOM.IS': 'Telecom', 'TCELL.IS': 'Telecom', 'ASTOR.IS': 'Retail',
    'HEKTS.IS': 'Textile',
    # Consumer
    'BIMAS.IS': 'Retail', 'PGSUS.IS': 'Travel', 'TAVHL.IS': 'Travel',
    # Aviation
    'THYAO.IS': 'Aviation',
    # Energy/Utilities
    'PETKM.IS': 'Petrochem', 'KONTR.IS': 'Construction',
    # Industrial
    'GUBRF.IS': 'Automotive', 'KOZAL.IS': 'Diversified',
    'KRDMD.IS': 'Steel', 'ODAS.IS': 'Energy', 'SISE.IS': 'Glass',
}

def get_segment(ticker):
    return 'A1'

def get_sector(ticker):
    """FIX 4: Get sector for rotation penalty."""
    return SECTOR_MAP.get(ticker, 'Other')


# --- TARİH VE MAKRO VERİ ---
START_DATE = "2015-01-01"
END_DATE = None # Bugüne kadar al

# TCMB API Key (Yabancı portföy akışı için)
# https://evds2.tcmb.gov.tr/ adresinden ücretsiz alınabilir
TCMB_API_KEY = "BURAYA_KENDI_API_ANAHTARINIZI_GIRIN"

MACRO_TICKERS = {
    "USDTRY": "TRY=X",
    "VIX": "^VIX",
    "SP500": "^GSPC",
    "XBANK": "XBANK.IS",
    "XU100": "XU100.IS",
    "GOLD": "GC=F",      # Altın (Gold Futures)
    "OIL": "BZ=F"        # Brent Petrol (Oil Futures)
}

# --- PARAMETRELER ---
# Zaman Periyodu
TIMEFRAME = 'W'  # 'D' for Daily, 'W' for Weekly

# Teknik İndikatörler (Haftalık)
RSI_PERIOD = 3          # 14 gün / 5 ≈ 3 hafta
MACD_FAST = 2           # 12 gün / 5 ≈ 2 hafta  
MACD_SLOW = 5           # 26 gün / 5 ≈ 5 hafta
MACD_SIGNAL = 2         # 9 gün / 5 ≈ 2 hafta
BB_LENGTH = 4           # 20 gün / 5 = 4 hafta
BB_STD = 2

# Model
TARGET_COL = "Hybrid" # main.py handle edecek
VAL_SIZE = 0.15

# Hibrit Strateji Eşikleri
HYBRID_THRESHOLDS = {
    'TREND': 0.005,  # %0.5 (Trend Rejiminde - Beta Odaklı - Düşük Eşik)
    'ALPHA': 0.008   # %0.8 (Yatay/Düşüş - Alpha Odaklı - Yüksek Eşik)
}

# Risk Yönetimi (Haftalık Bazlı)
COMMISSION_RATE = 0.0025
MIN_HOLDING_PERIODS = 5  # 5 hafta (~1.25 ay) (FIX 5)

# Sektörel farklılaştırma
MIN_HOLDING_BY_SECTOR = {
    'BANKING': 4,      # Daha hızlı hareket eder
    'HOLDING': 6,      # Yavaş hareket
    'INDUSTRIAL': 5,   # Orta
    'GROWTH': 3        # Momentum hızlı değişir
}
ATR_PERIOD = 3           # 14 gün / 5 ≈ 3 hafta

# Dinamik Stop/Profit (ATR Çarpanları)
# Daha sıkı stop, daha hızlı kar al
ATR_STOP_LOSS_MULTIPLIER = 2.0      # 1.5 -> 2.0 (FIX 6: Daha toleranslı)
ATR_TAKE_PROFIT_MULTIPLIER = 2.5    # 3.5 -> 2.5 (Karı daha erken cebe at - değişmedi)
ATR_TRAILING_STOP_MULTIPLIER = 1.8  # 1.5 -> 1.8 (FIX 8: Trailing stop gevşetildi)

# Sabit limitler (Sigorta olarak)
MAX_STOP_LOSS_PCT = 0.12    # %8 -> %12 (FIX 7: Max kayıp limiti artırıldı)
TRAILING_STOP_ACTIVE = True

# Güven Eşiği (YÜKSEK) - Faz 1 Güncellemesi
CONFIDENCE_THRESHOLDS = {
    'TIER_1': 0.72  # 0.60 -> 0.72 (Gradual artış, daha seçici)
}

# Sektörel farklılaştırma ekle
CONFIDENCE_THRESHOLDS_BY_SECTOR = {
    'BANKING': 0.70,     # Bankalar volatil, daha yüksek eşik
    'HOLDING': 0.65,     # Holdingler stabil
    'INDUSTRIAL': 0.68,  # Sanayi orta
    'GROWTH': 0.75       # Growth en riskli, en yüksek eşik
}

# Segment Ayarları (A1 Core)
SEGMENT_SETTINGS = {
    'A1': {
        'learning_rate_range': (0.05, 0.2),
        'regularization': 'low',
        'feature_focus': [
            # Temel teknik
            'USDTRY', 'VIX', 'Volatility', 'RSI', 'Close', 'MACD',
            # Yeni alpha kaynakları
            'PE', 'EBITDA', 'Revenue', 'Debt',  # Fundamental
            'Gold', 'Oil',  # Cross-asset
            'Sector_Rotation', 'XBANK'  # Sektör
        ],
    }
}

# Rejim - Optimize Edilmiş (Calmar Ratio: 31.14)
USE_ADAPTIVE_REGIME = True # Hisse bazlı dinamik eşik kullanımı (False ise aşağıdaki sabitler kullanılır)

REGIME_THRESHOLDS = {
    "volatility_low": 0.279,     # Optimize edilmedi (kullanılmıyor)
    "volatility_high": 0.61,     # 0.660 -> 0.61 (Daha hassas kriz tespiti)
    "cds_high": 600,
    "try_change_high": 0.0147,
    "momentum_threshold": 49,    # 64 -> 49 (Daha erken trend onayı)
    "min_regime_days": 2         # 6 -> 2 (Daha hızlı tepki)
}

# Macro Gate Eşikleri (Yeni)
ENABLE_MACRO_GATE = True  # False yapılırsa Gate devre dışı kalır (Ablation Study için)

MACRO_GATE_THRESHOLDS = {
    'VIX_HIGH': 30.0,
    'USDTRY_CHANGE_5D': 0.03,  # %3 (5 günlük değişim)
    'SP500_MOMENTUM': 0.0      # Negatif (< 0) ise Risk Off
}

# Optimize Edilmiş Model Parametreleri (Optuna Sonucu - Round 2)
OPTIMIZED_MODEL_PARAMS = {
    'learning_rate': 0.034,
    'num_leaves': 66,
    'max_depth': 10,
    'reg_alpha': 0.35,
    'reg_lambda': 0.62,
    'n_estimators': 300 # Backtest ile uyumlu olması için
}

# FIX 16: Sektör rotasyon cezası
ENABLE_SECTOR_ROTATION_PENALTY = True
MAX_SECTOR_CONCENTRATION = 0.40  # Bir sektöre max %40
