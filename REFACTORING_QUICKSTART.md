# ⚡ Refactoring Quick Start Guide

**5 dakikada refactoring'e başla!**

---

## 🎯 Hedef

Kod kalitesini **27.0/100 (F)** → **80.0/100 (B)** çıkarmak

---

## 📋 Önkoşullar

```bash
# 1. Doğru branch'te misin?
git branch
# changes branch'inde olmalısın

# 2. Testler geçiyor mu?
pytest tests/ -v
# 334/334 geçmeli

# 3. Kalite baseline'ı kaydet
python scripts/quality/run_quality_analysis.py > quality_baseline.txt
git add quality_baseline.txt
git commit -m "chore: Refactoring baseline"
```

---

## 🚀 Başla!

### Seçenek 1: Hızlı Başlangıç (Önerilen)

```bash
# 1. Yeni branch
git checkout -b refactoring/portfolio-state

# 2. İlk refactoring: PortfolioState
mkdir -p paper_trading/portfolio
cd paper_trading/portfolio

# 3. Repository oluştur
cat > portfolio_repository.py << 'EOF'
"""Portfolio data persistence."""
import json
import os

class PortfolioRepository:
    def __init__(self, state_file: str):
        self.state_file = state_file
    
    def load(self):
        if not os.path.exists(self.state_file):
            return None
        with open(self.state_file, 'r') as f:
            return json.load(f)
    
    def save(self, state):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
        return True
EOF

# 4. Test yaz
cd ../../tests
cat > test_portfolio_repository.py << 'EOF'
import pytest
from paper_trading.portfolio.portfolio_repository import PortfolioRepository

def test_save_and_load(tmp_path):
    repo = PortfolioRepository(str(tmp_path / "test.json"))
    state = {"cash": 100000}
    assert repo.save(state) is True
    assert repo.load() == state
EOF

# 5. Test et
pytest tests/test_portfolio_repository.py -v

# 6. Commit
git add .
git commit -m "refactor: PortfolioRepository oluşturuldu"

# 7. Kalite kontrolü
python scripts/quality/run_quality_analysis.py
```

### Seçenek 2: Detaylı Rehber

```bash
# Detaylı adımlar için:
cat REFACTORING_GUIDE.md

# Veya spesifik bölüm:
grep -A 50 "Adım 1:" REFACTORING_GUIDE.md
```

---

## 📊 İlerleme Takibi

### Her Gün Sonunda

```bash
# 1. Testler
pytest tests/ -v

# 2. Kalite analizi
python scripts/quality/run_quality_analysis.py

# 3. Skoru kaydet
echo "$(date +%Y-%m-%d): $(grep 'GENEL SKOR' CODE_QUALITY_REPORT.md)" >> quality_progress.log

# 4. Commit
git add .
git commit -m "refactor: Daily progress - [ne yaptın]"
git push
```

### Skor Takibi

```bash
# İlerlemeyi gör
cat quality_progress.log

# Grafik (opsiyonel)
python scripts/quality/plot_progress.py quality_progress.log
```

---

## 🎯 İlk Hafta Hedefleri

| Gün | Görev | Hedef Skor |
|-----|-------|------------|
| 1 | PortfolioRepository + Validator | +10 |
| 2 | PortfolioService + Formatter | +15 |
| 3 | StrategyHealth refactor | +10 |
| 4 | DataLoader refactor | +10 |
| 5 | Test & Integration | +5 |

**Hafta Sonu Hedef:** 50.0/100 (D)

---

## 🔥 Hızlı Kazanımlar

### 1. Config.py Duplicate'ini Sil (5 dk)

```bash
# Symlink zaten var, duplicate'i sil
rm config.py
git add config.py
git commit -m "refactor: config.py duplicate silindi"

# Kalite analizi
python scripts/quality/run_quality_analysis.py
# DRY skoru: 90 → 95 ✅
```

### 2. Magic Number'ları Düzelt (30 dk)

```bash
# Constants dosyası oluştur
cat > utils/constants.py << 'EOF'
"""Project-wide constants."""

# Trading
MAX_POSITIONS = 10
MAX_SINGLE_EXPOSURE = 0.10
MAX_TOTAL_EXPOSURE = 0.80

# Risk
DAILY_MAX_LOSS_PCT = 0.03
CONSECUTIVE_LOSS_LIMIT = 3

# Thresholds
CONFIDENCE_THRESHOLD = 0.85
VOLATILITY_THRESHOLD = 0.25
EOF

# Kullan
# Önce: if confidence > 0.85:
# Sonra: if confidence > CONFIDENCE_THRESHOLD:

git add .
git commit -m "refactor: Magic numbers constants'a taşındı"
```

### 3. Long Parameter List Düzelt (20 dk)

```python
# Önce:
def train_model(data, target, epochs, batch_size, lr, optimizer):
    pass

# Sonra:
from dataclasses import dataclass

@dataclass
class TrainingConfig:
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    optimizer: str = "adam"

def train_model(data, target, config: TrainingConfig):
    pass
```

---

## 🧪 Test Workflow

### Red-Green-Refactor

```bash
# 1. RED - Test yaz (başarısız)
cat > tests/test_new_feature.py << 'EOF'
def test_new_feature():
    result = new_feature()
    assert result == expected
EOF

pytest tests/test_new_feature.py -v
# FAIL ❌

# 2. GREEN - Minimum kod yaz (geçer)
# new_feature() implement et

pytest tests/test_new_feature.py -v
# PASS ✅

# 3. REFACTOR - Temizle
# Kodu optimize et, temizle

pytest tests/test_new_feature.py -v
# PASS ✅

# 4. Commit
git add .
git commit -m "feat: new_feature eklendi"
```

---

## 🚨 Sorun Giderme

### Test Başarısız

```bash
# Detaylı hata
pytest tests/ -v --tb=short

# Sadece başarısız olanlar
pytest tests/ --lf

# İlk hatada dur
pytest tests/ -x

# Debug mode
pytest tests/test_file.py -v -s
```

### Import Error

```bash
# __init__.py var mı?
find . -name "__init__.py"

# Python path
python -c "import sys; print('\n'.join(sys.path))"

# Module test
python -c "from paper_trading.portfolio import PortfolioRepository"
```

### Kalite Skoru Düşmedi

```bash
# Hangi metrik düşük?
python scripts/quality/run_quality_analysis.py | grep "Score"

# Spesifik analiz
python scripts/quality/check_srp_violations.py
python scripts/quality/check_complexity.py
```

---

## 📚 Daha Fazla Bilgi

### Dokümantasyon

- **REFACTORING_PLAN.md** - Kapsamlı plan (40-60 saat)
- **REFACTORING_GUIDE.md** - Adım adım rehber
- **docs/REFACTORING_README.md** - Genel bakış

### Analiz Araçları

```bash
# Tüm analizler
python scripts/quality/run_quality_analysis.py

# Bireysel
python scripts/quality/check_dry_violations.py
python scripts/quality/check_srp_violations.py
python scripts/quality/check_complexity.py
python scripts/quality/check_code_smells.py
```

---

## ✅ Checklist

Refactoring'e başlamadan önce:

- [ ] `changes` branch'indesin
- [ ] Tüm testler geçiyor (334/334)
- [ ] Baseline kaydedildi
- [ ] REFACTORING_PLAN.md okundu
- [ ] İlk hedef belirlendi

Her commit öncesi:

- [ ] Testler geçiyor
- [ ] Kalite analizi yapıldı
- [ ] Skor kaydedildi
- [ ] Commit message açıklayıcı

Her gün sonunda:

- [ ] Progress güncellendi
- [ ] Branch push edildi
- [ ] Blocker'lar dokümante edildi

---

## 🎉 İlk Başarı

İlk refactoring'ini tamamladın mı?

```bash
# Kutla! 🎉
echo "🎉 İlk refactoring tamamlandı!" >> refactoring_wins.txt
git add refactoring_wins.txt
git commit -m "chore: İlk refactoring başarısı!"

# Skoru kontrol et
python scripts/quality/run_quality_analysis.py | grep "GENEL SKOR"
```

---

**Başarılar! Refactoring yolculuğunda bol şans! 🚀**

**Sorular?** → REFACTORING_GUIDE.md → Troubleshooting
