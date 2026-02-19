# Backtest Guide

## Overview

Comprehensive guide for backtesting trading strategies in BIST30 AI Trader.

## Quick Start

```bash
# Run basic backtest
python scripts/analysis/run_backtest.py

# Walk-forward validation
python scripts/training/walk_forward_validation.py
```

## Backtest Engine

### Basic Usage

```python
from core.backtest.engine import BacktestEngine

# Initialize
engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,      # 0.1%
    slippage_model="adaptive"
)

# Run backtest
results = engine.run(
    start_date="2023-01-01",
    end_date="2023-12-31",
    model_path="models/saved/ranker.pkl"
)

# Print results
print(f"Total Return: {results['total_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
```

### Configuration

```python
BACKTEST_CONFIG = {
    'initial_capital': 100000,
    'commission': 0.001,
    'slippage_model': 'adaptive',
    'max_positions': 5,
    'position_size_method': 'kelly',
    'rebalance_frequency': 'daily'
}
```

## Portfolio Management

### Position Sizing

**Kelly Criterion:**
```python
from core.position_sizing import KellySizer

sizer = KellySizer(
    win_rate=0.55,
    avg_win=0.05,
    avg_loss=0.03
)

position_size = sizer.calculate(
    capital=100000,
    price=50.0
)
```

**Equal Weight:**
```python
position_size = capital / max_positions
```

**Risk-Based:**
```python
position_size = capital * risk_per_trade / stop_loss_distance
```

### Rebalancing

```python
# Daily rebalancing
engine.rebalance_frequency = 'daily'

# Weekly rebalancing
engine.rebalance_frequency = 'weekly'

# Monthly rebalancing
engine.rebalance_frequency = 'monthly'
```

## Risk Management

### Stop Loss

```python
# Percentage-based
STOP_LOSS_PCT = 0.10  # 10%

# ATR-based
stop_loss = entry_price - (2 * atr)

# Time-based
MAX_HOLDING_PERIOD = 30  # days
```

### Position Limits

```python
# Maximum position size
MAX_POSITION_SIZE = 0.25  # 25% of capital

# Maximum positions
MAX_POSITIONS = 5

# Sector limits
MAX_SECTOR_EXPOSURE = 0.40  # 40% per sector
```

### Drawdown Control

```python
# Maximum drawdown limit
MAX_DRAWDOWN_LIMIT = 0.20  # 20%

# Stop trading if exceeded
if current_drawdown > MAX_DRAWDOWN_LIMIT:
    engine.stop_trading()
```

## Slippage Modeling

### Adaptive Slippage

```python
def calculate_slippage(volume, avg_volume, order_size):
    """Calculate realistic slippage based on market impact."""
    impact_ratio = order_size / avg_volume
    
    if impact_ratio < 0.01:
        return 0.0002  # 2 bps
    elif impact_ratio < 0.05:
        return 0.0005  # 5 bps
    elif impact_ratio < 0.10:
        return 0.0010  # 10 bps
    else:
        # Additional impact for large orders
        extra_impact = (impact_ratio - 0.10) * 0.05
        return 0.0010 + extra_impact
```

### Fixed Slippage

```python
FIXED_SLIPPAGE = 0.0005  # 5 bps
```

## Performance Metrics

### Returns

```python
# Total return
total_return = (final_equity - initial_capital) / initial_capital

# Annual return
annual_return = (1 + total_return) ** (365 / days) - 1

# Daily returns
daily_returns = equity.pct_change()
```

### Risk Metrics

```python
# Sharpe ratio
sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std()

# Max drawdown
peak = equity.cummax()
drawdown = (equity - peak) / peak
max_drawdown = drawdown.min()

# Sortino ratio
downside_returns = daily_returns[daily_returns < 0]
sortino_ratio = np.sqrt(252) * daily_returns.mean() / downside_returns.std()
```

### Trading Metrics

```python
# Win rate
win_rate = winning_trades / total_trades

# Profit factor
profit_factor = gross_profit / gross_loss

# Average win/loss
avg_win = total_profit / winning_trades
avg_loss = total_loss / losing_trades
```

## Walk-Forward Validation

### Configuration

```python
WALK_FORWARD_CONFIG = {
    'train_window': 365,  # days
    'test_window': 90,    # days
    'step_size': 30,      # days
    'min_train_size': 180 # minimum training days
}
```

### Process

1. **Split data into windows**
2. **Train model on training window**
3. **Test on validation window**
4. **Roll forward**
5. **Aggregate results**

### Example

```python
from scripts.training.walk_forward_validation import comprehensive_walk_forward

results = comprehensive_walk_forward(
    start_date="2020-01-01",
    end_date="2023-12-31",
    train_window=365,
    test_window=90
)

print(f"Average NDCG@5: {results['avg_ndcg']:.4f}")
print(f"Average Sharpe: {results['avg_sharpe']:.2f}")
```

## Visualization

### Equity Curve

```python
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(results['equity_curve'])
plt.title('Equity Curve')
plt.xlabel('Date')
plt.ylabel('Equity')
plt.grid(True)
plt.show()
```

### Drawdown Chart

```python
plt.figure(figsize=(12, 6))
plt.fill_between(results['dates'], results['drawdown'], 0, alpha=0.3)
plt.title('Drawdown')
plt.xlabel('Date')
plt.ylabel('Drawdown %')
plt.grid(True)
plt.show()
```

### Returns Distribution

```python
plt.figure(figsize=(10, 6))
plt.hist(results['daily_returns'], bins=50, alpha=0.7)
plt.title('Returns Distribution')
plt.xlabel('Daily Return')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()
```

## Reporting

### Generate Report

```bash
python scripts/analysis/final_validation_report.py
```

### Report Contents

- Summary statistics
- Performance metrics
- Risk metrics
- Trade analysis
- Equity curve
- Drawdown chart
- Monthly returns heatmap

## Best Practices

1. **Use realistic assumptions** for commissions and slippage
2. **Test on multiple time periods** including bear markets
3. **Validate with walk-forward** for out-of-sample performance
4. **Monitor drawdowns** and implement risk controls
5. **Check for overfitting** by comparing in-sample vs out-of-sample
6. **Document assumptions** and limitations
7. **Regular retraining** with new data
8. **Stress testing** under extreme market conditions

## Common Pitfalls

### Look-Ahead Bias

```python
# BAD: Using future data
features['future_return'] = data['close'].shift(-1)

# GOOD: Only use past data
features['past_return'] = data['close'].shift(1)
```

### Survivorship Bias

```python
# Include delisted stocks in historical data
data = loader.fetch_all_stocks(include_delisted=True)
```

### Overfitting

```python
# Use walk-forward validation
# Limit model complexity
# Regularization
# Cross-validation
```

## Troubleshooting

### Unrealistic Returns

- Check for data leakage
- Verify slippage and commissions
- Review position sizing
- Check for look-ahead bias

### High Drawdowns

- Implement stop losses
- Reduce position sizes
- Add risk controls
- Diversify across sectors

### Poor Out-of-Sample Performance

- Model overfitting
- Market regime change
- Insufficient training data
- Feature engineering issues

## Related Documentation

- [Main README](../README.md)
- [Training Guide](training.md)
- [Risk Management](risk_management.md)
