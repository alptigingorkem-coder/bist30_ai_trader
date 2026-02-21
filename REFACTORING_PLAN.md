# 🔧 BIST30 AI Trader - Kapsamlı Refactoring Planı

**Tarih:** 2026-02-22  
**Mevcut Skor:** 27.0/100 (F)  
**Hedef Skor:** 80.0/100 (B - İyi)

---

## 📊 Mevcut Durum Özeti

| Metrik | Mevcut | Hedef | Öncelik |
|--------|--------|-------|---------|
| DRY | 90.0/100 ✅ | 95.0/100 | Düşük |
| SRP | 0.0/100 ⚠️ | 80.0/100 | **KRİTİK** |
| Complexity | 0.0/100 ⚠️ | 75.0/100 | **YÜKSEK** |
| Code Smells | 0.0/100 ⚠️ | 85.0/100 | **YÜKSEK** |

**Toplam İş Yükü Tahmini:** 40-60 saat (5-8 iş günü)

---

## 🎯 Faz 1: Kritik God Class'ları Refactor Et (Öncelik: KRİTİK)

**Süre:** 15-20 saat  
**Etki:** SRP skorunu 0 → 40'a çıkarır

### 1.1 PortfolioState Refactoring (686 satır, 38 method)

**Sorun:** 7 farklı sorumluluk taşıyor (Data Access, Business Logic, Presentation, Logging, Error Handling, Communication, File Operations)

**Çözüm:** Repository + Service + Formatter pattern

```
paper_trading/
├── portfolio/
│   ├── __init__.py
│   ├── portfolio_state.py          # Sadece state management (100-150 satır)
│   ├── portfolio_repository.py     # Data persistence (load/save) (80-100 satır)
│   ├── portfolio_service.py        # Business logic (trade operations) (150-200 satır)
│   ├── portfolio_validator.py      # Validation logic (80-100 satır)
│   ├── portfolio_formatter.py      # Presentation/reporting (100-120 satır)
│   └── portfolio_metrics.py        # Trade statistics & analysis (120-150 satır)
```

**Adımlar:**

1. **PortfolioRepository oluştur** (Data Access)
   - `_load_state()` → `load()`
   - `_save_state()` → `save()`
   - JSON serialization/deserialization

2. **PortfolioService oluştur** (Business Logic)
   - `apply_trade_decision()`
   - `_open_position()`, `_close_position()`
   - `_scale_in()`, `_scale_out()`
   - Trade execution logic

3. **PortfolioValidator oluştur** (Validation)
   - `can_open_new_position()`
   - `check_stress_limits()`
   - Risk validation logic

4. **PortfolioFormatter oluştur** (Presentation)
   - `get_trade_ledger()`
   - `export_trade_ledger_csv()`
   - `get_trade_statistics()`
   - `print_confidence_analysis()`
   - `print_stress_status()`

5. **PortfolioMetrics oluştur** (Analytics)
   - `get_confidence_bucket_analysis()`
   - `get_signal_accuracy_report()`
   - Statistical analysis methods

6. **PortfolioState'i basitleştir** (Core State)
   - Sadece state properties
   - Basit query methods
   - Dependency injection ile diğer sınıfları kullan

**Test Stratejisi:**
- Her yeni sınıf için unit test yaz
- Integration test'leri güncelle
- Mevcut testlerin geçtiğinden emin ol

---

### 1.2 StrategyHealth Refactoring (625 satır, 30 method)

**Sorun:** 7 farklı sorumluluk

**Çözüm:** Metrics + Analyzer + Reporter pattern

```
paper_trading/
├── health/
│   ├── __init__.py
│   ├── strategy_health.py          # Main coordinator (100-120 satır)
│   ├── health_metrics.py           # Metric calculations (150-180 satır)
│   ├── health_analyzer.py          # Analysis logic (120-150 satır)
│   ├── health_reporter.py          # Report generation (100-120 satır)
│   └── health_validator.py         # Health checks (80-100 satır)
```

**Adımlar:**

1. **HealthMetrics oluştur**
   - Win rate, profit factor, sharpe ratio calculations
   - Drawdown, volatility metrics
   - Pure calculation methods

2. **HealthAnalyzer oluştur**
   - Trend analysis
   - Pattern detection
   - Health score calculation

3. **HealthReporter oluştur**
   - Report formatting
   - Visualization data preparation
   - Export functionality

4. **HealthValidator oluştur**
   - Health threshold checks
   - Alert generation
   - Status validation

5. **StrategyHealth'i basitleştir**
   - Orchestrator role
   - Delegate to specialized classes

---

### 1.3 DataLoader Refactoring (460 satır, 10 method)

**Sorun:** 8 farklı sorumluluk

**Çözüm:** Repository + Cache + Validator pattern

```
utils/
├── data/
│   ├── __init__.py
│   ├── data_loader.py              # Main interface (80-100 satır)
│   ├── data_repository.py          # Data fetching (150-180 satır)
│   ├── data_cache.py               # Caching logic (80-100 satır)
│   ├── data_validator.py           # Data quality checks (80-100 satır)
│   └── data_transformer.py         # Data transformation (100-120 satır)
```

**Adımlar:**

1. **DataRepository oluştur**
   - Yahoo Finance fetching
   - İş Yatırım fallback
   - Raw data retrieval

2. **DataCache oluştur**
   - Cache management
   - Parquet file operations
   - Cache invalidation logic

3. **DataValidator oluştur**
   - Data quality checks
   - Gap detection
   - Validation rules

4. **DataTransformer oluştur**
   - Data cleaning
   - Feature engineering
   - Format conversion

5. **DataLoader'ı basitleştir**
   - Facade pattern
   - Coordinate other classes

---

## 🎯 Faz 2: Karmaşık Fonksiyonları Basitleştir (Öncelik: YÜKSEK)

**Süre:** 12-15 saat  
**Etki:** Complexity skorunu 0 → 60'a çıkarır

### 2.1 En Karmaşık 5 Fonksiyon

#### 2.1.1 `main()` in run_backtest.py (CC: 85, 620 satır)

**Sorun:** Çok uzun, çok karmaşık, her şeyi yapıyor

**Çözüm:** Extract method + Command pattern

```python
# Önce:
def main():
    # 620 satır kod...
    pass

# Sonra:
class BacktestCommand:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.data_loader = DataLoader()
        self.model_loader = ModelLoader()
        self.backtest_runner = BacktestRunner()
        self.report_generator = ReportGenerator()
    
    def execute(self):
        config = self._load_configuration()
        data = self._load_data(config)
        model = self._load_model(config)
        results = self._run_backtest(data, model, config)
        self._generate_report(results, config)
    
    def _load_configuration(self):
        # 30-40 satır
        pass
    
    def _load_data(self, config):
        # 40-50 satır
        pass
    
    def _load_model(self, config):
        # 30-40 satır
        pass
    
    def _run_backtest(self, data, model, config):
        # 50-60 satır
        pass
    
    def _generate_report(self, results, config):
        # 40-50 satır
        pass

def main():
    command = BacktestCommand()
    command.execute()
```

**Adımlar:**
1. Her major section'ı ayrı method'a çıkar
2. Her method'u test et
3. Command class'ı oluştur
4. main()'i basitleştir

---

#### 2.1.2 `run_backtest()` in engine.py (CC: 65, 417 satır)

**Sorun:** Çok fazla nested if, karmaşık logic

**Çözüm:** Strategy pattern + Guard clauses

```python
# Önce:
def run_backtest(self, data, signals, ...):
    # 417 satır nested if/else
    pass

# Sonra:
class BacktestStrategy:
    def __init__(self):
        self.position_manager = PositionManager()
        self.risk_manager = RiskManager()
        self.trade_executor = TradeExecutor()
    
    def run(self, data, signals):
        results = []
        for date, signal in signals.items():
            # Guard clauses
            if not self._is_valid_signal(signal):
                continue
            
            if not self._can_trade(date):
                continue
            
            trade = self._execute_trade(signal, date)
            if trade:
                results.append(trade)
        
        return self._aggregate_results(results)
    
    def _is_valid_signal(self, signal):
        # 10-15 satır
        pass
    
    def _can_trade(self, date):
        # 10-15 satır
        pass
    
    def _execute_trade(self, signal, date):
        # 30-40 satır
        pass
    
    def _aggregate_results(self, results):
        # 20-30 satır
        pass
```

**Adımlar:**
1. Guard clauses ekle (early returns)
2. Nested if'leri düzleştir
3. Her major logic'i ayrı method'a çıkar
4. Strategy pattern uygula

---

#### 2.1.3 `run_position_aware_session()` (CC: 36, 304 satır)

**Sorun:** Çok uzun, çok fazla sorumluluk

**Çözüm:** Extract method + Session class

```python
class PositionAwareSession:
    def __init__(self, portfolio, engine, model):
        self.portfolio = portfolio
        self.engine = engine
        self.model = model
        self.signal_generator = SignalGenerator(model)
        self.trade_executor = TradeExecutor(portfolio, engine)
        self.reporter = SessionReporter()
    
    def run(self):
        self._initialize_session()
        signals = self._generate_signals()
        trades = self._execute_trades(signals)
        self._finalize_session(trades)
    
    def _initialize_session(self):
        # 20-30 satır
        pass
    
    def _generate_signals(self):
        # 40-50 satır
        pass
    
    def _execute_trades(self, signals):
        # 50-60 satır
        pass
    
    def _finalize_session(self, trades):
        # 30-40 satır
        pass
```

---

### 2.2 Complexity Azaltma Teknikleri

**Tüm karmaşık fonksiyonlar için:**

1. **Guard Clauses** (Early Returns)
   ```python
   # Önce:
   if condition1:
       if condition2:
           if condition3:
               # actual logic
   
   # Sonra:
   if not condition1:
       return
   if not condition2:
       return
   if not condition3:
       return
   # actual logic
   ```

2. **Extract Method**
   - Her 20-30 satırlık logic bloğu → ayrı method
   - Descriptive method names

3. **Replace Nested Conditionals with Polymorphism**
   - Strategy pattern
   - State pattern

4. **Parameter Object Pattern**
   - 5+ parametre → config object

---

## 🎯 Faz 3: Code Smell'leri Temizle (Öncelik: YÜKSEK)

**Süre:** 8-10 saat  
**Etki:** Code Smells skorunu 0 → 70'e çıkarır

### 3.1 Long Functions (66 adet)

**Hedef:** Tüm fonksiyonları <50 satıra indir

**Yaklaşım:**
- Extract method pattern
- Her fonksiyon için max 3-4 sub-method
- Single responsibility per method

**Öncelikli Fonksiyonlar:**
1. `main()` in run_backtest.py (620 satır) → 50 satır
2. `run_backtest()` in engine.py (417 satır) → 80 satır
3. `run_position_aware_session()` (304 satır) → 60 satır
4. `comprehensive_walk_forward()` (291 satır) → 70 satır
5. `run_dynamic_backtest()` (280 satır) → 70 satır

---

### 3.2 Magic Numbers (Düşük öncelik ama kolay)

**Hedef:** Tüm magic number'ları named constant'a çevir

```python
# Önce:
if value > 0.85:
    pass

# Sonra:
CONFIDENCE_THRESHOLD = 0.85

if value > CONFIDENCE_THRESHOLD:
    pass
```

**Yaklaşım:**
- Her modül için constants.py oluştur
- Config dosyalarına taşı
- Centralized configuration

---

### 3.3 Long Parameter Lists (Orta öncelik)

**Hedef:** 5+ parametreli fonksiyonları düzelt

```python
# Önce:
def train_model(data, target, epochs, batch_size, learning_rate, optimizer, loss_fn):
    pass

# Sonra:
@dataclass
class TrainingConfig:
    epochs: int
    batch_size: int
    learning_rate: float
    optimizer: str
    loss_fn: str

def train_model(data, target, config: TrainingConfig):
    pass
```

---

### 3.4 Dead Code (Düşük öncelik)

**Hedef:** Kullanılmayan private fonksiyonları sil

**Yaklaşım:**
1. Code smell detector'ın listesini kullan
2. Her fonksiyonu kontrol et
3. Gerçekten kullanılmıyorsa sil
4. Git history'de kalır

---

## 🎯 Faz 4: DRY İhlallerini Düzelt (Öncelik: DÜŞÜK)

**Süre:** 3-4 saat  
**Etki:** DRY skorunu 90 → 95'e çıkarır

### 4.1 Config.py Duplicate'leri

**Sorun:** config.py ve config/config.py aynı kod

**Çözüm:** Symlink zaten var, config.py'yi sil

```bash
rm config.py
# config/config.py kullan
```

---

### 4.2 Test Helper Duplicate'leri

**Sorun:** test_ranking_model_*.py dosyalarında duplicate setup

**Çözüm:** Shared test fixture

```python
# tests/fixtures/ranking_model_fixtures.py
@pytest.fixture
def ranking_model_setup():
    # Shared setup code
    pass

# tests/test_ranking_model_blacklist.py
def test_something(ranking_model_setup):
    # Use fixture
    pass
```

---

## 📅 Uygulama Takvimi

### Hafta 1: Kritik Refactoring

| Gün | Görev | Süre | Hedef |
|-----|-------|------|-------|
| 1 | PortfolioState → Repository + Service | 6h | SRP +15 |
| 2 | PortfolioState → Formatter + Metrics | 6h | SRP +10 |
| 3 | StrategyHealth → Metrics + Analyzer | 6h | SRP +10 |
| 4 | DataLoader → Repository + Cache | 6h | SRP +10 |
| 5 | Test & Integration | 6h | Stability |

**Hafta 1 Hedef Skor:** 50.0/100 (D)

---

### Hafta 2: Complexity & Code Smells

| Gün | Görev | Süre | Hedef |
|-----|-------|------|-------|
| 1 | main() refactor | 6h | Complexity +20 |
| 2 | run_backtest() refactor | 6h | Complexity +15 |
| 3 | Top 10 long functions | 6h | Smells +30 |
| 4 | Magic numbers + Parameter objects | 4h | Smells +20 |
| 5 | Final testing & cleanup | 6h | Stability |

**Hafta 2 Hedef Skor:** 80.0/100 (B - İyi)

---

## 🧪 Test Stratejisi

### Her Refactoring İçin:

1. **Önce Test Yaz** (TDD)
   - Mevcut davranışı test et
   - Refactor sonrası aynı test geçmeli

2. **Incremental Refactoring**
   - Küçük adımlar
   - Her adımda test çalıştır
   - Commit frequently

3. **Integration Tests**
   - End-to-end testler
   - Paper trading simulation
   - Backtest validation

4. **Performance Tests**
   - Refactor sonrası performans düşmemeli
   - Benchmark critical paths

---

## 📊 İlerleme Takibi

### Günlük Kontrol:

```bash
# Her gün sonunda kalite analizi çalıştır
python scripts/quality/run_quality_analysis.py

# Skorları kaydet
echo "$(date): $(grep 'GENEL SKOR' CODE_QUALITY_REPORT.md)" >> quality_progress.log
```

### Milestone'lar:

- [ ] Faz 1 Tamamlandı: SRP > 40
- [ ] Faz 2 Tamamlandı: Complexity > 60
- [ ] Faz 3 Tamamlandı: Code Smells > 70
- [ ] Faz 4 Tamamlandı: DRY > 95
- [ ] **Final Hedef: Overall > 80**

---

## 🚨 Riskler ve Önlemler

### Risk 1: Breaking Changes

**Önlem:**
- Comprehensive test coverage
- Feature flags for new code
- Gradual rollout
- Keep old code until new code is stable

### Risk 2: Zaman Aşımı

**Önlem:**
- Prioritize critical issues
- Skip low-priority items if needed
- Focus on high-impact changes

### Risk 3: Paper Trading Kesintisi

**Önlem:**
- Refactor on `changes` branch
- Keep `master` stable
- Test thoroughly before merge
- Rollback plan ready

---

## 🎯 Başarı Kriterleri

### Minimum Kabul Kriterleri:

- ✅ Overall Score > 80.0/100
- ✅ SRP Score > 80.0/100
- ✅ Complexity Score > 75.0/100
- ✅ Code Smells Score > 85.0/100
- ✅ Tüm testler geçiyor (334/334)
- ✅ Paper trading çalışıyor
- ✅ Backtest sonuçları değişmedi

### Bonus Hedefler:

- 🎁 Overall Score > 85.0/100 (B+)
- 🎁 Zero critical code smells
- 🎁 Average CC < 8
- 🎁 No function > 100 lines

---

## 📚 Referanslar

### Design Patterns:
- Repository Pattern
- Service Layer Pattern
- Strategy Pattern
- Command Pattern
- Facade Pattern

### Refactoring Techniques:
- Extract Method
- Extract Class
- Replace Conditional with Polymorphism
- Introduce Parameter Object
- Replace Magic Number with Symbolic Constant

### Books:
- "Refactoring" by Martin Fowler
- "Clean Code" by Robert C. Martin
- "Design Patterns" by Gang of Four

---

## 🚀 Başlangıç Komutu

```bash
# 1. Yeni branch oluştur
git checkout -b refactoring/phase-1-god-classes

# 2. İlk refactoring'e başla
# PortfolioState'i böl

# 3. Her adımda test et
pytest tests/

# 4. Kalite kontrolü
python scripts/quality/run_quality_analysis.py

# 5. Commit
git add .
git commit -m "refactor: PortfolioState - Repository pattern uygulandı"
```

---

**Son Güncelleme:** 2026-02-22  
**Hazırlayan:** Kiro AI Assistant  
**Durum:** ✅ Plan Hazır - Uygulama Bekliyor
