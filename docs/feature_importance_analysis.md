# LightGBM Feature Importance Analizi - Kullanım Kılavuzu

## İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Kurulum](#kurulum)
3. [Hızlı Başlangıç](#hızlı-başlangıç)
4. [Detaylı Kullanım](#detaylı-kullanım)
5. [Yapılandırma](#yapılandırma)
6. [Çıktılar](#çıktılar)
7. [Sonuçları Yorumlama](#sonuçları-yorumlama)
8. [İleri Seviye Kullanım](#ileri-seviye-kullanım)
9. [Sorun Giderme](#sorun-giderme)
10. [SSS](#sss)

## Genel Bakış

Feature Importance Analizi, LightGBM ranking modelinizin performansını artırmak için SHAP (SHapley Additive exPlanations) değerlerini kullanarak feature'ları analiz eder ve düşük katkılı özellikleri otomatik olarak filtreler.

### Amaç

- **Hedef**: NDCG@3 metriğini 0.6217'den 0.65'e yükseltmek
- **Yöntem**: SHAP tabanlı feature importance analizi + otomatik feature selection
- **Sonuç**: Daha hızlı, daha etkili ve daha yüksek performanslı model

### Temel Özellikler

- ✅ SHAP değerleri ile feature importance hesaplama
- ✅ Otomatik feature selection ve blacklist oluşturma
- ✅ Baseline vs Optimized model karşılaştırması
- ✅ Görselleştirmeler (bar charts, SHAP plots, karşılaştırma grafikleri)
- ✅ Detaylı Markdown raporları
- ✅ RankingModel'e otomatik entegrasyon
- ✅ Çoklu ticker desteği ve hata toleransı

## Kurulum

### Gereksinimler

```bash
# Python 3.8+
pip install shap>=0.41.0
pip install matplotlib>=3.5.0
pip install lightgbm>=3.3.0
pip install pandas>=1.3.0
pip install numpy>=1.21.0
```

### Dosya Yapısı

```
project/
├── scripts/analysis/
│   ├── feature_importance_analyzer.py    # Ana orchestrator
│   ├── shap_analyzer.py                  # SHAP hesaplama
│   ├── feature_selector.py               # Feature selection
│   ├── model_comparator.py               # Model karşılaştırma
│   ├── visualizer.py                     # Görselleştirme
│   ├── report_generator.py               # Rapor oluşturma
│   ├── feature_importance_config.py      # Yapılandırma
│   └── run_feature_importance.py         # CLI script
├── models/
│   ├── ranking_model.py                  # RankingModel (blacklist desteği ile)
│   └── saved/
│       └── feature_blacklist.json        # Oluşturulan blacklist
└── reports/feature_importance/           # Analiz çıktıları
    ├── top_features.png
    ├── model_comparison.png
    ├── analysis_report_*.md
    └── analysis_metadata_*.json
```

## Hızlı Başlangıç

### 1. Temel Kullanım

En basit kullanım, varsayılan ayarlarla:

```bash
python scripts/analysis/run_feature_importance.py
```

Bu komut:
- `config.py` modülünden yapılandırmayı yükler
- 1000 örnekle SHAP analizi yapar
- 0.001 eşik değeriyle feature filtreleme yapar
- Sonuçları `reports/feature_importance/` dizinine kaydeder

### 2. Hızlı Test (Az Veri)

Sistemi test etmek için:

```bash
python scripts/analysis/run_feature_importance.py \
    --tickers THYAO,AKBNK \
    --sample-size 500 \
    --start-date 2024-01-01
```

### 3. Sonuçları Kontrol Etme

Analiz tamamlandıktan sonra:

```bash
# Blacklist'i görüntüle
cat models/saved/feature_blacklist.json

# En son raporu aç
ls -lt reports/feature_importance/analysis_report_*.md | head -1

# Grafikleri görüntüle
open reports/feature_importance/top_features.png
open reports/feature_importance/model_comparison.png
```

## Detaylı Kullanım

### CLI Parametreleri

#### Yapılandırma

```bash
--config CONFIG
```
Yapılandırma modülü adı (varsayılan: `config`)

**Örnek:**
```bash
python scripts/analysis/run_feature_importance.py --config banking
```

#### Analiz Parametreleri

```bash
--threshold THRESHOLD
```
Feature importance eşiği (varsayılan: 0.001). Bu değerin altındaki feature'lar blacklist'e alınır.

**Önerilen değerler:**
- `0.0005`: Agresif filtreleme (daha fazla feature çıkar)
- `0.001`: Dengeli (varsayılan)
- `0.005`: Konservatif (daha az feature çıkar)

**Örnek:**
```bash
python scripts/analysis/run_feature_importance.py --threshold 0.005
```

```bash
--sample-size SIZE
```
SHAP hesaplaması için örnek boyutu (varsayılan: 1000)

**Öneriler:**
- `500`: Hızlı test için
- `1000-2000`: Normal kullanım
- `5000+`: Yüksek doğruluk için (daha yavaş)

**Örnek:**
```bash
python scripts/analysis/run_feature_importance.py --sample-size 2000
```

#### Tarih Aralığı

```bash
--start-date YYYY-MM-DD
--end-date YYYY-MM-DD
```

Analiz için tarih aralığını belirler.

**Örnek:**
```bash
python scripts/analysis/run_feature_importance.py \
    --start-date 2023-01-01 \
    --end-date 2023-12-31
```

#### Ticker Seçimi

```bash
--tickers TICKER1,TICKER2,...
```

Analiz edilecek ticker'ları belirler (virgülle ayrılmış).

**Örnek:**
```bash
python scripts/analysis/run_feature_importance.py \
    --tickers THYAO,AKBNK,EREGL,GARAN,ISCTR
```

#### Çıktı Ayarları

```bash
--output-dir DIR
```
Çıktı dizini (varsayılan: `reports/feature_importance`)

**Örnek:**
```bash
python scripts/analysis/run_feature_importance.py \
    --output-dir reports/my_analysis
```

```bash
--save-models
```
Baseline ve optimized modelleri kaydet (opsiyonel)

**Örnek:**
```bash
python scripts/analysis/run_feature_importance.py --save-models
```

#### Loglama

```bash
--log-level LEVEL
```
Log seviyesi: DEBUG, INFO, WARNING, ERROR (varsayılan: INFO)

**Örnek:**
```bash
python scripts/analysis/run_feature_importance.py --log-level DEBUG
```

```bash
--quiet
```
Sadece hataları göster

**Örnek:**
```bash
python scripts/analysis/run_feature_importance.py --quiet
```

### Örnek Senaryolar

#### Senaryo 1: Kapsamlı Analiz (Production)

```bash
python scripts/analysis/run_feature_importance.py \
    --sample-size 5000 \
    --threshold 0.0005 \
    --save-models \
    --output-dir reports/production_analysis
```

#### Senaryo 2: Belirli Dönem Analizi

```bash
python scripts/analysis/run_feature_importance.py \
    --start-date 2023-01-01 \
    --end-date 2023-06-30 \
    --output-dir reports/q1_q2_2023
```

#### Senaryo 3: Sektör Bazlı Analiz

```bash
# Banking sektörü
python scripts/analysis/run_feature_importance.py \
    --config banking \
    --tickers AKBNK,GARAN,ISCTR,YKBNK \
    --output-dir reports/banking_analysis

# Energy sektörü
python scripts/analysis/run_feature_importance.py \
    --config energy \
    --tickers TUPRS,PETKM,AYGAZ \
    --output-dir reports/energy_analysis
```

#### Senaryo 4: Debug ve Sorun Giderme

```bash
python scripts/analysis/run_feature_importance.py \
    --log-level DEBUG \
    --tickers THYAO \
    --sample-size 100 \
    --output-dir reports/debug
```

## Yapılandırma

### Programatik Kullanım

Python kodundan doğrudan kullanım:

```python
from scripts.analysis.feature_importance_analyzer import FeatureImportanceAnalyzer
from scripts.analysis.feature_importance_config import AnalysisConfig
import config

# Yapılandırma oluştur
analysis_config = AnalysisConfig(
    sample_size=2000,
    importance_threshold=0.001,
    start_date="2023-01-01",
    end_date="2023-12-31",
    tickers=["THYAO", "AKBNK", "EREGL"],
    output_dir="reports/my_analysis",
    save_models=True
)

# Analyzer oluştur ve çalıştır
analyzer = FeatureImportanceAnalyzer(
    config_module=config,
    analysis_config=analysis_config
)

# Analizi çalıştır
result = analyzer.run_analysis()

# Sonuçları kullan
print(f"Baseline NDCG@3: {result.baseline_ndcg3:.4f}")
print(f"Optimized NDCG@3: {result.optimized_ndcg3:.4f}")
print(f"Improvement: {result.improvement_pct:.2f}%")
print(f"Blacklisted features: {len(result.blacklist)}")
```

### Yapılandırma Parametreleri

| Parametre | Tip | Varsayılan | Açıklama |
|-----------|-----|------------|----------|
| `sample_size` | int | 1000 | SHAP hesaplaması için örnek boyutu |
| `importance_threshold` | float | 0.001 | Feature filtreleme eşiği |
| `start_date` | str | None | Analiz başlangıç tarihi (YYYY-MM-DD) |
| `end_date` | str | None | Analiz bitiş tarihi (YYYY-MM-DD) |
| `tickers` | List[str] | None | Analiz edilecek ticker'lar |
| `output_dir` | str | "reports/feature_importance" | Çıktı dizini |
| `save_models` | bool | False | Modelleri kaydet |

## Çıktılar

### 1. Feature Blacklist

**Konum:** `models/saved/feature_blacklist.json`

**Format:** JSON array

**Örnek:**
```json
[
  "feature_123",
  "feature_456",
  "feature_789"
]
```

**Kullanım:** RankingModel otomatik olarak bu dosyayı okur ve blacklist'teki feature'ları filtreler.

### 2. Görselleştirmeler

#### a) Top Features Bar Chart

**Dosya:** `{output_dir}/top_features.png`

En önemli 20 feature'ı SHAP importance değerleriyle gösterir.

**Yorumlama:**
- Uzun barlar: Yüksek importance (model için kritik)
- Kısa barlar: Düşük importance (potansiyel blacklist adayları)

#### b) Model Comparison Chart

**Dosya:** `{output_dir}/model_comparison.png`

Baseline vs Optimized model karşılaştırması.

**Gösterilen metrikler:**
- NDCG@3 skorları
- Feature sayıları
- İyileştirme yüzdesi

### 3. Analiz Raporu

**Dosya:** `{output_dir}/analysis_report_YYYYMMDD_HHMMSS.md`

**İçerik:**
- Analiz özeti
- Veri istatistikleri
- Feature analizi
- Model performans karşılaştırması
- Top 20 en önemli feature'lar
- Öneriler

**Örnek rapor yapısı:**
```markdown
# Feature Importance Analysis Report

## Analysis Summary
- Timestamp: 2024-01-15 14:30:45
- Duration: 245.67 seconds
- Configuration: ...

## Data Summary
- Tickers analyzed: 5
- Data points: 12,345
- Date range: 2023-01-01 to 2023-12-31

## Feature Analysis
- Total features: 150
- Blacklisted: 45 (30.0%)
- Remaining: 105 (70.0%)

## Model Performance
- Baseline NDCG@3: 0.6217
- Optimized NDCG@3: 0.6543
- Improvement: +5.24%

## Top 20 Most Important Features
1. rsi_14: 0.045231
2. macd_signal: 0.038765
...
```

### 4. Metadata

**Dosya:** `{output_dir}/analysis_metadata_YYYYMMDD_HHMMSS.json`

**İçerik:**
```json
{
  "timestamp": "2024-01-15T14:30:45",
  "config": {
    "sample_size": 1000,
    "importance_threshold": 0.001,
    ...
  },
  "results": {
    "baseline_ndcg3": 0.6217,
    "optimized_ndcg3": 0.6543,
    "improvement_pct": 5.24,
    ...
  },
  "data": {
    "tickers": ["THYAO", "AKBNK", ...],
    "data_size": 12345,
    ...
  }
}
```

### 5. Kaydedilmiş Modeller (Opsiyonel)

**Dosyalar:**
- `{output_dir}/baseline_model.pkl`
- `{output_dir}/optimized_model.pkl`

**Koşul:** `--save-models` flag'i kullanıldığında

**Kullanım:**
```python
import pickle

with open('reports/feature_importance/baseline_model.pkl', 'rb') as f:
    baseline_model = pickle.load(f)
```

## Sonuçları Yorumlama

### Konsol Çıktısı

```
================================================================================
FEATURE IMPORTANCE ANALYSIS RESULTS
================================================================================

Timestamp: 2024-01-15 14:30:45
Duration: 245.67 seconds

--------------------------------------------------------------------------------
DATA SUMMARY
--------------------------------------------------------------------------------
Tickers analyzed: 5
Data points: 12,345
Tickers: THYAO, AKBNK, EREGL, GARAN, ISCTR

--------------------------------------------------------------------------------
FEATURE ANALYSIS
--------------------------------------------------------------------------------
Total features: 150
Blacklisted: 45 (30.0%)
Remaining: 105 (70.0%)

--------------------------------------------------------------------------------
MODEL PERFORMANCE
--------------------------------------------------------------------------------
Baseline NDCG@3:  0.6217
Optimized NDCG@3: 0.6543
Improvement:      +5.24%

✓ Success: Feature selection improved model performance!

--------------------------------------------------------------------------------
TOP 10 MOST IMPORTANT FEATURES
--------------------------------------------------------------------------------
 1. rsi_14                                    0.045231
 2. macd_signal                               0.038765
 3. volume_ratio                              0.032109
 4. price_momentum_5d                         0.028654
 5. bollinger_width                           0.025432
 ...
```

### Başarı Kriterleri

#### ✅ Başarılı Analiz

**Göstergeler:**
- Optimized NDCG@3 > Baseline NDCG@3
- İyileştirme yüzdesi > 0%
- Blacklist boyutu < %80

**Örnek:**
```
Baseline NDCG@3:  0.6217
Optimized NDCG@3: 0.6543
Improvement:      +5.24%
```

**Yorum:** Feature selection başarılı! Model performansı arttı.

**Sonraki adımlar:**
1. Blacklist'i production'a deploy et
2. Yeni modeli eğit ve test et
3. Sonuçları izle

#### ⚠️ Performans Düşüşü

**Göstergeler:**
- Optimized NDCG@3 < Baseline NDCG@3
- Negatif iyileştirme yüzdesi

**Örnek:**
```
Baseline NDCG@3:  0.6217
Optimized NDCG@3: 0.6105
Improvement:      -1.80%
```

**Yorum:** Çok fazla önemli feature filtrelenmiş olabilir.

**Çözümler:**
1. Threshold değerini düşür (örn: 0.001 → 0.0005)
2. Sample size'ı artır (daha doğru SHAP değerleri için)
3. Farklı tarih aralığı dene

#### ➡️ Değişiklik Yok

**Göstergeler:**
- Optimized NDCG@3 ≈ Baseline NDCG@3
- İyileştirme yüzdesi ≈ 0%

**Örnek:**
```
Baseline NDCG@3:  0.6217
Optimized NDCG@3: 0.6219
Improvement:      +0.03%
```

**Yorum:** Filtrelenen feature'lar zaten düşük katkılıydı.

**Sonraki adımlar:**
1. Threshold'u artır (daha fazla feature filtrele)
2. Feature engineering yap (yeni feature'lar ekle)
3. Farklı feature selection yöntemleri dene

### Feature Importance Yorumlama

#### Yüksek Importance (> 0.03)

**Anlamı:** Model için kritik feature'lar

**Örnekler:**
- `rsi_14`: 0.045
- `macd_signal`: 0.038
- `volume_ratio`: 0.032

**Aksiyon:** Bu feature'ları asla blacklist'e alma!

#### Orta Importance (0.01 - 0.03)

**Anlamı:** Yararlı ama kritik olmayan feature'lar

**Örnekler:**
- `price_momentum_5d`: 0.028
- `bollinger_width`: 0.025

**Aksiyon:** Dikkatli değerlendir, gerekirse koru.

#### Düşük Importance (< 0.01)

**Anlamı:** Düşük katkılı feature'lar

**Örnekler:**
- `feature_123`: 0.0008
- `feature_456`: 0.0005

**Aksiyon:** Blacklist adayları, güvenle filtrele.

## İleri Seviye Kullanım

### 1. Özel Feature Selection Stratejisi

```python
from scripts.analysis.feature_selector import FeatureSelector
import pandas as pd

# Importance tablosunu yükle
importance_df = pd.read_csv('importance_results.csv')

# Özel strateji: Top %20'yi koru, geri kalanını filtrele
selector = FeatureSelector(threshold=0.0)  # Eşik kullanma
top_20_pct = int(len(importance_df) * 0.2)
blacklist = importance_df.iloc[top_20_pct:]['feature'].tolist()

# Kaydet
selector.save_blacklist(blacklist)
```

### 2. Çoklu Threshold Karşılaştırması

```bash
# Farklı threshold'larla analiz yap
for threshold in 0.0005 0.001 0.005 0.01; do
    python scripts/analysis/run_feature_importance.py \
        --threshold $threshold \
        --output-dir reports/threshold_$threshold
done

# Sonuçları karşılaştır
python scripts/compare_threshold_results.py
```

### 3. Zaman Serisi Analizi

```python
# Farklı dönemlerde feature importance değişimini analiz et
periods = [
    ("2023-Q1", "2023-01-01", "2023-03-31"),
    ("2023-Q2", "2023-04-01", "2023-06-30"),
    ("2023-Q3", "2023-07-01", "2023-09-30"),
    ("2023-Q4", "2023-10-01", "2023-12-31"),
]

for name, start, end in periods:
    analyzer = FeatureImportanceAnalyzer(
        config_module=config,
        analysis_config=AnalysisConfig(
            start_date=start,
            end_date=end,
            output_dir=f"reports/{name}"
        )
    )
    analyzer.run_analysis()
```

### 4. Ensemble Feature Selection

```python
# Birden fazla analiz sonucunu birleştir
import json
from collections import Counter

blacklists = []
for i in range(5):
    # Farklı random seed'lerle analiz yap
    result = analyzer.run_analysis()
    blacklists.append(result.blacklist)

# En sık blacklist'e alınan feature'ları seç
all_features = [f for bl in blacklists for f in bl]
feature_counts = Counter(all_features)

# %80'den fazla analizde blacklist'e alınan feature'lar
threshold_count = len(blacklists) * 0.8
final_blacklist = [f for f, count in feature_counts.items() 
                   if count >= threshold_count]

# Kaydet
with open('models/saved/feature_blacklist.json', 'w') as f:
    json.dump(final_blacklist, f, indent=2)
```

## Sorun Giderme

### Hata 1: SHAP Kütüphanesi Bulunamadı

**Hata mesajı:**
```
ImportError: No module named 'shap'
```

**Çözüm:**
```bash
pip install shap>=0.41.0
```

### Hata 2: Yetersiz Bellek

**Hata mesajı:**
```
MemoryError: Unable to allocate array
```

**Çözümler:**
1. Sample size'ı azalt:
```bash
python scripts/analysis/run_feature_importance.py --sample-size 500
```

2. Daha az ticker kullan:
```bash
python scripts/analysis/run_feature_importance.py --tickers THYAO,AKBNK
```

3. Tarih aralığını daralt:
```bash
python scripts/analysis/run_feature_importance.py \
    --start-date 2024-01-01 \
    --end-date 2024-03-31
```

### Hata 3: Geçersiz Threshold

**Hata mesajı:**
```
ValueError: Threshold must be between 0 and 1, got -0.5
```

**Çözüm:**
0 ile 1 arasında bir değer kullanın:
```bash
python scripts/analysis/run_feature_importance.py --threshold 0.001
```

### Hata 4: Geçersiz Tarih Formatı

**Hata mesajı:**
```
ValueError: Invalid start date format: 2023/01/01. Expected YYYY-MM-DD
```

**Çözüm:**
YYYY-MM-DD formatını kullanın:
```bash
python scripts/analysis/run_feature_importance.py --start-date 2023-01-01
```

### Hata 5: Config Modülü Bulunamadı

**Hata mesajı:**
```
ModuleNotFoundError: Configuration module 'my_config' not found
```

**Çözüm:**
Geçerli bir config modülü kullanın:
```bash
python scripts/analysis/run_feature_importance.py --config config
```

### Hata 6: Yetersiz Veri

**Hata mesajı:**
```
ValueError: No valid data could be loaded
```

**Çözümler:**
1. Ticker'ların doğru olduğundan emin olun
2. Tarih aralığını kontrol edin
3. Veri kaynaklarının erişilebilir olduğunu doğrulayın

### Hata 7: Blacklist Çok Büyük

**Uyarı mesajı:**
```
WARNING: Blacklist contains 85% of features. Consider lowering threshold.
```

**Çözüm:**
Threshold değerini düşürün:
```bash
python scripts/analysis/run_feature_importance.py --threshold 0.0005
```

## SSS

### S1: Analiz ne kadar sürer?

**C:** Veri boyutuna bağlı:
- Küçük veri (< 1000 satır): 1-2 dakika
- Orta veri (1000-10000 satır): 3-5 dakika
- Büyük veri (> 10000 satır): 5-10 dakika

Sample size ve ticker sayısı da süreyi etkiler.

### S2: Hangi threshold değerini kullanmalıyım?

**C:** Başlangıç için:
- **0.001**: Dengeli (önerilen)
- **0.0005**: Daha az feature filtrele
- **0.005**: Daha fazla feature filtrele

Sonuçlara göre ayarlayın.

### S3: Blacklist otomatik olarak uygulanır mı?

**C:** Evet! RankingModel otomatik olarak `models/saved/feature_blacklist.json` dosyasını okur ve blacklist'teki feature'ları filtreler.

### S4: Blacklist'i nasıl geri alabilirim?

**C:** Blacklist dosyasını silin veya yeniden adlandırın:
```bash
mv models/saved/feature_blacklist.json models/saved/feature_blacklist.json.backup
```

### S5: Birden fazla analiz sonucunu nasıl karşılaştırırım?

**C:** Her analiz için farklı output dizini kullanın:
```bash
python scripts/analysis/run_feature_importance.py --output-dir reports/analysis1
python scripts/analysis/run_feature_importance.py --output-dir reports/analysis2
```

Sonra metadata dosyalarını karşılaştırın.

### S6: SHAP hesaplaması çok yavaş, nasıl hızlandırabilirim?

**C:** 
1. Sample size'ı azaltın: `--sample-size 500`
2. Daha az ticker kullanın
3. Tarih aralığını daraltın

### S7: Feature importance değerleri nasıl yorumlanır?

**C:** 
- **> 0.03**: Kritik feature'lar (asla filtrele)
- **0.01-0.03**: Yararlı feature'lar (dikkatli değerlendir)
- **< 0.01**: Düşük katkılı (güvenle filtrele)

### S8: Analiz sonuçları nerede saklanır?

**C:** Varsayılan olarak `reports/feature_importance/` dizininde. `--output-dir` ile değiştirebilirsiniz.

### S9: Önceki analiz sonuçları silinir mi?

**C:** Hayır! Her analiz timestamp ile kaydedilir, önceki sonuçlar korunur.

### S10: Production'da nasıl kullanmalıyım?

**C:**
1. Analizi çalıştır ve sonuçları değerlendir
2. Blacklist'i production'a deploy et
3. Yeni model eğit
4. A/B test yap
5. Performansı izle

## İlgili Dokümantasyon

- [CLI Kullanım Kılavuzu](feature_importance_cli_usage.md)
- [Tasarım Dokümanı](specs/lightgbm-feature-importance-analysis/design.md)
- [Gereksinim Dokümanı](specs/lightgbm-feature-importance-analysis/requirements.md)
- [Görev Listesi](specs/lightgbm-feature-importance-analysis/tasks.md)

## Destek

Sorularınız için:
- GitHub Issues: [Proje Repository]
- Dokümantasyon: Bu dosya ve ilgili dokümanlar
- Loglar: `logs/system.log` dosyasını kontrol edin
