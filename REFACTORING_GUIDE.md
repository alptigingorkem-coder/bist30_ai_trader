# 🛠️ Refactoring Implementation Guide

Bu dokümant refactoring planının adım adım uygulanması için pratik bir rehberdir.

---

## 📋 Başlamadan Önce Checklist

- [ ] `changes` branch'inde çalışıyorsun
- [ ] Tüm testler geçiyor (334/334)
- [ ] Paper trading çalışıyor
- [ ] Backup alındı
- [ ] Kalite analizi baseline'ı kaydedildi

```bash
# Baseline kaydet
python scripts/quality/run_quality_analysis.py > quality_baseline.txt
git add quality_baseline.txt
git commit -m "chore: Refactoring öncesi kalite baseline'ı"
```

---

## 🎯 Faz 1.1: PortfolioState Refactoring

### Adım 1: Yeni Klasör Yapısını Oluştur

```bash
mkdir -p paper_trading/portfolio
touch paper_trading/portfolio/__init__.py
touch paper_trading/portfolio/portfolio_state.py
touch paper_trading/portfolio/portfolio_repository.py
touch paper_trading/portfolio/portfolio_service.py
touch paper_trading/portfolio/portfolio_validator.py
touch paper_trading/portfolio/portfolio_formatter.py
touch paper_trading/portfolio/portfolio_metrics.py
```

### Adım 2: PortfolioRepository Oluştur

**Dosya:** `paper_trading/portfolio/portfolio_repository.py`

```python
"""
Portfolio data persistence layer.
Handles loading and saving portfolio state.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class PortfolioRepository:
    """Handles portfolio state persistence."""
    
    def __init__(self, state_file: str = "logs/paper_trading/portfolio_state.json"):
        self.state_file = state_file
    
    def load(self) -> Optional[Dict]:
        """Load portfolio state from file."""
        if not os.path.exists(self.state_file):
            return None
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading state: {e}")
            return None
    
    def save(self, state: Dict) -> bool:
        """Save portfolio state to file."""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
    
    def export_to_csv(self, trades: List[Dict], filepath: str) -> bool:
        """Export trades to CSV."""
        import csv
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if not trades:
                return False
            
            fieldnames = list(trades[0].keys())
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(trades)
            
            return True
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False
```

**Test:** `tests/test_portfolio_repository.py`

```python
import pytest
from pathlib import Path
from paper_trading.portfolio.portfolio_repository import PortfolioRepository


def test_save_and_load(tmp_path):
    """Test saving and loading state."""
    state_file = tmp_path / "test_state.json"
    repo = PortfolioRepository(str(state_file))
    
    # Save
    test_state = {
        "cash": 100000,
        "positions": {},
        "realized_pnl": 0
    }
    assert repo.save(test_state) is True
    
    # Load
    loaded = repo.load()
    assert loaded == test_state


def test_load_nonexistent_file():
    """Test loading non-existent file."""
    repo = PortfolioRepository("nonexistent.json")
    assert repo.load() is None


def test_export_csv(tmp_path):
    """Test CSV export."""
    csv_file = tmp_path / "trades.csv"
    repo = PortfolioRepository()
    
    trades = [
        {"symbol": "ASELS", "pnl": 100},
        {"symbol": "THYAO", "pnl": 200}
    ]
    
    assert repo.export_to_csv(trades, str(csv_file)) is True
    assert csv_file.exists()
```

**Çalıştır:**
```bash
pytest tests/test_portfolio_repository.py -v
```

### Adım 3: PortfolioValidator Oluştur

**Dosya:** `paper_trading/portfolio/portfolio_validator.py`

```python
"""
Portfolio validation logic.
Checks risk limits and trading constraints.
"""

from typing import Tuple, Dict


class PortfolioValidator:
    """Validates portfolio operations against risk limits."""
    
    def __init__(
        self,
        max_positions: int = 10,
        max_single_exposure: float = 0.10,
        max_total_exposure: float = 0.80,
        daily_max_loss_pct: float = 0.03,
        consecutive_loss_limit: int = 3
    ):
        self.max_positions = max_positions
        self.max_single_exposure = max_single_exposure
        self.max_total_exposure = max_total_exposure
        self.daily_max_loss_pct = daily_max_loss_pct
        self.consecutive_loss_limit = consecutive_loss_limit
    
    def can_open_position(
        self,
        symbol: str,
        size_pct: float,
        current_positions: Dict,
        cash: float,
        total_exposure: float,
        total_value: float
    ) -> Tuple[bool, str]:
        """Check if a new position can be opened."""
        # Already has position?
        if symbol in current_positions:
            return False, "ALREADY_HAS_POSITION"
        
        # Max positions reached?
        if len(current_positions) >= self.max_positions:
            return False, "MAX_POSITIONS_REACHED"
        
        # Single exposure limit
        if size_pct > self.max_single_exposure:
            return False, "EXCEEDS_SINGLE_EXPOSURE"
        
        # Total exposure limit
        current_exposure_ratio = total_exposure / total_value if total_value > 0 else 0
        if current_exposure_ratio + size_pct > self.max_total_exposure:
            return False, "EXCEEDS_TOTAL_EXPOSURE"
        
        # Sufficient cash?
        required_cash = total_value * size_pct
        if required_cash > cash:
            return False, "INSUFFICIENT_CASH"
        
        return True, "OK"
    
    def check_stress_limits(
        self,
        daily_pnl: float,
        consecutive_losses: int,
        initial_capital: float
    ) -> Tuple[bool, str]:
        """Check if trading should be halted due to stress limits."""
        # Daily max loss check
        if daily_pnl < 0:
            daily_loss_pct = abs(daily_pnl) / initial_capital
            if daily_loss_pct >= self.daily_max_loss_pct:
                return False, f"DAILY_MAX_LOSS ({daily_loss_pct*100:.1f}%)"
        
        # Consecutive loss check
        if consecutive_losses >= self.consecutive_loss_limit:
            return False, f"CONSECUTIVE_LOSSES ({consecutive_losses})"
        
        return True, "OK"
```

**Test:** `tests/test_portfolio_validator.py`

```python
import pytest
from paper_trading.portfolio.portfolio_validator import PortfolioValidator


def test_can_open_position_success():
    """Test successful position opening validation."""
    validator = PortfolioValidator()
    
    can_open, reason = validator.can_open_position(
        symbol="ASELS",
        size_pct=0.05,
        current_positions={},
        cash=100000,
        total_exposure=0,
        total_value=100000
    )
    
    assert can_open is True
    assert reason == "OK"


def test_can_open_position_already_has():
    """Test validation when position already exists."""
    validator = PortfolioValidator()
    
    can_open, reason = validator.can_open_position(
        symbol="ASELS",
        size_pct=0.05,
        current_positions={"ASELS": {}},
        cash=100000,
        total_exposure=0,
        total_value=100000
    )
    
    assert can_open is False
    assert reason == "ALREADY_HAS_POSITION"


def test_check_stress_limits_daily_loss():
    """Test stress limits with daily loss."""
    validator = PortfolioValidator(daily_max_loss_pct=0.03)
    
    can_trade, reason = validator.check_stress_limits(
        daily_pnl=-3500,  # 3.5% loss
        consecutive_losses=0,
        initial_capital=100000
    )
    
    assert can_trade is False
    assert "DAILY_MAX_LOSS" in reason
```

### Adım 4: Mevcut Kodu Migrate Et

**Strateji:**
1. Yeni sınıfları oluştur
2. Testleri yaz ve geçir
3. Eski PortfolioState'i yeni sınıfları kullanacak şekilde güncelle
4. Backward compatibility sağla
5. Eski kodu deprecate et
6. Tüm referansları güncelle
7. Eski kodu sil

**Migration Script:** `scripts/refactoring/migrate_portfolio_state.py`

```python
"""
PortfolioState migration helper.
Gradually migrates old code to new structure.
"""

def migrate_step_1_repository():
    """Step 1: Migrate to repository pattern."""
    print("Step 1: Creating PortfolioRepository...")
    # Implementation
    pass

def migrate_step_2_validator():
    """Step 2: Migrate to validator pattern."""
    print("Step 2: Creating PortfolioValidator...")
    # Implementation
    pass

# ... more steps
```

---

## 🧪 Test-Driven Refactoring Workflow

### Her Refactoring İçin:

```bash
# 1. Test yaz (RED)
pytest tests/test_new_feature.py -v
# FAIL - test henüz geçmiyor

# 2. Minimum kod yaz (GREEN)
# Sadece testi geçirecek kadar kod

pytest tests/test_new_feature.py -v
# PASS - test geçti

# 3. Refactor (REFACTOR)
# Kodu temizle, optimize et

pytest tests/test_new_feature.py -v
# PASS - hala geçiyor

# 4. Integration test
pytest tests/ -v
# Tüm testler geçmeli

# 5. Kalite kontrolü
python scripts/quality/run_quality_analysis.py

# 6. Commit
git add .
git commit -m "refactor: [component] - [what changed]"
```

---

## 📊 İlerleme Takip Şablonu

**Dosya:** `refactoring_progress.md`

```markdown
# Refactoring Progress

## Faz 1: God Classes

### PortfolioState
- [x] Repository created (2h)
- [x] Validator created (1.5h)
- [ ] Service created (3h)
- [ ] Formatter created (2h)
- [ ] Metrics created (2h)
- [ ] Integration (2h)
- [ ] Tests passing (1h)

**Status:** 30% complete  
**Time spent:** 3.5h / 13.5h  
**Blockers:** None

### StrategyHealth
- [ ] Metrics created
- [ ] Analyzer created
- [ ] Reporter created
- [ ] Validator created
- [ ] Integration
- [ ] Tests passing

**Status:** 0% complete

## Quality Scores

| Date | Overall | DRY | SRP | Complexity | Smells |
|------|---------|-----|-----|------------|--------|
| 2026-02-22 | 27.0 | 90.0 | 0.0 | 0.0 | 0.0 |
| 2026-02-23 | 35.0 | 90.0 | 15.0 | 0.0 | 5.0 |
| ... | ... | ... | ... | ... | ... |
```

---

## 🚨 Troubleshooting

### Problem: Testler Başarısız Oluyor

**Çözüm:**
```bash
# 1. Hangi test başarısız?
pytest tests/ -v --tb=short

# 2. Sadece o testi çalıştır
pytest tests/test_specific.py::test_function -v

# 3. Debug mode
pytest tests/test_specific.py::test_function -v -s

# 4. Son working commit'e dön
git diff HEAD
git checkout -- problematic_file.py
```

### Problem: Import Errors

**Çözüm:**
```python
# __init__.py dosyalarını kontrol et
# Circular import var mı?

# Dependency graph çiz
pydeps paper_trading --max-bacon=2
```

### Problem: Performance Düştü

**Çözüm:**
```bash
# Profiling yap
python -m cProfile -o profile.stats scripts/analysis/run_backtest.py

# Sonuçları analiz et
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

---

## 📚 Useful Commands

```bash
# Kalite analizi
python scripts/quality/run_quality_analysis.py

# Sadece DRY
python scripts/quality/check_dry_violations.py

# Sadece SRP
python scripts/quality/check_srp_violations.py

# Sadece Complexity
python scripts/quality/check_complexity.py

# Sadece Code Smells
python scripts/quality/check_code_smells.py

# Tüm testler
pytest tests/ -v

# Coverage
pytest tests/ --cov=paper_trading --cov-report=html

# Specific test
pytest tests/test_portfolio.py -v -k "test_open_position"

# Failed tests only
pytest tests/ --lf

# Stop on first failure
pytest tests/ -x

# Parallel testing
pytest tests/ -n auto
```

---

## 🎯 Daily Checklist

Her gün sonunda:

- [ ] Tüm testler geçiyor
- [ ] Kalite analizi çalıştırıldı
- [ ] Skor kaydedildi
- [ ] Progress güncellendi
- [ ] Commit yapıldı
- [ ] Branch push edildi

```bash
# Daily routine
pytest tests/ -v
python scripts/quality/run_quality_analysis.py
git add .
git commit -m "refactor: Daily progress - [what you did]"
git push origin refactoring/phase-1-god-classes
```

---

## 🏁 Completion Criteria

Bir faz tamamlanmış sayılır:

- ✅ Tüm planlanan sınıflar oluşturuldu
- ✅ Tüm testler geçiyor (334/334)
- ✅ Code coverage > 80%
- ✅ Kalite skoru hedefi aşıldı
- ✅ Paper trading çalışıyor
- ✅ Backtest sonuçları değişmedi
- ✅ Documentation güncellendi
- ✅ Code review yapıldı

---

**Başarılar! 🚀**
