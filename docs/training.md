# Model Training Guide

## Overview

This guide covers training machine learning models for the BIST30 AI Trader system.

## Available Models

### 1. LightGBM Ranker

Fast gradient boosting model for daily stock ranking.

**Features:**
- Fast training and inference
- Handles missing values
- Feature importance analysis
- NDCG@5 optimization

**Training:**
```bash
python scripts/training/train_models.py
```

**Configuration:**
```python
# In config.py
LGBM_PARAMS = {
    'objective': 'lambdarank',
    'metric': 'ndcg',
    'ndcg_eval_at': [5],
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.9
}
```

### 2. CatBoost Ranker

Categorical feature handling with ranking objectives.

**Features:**
- Automatic categorical encoding
- Robust to overfitting
- GPU acceleration support
- NDCG@5 optimization

**Training:**
```bash
python scripts/training/train_catboost.py
```

**Configuration:**
```python
CATBOOST_PARAMS = {
    'loss_function': 'YetiRank',
    'iterations': 1000,
    'learning_rate': 0.03,
    'depth': 6
}
```

### 3. TFT (Temporal Fusion Transformer)

Deep learning model for time series forecasting.

**Features:**
- Attention mechanisms
- Multi-horizon forecasting
- Interpretable predictions
- GPU required for training

**Training:**
```bash
python scripts/training/train_tft.py
```

**Requirements:**
- PyTorch with GPU support
- AMD ROCm or NVIDIA CUDA

## Training Pipeline

### 1. Data Preparation

```python
from utils.data_loader import DataLoader

# Load data
loader = DataLoader(start_date="2020-01-01")
data = loader.fetch_stock_data("THYAO")

# Feature engineering
from utils.feature_engineering import FeatureEngineer
fe = FeatureEngineer()
features = fe.create_features(data)
```

### 2. Train-Test Split

```python
# Time-based split
train_end = "2023-06-30"
test_start = "2023-07-01"

train_data = data[data.index <= train_end]
test_data = data[data.index >= test_start]
```

### 3. Model Training

```python
from models.ranking_model import RankingModel

# Initialize model
model = RankingModel()

# Train
model.train(
    X_train=train_features,
    y_train=train_labels,
    group_train=train_groups
)

# Save
model.save("models/saved/ranker.pkl")
```

### 4. Evaluation

```python
# Predict
predictions = model.predict(test_features)

# Calculate metrics
from sklearn.metrics import ndcg_score
ndcg = ndcg_score([test_labels], [predictions], k=5)
print(f"NDCG@5: {ndcg:.4f}")
```

## Walk-Forward Validation

Robust out-of-sample testing with rolling windows.

```bash
python scripts/training/walk_forward_validation.py
```

**Process:**
1. Split data into windows (e.g., 12 months train, 3 months test)
2. Train model on training window
3. Test on validation window
4. Roll forward and repeat
5. Aggregate results

**Configuration:**
```python
WALK_FORWARD_CONFIG = {
    'train_window': 365,  # days
    'test_window': 90,    # days
    'step_size': 30       # days
}
```

## Hyperparameter Tuning

### Optuna Integration

```bash
python scripts/training/optimize_hyperparameters.py
```

**Example:**
```python
import optuna

def objective(trial):
    params = {
        'num_leaves': trial.suggest_int('num_leaves', 20, 50),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1),
        'feature_fraction': trial.suggest_float('feature_fraction', 0.7, 1.0)
    }
    
    model = RankingModel(**params)
    model.train(X_train, y_train)
    score = model.evaluate(X_val, y_val)
    
    return score

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
```

## MLflow Tracking

All training runs are logged to MLflow.

**Start MLflow UI:**
```bash
mlflow ui --port 5000
```

**Access:** http://localhost:5000

**Logged Metrics:**
- NDCG@5
- Training loss
- Validation loss
- Feature importance
- Model parameters

## Feature Engineering

### Technical Indicators

```python
# Price-based
features['returns'] = data['close'].pct_change()
features['volatility'] = data['returns'].rolling(20).std()
features['rsi'] = calculate_rsi(data['close'])

# Volume-based
features['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()

# Momentum
features['momentum_5d'] = data['close'] / data['close'].shift(5) - 1
features['momentum_20d'] = data['close'] / data['close'].shift(20) - 1
```

### Fundamental Features

```python
# From feature store
fundamentals = loader.load_fundamentals("THYAO")
features['pe_ratio'] = fundamentals['pe_ratio']
features['pb_ratio'] = fundamentals['pb_ratio']
features['roe'] = fundamentals['roe']
```

### Macro Features

```python
# Market regime
features['regime'] = macro_gate.detect_regime(data)

# Market indicators
features['market_return'] = market_data['close'].pct_change()
features['market_volatility'] = market_data['returns'].rolling(20).std()
```

## Model Comparison

```bash
python scripts/analysis/compare_improvements.py
```

Compares multiple models on:
- NDCG@5
- Sharpe ratio
- Max drawdown
- Win rate
- Training time

## Best Practices

1. **Always use walk-forward validation** for realistic performance estimates
2. **Track experiments with MLflow** for reproducibility
3. **Monitor feature importance** to understand model behavior
4. **Retrain regularly** (e.g., monthly) with new data
5. **Use ensemble methods** to reduce model risk
6. **Validate on multiple time periods** including bear markets
7. **Check for data leakage** in feature engineering
8. **Save model artifacts** with version control

## Troubleshooting

### Out of Memory

```python
# Reduce batch size
BATCH_SIZE = 1024  # Instead of 4096

# Use data sampling
train_data = train_data.sample(frac=0.5)
```

### Slow Training

```python
# Use GPU
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Reduce model complexity
params['num_leaves'] = 20  # Instead of 50
params['max_depth'] = 5    # Instead of 10
```

### Poor Performance

1. Check for data leakage
2. Verify feature engineering
3. Try different hyperparameters
4. Use more training data
5. Check label quality

## Related Documentation

- [Main README](../README.md)
- [Feature Importance Analysis](feature_importance_analysis.md)
- [Backtest Guide](backtest.md)
