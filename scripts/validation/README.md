# Paper Trading Readiness Validation

Bu klasör, BIST30 AI Trader sisteminin paper trading'e hazır olup olmadığını değerlendiren validation script'lerini içerir.

## 📋 Validation Script'leri

### 1. `check_project_structure.py`
README'de belirtilen script yapılanmasını doğrular.

**Kontrol Edilen:**
- `scripts/analysis/` klasörü ve dosyaları
- `scripts/training/` klasörü ve dosyaları
- `scripts/ops/` klasörü ve dosyaları
- `scripts/maintenance/` klasörü ve dosyaları
- `scripts/validation/` klasörü ve dosyaları

### 2. `check_infrastructure.py`
Altyapı bileşenlerinin kurulu ve çalışır durumda olduğunu kontrol eder.

**Kontrol Edilen:**
- TimescaleDB bağlantısı
- FastAPI kurulumu
- Docker ve Docker Compose
- MLflow database
- Environment variables (.env)

### 3. `check_models.py`
Tüm ML modellerinin eğitilmiş ve güncel olduğunu doğrular.

**Kontrol Edilen:**
- LightGBM Ranker (ağırlık: 10/10)
- CatBoost Ranker (ağırlık: 8/10)
- TFT Model (ağırlık: 6/10)

**Yaş Kriterleri:**
- < 7 gün: ✅ Güncel (100%)
- 7-30 gün: 🟡 Eski (75%)
- > 30 gün: ⚠️ Çok eski (30%)

### 4. `check_paper_trading_script.py`
Paper trading script'inin mevcut ve çalışır durumda olduğunu test eder.

**Kontrol Edilen:**
- Script dosyası varlığı
- Kritik bileşenler (RiskManager, portfolio, PaperTrader)
- Opsiyonel bileşenler (regime detection, main function)
- Dry-run test (60 saniye timeout)

### 5. `check_walk_forward_results.py`
Walk-forward validation sonuçlarının kabul edilebilir olduğunu değerlendirir.

**Kriterler:**
- Sharpe Ratio > 1.5 ✅
- Sharpe Std Dev < 1.0 ✅
- Max Drawdown < -20% ⚠️
- Win Rate > 55% ✅

### 6. `check_config_params.py`
config.py'deki kritik parametrelerin güvenli aralıkta olduğunu kontrol eder.

**Kontrol Edilen:**
- `RISK_PER_TRADE`: 0.01-0.05 arası (önerilen: 0.03)
- `MAX_DRAWDOWN_LIMIT`: 0.10-0.20 arası (önerilen: 0.15)
- `USE_ADAPTIVE_REGIME`: True olmalı
- `ENABLE_MACRO_GATE`: True olmalı

## 🎯 Master Script: `paper_trading_readiness.py`

Tüm validation script'lerini çalıştırır ve final GO/NO-GO kararı verir.

### Kullanım

```bash
python3 scripts/validation/paper_trading_readiness.py
```

### Çıktı

Script şunları üretir:
1. Konsol çıktısı (detaylı sonuçlar)
2. `PAPER_TRADING_READINESS_REPORT.md` (markdown rapor)
3. Exit code (0 = GO, 1 = NO-GO/CONDITIONAL)

### Karar Kriterleri

| Skor | Karar | Açıklama |
|------|-------|----------|
| ≥ 90% | 🟢 GO | Paper trading'e hazır |
| 75-90% | 🟡 CONDITIONAL GO | Küçük düzeltmelerle başlayabilir |
| < 75% | 🔴 NO-GO | Kritik sorunlar var |

### Ağırlıklar

| Kategori | Ağırlık | Açıklama |
|----------|---------|----------|
| Proje Yapılanması | 5/10 | Temel yapı |
| Altyapı | 8/10 | Önemli |
| Model Eğitimleri | 10/10 | Kritik |
| Paper Trading Script | 10/10 | Kritik |
| Walk-Forward Sonuçları | 10/10 | Kritik |
| Config Parametreleri | 7/10 | Önemli |

## 📊 Son Durum (2026-02-19)

**Final Skor: 83.5%**
**Karar: 🟡 CONDITIONAL GO**

### Başarılı Kontroller ✅
- ✅ Proje Yapılanması (100%)
- ✅ Altyapı (83.3%)
- ✅ Model Eğitimleri (100%)
- ✅ Walk-Forward Sonuçları (75%)
- ✅ Config Parametreleri (100%)

### İyileştirme Gereken Alan 🟡
- 🟡 Paper Trading Script (56%)
  - Dry-run testi başarısız
  - Regime detection entegrasyonu eksik (opsiyonel)
  - Main function eksik (opsiyonel)

### Öneriler

1. **Paper Trading Script İyileştirmeleri:**
   - Regime detection entegrasyonu ekle
   - Main function ekle
   - Dry-run testini düzelt

2. **Walk-Forward Max Drawdown:**
   - Mevcut: -41.2%
   - Hedef: < -20%
   - Risk yönetimi parametrelerini gözden geçir

3. **Sonraki Adımlar:**
   - Script iyileştirmelerini yap
   - Validation'ı tekrar çalıştır
   - %90+ skor aldıktan sonra paper trading başlat

## 🚀 Paper Trading Başlatma

Validation başarılı olduktan sonra:

```bash
# 1. Git snapshot
git tag v1.0-paper-trading
git push origin master --tags

# 2. Paper trading başlat
python3 scripts/ops/paper_trading_runner.py

# 3. 2 hafta günlük takip
# - Günlük performance logları
# - Weekly rapor oluştur
# - Anomali tespiti

# 4. 2 hafta sonra değerlendirme
# - Sharpe >1.5 → Canlıya geç (küçük sermaye)
# - Sharpe 1.0-1.5 → 1 ay daha paper trading
# - Sharpe <1.0 → Model revizyonu
```

## 📝 Notlar

- Tüm script'ler Python 3.12+ gerektirir
- Virtual environment aktif olmalı
- TimescaleDB çalışıyor olmalı (opsiyonel)
- Model dosyaları `models/saved/` klasöründe olmalı
