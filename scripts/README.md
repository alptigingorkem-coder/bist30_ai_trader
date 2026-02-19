# Scripts Directory

This directory contains executable scripts organized by functionality.

## 📁 Directory Structure

```
scripts/
├── analysis/          # Analysis and reporting tools
├── training/          # Model training scripts
├── validation/        # System validation tools
├── maintenance/       # Code maintenance utilities
├── ops/              # Operations and deployment
├── migration/        # Database migrations
└── utility/          # General utility scripts
```

## 🔧 Utility Modules

### Analysis Utils (`analysis/utils.py`)

Common financial metrics and analysis functions.

**Functions:**
- `calculate_max_drawdown(cumulative_returns)` - Calculate maximum drawdown
- `calculate_sharpe_ratio(returns)` - Calculate annualized Sharpe ratio

**Usage:**
```python
from scripts.analysis.utils import calculate_max_drawdown, calculate_sharpe_ratio

# Calculate metrics
max_dd = calculate_max_drawdown(cumulative_returns)
sharpe = calculate_sharpe_ratio(daily_returns)
```

### Validation Utils (`validation/utils.py`)

Helper functions for validation scripts.

**Functions:**
- `get_python_files(project_root)` - Find all Python files excluding specific directories

**Usage:**
```python
from scripts.validation.utils import get_python_files
from pathlib import Path

# Get all Python files
files = get_python_files(Path.cwd())
```

### Training Utils (`training/utils.py`)

Helper functions for model training.

**Functions:**
- `ensure_model_dir()` - Ensure models/saved directory exists

**Usage:**
```python
from scripts.training.utils import ensure_model_dir

# Create model directory if needed
ensure_model_dir()
```

### Verification Utils (`utility/verification_utils.py`)

Database and system verification tools.

**Functions:**
- `verify_db_records()` - Verify database records
- `verify_slippage()` - Test slippage calculations
- `test_slippage(engine, vol, avg_vol, size)` - Test specific slippage scenario

**Usage:**
```python
from scripts.utility.verification_utils import verify_db_records, verify_slippage

# Verify database
verify_db_records()

# Test slippage
verify_slippage()
```

## 📊 Analysis Scripts

### Feature Importance Analysis

```bash
# Run feature importance analysis
python scripts/analysis/run_feature_importance.py --config configs/banking.py

# With visualization
python scripts/analysis/run_feature_importance.py \
    --config configs/banking.py \
    --visualize \
    --top-n 20
```

### Performance Analysis

```bash
# Get training metrics
python scripts/analysis/get_training_metrics.py

# Compare models
python scripts/analysis/compare_improvements.py

# Run benchmark
python scripts/analysis/run_benchmark.py
```

## 🎓 Training Scripts

### Model Training

```bash
# Train LightGBM ranker
python scripts/training/train_models.py

# Train CatBoost ranker
python scripts/training/train_catboost.py

# Train TFT model
python scripts/training/train_tft.py
```

### Validation

```bash
# Walk-forward validation
python scripts/training/walk_forward_validation.py

# Validate model
python scripts/training/validate_model.py
```

## ✅ Validation Scripts

### System Checks

```bash
# Check integration
python scripts/validation/check_integration.py

# Check requirements
python scripts/validation/check_requirements.py

# Verify integration
python scripts/validation/verify_integration.py
```

## 🔧 Maintenance Scripts

See [maintenance/README.md](maintenance/README.md) for detailed documentation.

```bash
# Find unused files
python scripts/maintenance/find_unused_files.py

# Find duplicate code
python scripts/maintenance/find_duplicate_code.py

# Generate cleanup report
python scripts/maintenance/generate_cleanup_report.py
```

## 🚀 Operations Scripts

### Paper Trading

```bash
# Start paper trading
python scripts/ops/paper_trading_runner.py

# Daily run
python scripts/ops/daily_run.py
```

### Environment

```bash
# Check environment
python scripts/ops/check_env.py

# Validate environment
python scripts/ops/validate_env.py
```

## 🗄️ Migration Scripts

```bash
# Migrate to database
python scripts/migration/migrate_to_db.py
```

## 💡 Tips

- All scripts support `--help` flag for usage information
- Use virtual environment: `source .venv/bin/activate`
- Check logs in `reports/` directory
- Most scripts support dry-run mode for safety

## 📚 Related Documentation

- [Feature Importance Guide](../docs/feature_importance_cli_usage.md)
- [Maintenance Tools](maintenance/README.md)
- [Main README](../README.md)
