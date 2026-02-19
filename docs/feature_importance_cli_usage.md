# Feature Importance Analysis CLI - Kullanım Kılavuzu

## Genel Bakış

`run_feature_importance.py` scripti, LightGBM modelinin feature importance analizini SHAP değerleri kullanarak gerçekleştirir. Script, komut satırından çalıştırılabilir ve çeşitli parametrelerle özelleştirilebilir.

## Temel Kullanım

### Varsayılan Ayarlarla Çalıştırma

```bash
python scripts/analysis/run_feature_importance.py
```

Bu komut:
- `config.py` modülünden yapılandırmayı yükler
- 1000 örnekle SHAP analizi yapar
- 0.001 eşik değeriyle feature filtreleme yapar
- Sonuçları `reports/feature_importance/` dizinine kaydeder

### Özel Parametrelerle Çalıştırma

```bash
python scripts/analysis/run_feature_importance.py \
    --threshold 0.005 \
    --sample-size 2000 \
    --start-date 2023-01-01 \
    --end-date 2023-12-31
```

## Parametreler

### Yapılandırma

- `--config CONFIG`: Yapılandırma modülü adı (varsayılan: `config`)
  ```bash
  python scripts/analysis/run_feature_importance.py --config sector_config
  ```

### Analiz Parametreleri

- `--threshold THRESHOLD`: Feature importance eşiği (varsayılan: 0.001)
  - Bu değerin altındaki feature'lar blacklist'e alınır
  - Geçerli aralık: 0.0 - 1.0
  ```bash
  python scripts/analysis/run_feature_importance.py --threshold 0.005
  ```

- `--sample-size SIZE`: SHAP hesaplaması için örnek boyutu (varsayılan: 1000)
  - Daha büyük değerler daha doğru ama daha yavaş
  ```bash
  python scripts/analysis/run_feature_importance.py --sample-size 2000
  ```

### Tarih Aralığı

- `--start-date YYYY-MM-DD`: Analiz başlangıç tarihi
- `--end-date YYYY-MM-DD`: Analiz bitiş tarihi

```bash
python scripts/analysis/run_feature_importance.py \
    --start-date 2023-01-01 \
    --end-date 2023-12-31
```

### Ticker Seçimi

- `--tickers TICKER1,TICKER2,...`: Analiz edilecek ticker'lar (virgülle ayrılmış)

```bash
python scripts/analysis/run_feature_importance.py --tickers THYAO,AKBNK,EREGL
```

### Çıktı Ayarları

- `--output-dir DIR`: Çıktı dizini (varsayılan: `reports/feature_importance`)
  ```bash
  python scripts/analysis/run_feature_importance.py --output-dir reports/my_analysis
  ```

- `--save-models`: Baseline ve optimized modelleri kaydet
  ```bash
  python scripts/analysis/run_feature_importance.py --save-models
  ```

### Loglama

- `--log-level LEVEL`: Log seviyesi (DEBUG, INFO, WARNING, ERROR)
  ```bash
  python scripts/analysis/run_feature_importance.py --log-level DEBUG
  ```

- `--quiet`: Sadece hataları göster
  ```bash
  python scripts/analysis/run_feature_importance.py --quiet
  ```

## Örnek Senaryolar

### 1. Hızlı Test (Az Veri)

```bash
python scripts/analysis/run_feature_importance.py \
    --tickers THYAO,AKBNK \
    --sample-size 500 \
    --start-date 2024-01-01
```

### 2. Kapsamlı Analiz (Tüm Veri)

```bash
python scripts/analysis/run_feature_importance.py \
    --sample-size 5000 \
    --threshold 0.0005 \
    --save-models
```

### 3. Belirli Dönem Analizi

```bash
python scripts/analysis/run_feature_importance.py \
    --start-date 2023-01-01 \
    --end-date 2023-06-30 \
    --output-dir reports/q1_q2_2023
```

### 4. Debug Modu

```bash
python scripts/analysis/run_feature_importance.py \
    --log-level DEBUG \
    --tickers THYAO \
    --sample-size 100
```

## Çıktı Dosyaları

Analiz tamamlandığında aşağıdaki dosyalar oluşturulur:

### 1. Blacklist
- **Konum**: `models/saved/feature_blacklist.json`
- **İçerik**: Filtrelenen feature'ların listesi
- **Format**: JSON array

### 2. Görselleştirmeler
- **Konum**: `{output_dir}/`
- **Dosyalar**:
  - `top_features.png`: En önemli 20 feature'ın bar chart'ı
  - `model_comparison.png`: Baseline vs Optimized karşılaştırması

### 3. Rapor
- **Konum**: `{output_dir}/analysis_report_YYYYMMDD_HHMMSS.md`
- **İçerik**: Detaylı analiz raporu (Markdown formatında)

### 4. Metadata
- **Konum**: `{output_dir}/analysis_metadata_YYYYMMDD_HHMMSS.json`
- **İçerik**: Analiz parametreleri ve sonuçları (JSON formatında)

### 5. Modeller (opsiyonel)
- **Konum**: `{output_dir}/baseline_model.pkl` ve `optimized_model.pkl`
- **Koşul**: `--save-models` flag'i kullanıldığında

## Çıktı Yorumlama

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
 ...
```

### Başarı Kriterleri

- **Pozitif İyileştirme**: Optimized NDCG@3 > Baseline NDCG@3
  - ✓ Feature selection başarılı
  
- **Negatif İyileştirme**: Optimized NDCG@3 < Baseline NDCG@3
  - ⚠️ Threshold değerini artırmayı deneyin
  
- **Değişiklik Yok**: Optimized NDCG@3 = Baseline NDCG@3
  - → Filtrelenen feature'lar zaten düşük katkılıydı

## Hata Durumları

### 1. Geçersiz Threshold

```bash
❌ Error: Threshold must be between 0 and 1, got -0.5
```

**Çözüm**: 0 ile 1 arasında bir değer kullanın.

### 2. Geçersiz Tarih Formatı

```bash
❌ Error: Invalid start date format: 2023/01/01. Expected YYYY-MM-DD
```

**Çözüm**: YYYY-MM-DD formatını kullanın (örn: 2023-01-01).

### 3. Config Modülü Bulunamadı

```bash
❌ Error: Configuration module 'my_config' not found.
```

**Çözüm**: Geçerli bir config modülü adı kullanın veya modülü oluşturun.

### 4. Yetersiz Veri

```bash
❌ Analysis failed: No valid data could be loaded.
```

**Çözüm**: 
- Ticker'ların doğru olduğundan emin olun
- Tarih aralığını kontrol edin
- Veri kaynaklarının erişilebilir olduğunu doğrulayın

## İpuçları

1. **İlk Çalıştırma**: Küçük bir ticker listesi ve düşük sample size ile başlayın
2. **Threshold Ayarı**: 0.001 ile başlayın, sonuçlara göre ayarlayın
3. **Sample Size**: 1000-2000 arası genellikle yeterlidir
4. **Debug**: Sorun yaşarsanız `--log-level DEBUG` kullanın
5. **Performans**: Büyük veri setleri için `--sample-size` değerini düşürün

## Yardım

Tüm parametreleri görmek için:

```bash
python scripts/analysis/run_feature_importance.py --help
```

## İlgili Dokümantasyon

- [Feature Importance Analysis Tasarım Dokümanı](../docs/specs/lightgbm-feature-importance-analysis/design.md)
- [Gereksinim Dokümanı](../docs/specs/lightgbm-feature-importance-analysis/requirements.md)
