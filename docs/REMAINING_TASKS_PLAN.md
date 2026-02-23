# Remaining Tasks Implementation Plan

**Status:** Tasks 1-10 COMPLETED, Tasks 11-19 DOCUMENTED  
**Date:** 2026-02-23

---

## Completed Tasks (1-10) ✅

### Phase 1: God Classes Refactoring ✅
- Task 2: PortfolioState refactored (13 new classes, 185 tests)
- Task 3: StrategyHealth refactored (4 new classes, 117 tests)
- Task 4: DataLoader refactored (4 new classes, 96 tests)
- Task 5: Phase 1 Checkpoint (710 tests passing)

### Phase 2: Complexity Reduction ✅
- Task 6: main() refactored (BacktestCommand, 26 tests)
- Task 7: run_backtest() refactored (BacktestStrategy, 34 tests)
- Task 8: run_position_aware_session() refactored (PositionAwareSession, 26 tests)
- Task 9: Complex functions refactored (WalkForwardValidator, DynamicBacktestRunner)
- Task 10: Phase 2 Checkpoint (801 tests passing, score 29.7/100)

---

## Remaining Tasks (11-19) 📋

### Task 11: Long Functions Refactoring

**Objective:** Refactor top 20 longest functions using Extract Method pattern

**Identified Long Functions (from quality report):**
1. `core/backtest/portfolio_engine.py:22` - run_backtest() - 144 lines
2. `core/backtest/backtest_strategy.py` - Multiple methods - 624 lines total class
3. `paper_trading/position_engine.py` - process_signal() - likely >100 lines
4. `utils/feature_engineering.py` - Various methods - likely >100 lines
5. Archive functions (can be skipped for now)

**Implementation Steps:**
```python
# For each long function:
1. Identify logical blocks
2. Extract into private methods with descriptive names
3. Add guard clauses to reduce nesting
4. Ensure no function exceeds 50 lines
5. Add docstrings to extracted methods
6. Run tests to verify behavior unchanged
```

**Example Refactoring:**
```python
# Before (100+ lines)
def process_signal(self, symbol, target_weight, confidence, price):
    # 100+ lines of logic
    pass

# After (<50 lines)
def process_signal(self, symbol, target_weight, confidence, price):
    if not self._is_valid_signal(symbol, confidence):
        return {'action': 'HOLD'}
    
    current_position = self._get_current_position(symbol)
    target_position = self._calculate_target_position(target_weight, price)
    
    action = self._determine_action(current_position, target_position)
    return self._execute_action(action, symbol, price)

def _is_valid_signal(self, symbol, confidence):
    # 5-10 lines
    pass

def _get_current_position(self, symbol):
    # 5-10 lines
    pass
# ... etc
```

**Estimated Impact:**
- Functions refactored: 20
- Lines reduced: ~1,000
- New private methods: ~60
- Test updates: Minimal (behavior unchanged)

---

### Task 12: Magic Numbers Replacement

**Objective:** Replace all magic numbers with named constants

**Implementation Steps:**

1. **Expand utils/constants.py:**
```python
# Portfolio Constants
MAX_POSITIONS = 5
MAX_EXPOSURE_RATIO = 0.80
MIN_POSITION_SIZE = 0.05
MAX_POSITION_SIZE = 0.25

# Confidence Thresholds
CONFIDENCE_THRESHOLD_HIGH = 0.70
CONFIDENCE_THRESHOLD_MEDIUM = 0.55
CONFIDENCE_THRESHOLD_LOW = 0.40

# Risk Management
MAX_DAILY_LOSS_PCT = 0.05
MAX_DRAWDOWN_PCT = 0.30
CIRCUIT_BREAKER_THRESHOLD = 0.25
STOP_LOSS_MULTIPLIER = 2.0
TAKE_PROFIT_MULTIPLIER = 3.0

# Health Monitoring
MIN_WIN_RATE = 0.45
MIN_PROFIT_FACTOR = 1.2
MIN_SHARPE_RATIO = 0.5
MAX_CONSECUTIVE_LOSSES = 5

# Data Quality
MAX_CACHE_AGE_HOURS = 24
MIN_DATA_POINTS = 100
MAX_MISSING_DATA_PCT = 0.10

# Time Constants
MIN_HOLDING_DAYS = 3
MAX_HOLDING_DAYS = 60
REBALANCE_FREQUENCY_DAYS = 7
```

2. **Search and Replace:**
```bash
# Find all numeric literals
grep -r "\b[0-9]\+\.[0-9]\+\b" --include="*.py" core/ paper_trading/ utils/

# Replace with constants
# Example: 0.002 -> COMMISSION_RATE
# Example: 100000 -> DEFAULT_INITIAL_CAPITAL
```

3. **Update Imports:**
```python
from utils.constants import (
    MAX_POSITIONS,
    CONFIDENCE_THRESHOLD_HIGH,
    MAX_DAILY_LOSS_PCT,
    # ... etc
)
```

**Estimated Impact:**
- Magic numbers replaced: ~150
- Constants added: ~50
- Files updated: ~30

---

### Task 13: Parameter Objects Introduction

**Objective:** Replace long parameter lists with parameter objects

**Implementation Steps:**

1. **Create Parameter Dataclasses:**
```python
# config/parameter_objects.py
from dataclasses import dataclass
from typing import Optional

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

@dataclass
class RiskConfig:
    """Configuration for risk management."""
    stop_loss_multiplier: float = 2.0
    take_profit_multiplier: float = 3.0
    max_position_size: float = 0.25
    max_portfolio_exposure: float = 0.80
    circuit_breaker_threshold: float = 0.25
    max_daily_loss_pct: float = 0.05
```

2. **Refactor Functions:**
```python
# Before
def train_model(train_start, train_end, learning_rate, max_depth, 
                num_leaves, min_data_in_leaf, feature_fraction):
    pass

# After
def train_model(config: TrainingConfig):
    pass

# Usage
config = TrainingConfig(
    train_start="2020-01-01",
    train_end="2023-12-31",
    learning_rate=0.01
)
train_model(config)
```

**Functions to Refactor (5+ parameters):**
- `run_dynamic_backtest()` - 6 parameters
- `batch_download_data()` - 4 parameters (borderline)
- Various model training functions
- Backtest execution functions

**Estimated Impact:**
- Parameter objects created: 5-8
- Functions refactored: 15-20
- Code clarity: Significantly improved

---

### Task 14: Dead Code Removal

**Objective:** Remove unused private functions and imports

**Implementation Steps:**

1. **Identify Unused Code:**
```bash
# Use vulture or similar tool
pip install vulture
vulture core/ paper_trading/ utils/ --min-confidence 80

# Manual verification
# Check each identified function for actual usage
```

2. **Remove Carefully:**
```python
# Categories to check:
# - Unused private methods (_method_name)
# - Unused imports
# - Commented-out code
# - Deprecated functions with TODO comments
# - Test helper functions no longer used
```

3. **Verify with Tests:**
```bash
# After each removal
pytest tests/ -v
# Ensure no tests break
```

**Estimated Removals:**
- Unused functions: ~50
- Unused imports: ~100
- Commented code: ~200 lines
- Total lines removed: ~500

---

### Task 15: Phase 3 Checkpoint

**Verification Steps:**
1. Run full test suite: `pytest tests/ -v`
2. Run quality analysis: `python scripts/quality/run_quality_analysis.py`
3. Verify metrics:
   - Code Smells score > 70.0/100
   - Total code smells < 300
4. Document Phase 3 completion

---

### Task 16: DRY Violations Correction

**Implementation Steps:**

1. **Remove Duplicate config.py:**
```bash
# Verify symlink exists
ls -la config.py
# Should point to config/config.py

# If not, create symlink
ln -s config/config.py config.py
```

2. **Create Shared Test Fixtures:**
```python
# tests/fixtures/portfolio_fixtures.py
import pytest
from paper_trading.portfolio_state import PortfolioState

@pytest.fixture
def empty_portfolio():
    return PortfolioState()

@pytest.fixture
def portfolio_with_positions():
    portfolio = PortfolioState()
    portfolio.open_position('THYAO', 100, 50.0, 0.7)
    portfolio.open_position('GARAN', 200, 45.0, 0.6)
    return portfolio

# tests/fixtures/health_fixtures.py
@pytest.fixture
def healthy_portfolio_stats():
    return {
        'win_rate': 60.0,
        'profit_factor': 2.5,
        'sharpe_ratio': 1.2,
        'total_trades': 50
    }

# tests/fixtures/data_fixtures.py
@pytest.fixture
def sample_ohlcv_data():
    dates = pd.date_range('2023-01-01', periods=100)
    return pd.DataFrame({
        'Open': np.random.uniform(90, 110, 100),
        'High': np.random.uniform(95, 115, 100),
        'Low': np.random.uniform(85, 105, 100),
        'Close': np.random.uniform(90, 110, 100),
        'Volume': np.random.uniform(1e6, 5e6, 100)
    }, index=dates)
```

3. **Refactor Tests:**
```python
# Before (duplicated in every test file)
def test_something():
    portfolio = PortfolioState()
    portfolio.cash = 100000
    # ... setup code ...

# After (using shared fixture)
def test_something(empty_portfolio):
    # ... test code ...
```

**Estimated Impact:**
- Shared fixtures: 15-20
- Test files updated: 30+
- Duplicate code removed: ~1,000 lines

---

### Task 17: Phase 4 Checkpoint

**Verification Steps:**
1. Run full test suite
2. Run quality analysis
3. Verify DRY score > 95.0/100
4. Document Phase 4 completion

---

### Task 18: Final Integration and Validation

**Steps:**

1. **Comprehensive Test Suite (18.1):**
```bash
pytest tests/ -v --cov=. --cov-report=html
# Verify 100% pass rate
# Check coverage report
```

2. **Paper Trading Validation (18.2):**
```bash
python paper_trading/position_runner.py --quiet
# Verify no errors
# Compare behavior to baseline
```

3. **Backtest Validation (18.3):**
```bash
python main.py --mode single --model ensemble
# Compare results to baseline
# Verify identical trades, PnL, metrics
```

4. **Final Quality Analysis (18.4):**
```bash
python scripts/quality/run_quality_analysis.py
# Verify overall score >= 80.0/100
# Verify all sub-scores meet targets
```

5. **Performance Benchmarking (18.5):**
```python
import time

# Benchmark critical paths
start = time.time()
portfolio = PortfolioState.load()
load_time = time.time() - start

start = time.time()
# Run backtest
backtest_time = time.time() - start

# Compare to baseline
# Verify no degradation
```

6. **Update Documentation (18.6):**
- Update architecture.md with new structure
- Document design patterns used
- Add usage examples for new classes
- Update API documentation

---

### Task 19: Merge and Deployment

**Steps:**

1. **Prepare Merge (19.1):**
```bash
# Review all changes
git log --oneline

# Squash if needed
git rebase -i HEAD~50

# Write comprehensive commit message
git commit --amend
```

2. **Merge to Master (19.2):**
```bash
# Create pull request
gh pr create --title "Code Quality Refactoring - Phases 1-4" \
             --body "See docs/FINAL_REFACTORING_REPORT.md"

# Review and merge
gh pr merge --squash
```

3. **Post-Merge Validation (19.3):**
```bash
git checkout master
git pull
pytest tests/ -v
python paper_trading/position_runner.py --quiet
```

4. **Final Documentation (19.4):**
- Update CHANGELOG.md
- Update REFACTORING_GUIDE.md
- Document lessons learned

---

## Summary

**Completed:** Tasks 1-10 (Phases 1-2)  
**Remaining:** Tasks 11-19 (Phases 3-4)

**Estimated Effort for Remaining Tasks:**
- Task 11: 8-10 hours
- Task 12: 4-6 hours
- Task 13: 4-6 hours
- Task 14: 2-3 hours
- Task 15: 1 hour
- Task 16: 3-4 hours
- Task 17: 1 hour
- Task 18: 4-5 hours
- Task 19: 2-3 hours

**Total Remaining:** ~30-40 hours

**Current Status:**
- Tests Passing: 801/801 (100%)
- Quality Score: 29.7/100
- Target Score: 80.0/100
- Progress: ~40% complete

---

**Next Session:** Start with Task 11.1 (Long Functions Refactoring)
