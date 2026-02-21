"""
Project-wide constants.
Centralized location for magic numbers and configuration values.
"""

# ============================================================================
# TRADING PARAMETERS
# ============================================================================

# Position Limits
MAX_POSITIONS = 10
MAX_SINGLE_EXPOSURE = 0.10  # 10% of portfolio
MAX_TOTAL_EXPOSURE = 0.80   # 80% of portfolio

# Position Sizing
DEFAULT_POSITION_SIZE = 0.05  # 5% of portfolio
MIN_POSITION_SIZE = 0.02      # 2% of portfolio
MAX_POSITION_SIZE = 0.15      # 15% of portfolio

# ============================================================================
# RISK MANAGEMENT
# ============================================================================

# Daily Risk Limits
DAILY_MAX_LOSS_PCT = 0.03           # 3% daily max loss
CONSECUTIVE_LOSS_LIMIT = 3          # Stop after 3 consecutive losses
EXPOSURE_DECAY_RATE = 0.20          # 20% exposure reduction per loss

# Stop Loss / Take Profit
DEFAULT_STOP_LOSS_PCT = 0.05        # 5% stop loss
DEFAULT_TAKE_PROFIT_PCT = 0.10      # 10% take profit
TRAILING_STOP_PCT = 0.03            # 3% trailing stop

# ============================================================================
# SIGNAL THRESHOLDS
# ============================================================================

# Confidence Thresholds
CONFIDENCE_THRESHOLD_HIGH = 0.85    # High confidence signal
CONFIDENCE_THRESHOLD_MEDIUM = 0.70  # Medium confidence signal
CONFIDENCE_THRESHOLD_LOW = 0.60     # Low confidence signal

# Regime Detection
VOLATILITY_LOW_THRESHOLD = 0.25
VOLATILITY_HIGH_THRESHOLD = 0.61
CDS_HIGH_THRESHOLD = 550
TRY_CHANGE_HIGH_THRESHOLD = 0.012
MOMENTUM_THRESHOLD = 49

# ============================================================================
# MODEL PARAMETERS
# ============================================================================

# Training
DEFAULT_EPOCHS = 100
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 0.001
EARLY_STOPPING_PATIENCE = 10

# Validation
MIN_TRAIN_SAMPLES = 1000
MIN_VALIDATION_SAMPLES = 200
TEST_SIZE_RATIO = 0.2

# ============================================================================
# DATA PARAMETERS
# ============================================================================

# Time Windows
LOOKBACK_DAYS = 252         # 1 year
MIN_HISTORY_DAYS = 60       # Minimum data required
MAX_DATA_GAP_DAYS = 5       # Maximum acceptable gap

# Feature Engineering
SMA_SHORT_PERIOD = 20
SMA_LONG_PERIOD = 50
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

# Thresholds
MIN_SHARPE_RATIO = 1.0
MIN_WIN_RATE = 0.50         # 50%
MIN_PROFIT_FACTOR = 1.5
MAX_DRAWDOWN_PCT = 0.20     # 20%

# ============================================================================
# FILE PATHS
# ============================================================================

# Data
DATA_CACHE_DIR = "data/live_cache"
FEATURE_STORE_DIR = "data/feature_store"
MODEL_SAVE_DIR = "models/saved"

# Logs
LOG_DIR = "logs"
PAPER_TRADING_LOG_DIR = "logs/paper_trading"
BACKTEST_LOG_DIR = "logs/backtest"

# Reports
REPORT_DIR = "reports"
VALIDATION_REPORT_DIR = "reports/validation"

# ============================================================================
# MISC
# ============================================================================

# Timeouts
API_TIMEOUT_SECONDS = 30
DATA_FETCH_TIMEOUT = 60

# Retry
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# Precision
PRICE_DECIMAL_PLACES = 2
PERCENTAGE_DECIMAL_PLACES = 2
RATIO_DECIMAL_PLACES = 3
