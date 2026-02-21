# Design Document: Code Quality Refactoring

## Overview

This design document outlines the technical approach for refactoring the BIST30 AI Trader codebase from a quality score of 27.0/100 to 80.0/100. The refactoring will be executed in four sequential phases, each targeting specific quality metrics while maintaining system functionality and production stability.

The refactoring strategy employs established design patterns (Repository, Service Layer, Command, Strategy, Facade) and proven refactoring techniques (Extract Method, Extract Class, Guard Clauses, Parameter Objects). All work will be performed on a separate branch with incremental commits, comprehensive testing, and continuous quality measurement.

### Key Design Principles

1. **Incremental Refactoring**: Small, testable changes with frequent commits
2. **Test-Driven Refactoring**: Tests pass before and after each change
3. **Single Responsibility**: Each class has one clear purpose
4. **Backward Compatibility**: Existing APIs remain functional during transition
5. **Production Safety**: Master branch remains stable for paper trading

### Success Metrics

- Overall Score: 27.0 → 80.0/100
- SRP Score: 0.0 → 80.0/100
- Complexity Score: 0.0 → 75.0/100
- Code Smells Score: 0.0 → 85.0/100
- DRY Score: 90.0 → 95.0/100

## Architecture

### Phase 1: God Classes Refactoring Architecture

The god classes (PortfolioState, StrategyHealth, DataLoader) will be decomposed using the **Repository + Service + Specialized Components** pattern. This architecture separates concerns into distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Code                              │
│              (Existing code using god classes)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Facade/Coordinator                          │
│         (Simplified god class or new coordinator)            │
│              - Delegates to specialized classes              │
│              - Maintains backward compatibility              │
└────┬────────────┬────────────┬────────────┬─────────────────┘
     │            │            │            │
     ▼            ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐
│Repository│ │ Service │ │Validator │ │Formatter │
│         │ │         │ │          │ │          │
│ Load    │ │Business │ │Validation│ │Reporting │
│ Save    │ │ Logic   │ │  Rules   │ │ Display  │
│Serialize│ │Transform│ │  Checks  │ │  Export  │
└─────────┘ └─────────┘ └──────────┘ └──────────┘
```

### Phase 2: Complexity Reduction Architecture

Complex functions will be refactored using the **Command Pattern** for orchestration and **Strategy Pattern** for conditional logic:

```
┌─────────────────────────────────────────────────────────────┐
│                    Original Function                         │
│              (e.g., main() with 620 lines)                   │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼ Refactor to
┌─────────────────────────────────────────────────────────────┐
│                   Command Coordinator                        │
│                    (50-80 lines)                             │
│  - Orchestrates workflow                                     │
│  - Delegates to specialized commands                         │
└────┬────────────┬────────────┬────────────┬─────────────────┘
     │            │            │            │
     ▼            ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│LoadConfig│ │ LoadData │ │RunBacktest│ │Generate  │
│ Command  │ │ Command  │ │  Command  │ │  Report  │
│          │ │          │ │           │ │  Command │
│ 30-40    │ │ 40-50    │ │  50-60    │ │  40-50   │
│  lines   │ │  lines   │ │   lines   │ │  lines   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### Refactoring Branch Strategy

```
master (stable, paper trading)
  │
  └─── refactoring/phase-1-god-classes
         │
         ├─── refactoring/phase-1-portfolio-state
         ├─── refactoring/phase-1-strategy-health
         └─── refactoring/phase-1-data-loader
```

Each sub-branch is merged back to the phase branch after testing, then the phase branch is merged to master after phase completion and validation.

## Components and Interfaces

### Phase 1 Components

#### 1.1 PortfolioState Decomposition

**PortfolioRepository** (Data Persistence)
```python
class PortfolioRepository:
    """Handles portfolio state persistence operations."""
    
    def __init__(self, state_file: str):
        self.state_file = state_file
    
    def load(self) -> dict:
        """Load portfolio state from JSON file."""
        # Returns: dict with positions, trades, cash, etc.
    
    def save(self, state: dict) -> None:
        """Save portfolio state to JSON file."""
    
    def _serialize_state(self, state: dict) -> str:
        """Convert state to JSON string."""
    
    def _deserialize_state(self, json_str: str) -> dict:
        """Convert JSON string to state dict."""
```

**PortfolioService** (Business Logic)
```python
class PortfolioService:
    """Handles portfolio trade execution logic."""
    
    def __init__(self, state: PortfolioState, validator: PortfolioValidator):
        self.state = state
        self.validator = validator
    
    def apply_trade_decision(self, decision: dict) -> dict:
        """Execute a trade decision (open, close, scale)."""
        # Returns: trade result dict
    
    def open_position(self, symbol: str, price: float, quantity: float, 
                     side: str, confidence: float = None, 
                     regime: str = None) -> dict:
        """Open a new position."""
    
    def close_position(self, symbol: str, price: float) -> dict:
        """Close an existing position."""
    
    def scale_in(self, symbol: str, price: float, quantity: float) -> dict:
        """Add to an existing position."""
    
    def scale_out(self, symbol: str, price: float, pct: float) -> dict:
        """Reduce an existing position."""
```

**PortfolioValidator** (Validation Logic)
```python
class PortfolioValidator:
    """Handles portfolio validation and risk checks."""
    
    def __init__(self, config: dict):
        self.max_positions = config.get('max_positions', 10)
        self.max_exposure = config.get('max_exposure', 0.95)
        self.stress_limits = config.get('stress_limits', {})
    
    def can_open_new_position(self, symbol: str, size_pct: float, 
                             current_state: dict) -> Tuple[bool, str]:
        """Check if a new position can be opened."""
        # Returns: (can_open, reason)
    
    def check_stress_limits(self, current_state: dict) -> Tuple[bool, str]:
        """Check if stress limits are exceeded."""
    
    def validate_trade_size(self, symbol: str, quantity: float, 
                           price: float, current_state: dict) -> Tuple[bool, str]:
        """Validate trade size against limits."""
```

**PortfolioFormatter** (Presentation)
```python
class PortfolioFormatter:
    """Handles portfolio reporting and display."""
    
    def get_trade_ledger(self, trades: List[dict]) -> List[dict]:
        """Format trade history for display."""
    
    def export_trade_ledger_csv(self, trades: List[dict], 
                                filepath: str = None) -> str:
        """Export trade ledger to CSV file."""
    
    def format_stress_status(self, stress_state: dict) -> str:
        """Format stress status for display."""
    
    def format_position_summary(self, positions: dict) -> str:
        """Format current positions for display."""
```

**PortfolioMetrics** (Analytics)
```python
class PortfolioMetrics:
    """Handles portfolio statistical analysis."""
    
    def get_trade_statistics(self, trades: List[dict]) -> dict:
        """Calculate comprehensive trade statistics."""
        # Returns: win_rate, profit_factor, avg_win, avg_loss, etc.
    
    def get_confidence_bucket_analysis(self, trades: List[dict]) -> dict:
        """Analyze performance by confidence buckets."""
    
    def get_signal_accuracy_report(self, trades: List[dict]) -> dict:
        """Analyze signal accuracy by regime and confidence."""
    
    def calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio from returns."""
```

**Refactored PortfolioState** (Coordinator)
```python
class PortfolioState:
    """Coordinates portfolio operations using specialized components."""
    
    def __init__(self, state_file: str = "logs/paper_trading/portfolio_state.json"):
        self.repository = PortfolioRepository(state_file)
        self.validator = PortfolioValidator(config)
        self.service = PortfolioService(self, self.validator)
        self.formatter = PortfolioFormatter()
        self.metrics = PortfolioMetrics()
        
        # Core state (simplified)
        self.positions = {}
        self.closed_trades = []
        self.cash = 100000.0
        self.initial_capital = 100000.0
    
    # Delegate methods to specialized components
    def apply_trade_decision(self, decision: dict) -> dict:
        return self.service.apply_trade_decision(decision)
    
    def get_trade_statistics(self) -> dict:
        return self.metrics.get_trade_statistics(self.closed_trades)
    
    def save(self) -> None:
        state = self._get_state_dict()
        self.repository.save(state)
    
    @classmethod
    def load(cls, state_file: str) -> 'PortfolioState':
        instance = cls(state_file)
        state = instance.repository.load()
        instance._set_state_from_dict(state)
        return instance
```

#### 1.2 StrategyHealth Decomposition

**HealthMetrics** (Calculations)
```python
class HealthMetrics:
    """Calculates strategy health metrics."""
    
    def calculate_win_rate(self, trades: List[dict]) -> float:
        """Calculate win rate from trades."""
    
    def calculate_profit_factor(self, trades: List[dict]) -> float:
        """Calculate profit factor."""
    
    def calculate_sharpe_ratio(self, equity_curve: List[float]) -> float:
        """Calculate Sharpe ratio from equity curve."""
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown."""
    
    def calculate_rolling_metrics(self, trades: List[dict], 
                                  window: int) -> dict:
        """Calculate metrics over rolling window."""
```

**HealthAnalyzer** (Analysis Logic)
```python
class HealthAnalyzer:
    """Analyzes strategy health and trends."""
    
    def __init__(self, metrics: HealthMetrics):
        self.metrics = metrics
    
    def calculate_health_score(self, trades: List[dict], 
                              equity_curve: List[float]) -> float:
        """Calculate overall health score (0-100)."""
    
    def analyze_regime_performance(self, trades: List[dict]) -> dict:
        """Analyze performance by market regime."""
    
    def detect_degradation(self, recent_trades: List[dict], 
                          historical_trades: List[dict]) -> Tuple[bool, str]:
        """Detect if strategy is degrading."""
    
    def get_regime_recommendation(self, current_regime: str, 
                                 regime_stats: dict) -> dict:
        """Recommend whether to trade in current regime."""
```

**HealthReporter** (Reporting)
```python
class HealthReporter:
    """Generates strategy health reports."""
    
    def format_health_report(self, health_data: dict) -> str:
        """Format comprehensive health report."""
    
    def get_health_summary(self, health_data: dict) -> dict:
        """Get summary health data for API/UI."""
    
    def export_health_report(self, health_data: dict, 
                            filepath: str) -> None:
        """Export health report to file."""
```

**HealthValidator** (Health Checks)
```python
class HealthValidator:
    """Validates strategy health against thresholds."""
    
    def __init__(self, thresholds: dict):
        self.min_win_rate = thresholds.get('min_win_rate', 45.0)
        self.min_profit_factor = thresholds.get('min_profit_factor', 1.2)
        self.max_drawdown = thresholds.get('max_drawdown', 0.15)
    
    def is_healthy(self, metrics: dict) -> bool:
        """Check if strategy meets health thresholds."""
    
    def check_invalidation_rules(self, metrics: dict) -> Tuple[StrategyState, str]:
        """Check if strategy should be invalidated."""
    
    def should_skip_regime(self, regime: str, regime_stats: dict) -> Tuple[bool, str]:
        """Check if regime should be skipped."""
```

#### 1.3 DataLoader Decomposition

**DataRepository** (Data Fetching)
```python
class DataRepository:
    """Handles raw data fetching from sources."""
    
    def fetch_from_yahoo(self, symbol: str, start_date: str, 
                        end_date: str) -> pd.DataFrame:
        """Fetch data from Yahoo Finance."""
    
    def fetch_from_is_yatirim(self, symbol: str, start_date: str, 
                              end_date: str) -> pd.DataFrame:
        """Fetch data from İş Yatırım (fallback)."""
    
    def fetch_with_fallback(self, symbol: str, start_date: str, 
                           end_date: str) -> pd.DataFrame:
        """Fetch data with automatic fallback."""
```

**DataCache** (Caching)
```python
class DataCache:
    """Handles data caching operations."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
    
    def get(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Get data from cache if available and valid."""
    
    def put(self, symbol: str, data: pd.DataFrame) -> None:
        """Store data in cache."""
    
    def invalidate(self, symbol: str) -> None:
        """Invalidate cache for symbol."""
    
    def is_cache_valid(self, symbol: str, max_age_hours: int = 24) -> bool:
        """Check if cached data is still valid."""
```

**DataValidator** (Data Quality)
```python
class DataValidator:
    """Validates data quality."""
    
    def validate_data(self, data: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate data quality and completeness."""
        # Returns: (is_valid, list_of_issues)
    
    def check_for_gaps(self, data: pd.DataFrame) -> List[str]:
        """Check for missing dates in data."""
    
    def check_for_anomalies(self, data: pd.DataFrame) -> List[str]:
        """Check for price anomalies."""
    
    def validate_columns(self, data: pd.DataFrame) -> bool:
        """Validate required columns exist."""
```

**DataTransformer** (Data Processing)
```python
class DataTransformer:
    """Transforms and cleans data."""
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize data."""
    
    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to data."""
    
    def resample_data(self, data: pd.DataFrame, freq: str) -> pd.DataFrame:
        """Resample data to different frequency."""
    
    def align_data(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Align multiple dataframes to same dates."""
```

### Phase 2 Components

#### 2.1 BacktestCommand (for main() refactoring)

```python
class BacktestCommand:
    """Orchestrates backtest execution workflow."""
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.data_loader = DataLoader()
        self.model_loader = ModelLoader()
        self.backtest_runner = BacktestRunner()
        self.report_generator = ReportGenerator()
    
    def execute(self) -> None:
        """Execute complete backtest workflow."""
        config = self._load_configuration()
        data = self._load_data(config)
        model = self._load_model(config)
        results = self._run_backtest(data, model, config)
        self._generate_report(results, config)
    
    def _load_configuration(self) -> dict:
        """Load and validate configuration."""
        # Guard clauses for validation
        # 30-40 lines
    
    def _load_data(self, config: dict) -> dict:
        """Load and prepare data."""
        # 40-50 lines
    
    def _load_model(self, config: dict) -> Any:
        """Load trained model."""
        # 30-40 lines
    
    def _run_backtest(self, data: dict, model: Any, config: dict) -> dict:
        """Run backtest simulation."""
        # 50-60 lines
    
    def _generate_report(self, results: dict, config: dict) -> None:
        """Generate and save backtest report."""
        # 40-50 lines
```

#### 2.2 BacktestStrategy (for run_backtest() refactoring)

```python
class BacktestStrategy:
    """Executes backtest strategy with simplified logic."""
    
    def __init__(self, config: dict):
        self.position_manager = PositionManager(config)
        self.risk_manager = RiskManager(config)
        self.trade_executor = TradeExecutor(config)
    
    def run(self, data: pd.DataFrame, signals: dict) -> dict:
        """Run backtest with guard clauses."""
        results = []
        
        for date, signal in signals.items():
            # Guard clauses (early returns)
            if not self._is_valid_signal(signal):
                continue
            
            if not self._can_trade(date, data):
                continue
            
            if not self.risk_manager.check_risk_limits(self.position_manager.state):
                continue
            
            # Execute trade
            trade = self._execute_trade(signal, date, data)
            if trade:
                results.append(trade)
        
        return self._aggregate_results(results)
    
    def _is_valid_signal(self, signal: dict) -> bool:
        """Validate signal quality."""
        # Guard clause logic
        # 10-15 lines
    
    def _can_trade(self, date: str, data: pd.DataFrame) -> bool:
        """Check if trading is allowed on date."""
        # 10-15 lines
    
    def _execute_trade(self, signal: dict, date: str, data: pd.DataFrame) -> Optional[dict]:
        """Execute single trade."""
        # 30-40 lines
    
    def _aggregate_results(self, results: List[dict]) -> dict:
        """Aggregate trade results into summary."""
        # 20-30 lines
```

#### 2.3 PositionAwareSession (for run_position_aware_session() refactoring)

```python
class PositionAwareSession:
    """Manages position-aware trading session."""
    
    def __init__(self, portfolio: PortfolioState, engine: BacktestEngine, 
                 model: Any):
        self.portfolio = portfolio
        self.engine = engine
        self.model = model
        self.signal_generator = SignalGenerator(model)
        self.trade_executor = TradeExecutor(portfolio, engine)
        self.reporter = SessionReporter()
    
    def run(self) -> dict:
        """Execute complete trading session."""
        self._initialize_session()
        signals = self._generate_signals()
        trades = self._execute_trades(signals)
        results = self._finalize_session(trades)
        return results
    
    def _initialize_session(self) -> None:
        """Initialize session state."""
        # 20-30 lines
    
    def _generate_signals(self) -> dict:
        """Generate trading signals."""
        # 40-50 lines
    
    def _execute_trades(self, signals: dict) -> List[dict]:
        """Execute trades from signals."""
        # 50-60 lines
    
    def _finalize_session(self, trades: List[dict]) -> dict:
        """Finalize session and generate summary."""
        # 30-40 lines
```

### Phase 3 Components

#### 3.1 Constants Module

```python
# utils/constants.py (already exists, will be expanded)

# Portfolio constants
MAX_POSITIONS = 10
MAX_EXPOSURE_RATIO = 0.95
DEFAULT_POSITION_SIZE = 0.10

# Confidence thresholds
CONFIDENCE_THRESHOLD_HIGH = 0.85
CONFIDENCE_THRESHOLD_MEDIUM = 0.70
CONFIDENCE_THRESHOLD_LOW = 0.55

# Risk management
MAX_DAILY_LOSS_PCT = 0.02
MAX_POSITION_LOSS_PCT = 0.05
STRESS_DECAY_RATE = 0.1

# Health monitoring
MIN_WIN_RATE = 45.0
MIN_PROFIT_FACTOR = 1.2
MAX_DRAWDOWN_PCT = 0.15
MIN_TRADES_FOR_ANALYSIS = 30

# Data quality
MAX_CACHE_AGE_HOURS = 24
MIN_DATA_POINTS = 100
MAX_PRICE_CHANGE_PCT = 0.20  # Anomaly detection
```

#### 3.2 Parameter Objects

```python
@dataclass
class TrainingConfig:
    """Configuration for model training."""
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    optimizer: str = "adam"
    loss_function: str = "mse"
    validation_split: float = 0.2
    early_stopping_patience: int = 10

@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    commission: float = 0.001
    slippage: float = 0.0005
    max_positions: int = 10
    position_sizing: str = "equal_weight"
    rebalance_frequency: str = "daily"

@dataclass
class RiskConfig:
    """Configuration for risk management."""
    max_position_size: float = 0.15
    max_exposure: float = 0.95
    max_daily_loss: float = 0.02
    max_position_loss: float = 0.05
    stop_loss_pct: float = 0.08
    take_profit_pct: float = 0.15
```

## Data Models

### Core Data Structures

#### Portfolio State Model
```python
@dataclass
class Position:
    """Represents an open position."""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    side: str  # "long" or "short"
    entry_date: str
    confidence: Optional[float] = None
    regime: Optional[str] = None
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def pnl(self) -> float:
        if self.side == "long":
            return (self.current_price - self.entry_price) * self.quantity
        else:
            return (self.entry_price - self.current_price) * self.quantity
    
    @property
    def pnl_pct(self) -> float:
        if self.side == "long":
            return (self.current_price - self.entry_price) / self.entry_price
        else:
            return (self.entry_price - self.current_price) / self.entry_price

@dataclass
class Trade:
    """Represents a closed trade."""
    symbol: str
    side: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    confidence: Optional[float] = None
    regime: Optional[str] = None
    exit_reason: str = "signal"  # "signal", "stop_loss", "take_profit", "time"
```

#### Health State Model
```python
@dataclass
class HealthMetricsData:
    """Container for health metrics."""
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    avg_win: float
    avg_loss: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class RegimePerformance:
    """Performance metrics for a specific regime."""
    regime: str
    trade_count: int
    win_rate: float
    profit_factor: float
    avg_pnl: float
    total_pnl: float
    
    def is_sufficient_data(self, min_trades: int = 10) -> bool:
        return self.trade_count >= min_trades
```

#### Signal Model
```python
@dataclass
class TradingSignal:
    """Represents a trading signal."""
    symbol: str
    date: str
    action: str  # "buy", "sell", "hold"
    confidence: float
    regime: str
    features: dict
    model_prediction: float
    
    def is_high_confidence(self, threshold: float = CONFIDENCE_THRESHOLD_HIGH) -> bool:
        return self.confidence >= threshold
    
    def should_trade(self, min_confidence: float = CONFIDENCE_THRESHOLD_LOW) -> bool:
        return self.confidence >= min_confidence and self.action != "hold"
```

### Data Flow

```
┌──────────────┐
│ Market Data  │
│   Source     │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│DataRepository│────▶│  DataCache   │
└──────┬───────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│DataValidator │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│DataTransformer│
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│    Model     │────▶│TradingSignal │
└──────────────┘     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │PortfolioService│
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Position   │
                     │     or       │
                     │    Trade     │
                     └──────────────┘
```


## Error Handling

### Error Handling Strategy

The refactoring will maintain and improve the existing error handling approach while ensuring errors are handled at appropriate levels:

1. **Repository Layer**: Handle I/O errors (file not found, permission denied, corrupt data)
2. **Service Layer**: Handle business logic errors (invalid trades, insufficient funds)
3. **Validator Layer**: Return validation results (success/failure with reasons)
4. **Coordinator Layer**: Aggregate errors and provide user-friendly messages

### Error Categories

#### Data Errors
```python
class DataError(Exception):
    """Base class for data-related errors."""
    pass

class DataNotFoundError(DataError):
    """Raised when required data is not available."""
    pass

class DataValidationError(DataError):
    """Raised when data fails validation."""
    pass

class CacheError(DataError):
    """Raised when cache operations fail."""
    pass
```

#### Trading Errors
```python
class TradingError(Exception):
    """Base class for trading-related errors."""
    pass

class InsufficientFundsError(TradingError):
    """Raised when insufficient funds for trade."""
    pass

class PositionLimitError(TradingError):
    """Raised when position limits are exceeded."""
    pass

class InvalidTradeError(TradingError):
    """Raised when trade parameters are invalid."""
    pass
```

### Error Handling Patterns

#### Repository Pattern
```python
class PortfolioRepository:
    def load(self) -> dict:
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"State file not found: {self.state_file}, creating new state")
            return self._create_default_state()
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt state file: {e}")
            raise DataValidationError(f"Failed to parse state file: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading state: {e}")
            raise DataError(f"Failed to load state: {e}")
```

#### Validator Pattern
```python
class PortfolioValidator:
    def can_open_new_position(self, symbol: str, size_pct: float, 
                             current_state: dict) -> Tuple[bool, str]:
        """Returns (can_open, reason) instead of raising exceptions."""
        
        # Check position limit
        if current_state['position_count'] >= self.max_positions:
            return False, f"Maximum positions ({self.max_positions}) reached"
        
        # Check exposure limit
        new_exposure = current_state['exposure'] + size_pct
        if new_exposure > self.max_exposure:
            return False, f"Would exceed max exposure ({self.max_exposure})"
        
        # Check if already have position
        if symbol in current_state['positions']:
            return False, f"Already have position in {symbol}"
        
        return True, "OK"
```

#### Service Pattern
```python
class PortfolioService:
    def apply_trade_decision(self, decision: dict) -> dict:
        """Execute trade with comprehensive error handling."""
        try:
            # Validate decision
            if not self._is_valid_decision(decision):
                return {'success': False, 'error': 'Invalid decision format'}
            
            # Check if can trade
            can_trade, reason = self.validator.can_open_new_position(
                decision['symbol'], 
                decision['size_pct'],
                self.state.get_state_dict()
            )
            
            if not can_trade:
                return {'success': False, 'error': reason}
            
            # Execute trade
            trade = self.open_position(
                decision['symbol'],
                decision['price'],
                decision['quantity'],
                decision['side'],
                decision.get('confidence'),
                decision.get('regime')
            )
            
            return {'success': True, 'trade': trade}
            
        except InsufficientFundsError as e:
            logger.warning(f"Insufficient funds: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in trade execution: {e}", exc_info=True)
            return {'success': False, 'error': f"Internal error: {e}"}
```

### Logging Strategy

Each layer will have appropriate logging:

```python
# Repository layer: INFO for operations, WARNING for fallbacks, ERROR for failures
logger.info(f"Loading portfolio state from {self.state_file}")
logger.warning(f"State file not found, creating default state")
logger.error(f"Failed to load state: {e}")

# Service layer: INFO for trades, WARNING for rejected trades, ERROR for failures
logger.info(f"Opening position: {symbol} @ {price}")
logger.warning(f"Trade rejected: {reason}")
logger.error(f"Trade execution failed: {e}")

# Validator layer: DEBUG for checks, INFO for violations
logger.debug(f"Checking position limit: {current} / {max}")
logger.info(f"Position limit exceeded: {current} >= {max}")
```

## Testing Strategy

### Dual Testing Approach

The refactoring will employ both unit tests and property-based tests for comprehensive coverage:

**Unit Tests**: Validate specific examples, edge cases, and error conditions
- Test specific scenarios with known inputs and expected outputs
- Test edge cases (empty lists, zero values, boundary conditions)
- Test error handling (invalid inputs, missing data, exceptions)
- Test integration between components

**Property-Based Tests**: Validate universal properties across all inputs
- Test invariants that should always hold
- Test round-trip properties (serialize/deserialize, parse/print)
- Test metamorphic properties (relationships between operations)
- Run minimum 100 iterations per property test

### Testing Framework

**Unit Testing**: pytest with fixtures
**Property-Based Testing**: Hypothesis library
**Coverage Target**: Maintain or improve current coverage (aim for >85%)

### Test Organization

```
tests/
├── fixtures/
│   ├── portfolio_fixtures.py      # Shared portfolio test data
│   ├── health_fixtures.py         # Shared health test data
│   └── data_fixtures.py           # Shared data test data
├── unit/
│   ├── test_portfolio_repository.py
│   ├── test_portfolio_service.py
│   ├── test_portfolio_validator.py
│   ├── test_health_metrics.py
│   └── ...
├── property/
│   ├── test_portfolio_properties.py
│   ├── test_health_properties.py
│   └── ...
└── integration/
    ├── test_portfolio_integration.py
    ├── test_backtest_integration.py
    └── ...
```

### Property-Based Test Configuration

Each property test will be tagged with a comment referencing the design property:

```python
from hypothesis import given, strategies as st
import pytest

# Feature: code-quality-refactoring, Property 1: Portfolio state round-trip
@given(st.builds(PortfolioState))
def test_portfolio_state_serialization_roundtrip(portfolio_state):
    """For any portfolio state, serializing then deserializing should produce equivalent state."""
    # Serialize
    serialized = portfolio_state.repository._serialize_state(portfolio_state._get_state_dict())
    
    # Deserialize
    deserialized_dict = portfolio_state.repository._deserialize_state(serialized)
    
    # Create new state from deserialized data
    new_state = PortfolioState()
    new_state._set_state_from_dict(deserialized_dict)
    
    # Assert equivalence
    assert new_state.cash == portfolio_state.cash
    assert new_state.positions == portfolio_state.positions
    assert len(new_state.closed_trades) == len(portfolio_state.closed_trades)
```

### Test Strategy by Phase

#### Phase 1: God Classes Refactoring Tests

For each new class created:
1. Write unit tests for each public method
2. Write property tests for invariants
3. Write integration tests for class interactions
4. Ensure existing tests still pass

Example test plan for PortfolioRepository:
```python
# Unit tests
def test_load_existing_state()
def test_load_missing_file_creates_default()
def test_load_corrupt_file_raises_error()
def test_save_creates_valid_json()
def test_save_preserves_all_fields()

# Property tests
@given(st.dictionaries(...))
def test_serialize_deserialize_roundtrip(state_dict)

# Integration tests
def test_repository_integrates_with_portfolio_state()
```

#### Phase 2: Complexity Reduction Tests

For each refactored function:
1. Ensure existing tests still pass
2. Add tests for new extracted methods
3. Add property tests for complex logic

Example test plan for BacktestCommand:
```python
# Unit tests
def test_load_configuration_valid_config()
def test_load_configuration_missing_file()
def test_load_data_with_cache()
def test_load_data_without_cache()
def test_run_backtest_generates_results()

# Integration tests
def test_execute_complete_workflow()
def test_execute_with_invalid_config()

# Property tests
@given(st.builds(BacktestConfig))
def test_backtest_results_deterministic(config)
```

#### Phase 3: Code Smells Tests

For refactored code:
1. Ensure tests use named constants instead of magic numbers
2. Update tests to use parameter objects
3. Remove tests for deleted dead code

#### Phase 4: DRY Violations Tests

For shared fixtures:
1. Create reusable fixtures in tests/fixtures/
2. Update existing tests to use shared fixtures
3. Ensure no test duplication

### Regression Testing

Before and after each phase:
1. Run full test suite: `pytest tests/`
2. Run paper trading simulation: `python scripts/paper_trading_runner.py --dry-run`
3. Run sample backtest: `python scripts/run_backtest.py --config test_config.yaml`
4. Compare backtest results to ensure identical output
5. Run quality analysis: `python scripts/quality/run_quality_analysis.py`

### Performance Testing

For critical paths:
```python
import pytest
import time

def test_portfolio_state_load_performance():
    """Ensure portfolio state loads in <100ms."""
    start = time.time()
    state = PortfolioState.load()
    elapsed = time.time() - start
    assert elapsed < 0.1, f"Load took {elapsed}s, expected <0.1s"

def test_backtest_performance():
    """Ensure backtest completes in reasonable time."""
    # Benchmark before refactoring
    # Ensure refactored version is not slower
    pass
```

### Continuous Integration

Each commit should:
1. Pass all tests
2. Maintain or improve code coverage
3. Pass linting (flake8, black, mypy)
4. Update quality score in positive direction


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

For this refactoring project, the correctness properties focus on ensuring that the refactored code maintains behavioral equivalence with the original code. Since this is a refactoring project (not new feature development), the primary correctness concern is that the system continues to work exactly as it did before, while improving code quality metrics.

### Property 1: API Contract Preservation

*For any* public method that existed in the original god classes, calling that method with the same arguments on the refactored classes should produce the same result.

**Validates: Requirements 1.5**

**Rationale**: When god classes are refactored into smaller classes, the public API must remain unchanged to ensure existing code continues to work. This property ensures behavioral equivalence at the API level.

**Testing Approach**: 
- Identify all public methods in PortfolioState, StrategyHealth, and DataLoader
- For each method, generate random valid inputs
- Call the method on both original and refactored implementations
- Assert that outputs are equivalent

**Example**:
```python
from hypothesis import given, strategies as st

# Feature: code-quality-refactoring, Property 1: API Contract Preservation
@given(
    symbol=st.text(min_size=1, max_size=10),
    size_pct=st.floats(min_value=0.01, max_value=0.20)
)
def test_portfolio_can_open_position_api_preserved(symbol, size_pct):
    """For any symbol and size, the refactored can_open_new_position should behave identically."""
    # Setup both original and refactored instances with same state
    original_state = PortfolioStateOriginal()
    refactored_state = PortfolioState()
    
    # Call method on both
    original_result = original_state.can_open_new_position(symbol, size_pct)
    refactored_result = refactored_state.can_open_new_position(symbol, size_pct)
    
    # Assert same behavior
    assert original_result[0] == refactored_result[0]  # Same boolean result
    assert original_result[1] == refactored_result[1]  # Same reason string
```

### Property 2: Backtest Determinism

*For any* backtest configuration and historical data, running the backtest before and after refactoring should produce identical results (same trades, same PnL, same metrics).

**Validates: Requirements 6.4**

**Rationale**: Refactoring should not change the computational behavior of the system. Backtest results are the ultimate test of behavioral equivalence for a trading system. If backtest results change, the refactoring has introduced a bug.

**Testing Approach**:
- Generate random backtest configurations (date ranges, symbols, parameters)
- Run backtest with original code and save results
- Run backtest with refactored code
- Assert all results are identical (trades, PnL, metrics, equity curve)

**Example**:
```python
from hypothesis import given, strategies as st
import pytest

# Feature: code-quality-refactoring, Property 2: Backtest Determinism
@given(
    start_date=st.dates(min_value=date(2020, 1, 1), max_value=date(2023, 1, 1)),
    end_date=st.dates(min_value=date(2023, 1, 2), max_value=date(2024, 1, 1)),
    initial_capital=st.floats(min_value=10000, max_value=1000000),
    symbols=st.lists(st.sampled_from(['THYAO', 'AKBNK', 'GARAN', 'ISCTR']), 
                     min_size=1, max_size=5)
)
def test_backtest_results_unchanged_after_refactoring(start_date, end_date, 
                                                      initial_capital, symbols):
    """For any backtest configuration, results should be identical before and after refactoring."""
    # Ensure end_date > start_date
    if end_date <= start_date:
        return
    
    config = BacktestConfig(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        initial_capital=initial_capital,
        symbols=symbols
    )
    
    # Run with original code (saved baseline)
    original_results = run_backtest_original(config)
    
    # Run with refactored code
    refactored_results = run_backtest_refactored(config)
    
    # Assert identical results
    assert len(original_results['trades']) == len(refactored_results['trades'])
    assert abs(original_results['total_pnl'] - refactored_results['total_pnl']) < 0.01
    assert abs(original_results['sharpe_ratio'] - refactored_results['sharpe_ratio']) < 0.001
    assert original_results['equity_curve'] == refactored_results['equity_curve']
```

### Property 3: Backward Compatibility

*For any* existing code that uses the original god classes, that code should continue to work without modification after the refactoring.

**Validates: Requirements 6.5**

**Rationale**: Refactoring should not break existing code. The refactored classes should maintain the same interface and behavior as the original classes, allowing existing code to work without changes. This is achieved through the Facade pattern where the refactored god class delegates to specialized components.

**Testing Approach**:
- Identify existing code that uses PortfolioState, StrategyHealth, DataLoader
- Run that code with refactored classes
- Assert no errors and same behavior

**Example**:
```python
from hypothesis import given, strategies as st

# Feature: code-quality-refactoring, Property 3: Backward Compatibility
@given(
    trades=st.lists(
        st.fixed_dictionaries({
            'symbol': st.text(min_size=1, max_size=10),
            'pnl': st.floats(min_value=-1000, max_value=1000),
            'confidence': st.floats(min_value=0.5, max_value=1.0)
        }),
        min_size=10,
        max_size=100
    )
)
def test_existing_code_works_with_refactored_classes(trades):
    """For any list of trades, existing analysis code should work with refactored PortfolioState."""
    # Create refactored portfolio state
    portfolio = PortfolioState()
    portfolio.closed_trades = trades
    
    # This is existing code that should still work
    try:
        # Existing method calls
        stats = portfolio.get_trade_statistics()
        confidence_analysis = portfolio.get_confidence_bucket_analysis()
        ledger = portfolio.get_trade_ledger()
        
        # Should not raise any errors
        assert isinstance(stats, dict)
        assert isinstance(confidence_analysis, dict)
        assert isinstance(ledger, list)
        
        # Should have expected keys (same as original)
        assert 'win_rate' in stats
        assert 'profit_factor' in stats
        assert 'total_trades' in stats
        
    except AttributeError as e:
        pytest.fail(f"Backward compatibility broken: {e}")
    except TypeError as e:
        pytest.fail(f"API signature changed: {e}")
```

### Property 4: State Serialization Round-Trip

*For any* portfolio state, serializing it to JSON and then deserializing should produce an equivalent state.

**Validates: Requirements 1.5 (indirectly - ensures data persistence works correctly)**

**Rationale**: The PortfolioRepository handles serialization/deserialization. This is a critical operation for paper trading, as state must be persisted between sessions. A round-trip property ensures no data is lost or corrupted during save/load operations.

**Testing Approach**:
- Generate random portfolio states
- Serialize to JSON
- Deserialize from JSON
- Assert all fields are equivalent

**Example**:
```python
from hypothesis import given, strategies as st

# Feature: code-quality-refactoring, Property 4: State Serialization Round-Trip
@given(
    cash=st.floats(min_value=0, max_value=1000000),
    positions=st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.fixed_dictionaries({
            'quantity': st.floats(min_value=1, max_value=1000),
            'entry_price': st.floats(min_value=1, max_value=1000),
            'current_price': st.floats(min_value=1, max_value=1000)
        })
    ),
    trades=st.lists(
        st.fixed_dictionaries({
            'symbol': st.text(min_size=1, max_size=10),
            'pnl': st.floats(min_value=-1000, max_value=1000)
        }),
        max_size=50
    )
)
def test_portfolio_state_serialization_roundtrip(cash, positions, trades):
    """For any portfolio state, serialize then deserialize should preserve all data."""
    # Create state
    state = PortfolioState()
    state.cash = cash
    state.positions = positions
    state.closed_trades = trades
    
    # Serialize
    state_dict = state._get_state_dict()
    serialized = state.repository._serialize_state(state_dict)
    
    # Deserialize
    deserialized_dict = state.repository._deserialize_state(serialized)
    
    # Create new state from deserialized data
    new_state = PortfolioState()
    new_state._set_state_from_dict(deserialized_dict)
    
    # Assert equivalence
    assert abs(new_state.cash - state.cash) < 0.01
    assert new_state.positions.keys() == state.positions.keys()
    assert len(new_state.closed_trades) == len(state.closed_trades)
```

### Property 5: Validation Consistency

*For any* portfolio state and trade decision, the validator should return consistent results regardless of how many times it's called.

**Validates: Requirements 1.5 (indirectly - ensures validation logic is deterministic)**

**Rationale**: Validation logic should be pure and deterministic. Given the same inputs, it should always return the same result. This property ensures the PortfolioValidator is implemented correctly without side effects.

**Testing Approach**:
- Generate random portfolio states and trade decisions
- Call validator multiple times with same inputs
- Assert results are always identical

**Example**:
```python
from hypothesis import given, strategies as st

# Feature: code-quality-refactoring, Property 5: Validation Consistency
@given(
    symbol=st.text(min_size=1, max_size=10),
    size_pct=st.floats(min_value=0.01, max_value=0.30),
    current_positions=st.integers(min_value=0, max_value=15),
    current_exposure=st.floats(min_value=0.0, max_value=1.0)
)
def test_validator_returns_consistent_results(symbol, size_pct, current_positions, 
                                              current_exposure):
    """For any validation inputs, calling validator multiple times should return same result."""
    validator = PortfolioValidator({'max_positions': 10, 'max_exposure': 0.95})
    
    state = {
        'position_count': current_positions,
        'exposure': current_exposure,
        'positions': {}
    }
    
    # Call validator multiple times
    result1 = validator.can_open_new_position(symbol, size_pct, state)
    result2 = validator.can_open_new_position(symbol, size_pct, state)
    result3 = validator.can_open_new_position(symbol, size_pct, state)
    
    # All results should be identical
    assert result1 == result2 == result3
```

### Property 6: Metrics Calculation Invariants

*For any* list of trades, certain invariants should hold in the calculated metrics (e.g., win_rate should be between 0 and 100, profit_factor should be non-negative).

**Validates: Requirements 1.5 (indirectly - ensures metrics calculations are correct)**

**Rationale**: The PortfolioMetrics class calculates various statistics. These calculations should always produce valid results within expected ranges. This property catches calculation errors and edge cases.

**Testing Approach**:
- Generate random trade lists
- Calculate metrics
- Assert invariants hold (ranges, relationships between metrics)

**Example**:
```python
from hypothesis import given, strategies as st

# Feature: code-quality-refactoring, Property 6: Metrics Calculation Invariants
@given(
    trades=st.lists(
        st.fixed_dictionaries({
            'symbol': st.text(min_size=1, max_size=10),
            'pnl': st.floats(min_value=-1000, max_value=1000, allow_nan=False),
            'pnl_pct': st.floats(min_value=-1.0, max_value=5.0, allow_nan=False),
            'side': st.sampled_from(['long', 'short'])
        }),
        min_size=1,
        max_size=100
    )
)
def test_metrics_calculation_invariants(trades):
    """For any list of trades, calculated metrics should satisfy invariants."""
    metrics = PortfolioMetrics()
    stats = metrics.get_trade_statistics(trades)
    
    # Invariants that should always hold
    assert 0 <= stats['win_rate'] <= 100, "Win rate should be between 0 and 100"
    assert stats['profit_factor'] >= 0, "Profit factor should be non-negative"
    assert stats['total_trades'] == len(trades), "Total trades should match input"
    assert stats['winning_trades'] + stats['losing_trades'] <= stats['total_trades']
    
    # If there are winning trades, avg_win should be positive
    if stats['winning_trades'] > 0:
        assert stats['avg_win'] > 0, "Average win should be positive when there are wins"
    
    # If there are losing trades, avg_loss should be negative
    if stats['losing_trades'] > 0:
        assert stats['avg_loss'] < 0, "Average loss should be negative when there are losses"
```

### Testing Notes

All property-based tests will be configured to run a minimum of 100 iterations to ensure comprehensive coverage of the input space. Each test will be tagged with a comment referencing the property number and description for traceability.

The properties focus on behavioral equivalence and correctness of the refactored code, rather than code quality metrics (which are measured separately by the quality analysis script). This ensures that refactoring improves code structure without changing system behavior.

