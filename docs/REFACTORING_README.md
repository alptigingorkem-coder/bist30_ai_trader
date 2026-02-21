# 🔧 Refactoring Documentation

Bu klasör BIST30 AI Trader projesinin kod kalitesi iyileştirme sürecini dokümante eder.

---

## 📚 Dokümantasyon

### 1. [CODE_QUALITY_REPORT.md](../CODE_QUALITY_REPORT.md)
**Mevcut durum analizi**

- Genel skor: 27.0/100 (F)
- DRY: 90.0/100 ✅
- SRP: 0.0/100 ⚠️
- Complexity: 0.0/100 ⚠️
- Code Smells: 0.0/100 ⚠️

**Tespit edilen sorunlar:**
- 92 SRP ihlali (God classes)
- 67 karmaşık fonksiyon (CC > 10)
- 1209 code smell (66 kritik)
- 6 duplicate kod grubu

### 2. [REFACTORING_PLAN.md](../REFACTORING_PLAN.md)
**Kapsamlı refactoring stratejisi**

**4 Fazlı Plan:**
- **Faz 1:** God Class'ları Refactor Et (15-20h) → SRP 0→40
- **Faz 2:** Karmaşık Fonksiyonları Basitleştir (12-15h) → Complexity 0→60
- **Faz 3:** Code Smell'leri Temizle (8-10h) → Smells 0→70
- **Faz 4:** DRY İhlallerini Düzelt (3-4h) → DRY 90→95

**Hedef:** 80.0/100 (B - İyi)  
**Süre:** 40-60 saat (5-8 iş günü)

### 3. [REFACTORING_GUIDE.md](../REFACTORING_GUIDE.md)
**Adım adım implementation rehberi**

- Test-driven refactoring workflow
- Kod örnekleri ve şablonlar
- Troubleshooting guide
- Daily checklist
- Completion criteria

---

## 🎯 Hızlı Başlangıç

### 1. Mevcut Durumu Analiz Et

```bash
# Kalite analizi çalıştır
python scripts/quality/run_quality_analysis.py

# Raporu oku
cat CODE_QUALITY_REPORT.md
```

### 2. Refactoring Planını İncele

```bash
# Ana planı oku
cat REFACTORING_PLAN.md

# Implementation guide'ı oku
cat REFACTORING_GUIDE.md
```

### 3. Refactoring'e Başla

```bash
# Yeni branch oluştur
git checkout -b refactoring/phase-1-god-classes

# İlk adımı uygula (PortfolioState)
# REFACTORING_GUIDE.md'deki adımları takip et

# Test et
pytest tests/ -v

# Kalite kontrolü
python scripts/quality/run_quality_analysis.py

# Commit
git add .
git commit -m "refactor: PortfolioState - Repository pattern uygulandı"
```

---

## 📊 İlerleme Takibi

### Kalite Skorları

| Tarih | Overall | DRY | SRP | Complexity | Smells | Notlar |
|-------|---------|-----|-----|------------|--------|--------|
| 2026-02-22 | 27.0 | 90.0 | 0.0 | 0.0 | 0.0 | Baseline |
| ... | ... | ... | ... | ... | ... | ... |

### Milestone'lar

- [ ] **Faz 1 Tamamlandı** - SRP > 40 (Hedef: 1 hafta)
- [ ] **Faz 2 Tamamlandı** - Complexity > 60 (Hedef: 1.5 hafta)
- [ ] **Faz 3 Tamamlandı** - Smells > 70 (Hedef: 2 hafta)
- [ ] **Faz 4 Tamamlandı** - DRY > 95 (Hedef: 2 hafta)
- [ ] **Final Hedef** - Overall > 80 (Hedef: 2 hafta)

---

## 🔍 Analiz Araçları

### Kalite Analizi

```bash
# Tüm analizler
python scripts/quality/run_quality_analysis.py

# Bireysel analizler
python scripts/quality/check_dry_violations.py
python scripts/quality/check_srp_violations.py
python scripts/quality/check_complexity.py
python scripts/quality/check_code_smells.py
```

### Test Coverage

```bash
# Coverage raporu
pytest tests/ --cov=. --cov-report=html

# HTML raporu aç
open htmlcov/index.html
```

### Complexity Analizi

```bash
# Radon ile complexity
radon cc . -a -nb

# McCabe complexity
flake8 . --max-complexity=10
```

---

## 🎯 Öncelikli Refactoring Hedefleri

### 1. God Classes (KRİTİK)

**PortfolioState** (686 satır, 38 method)
```
Hedef: 6 ayrı sınıfa böl
- PortfolioState (core state)
- PortfolioRepository (persistence)
- PortfolioService (business logic)
- PortfolioValidator (validation)
- PortfolioFormatter (presentation)
- PortfolioMetrics (analytics)
```

**StrategyHealth** (625 satır, 30 method)
```
Hedef: 5 ayrı sınıfa böl
- StrategyHealth (coordinator)
- HealthMetrics (calculations)
- HealthAnalyzer (analysis)
- HealthReporter (reporting)
- HealthValidator (validation)
```

**DataLoader** (460 satır, 10 method)
```
Hedef: 5 ayrı sınıfa böl
- DataLoader (facade)
- DataRepository (fetching)
- DataCache (caching)
- DataValidator (validation)
- DataTransformer (transformation)
```

### 2. Karmaşık Fonksiyonlar (YÜKSEK)

**main()** in run_backtest.py (CC: 85, 620 satır)
```
Hedef: Command pattern + Extract method
- BacktestCommand class
- 5-6 küçük method
- Her method < 50 satır
```

**run_backtest()** in engine.py (CC: 65, 417 satır)
```
Hedef: Strategy pattern + Guard clauses
- BacktestStrategy class
- Nested if'leri düzleştir
- Extract method
```

### 3. Code Smells (YÜKSEK)

- 66 Long Function → Extract method
- Magic numbers → Named constants
- Long parameter lists → Parameter objects
- Dead code → Remove

---

## 📖 Refactoring Patterns

### Repository Pattern
```python
class Repository:
    def load(self) -> Data
    def save(self, data: Data) -> bool
    def delete(self, id: str) -> bool
```

### Service Layer Pattern
```python
class Service:
    def __init__(self, repository: Repository):
        self.repository = repository
    
    def execute_business_logic(self, params):
        # Business logic here
        pass
```

### Strategy Pattern
```python
class Strategy(ABC):
    @abstractmethod
    def execute(self, data):
        pass

class ConcreteStrategy(Strategy):
    def execute(self, data):
        # Implementation
        pass
```

### Command Pattern
```python
class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class ConcreteCommand(Command):
    def execute(self):
        # Implementation
        pass
```

---

## 🚨 Önemli Notlar

### ⚠️ Dikkat Edilmesi Gerekenler

1. **Paper Trading Kesintisi Olmamalı**
   - `master` branch stabil kalmalı
   - Refactoring `changes` branch'inde yapılmalı
   - Merge öncesi kapsamlı test

2. **Backward Compatibility**
   - Eski API'yi hemen kaldırma
   - Deprecation warnings ekle
   - Gradual migration

3. **Test Coverage**
   - Her refactoring için test yaz
   - Coverage > 80% hedefle
   - Integration testleri unutma

4. **Performance**
   - Refactor sonrası performans düşmemeli
   - Critical path'leri benchmark'la
   - Profiling yap

### ✅ Best Practices

1. **Small Steps**
   - Küçük, incremental değişiklikler
   - Her adımda test et
   - Sık commit

2. **Test-Driven**
   - Önce test yaz
   - Sonra refactor et
   - Test geçene kadar devam et

3. **Documentation**
   - Değişiklikleri dokümante et
   - Docstring'leri güncelle
   - README'leri güncelle

4. **Code Review**
   - Her major refactoring için review
   - Pair programming düşün
   - Feedback al

---

## 📞 Yardım ve Destek

### Sorun mu yaşıyorsun?

1. **REFACTORING_GUIDE.md** → Troubleshooting bölümüne bak
2. **Test başarısız** → `pytest tests/ -v --tb=short`
3. **Import error** → `__init__.py` dosyalarını kontrol et
4. **Performance düştü** → Profiling yap

### Useful Commands

```bash
# Kalite analizi
python scripts/quality/run_quality_analysis.py

# Testler
pytest tests/ -v

# Coverage
pytest tests/ --cov=. --cov-report=html

# Specific test
pytest tests/test_file.py::test_function -v

# Debug mode
pytest tests/test_file.py -v -s

# Stop on first failure
pytest tests/ -x
```

---

## 🎉 Başarı Kriterleri

Refactoring başarılı sayılır:

- ✅ Overall Score > 80.0/100
- ✅ SRP Score > 80.0/100
- ✅ Complexity Score > 75.0/100
- ✅ Code Smells Score > 85.0/100
- ✅ Tüm testler geçiyor (334/334)
- ✅ Paper trading çalışıyor
- ✅ Backtest sonuçları değişmedi
- ✅ Performance düşmedi
- ✅ Documentation güncellendi

---

**Son Güncelleme:** 2026-02-22  
**Durum:** 📋 Plan Hazır - Uygulama Bekliyor  
**Hedef Tamamlanma:** 2 hafta
