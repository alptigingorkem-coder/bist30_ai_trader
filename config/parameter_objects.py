"""
Parameter Objects for reducing long parameter lists.

This module contains dataclasses that group related parameters together,
making function signatures cleaner and more maintainable.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class TrainingConfig:
    """Configuration for model training."""
    train_start: str
    train_end: str
    validation_split: float = 0.9
    learning_rate: float = 0.01
    max_depth: int = 6
    num_leaves: int = 31
    min_data_in_leaf: int = 20
    feature_fraction: float = 0.8
    bagging_fraction: float = 0.8
    bagging_freq: int = 5
    early_stopping_rounds: int = 50
    verbose: int = -1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for model training."""
        return {
            'learning_rate': self.learning_rate,
            'max_depth': self.max_depth,
            'num_leaves': self.num_leaves,
            'min_data_in_leaf': self.min_data_in_leaf,
            'feature_fraction': self.feature_fraction,
            'bagging_fraction': self.bagging_fraction,
            'bagging_freq': self.bagging_freq,
            'verbose': self.verbose
        }


@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""
    initial_capital: float = 100000.0
    commission: float = 0.002
    max_drawdown_limit: float = 0.30
    enable_risk_sizing: bool = False
    enable_kelly: bool = True
    risk_per_trade: float = 0.02
    max_single_pos_weight: float = 0.20
    min_holding_days: int = 0
    max_positions: int = 5
    
    # Date range
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    # Regime settings
    enable_regime_detection: bool = True
    regime_thresholds: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        """Initialize default regime thresholds if not provided."""
        if self.regime_thresholds is None:
            self.regime_thresholds = {
                'volatility_low': 0.25,
                'volatility_high': 0.61,
                'cds_high': 550,
                'try_change_high': 0.012
            }


@dataclass
class RiskConfig:
    """Configuration for risk management."""
    stop_loss_multiplier: float = 2.0
    take_profit_multiplier: float = 3.0
    max_position_size: float = 0.25
    max_portfolio_exposure: float = 0.80
    circuit_breaker_threshold: float = 0.25
    max_daily_loss_pct: float = 0.05
    max_consecutive_losses: int = 5
    trailing_stop_pct: float = 0.03
    
    # Position sizing
    enable_kelly: bool = True
    risk_per_trade: float = 0.02
    min_position_size: float = 0.02
    
    # Holding periods
    min_holding_days: int = 3
    max_holding_days: int = 60


@dataclass
class DataConfig:
    """Configuration for data loading and processing."""
    tickers: list
    start_date: str
    end_date: str
    
    # Cache settings
    use_cache: bool = True
    cache_dir: str = "data/live_cache"
    max_cache_age_hours: int = 24
    
    # Data quality
    min_data_points: int = 100
    max_missing_data_pct: float = 0.10
    fill_method: str = "ffill"
    
    # Feature engineering
    add_technical_indicators: bool = True
    add_macro_features: bool = True
    
    # Validation
    validate_data: bool = True
    check_for_gaps: bool = True
    check_for_anomalies: bool = True


@dataclass
class WalkForwardConfig:
    """Configuration for walk-forward validation."""
    train_window_days: int = 252  # 1 year
    test_window_days: int = 63    # 3 months
    step_days: int = 21           # 1 month
    min_train_samples: int = 1000
    
    # Training settings
    training_config: Optional[TrainingConfig] = None
    
    # Backtest settings
    backtest_config: Optional[BacktestConfig] = None
    
    # Output settings
    save_results: bool = True
    results_dir: str = "reports/walk_forward"
    verbose: bool = True


@dataclass
class FeatureEngineeringConfig:
    """Configuration for feature engineering."""
    # Technical indicators
    add_sma: bool = True
    sma_periods: list = field(default_factory=lambda: [20, 50, 200])
    
    add_rsi: bool = True
    rsi_period: int = 14
    
    add_macd: bool = True
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    add_atr: bool = True
    atr_period: int = 14
    
    add_bollinger: bool = True
    bollinger_period: int = 20
    bollinger_std: float = 2.0
    
    # Volatility features
    add_volatility: bool = True
    volatility_windows: list = field(default_factory=lambda: [10, 20, 60])
    
    # Momentum features
    add_momentum: bool = True
    momentum_periods: list = field(default_factory=lambda: [5, 10, 20])
    
    # Volume features
    add_volume_features: bool = True
    volume_ma_period: int = 20
    
    # Lag features
    add_lags: bool = True
    lag_periods: list = field(default_factory=lambda: [1, 2, 3, 5, 10])


@dataclass
class PaperTradingConfig:
    """Configuration for paper trading."""
    initial_capital: float = 10000.0
    max_positions: int = 5
    max_position_size: float = 0.20
    min_weight_change: float = 0.03
    
    # Risk management
    risk_config: Optional[RiskConfig] = None
    
    # Data refresh
    refresh_interval_minutes: int = 60
    market_hours_only: bool = True
    
    # Logging
    log_trades: bool = True
    log_dir: str = "logs/paper_trading"
    
    # Notifications
    enable_notifications: bool = False
    notification_email: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default risk config if not provided."""
        if self.risk_config is None:
            self.risk_config = RiskConfig()
