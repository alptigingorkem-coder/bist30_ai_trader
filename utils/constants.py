"""
Project-wide constants.
Centralized location for magic numbers and configuration values.
"""

# ============================================================================
# TRADING PARAMETERS
# ============================================================================

# Position Limits
MAX_POSITIONS = 10
MAX_POSITIONS_DEFAULT = 5  # Default max positions for conservative strategy
MAX_SINGLE_EXPOSURE = 0.10  # 10% of portfolio
MAX_TOTAL_EXPOSURE = 0.80   # 80% of portfolio
MAX_EXPOSURE_RATIO = 0.80   # Alias for MAX_TOTAL_EXPOSURE

# Position Sizing
DEFAULT_POSITION_SIZE = 0.05  # 5% of portfolio
MIN_POSITION_SIZE = 0.02      # 2% of portfolio
MAX_POSITION_SIZE = 0.15      # 15% of portfolio
MAX_SINGLE_POS_WEIGHT = 0.20  # 20% max single position weight

# Cash Management
MIN_CASH_RESERVE = 0.10  # 10% minimum cash reserve
CASH_USAGE_PCT = 0.99    # Use 99% of available cash for trades

# ============================================================================
# RISK MANAGEMENT
# ============================================================================

# Daily Risk Limits
DAILY_MAX_LOSS_PCT = 0.03           # 3% daily max loss
MAX_DAILY_LOSS_PCT = 0.05           # 5% max daily loss (circuit breaker)
CONSECUTIVE_LOSS_LIMIT = 3          # Stop after 3 consecutive losses
MAX_CONSECUTIVE_LOSSES = 5          # Maximum consecutive losses before pause
EXPOSURE_DECAY_RATE = 0.20          # 20% exposure reduction per loss

# Stop Loss / Take Profit
DEFAULT_STOP_LOSS_PCT = 0.05        # 5% stop loss
DEFAULT_TAKE_PROFIT_PCT = 0.10      # 10% take profit
TRAILING_STOP_PCT = 0.03            # 3% trailing stop
STOP_LOSS_MULTIPLIER = 2.0          # ATR multiplier for stop loss
TAKE_PROFIT_MULTIPLIER = 3.0        # ATR multiplier for take profit

# Circuit Breaker
CIRCUIT_BREAKER_THRESHOLD = 0.25    # 25% drawdown triggers circuit breaker
MAX_DRAWDOWN_LIMIT = 0.30           # 30% max drawdown limit

# Risk Per Trade
RISK_PER_TRADE = 0.02               # 2% risk per trade
RISK_PER_TRADE_CONSERVATIVE = 0.01  # 1% risk for conservative mode

# ============================================================================
# SIGNAL THRESHOLDS
# ============================================================================

# Confidence Thresholds
CONFIDENCE_THRESHOLD_HIGH = 0.85    # High confidence signal
CONFIDENCE_THRESHOLD_MEDIUM = 0.70  # Medium confidence signal
CONFIDENCE_THRESHOLD_LOW = 0.60     # Low confidence signal
CONFIDENCE_THRESHOLD_MIN = 0.55     # Minimum confidence to trade

# Weight Change Thresholds
MIN_WEIGHT_CHANGE = 0.03            # 3% minimum weight change for rebalancing
REBALANCE_THRESHOLD = 0.10          # 10% threshold for rebalancing

# Regime Detection
VOLATILITY_LOW_THRESHOLD = 0.25
VOLATILITY_HIGH_THRESHOLD = 0.61
CDS_HIGH_THRESHOLD = 550
TRY_CHANGE_HIGH_THRESHOLD = 0.012
MOMENTUM_THRESHOLD = 49
MIN_REGIME_DAYS = 3                 # Minimum days to confirm regime change

# VIX Thresholds
VIX_CRISIS = 35.0                   # VIX level indicating crisis
VIX_VOLATILE = 25.0                 # VIX level indicating volatility
VIX_NORMAL = 20.0                   # VIX level indicating normal market

# Trend Detection
SMA_TREND_THRESHOLD = 0.015         # 1.5% threshold for trend detection
ATR_SPIKE_MULTIPLIER = 1.8          # ATR spike multiplier
SIDEWAYS_RANGE = 0.008              # 0.8% range for sideways market
SIDEWAYS_MAX_DAYS = 15              # Maximum days in sideways market

# ============================================================================
# MODEL PARAMETERS
# ============================================================================

# Training
DEFAULT_EPOCHS = 100
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 0.001
EARLY_STOPPING_PATIENCE = 10
VALIDATION_SPLIT = 0.9      # 90% train, 10% validation

# LightGBM Parameters
LIGHTGBM_MAX_DEPTH = 6
LIGHTGBM_NUM_LEAVES = 31
LIGHTGBM_MIN_DATA_IN_LEAF = 20
LIGHTGBM_FEATURE_FRACTION = 0.8
LIGHTGBM_BAGGING_FRACTION = 0.8
LIGHTGBM_BAGGING_FREQ = 5

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
MIN_HOLDING_DAYS = 3        # Minimum holding period
MAX_HOLDING_DAYS = 60       # Maximum holding period
REBALANCE_FREQUENCY_DAYS = 7  # Rebalance every 7 days

# Cache Settings
MAX_CACHE_AGE_HOURS = 24    # 24 hours cache validity
CACHE_ROLLING_WINDOW = 20   # 20-day rolling window for cache

# Data Quality
MIN_DATA_POINTS = 100       # Minimum data points required
MAX_MISSING_DATA_PCT = 0.10 # 10% maximum missing data
MIN_LIQUIDITY_THRESHOLD = 0 # Minimum liquidity threshold (0 = disabled)

# Feature Engineering
SMA_SHORT_PERIOD = 20
SMA_LONG_PERIOD = 50
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ATR_PERIOD = 14             # ATR calculation period
ATR_MA_PERIOD = 60          # ATR moving average period
VOLATILITY_WINDOW = 20      # Volatility calculation window

# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

# Thresholds
MIN_SHARPE_RATIO = 1.0
MIN_SHARPE_RATIO_ACCEPTABLE = 0.5   # Acceptable Sharpe ratio
MIN_WIN_RATE = 0.50         # 50%
MIN_WIN_RATE_ACCEPTABLE = 0.45  # 45% acceptable win rate
MIN_PROFIT_FACTOR = 1.5
MIN_PROFIT_FACTOR_ACCEPTABLE = 1.2  # Acceptable profit factor
MAX_DRAWDOWN_PCT = 0.20     # 20%

# Health Monitoring
HEALTH_CHECK_WINDOW = 30    # 30-day health check window
MIN_TRADES_FOR_HEALTH = 10  # Minimum trades for health calculation

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

# ============================================================================
# TRADING EXECUTION
# ============================================================================

# Commission and Slippage
DEFAULT_COMMISSION = 0.002          # 0.2% commission
COMMISSION_RATE = 0.002             # Alias for DEFAULT_COMMISSION
BASE_SLIPPAGE = 0.0005              # 0.05% base slippage
IMPACT_SLIPPAGE_FACTOR = 0.1        # Impact slippage factor
MAX_SLIPPAGE = 0.03                 # 3% maximum slippage
DEFAULT_SLIPPAGE = 0.001            # 0.1% default slippage

# Initial Capital
DEFAULT_INITIAL_CAPITAL = 100000.0  # 100,000 TL default capital
INITIAL_CAPITAL_PAPER = 10000.0     # 10,000 TL for paper trading

# Trade Filters
MIN_TRADE_VALUE = 100.0             # Minimum trade value in TL
TRADE_BUFFER_PCT = 0.005            # 0.5% buffer to avoid small trades

# ============================================================================
# REGIME-BASED MULTIPLIERS
# ============================================================================

# Position Multipliers by Regime
REGIME_MULT_TREND_UP = 1.0          # Full position in uptrend
REGIME_MULT_NORMAL = 0.8            # 80% position in normal market
REGIME_MULT_SIDEWAYS = 0.5          # 50% position in sideways market
REGIME_MULT_VOLATILE = 0.0          # No position in volatile market
REGIME_MULT_CRISIS = 0.0            # No position in crisis

# Stop Loss Multipliers by Regime
REGIME_SL_TREND_UP = 1.5            # Wider stop in uptrend
REGIME_SL_NORMAL = 1.3              # Normal stop
REGIME_SL_SIDEWAYS = 1.2            # Tighter stop in sideways
REGIME_SL_VOLATILE = 1.0            # Tight stop in volatile
REGIME_SL_CRISIS = 0.8              # Very tight stop in crisis

# Max Positions by Regime
REGIME_MAX_POS_TREND_UP = 5         # 5 positions in uptrend
REGIME_MAX_POS_NORMAL = 4           # 4 positions in normal
REGIME_MAX_POS_SIDEWAYS = 3         # 3 positions in sideways
REGIME_MAX_POS_VOLATILE = 0         # No positions in volatile
REGIME_MAX_POS_CRISIS = 0           # No positions in crisis
