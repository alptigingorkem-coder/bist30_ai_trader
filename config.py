# Config Settings for BIST30 AI Trader - CORE ONLY STRATEGY

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

# FIX 4: Sector Classification for Rotation Penalty & Model Dummies
SECTOR_MAP = {
    # Banks
    'AKBNK.IS': 'Banking', 'GARAN.IS': 'Banking', 'ISCTR.IS': 'Banking', 
    'YKBNK.IS': 'Banking', 'TSKB.IS': 'Banking',
    # Conglomerates / Holdings
    'KCHOL.IS': 'Holding', 'SAHOL.IS': 'Holding', 'ALARK.IS': 'Holding',
    # Industrial & Manufacturing
    'ASELS.IS': 'Defense', 'FROTO.IS': 'Automotive', 'TOASO.IS': 'Automotive',
    'SASA.IS': 'Chemicals', 'PETKM.IS': 'Chemicals', 'SISE.IS': 'Glass',
    'ENKAI.IS': 'Construction', 'KONTR.IS': 'Technology',
    # Materials (Steel & Cement)
    'EREGL.IS': 'Steel', 'KRDMD.IS': 'Steel', 'OYAKC.IS': 'Cement',
    # Energy
    'ODAS.IS': 'Energy', 'ASTOR.IS': 'Energy',
    # Consumer & Retail
    'BIMAS.IS': 'Retail', 'HEKTS.IS': 'Agri', 'GUBRF.IS': 'Agri',
    # Aviation & Transport
    'THYAO.IS': 'Aviation', 'PGSUS.IS': 'Aviation', 'TAVHL.IS': 'Aviation',
    # Telecom
    'TTKOM.IS': 'Telecom', 'TCELL.IS': 'Telecom',
    # Real Estate
    'EKGYO.IS': 'RealEstate',
    # Energy (Refining) & Mining
    'TUPRS.IS': 'Energy',
    'KOZAL.IS': 'Mining',
}

def get_segment(ticker):
    return 'A1'

def get_sector(ticker):
    """FIX 4: Get sector for rotation penalty."""
    # Suffix removal
    clean_ticker = ticker.replace('.IS', '')
    
    # Check both full and clean ticker in map
    if ticker in SECTOR_MAP:
        return SECTOR_MAP[ticker]
    if clean_ticker in SECTOR_MAP:
        # SECTOR_MAP içinde anahtarlar .IS ile bitiyorsa clean_ticker + .IS dene
        # Ama SECTOR_MAP'te anahtarlar .IS'li tanımlanmış.
        # Bu durumda clean_ticker gelirse sonuna .IS ekleyip bakmalı.
        return SECTOR_MAP.get(clean_ticker + '.IS', 'Other')
        
    # Reverse check: Eğer clean_ticker SECTOR_MAP'te varsa
    # (Yukarıdaki SECTOR_MAP'te anahtarlar .IS'li, o yüzden clean_ticker + .IS'i denedik)
    
    return 'Other'


# --- TARİH VE MAKRO VERİ ---
START_DATE = "2015-01-01" # Gerçek veri odaklı başlangıç
END_DATE = None # Bugüne kadar al

# Overfitting Önleme (Strict Split)
TRAIN_END_DATE = "2024-12-31" 
TEST_START_DATE = "2025-01-01" 

# Ablation / Sentetik Veri Kontrolü
ENABLE_SYNTHETIC_DATA = False # Kullanıcı isteği: Sadece gerçek veri




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
TIMEFRAME = 'D'  # 'D' for Daily (CHANGED FROM WEEKLY)

# Teknik İndikatörler (Günlük Standart)
RSI_PERIOD = 14         # Standart
MACD_FAST = 12          # Standart
MACD_SLOW = 26          # Standart
MACD_SIGNAL = 9         # Standart
BB_LENGTH = 20          # Standart
BB_STD = 2

# Model Target Optimizasyonu
LABEL_TYPE = 'RawRank'       # 'RawRank', 'Quantile', 'RiskAdjusted'
FORWARD_WINDOW = 1           # Kaç günlük getiri hedefleniyor (1-5)
NUM_QUANTILES = 5            # Quantile ranking için grup sayısı

# Model
MODEL_TYPE = 'ensemble'      # 'lightgbm', 'catboost', 'ensemble'
TARGET_COL = "Excess_Return" 
VAL_SIZE = 0.15
LABEL_TYPE = 'Hybrid'        # 'RawRank', 'Quantile', 'Hybrid'
HYBRID_WEIGHT = 0.85          # Daha çok raw rank odaklı (0.7 -> 0.85)
FORWARD_WINDOWS = [1, 5]     # T+1 ve T+5
FORWARD_WEIGHTS = [0.6, 0.4] # T+1 daha ağır

# Sızıntı (Leakage) sütunları - Bunlar asla model girdisi olmamalı
LEAKAGE_COLS = [
    'NextDay_Close', 'NextDay_Return', 'Excess_Return', 
    'Excess_Return_RiskAdjusted', 'NextDay_XU100_Return', 
    'Log_Return', 'NextDay_Direction', 'ExitReason'
]

# Hibrit Strateji Eşikleri
HYBRID_THRESHOLDS = {
    'TREND': 0.005,  
    'ALPHA': 0.008   
}

# Risk Yönetimi (Günlük Bazlı)
COMMISSION_RATE = 0.0025
REBALANCE_FREQUENCY = 'W'    # 'D' (Daily), 'W' (Weekly)
MIN_HOLDING_DAYS = 7         # 5 -> 7 (User Protoly: 7-10 gün)
MIN_HOLDING_PERIODS = 7      
MIN_HOLDING_BY_SECTOR = {
    'BANKING': 1,      
    'HOLDING': 3,      
    'INDUSTRIAL': 2,   
    'GROWTH': 1        
}
ATR_PERIOD = 14          # Standart

# Dinamik Stop/Profit (ATR Çarpanları - Günlük için optimize edilecek, şimdilik safety)
# Dinamik Stop/Profit (Optimize Edildi - Sıkı Takip)
# Dinamik Stop/Profit (AGRESİF MOD - Trend Following - RESTORED STRICT)
ATR_STOP_LOSS_MULTIPLIER = 3.0     
ATR_TAKE_PROFIT_MULTIPLIER = 7.0   
ATR_TRAILING_STOP_MULTIPLIER = 2.5 

# Portfolio Diversification

# Sabit limitler (Sigorta olarak)
MAX_STOP_LOSS_PCT = 0.10    # %4 -> %10 (Volatilitede patlamamak için)
TRAILING_STOP_ACTIVE = True

# Portföy Yapılandırması (Çeşitlendirme & Risk)
PORTFOLIO_SIZE = 5           # 7 -> 5 (Konsantrasyon Artırıldı)
WEIGHTING_STRATEGY = 'RiskParity' 
RISK_PER_TRADE = 0.02        

ENABLE_MOMENTUM_FILTER = False # Temporarily disabled to verify baseline
MAX_SINGLE_POS_WEIGHT = 0.33 # Tek bir hisseye ayrılacak max ağırlık (limit)
ENABLE_RISK_SIZING = True    # Risk-based sizing aktif/pasif

# Güven Eşiği (AGRESİF - %0.60)
CONFIDENCE_THRESHOLDS = {
    'TIER_1': 0.50  # 0.60 -> 0.50 (Daha fazla sinyal yakalamak için düşürüldü)
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

# Macro Gate Eşikleri (AGRESİF - KAPALI)
ENABLE_MACRO_GATE = True  # Alpha koruması için aktif
# Macro Gate (Global Risk Yönetimi)
# Macro Gate (Global Risk Yönetimi)
MACRO_GATE_THRESHOLDS = {
    'VIX_HIGH': 40.0,         # 30.0 -> 40.0 (Daha gevşek)
    'USDTRY_CHANGE_5D': 0.05, # 0.03 -> 0.05 (Daha gevşek)
    'SP500_MOMENTUM': -0.06   # -0.04 -> -0.06 (Daha toleranslı)
}

# Optimize Edilmiş Model Parametreleri (Optuna Sonucu - Round 3 - 500 Trials)
# Veriler: 2015-2023 Train, 2023-2024 Valid. Best NDCG@5: 0.2906
OPTIMIZED_MODEL_PARAMS = {
    'learning_rate': 0.01538,
    'num_leaves': 77,
    'max_depth': 6,
    'min_child_samples': 66,
    'reg_alpha': 0.9187,
    'reg_lambda': 0.4115,
    'n_estimators': 1000, 
    'early_stopping_rounds': 50 
}

# Sektör rotasyon cezası (AGRESİF - ESNEK)
ENABLE_SECTOR_ROTATION_PENALTY = True
MAX_SECTOR_CONCENTRATION = 0.70  # %40 -> %70 (Fırsat olan sektöre yüklenmek için)
