import platform
import os
import torch

from utils.logging_config import get_logger

_log = get_logger(__name__)

# ─────────────────────────────────────────────────────────────
# YAML-based Settings Loader
# ─────────────────────────────────────────────────────────────
_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.yaml")
_settings = {}

def _load_settings():
    """settings.yaml'ı yükle, env variable override uygula."""
    global _settings
    try:
        import yaml
        if os.path.exists(_SETTINGS_PATH):
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                _settings = yaml.safe_load(f) or {}
            _log.debug("settings.yaml loaded (%d top-level keys)", len(_settings))
        else:
            _log.warning("settings.yaml not found, using hardcoded defaults")
    except ImportError:
        _log.warning("PyYAML not installed, using hardcoded defaults")
    except Exception as e:
        _log.error("settings.yaml load error: %s", e)

def _cfg(section: str, key: str, default=None):
    """
    Config değeri al: settings.yaml > env variable > hardcoded default.
    Env override: BIST_{SECTION}_{KEY} (büyük harf).
    """
    env_key = f"BIST_{section.upper()}_{key.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        # Tip dönüşümü
        if isinstance(default, bool):
            return env_val.lower() in ("true", "1", "yes")
        if isinstance(default, int):
            return int(env_val)
        if isinstance(default, float):
            return float(env_val)
        return env_val
    
    sect = _settings.get(section, {})
    if isinstance(sect, dict) and key in sect:
        return sect[key]
    return default

_load_settings()

# ─────────────────────────────────────────────────────────────
# Device Detection
# ─────────────────────────────────────────────────────────────
def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
         return torch.device("mps")
    return torch.device("cpu")

DEVICE = get_device()
_log.info("Mevcut Cihaz: %s", DEVICE)

# --- TIER SISTEMI (SADELEŞTİRİLMİŞ) ---
# Sadece Tier 1 (Core) Aktif
# --- ABLATION STUDY CONFIG ---
ENABLE_MACRO_IN_MODEL = _cfg("features", "enable_macro_in_model", False)

TIERS = {
    'TIER_1': [
        # Pozitif Alpha Üretenler (2024 OOS Backtest Sonuçlarına Göre)
        "TSKB.IS",   # +%11 (En İyi)
        "EREGL.IS",  # +%7.5
        "ODAS.IS",   # +%5.9
        "TTKOM.IS",  # +%5.2
        "AKBNK.IS",  # +%5.1
        # Potansiyeller (Düşük ama Pozitif)
        "EKGYO.IS",  # ~%2-3 (Volatil)
        "SISE.IS",   # ~%2-3
        "KOZAL.IS",  # Mining Sektör Lideri
        "SAHOL.IS",  # Holding
        "YKBNK.IS"   # Banka
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
START_DATE = _cfg("dates", "start", "2015-01-01")
END_DATE = None

# Overfitting Önleme (Strict Split)
TRAIN_END_DATE = _cfg("dates", "train_end", "2023-12-31")
TEST_START_DATE = _cfg("dates", "test_start", "2024-01-01")

# KAP Entegrasyonu
ENABLE_KAP_FEATURES = _cfg("features", "enable_kap_features", False)





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
TIMEFRAME = 'D'

# Teknik İndikatörler
RSI_PERIOD = _cfg("indicators", "rsi_period", 14)
MACD_FAST = _cfg("indicators", "macd_fast", 12)
MACD_SLOW = _cfg("indicators", "macd_slow", 26)
MACD_SIGNAL = _cfg("indicators", "macd_signal", 9)
BB_LENGTH = _cfg("indicators", "bollinger_length", 20)
BB_STD = _cfg("indicators", "bollinger_std", 2)

# Model Target
LABEL_TYPE = 'RawRank'
FORWARD_WINDOW = 1
NUM_QUANTILES = 5

# Model
MODEL_TYPE = _cfg("model", "type", "ensemble")
TARGET_COL = "Excess_Return"
VAL_SIZE = _cfg("model", "val_size", 0.15)
LABEL_TYPE = _cfg("model", "label_type", "Hybrid")
HYBRID_WEIGHT = _cfg("model", "hybrid_weight", 0.85)
FORWARD_WINDOWS = _cfg("model", "forward_windows", [1, 5])
FORWARD_WEIGHTS = _cfg("model", "forward_weights", [0.6, 0.4])

# Leakage sütunları (yapısal, YAML'e taşınmaz)
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

# Risk Yönetimi
COMMISSION_RATE = _cfg("risk", "commission_rate", 0.0025)
REBALANCE_FREQUENCY = _cfg("risk", "rebalance_frequency", "W")
MIN_HOLDING_DAYS = _cfg("risk", "min_holding_days", 7)
MIN_HOLDING_PERIODS = MIN_HOLDING_DAYS
MIN_HOLDING_BY_SECTOR = {
    'BANKING': 1, 'HOLDING': 3, 'INDUSTRIAL': 2, 'GROWTH': 1
}
ATR_PERIOD = _cfg("indicators", "atr_period", 14)

# Dinamik Stop/Profit (ATR Çarpanları)
ATR_STOP_LOSS_MULTIPLIER = _cfg("risk", "stop_loss_atr_mult", 3.0)
ATR_TAKE_PROFIT_MULTIPLIER = _cfg("risk", "take_profit_atr_mult", 15.0)
ATR_TRAILING_STOP_MULTIPLIER = _cfg("risk", "trailing_stop_atr_mult", 3.0)

# Sabit limitler
MAX_STOP_LOSS_PCT = _cfg("risk", "max_stop_loss_pct", 0.10)
TRAILING_STOP_ACTIVE = _cfg("risk", "trailing_stop_active", True)

# Portföy Yapılandırması
PORTFOLIO_SIZE = _cfg("portfolio", "size", 3)
WEIGHTING_STRATEGY = _cfg("portfolio", "weighting", "EqualWeight")
RISK_PER_TRADE = _cfg("risk", "risk_per_trade", 0.05)

ENABLE_MOMENTUM_FILTER = _cfg("portfolio", "enable_momentum_filter", False)
MAX_SINGLE_POS_WEIGHT = _cfg("portfolio", "max_single_pos_weight", 0.33)
ENABLE_RISK_SIZING = _cfg("risk", "enable_risk_sizing", True)

CONFIDENCE_THRESHOLDS = {
    'TIER_1': 0.30  # 0.35 -> 0.30 (Ultra Aggressive - Low Confidence OK)
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

# Rejim
USE_ADAPTIVE_REGIME = _cfg("regime", "use_adaptive", True)

REGIME_THRESHOLDS = {
    "volatility_low": _cfg("regime", "volatility_low", 0.279),
    "volatility_high": _cfg("regime", "volatility_high", 0.61),
    "cds_high": 600,
    "try_change_high": 0.0147,
    "momentum_threshold": _cfg("regime", "momentum_threshold", 49),
    "min_regime_days": _cfg("regime", "min_regime_days", 2)
}

# Macro Gate
ENABLE_MACRO_GATE = _cfg("macro_gate", "enabled", True)
MACRO_GATE_THRESHOLDS = {
    'VIX_HIGH': _cfg("macro_gate", "vix_high", 40.0),
    'USDTRY_CHANGE_5D': _cfg("macro_gate", "usdtry_change_5d", 0.05),
    'SP500_MOMENTUM': _cfg("macro_gate", "sp500_momentum", -0.06)
}

# Optimize Edilmiş LightGBM Parametreleri
OPTIMIZED_MODEL_PARAMS = {
    'learning_rate': _cfg("lgbm_params", "learning_rate", 0.01538),
    'num_leaves': _cfg("lgbm_params", "num_leaves", 77),
    'max_depth': _cfg("lgbm_params", "max_depth", 6),
    'min_child_samples': _cfg("lgbm_params", "min_child_samples", 66),
    'reg_alpha': _cfg("lgbm_params", "reg_alpha", 0.9187),
    'reg_lambda': _cfg("lgbm_params", "reg_lambda", 0.4115),
    'n_estimators': _cfg("lgbm_params", "n_estimators", 1000),
    'early_stopping_rounds': _cfg("lgbm_params", "early_stopping_rounds", 50)
}

# TFT Parametreleri (GPU Optimized)
TFT_LEARNING_RATE = _cfg("tft_params", "learning_rate", 0.03)
TFT_HIDDEN_SIZE = _cfg("tft_params", "hidden_size", 128)
TFT_ATTENTION_HEADS = _cfg("tft_params", "attention_head_size", 4)
TFT_DROPOUT = _cfg("tft_params", "dropout", 0.15)
TFT_HIDDEN_CONTINUOUS_SIZE = _cfg("tft_params", "hidden_continuous_size", 16)
TFT_LSTM_LAYERS = _cfg("tft_params", "lstm_layers", 2)
TFT_BATCH_SIZE = _cfg("tft_params", "batch_size", 128)

# Sektör Rotasyonu
ENABLE_SECTOR_ROTATION_PENALTY = _cfg("sector_rotation", "enabled", True)
MAX_SECTOR_CONCENTRATION = _cfg("sector_rotation", "max_concentration", 0.70)
