# Temizlik Yapılandırma Kılavuzu

`cleanup_config.yaml` aracılığıyla geliştirme sonrası temizlik sistemini yapılandırmak için kapsamlı kılavuz.

## İçindekiler

- [Genel Bakış](#genel-bakış)
- [Yapılandırma Dosyası Konumu](#yapılandırma-dosyası-konumu)
- [Yapılandırma Yapısı](#yapılandırma-yapısı)
- [Yapılandırma Seçenekleri](#yapılandırma-seçenekleri)
  - [Eşikler](#eşikler)
  - [Hariç Tutmalar](#hariç-tutmalar)
  - [Script Kategorileri](#script-kategorileri)
- [Örnek Yapılandırmalar](#örnek-yapılandırmalar)
- [Eşik Ayarlama Kılavuzu](#eşik-ayarlama-kılavuzu)
- [En İyi Uygulamalar](#en-iyi-uygulamalar)
- [Sorun Giderme](#sorun-giderme)

## Genel Bakış

`cleanup_config.yaml` dosyası, bakım scriptlerinin kod tabanınızı nasıl analiz edip temizlediğini kontrol eder. Şunları özelleştirmenize olanak tanır:

- Küçük ve büyük dosyaları tanımlamak için **dosya boyutu eşikleri**
- Log dosyaları ve geçici yapıtlar için **saklama politikaları**
- Kopya kod tespiti için **benzerlik eşikleri**
- Atlanacak dizinler ve dosyalar için **hariç tutma desenleri**
- Scriptleri kullanım desenine göre düzenlemek için **script kategorizasyon kuralları**

Tüm bakım scriptleri bu yapılandırmaya saygı gösterir ve temizlik sistemi genelinde tutarlı davranış sağlar.

## Yapılandırma Dosyası Konumu

Yapılandırma dosyası **proje kökü**ne yerleştirilmelidir:

```
projeniz/
├── cleanup_config.yaml    ← Yapılandırma dosyası burada
├── scripts/
│   └── maintenance/
├── src/
└── tests/
```

**Alternatif konumlar**:
- `--config` bayrağını kullanarak özel bir yol belirtin:
  ```bash
  python scripts/maintenance/find_unused_files.py --config /yol/yapilandirma.yaml
  ```

**Varsayılan davranış**:
- Yapılandırma dosyası bulunamazsa, sistem yerleşik varsayılanları kullanır
- Dosya eksikse hata oluşturulmaz
- Yapılandırma dosyası olmadan başlayabilir ve daha sonra ekleyebilirsiniz

## Yapılandırma Yapısı

Yapılandırma dosyasının üç ana bölümü vardır:

```yaml
thresholds:
  # Dosya boyutu ve benzerlik eşikleri
  
exclusions:
  # Hariç tutulacak dizinler ve desenler
  
script_categories:
  # Scriptleri kategorize etme kuralları
```

Her bölüm isteğe bağlıdır. Bir bölüm eksikse, o bölüm için varsayılanlar kullanılır.

## Yapılandırma Seçenekleri

### Eşikler

Çeşitli temizlik işlemleri için sayısal eşikleri kontrol eder.

```yaml
thresholds:
  small_file_lines: 100
  large_file_lines: 500
  log_retention_days: 30
  duplicate_similarity: 0.85
```

#### `small_file_lines`

**Tür**: Tam sayı  
**Varsayılan**: 100  
**Aralık**: 1 - 1000  
**Kullanan**: `find_small_files.py`, `suggest_merges.py`

Bu kadar satırdan az kod içeren dosyalar "küçük" olarak kabul edilir ve birleştirme adayı olabilir.

**Satır olarak ne sayılır**:
- Yalnızca boş olmayan, yorum olmayan satırlar sayılır
- Docstring'ler kod olarak sayılır
- Import'lar kod olarak sayılır

**Ayarlama rehberi**:
- **50-75**: Çok sıkı, orta derecede küçük dosyaları bile tanımlar
- **100**: Varsayılan, çoğu proje için iyi denge
- **150-200**: Hoşgörülü, yalnızca çok küçük dosyaları işaretler

**Örnek**:
```yaml
thresholds:
  small_file_lines: 75  # Daha agresif küçük dosya tespiti
```

#### `large_file_lines`

**Tür**: Tam sayı  
**Varsayılan**: 500  
**Aralık**: 100 - 5000  
**Kullanan**: `find_large_files.py`, `suggest_merges.py`

Bu kadar satırdan fazla kod içeren dosyalar "büyük" olarak kabul edilir ve bölme gerektirebilir.

**Satır olarak ne sayılır**:
- Yalnızca boş olmayan, yorum olmayan satırlar sayılır
- Docstring'ler kod olarak sayılır
- Import'lar kod olarak sayılır

**Ayarlama rehberi**:
- **300-400**: Sıkı, daha küçük dosyaları teşvik eder
- **500**: Varsayılan, yaygın en iyi uygulamaları takip eder
- **700-1000**: Hoşgörülü, yalnızca çok büyük dosyaları işaretler

**Önemli kısıt**:
- `small_file_lines`'dan büyük olmalıdır
- Önerilen boşluk: eşikler arasında en az 200 satır
- Eşikler arasındaki dosyalar "normal" boyut olarak kabul edilir

**Örnek**:
```yaml
thresholds:
  small_file_lines: 100
  large_file_lines: 600  # Daha hoşgörülü büyük dosya eşiği
```

#### `log_retention_days`

**Tür**: Tam sayı  
**Varsayılan**: 30  
**Aralık**: 1 - 365  
**Kullanan**: `auto_cleanup.py`

Bu kadar günden eski log dosyaları otomatik temizlik sırasında kaldırılır.

**Log dosyası olarak ne nitelenir**:
- `.log` uzantılı dosyalar
- `logs/` veya `log/` adlı dizinlerdeki dosyalar
- `*.log.*` desenine uyan dosyalar (örn. `app.log.2024-01-15`)

**Ayarlama rehberi**:
- **7-14 gün**: Kısa saklama, disk alanı tasarrufu
- **30 gün**: Varsayılan, çoğu proje için iyi
- **60-90 gün**: Uzun saklama, geçmiş sorunları hata ayıklamak için yararlı
- **180+ gün**: Çok uzun saklama, bunun yerine arşivlemeyi düşünün

**Örnek**:
```yaml
thresholds:
  log_retention_days: 14  # Logları yalnızca 2 hafta sakla
```

#### `duplicate_similarity`

**Tür**: Ondalık sayı  
**Varsayılan**: 0.85  
**Aralık**: 0.0 - 1.0  
**Kullanan**: `find_duplicate_code.py`

İki fonksiyonun kopya olarak kabul edilmesi için minimum benzerlik skoru.

**Benzerlik nasıl hesaplanır**:
- Kod normalleştirilir (boşluklar ve yorumlar kaldırılır)
- Dizi eşleştirme algoritması normalleştirilmiş kodu karşılaştırır
- 1.0 skoru = özdeş kod
- 0.0 skoru = tamamen farklı kod

**Ayarlama rehberi**:
- **0.95-1.0**: Çok sıkı, yalnızca neredeyse özdeş kod
- **0.85**: Varsayılan, küçük varyasyonlarla çoğu kopyayı yakalar
- **0.70-0.80**: Orta, daha fazla varyasyonla benzer kodu yakalar
- **0.50-0.65**: Hoşgörülü, yanlış pozitiflere neden olabilir

**Örnek**:
```yaml
thresholds:
  duplicate_similarity: 0.90  # Daha sıkı kopya tespiti
```

**Dengeler**:
- Daha yüksek eşik: Daha az yanlış pozitif, benzer kodu kaçırabilir
- Daha düşük eşik: Daha fazla kopya bulunur, gözden geçirilecek daha fazla yanlış pozitif

---

### Hariç Tutmalar

Hangi dizinlerin ve dosyaların analizden hariç tutulacağını kontrol eder.

```yaml
exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
  patterns:
    - "test_*.py"
    - "__init__.py"
```

#### `directories`

**Tür**: String listesi  
**Varsayılan**: Yaygın sanal ortam ve önbellek dizinleri  
**Kullanan**: Tüm scriptler

Dosya taraması sırasında tamamen atlanacak dizinler.

**Varsayılan hariç tutmalar**:
```yaml
directories:
  - .venv
  - __pycache__
  - .git
  - node_modules
  - .pytest_cache
  - .mypy_cache
  - .tox
  - build
  - dist
  - "*.egg-info"
  - .vscode
  - .idea
  - htmlcov
  - .coverage
```

**Ne zaman hariç tutma eklenmelidir**:
- Sanal ortamlar (venv, env, virtualenv)
- Derleme yapıtları (build, dist, target)
- IDE dizinleri (.vscode, .idea, .eclipse)
- Önbellek dizinleri (.cache, .pytest_cache)
- Üçüncü taraf kod (vendor, external, lib)
- Oluşturulan kod (generated, auto-generated)

**Desen desteği**:
- Tam adlar: `.venv`, `build`
- Joker karakterler: `*.egg-info`, `*-cache`
- Göreceli yollar: `docs/build`, `src/generated`

**Örnek**:
```yaml
exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
    - node_modules
    - .pytest_cache
    - build
    - dist
    - vendor           # Üçüncü taraf kod
    - docs/build       # Oluşturulan dokümantasyon
    - src/generated    # Otomatik oluşturulan kod
```

#### `patterns`

**Tür**: String listesi  
**Varsayılan**: Test dosyaları ve özel Python dosyaları  
**Kullanan**: `find_unused_files.py`, `find_small_files.py`, `find_large_files.py`

Kullanılmayan dosya tespiti ve boyut analizinden hariç tutulacak dosya desenleri.

**Varsayılan hariç tutmalar**:
```yaml
patterns:
  - "test_*.py"
  - "*_test.py"
  - "__init__.py"
  - "__main__.py"
  - "setup.py"
  - "conftest.py"
```

**Bu varsayılanların nedeni**:
- `test_*.py`, `*_test.py`: Test dosyaları doğrudan import edilmeyebilir
- `__init__.py`: Paket işaretleyicileri, genellikle boş veya minimal
- `__main__.py`: Giriş noktaları, import edilmez
- `setup.py`: Kurulum scripti, import edilmez
- `conftest.py`: Pytest yapılandırması, import edilmez

**Ne zaman hariç tutma eklenmelidir**:
- Giriş noktası scriptleri (main.py, run.py, cli.py)
- Yapılandırma dosyaları (config.py, settings.py)
- Geçiş scriptleri (migrate_*.py, migration_*.py)
- Tek seferlik scriptler (setup_*.py, install_*.py)

**Desen sözdizimi**:
- Joker karakterler: `*` herhangi bir karakterle eşleşir
- Önek: `test_*.py`, `test_foo.py`, `test_bar.py` ile eşleşir
- Sonek: `*_test.py`, `foo_test.py`, `bar_test.py` ile eşleşir
- Tam: `"setup.py"` yalnızca `setup.py` ile eşleşir

**Örnek**:
```yaml
exclusions:
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "__init__.py"
    - "__main__.py"
    - "setup.py"
    - "conftest.py"
    - "main.py"         # Giriş noktası
    - "cli.py"          # Komut satırı arayüzü
    - "migrate_*.py"    # Geçiş scriptleri
    - "*_config.py"     # Yapılandırma dosyaları
```

---

### Script Kategorileri

Scriptlerin nasıl kategorize edilip düzenleneceğini kontrol eder.

```yaml
script_categories:
  production:
    - train_models.py
    - run_backtest.py
  analysis_keywords:
    - analyze
    - check
  maintenance_keywords:
    - migrate
    - update
  test_keywords:
    - test
    - verify
```

#### `production`

**Tür**: String listesi  
**Varsayılan**: Boş liste  
**Kullanan**: `organize_scripts.py`

`scripts/` kök seviyesinde kalması gereken üretim scriptlerinin açık listesi.

**Üretim scriptleri nedir**:
- Üretim veya geliştirme iş akışlarında düzenli olarak kullanılan scriptler
- Shell scriptlerinde, dokümantasyonda veya CI/CD'de referans edilen scriptler
- Kolayca erişilebilir olması gereken kritik scriptler

**Neden açıkça listelenmeli**:
- Kazara yeniden düzenlemeyi önler
- Üretim scriptlerini belirgin hale getirir
- Öngörülebilir konumlarda kalmalarını sağlar

**Örnek**:
```yaml
script_categories:
  production:
    - train_models.py
    - run_backtest.py
    - daily_run.py
    - paper_trading_runner.py
    - data_fetcher.py
    - model_evaluator.py
```

**En iyi uygulamalar**:
- Yalnızca düzenli çalışan scriptleri listeleyin
- Dokümantasyonda referans edilen scriptleri dahil edin
- Otomasyonda kullanılan scriptleri dahil edin
- Listeyi minimal tutun (tipik olarak 5-10 script)

#### `analysis_keywords`

**Tür**: String listesi  
**Varsayılan**: Yaygın analiz ile ilgili anahtar kelimeler  
**Kullanan**: `organize_scripts.py`

Analiz scriptlerini tanımlayan anahtar kelimeler (`scripts/analysis/`'e gitmeli).

**Varsayılan anahtar kelimeler**:
```yaml
analysis_keywords:
  - analyze
  - check
  - inspect
  - compare
  - evaluate
  - report
  - visualize
  - plot
```

**Analiz scriptleri nedir**:
- Seyrek analiz veya hata ayıklama için scriptler
- Rapor veya görselleştirme oluşturan scriptler
- Sonuçları karşılaştıran veya değerlendiren scriptler
- Araştırma için kullanılan scriptler

**Kategorizasyon mantığı**:
- Script adı herhangi bir anahtar kelime içeriyorsa → analiz olarak kategorize edilir
- Büyük/küçük harf duyarsız eşleştirme
- Kısmi eşleştirme (örn. "analyzer", "analyze" ile eşleşir)

**Örnek**:
```yaml
script_categories:
  analysis_keywords:
    - analyze
    - check
    - inspect
    - compare
    - evaluate
    - report
    - visualize
    - plot
    - explore      # Eklendi
    - investigate  # Eklendi
    - profile      # Eklendi
```

**Eşleşen script örnekleri**:
- `analyze_features.py` → analiz ("analyze" içerir)
- `check_data_quality.py` → analiz ("check" içerir)
- `compare_models.py` → analiz ("compare" içerir)
- `visualize_results.py` → analiz ("visualize" içerir)

#### `maintenance_keywords`

**Tür**: String listesi  
**Varsayılan**: Yaygın bakım ile ilgili anahtar kelimeler  
**Kullanan**: `organize_scripts.py`

Bakım scriptlerini tanımlayan anahtar kelimeler (`scripts/maintenance/`'e gitmeli).

**Varsayılan anahtar kelimeler**:
```yaml
maintenance_keywords:
  - migrate
  - update
  - fix
  - clean
  - convert
  - setup
  - install
```

**Bakım scriptleri nedir**:
- Tek seferlik veya seyrek kurulum scriptleri
- Veri veya kod için geçiş scriptleri
- Mevcut verileri düzelten veya güncelleyen scriptler
- Kurulum veya yapılandırma scriptleri

**Kategorizasyon mantığı**:
- Script adı herhangi bir anahtar kelime içeriyorsa → bakım olarak kategorize edilir
- Büyük/küçük harf duyarsız eşleştirme
- Kısmi eşleştirme (örn. "migration", "migrate" ile eşleşir)

**Örnek**:
```yaml
script_categories:
  maintenance_keywords:
    - migrate
    - update
    - fix
    - clean
    - convert
    - setup
    - install
    - repair      # Eklendi
    - rebuild     # Eklendi
    - initialize  # Eklendi
```

**Eşleşen script örnekleri**:
- `migrate_database.py` → bakım ("migrate" içerir)
- `update_config.py` → bakım ("update" içerir)
- `fix_data_issues.py` → bakım ("fix" içerir)
- `cleanup_old_files.py` → bakım ("clean" içerir)

#### `test_keywords`

**Tür**: String listesi  
**Varsayılan**: Yaygın test ile ilgili anahtar kelimeler  
**Kullanan**: `organize_scripts.py`

Entegrasyon test scriptlerini tanımlayan anahtar kelimeler (`scripts/tests/`'e gitmeli).

**Varsayılan anahtar kelimeler**:
```yaml
test_keywords:
  - test
  - verify
  - validate
  - debug
  - benchmark
```

**Test scriptleri nedir**:
- Entegrasyon test scriptleri (birim testleri değil)
- Doğrulama scriptleri
- Validasyon scriptleri
- Hata ayıklama yardımcı programları
- Kıyaslama scriptleri

**Not**: `tests/` dizinindeki birim testler bu yapılandırmadan etkilenmez.

**Kategorizasyon mantığı**:
- Script adı herhangi bir anahtar kelime içeriyorsa → test olarak kategorize edilir
- Büyük/küçük harf duyarsız eşleştirme
- Kısmi eşleştirme (örn. "testing", "test" ile eşleşir)

**Örnek**:
```yaml
script_categories:
  test_keywords:
    - test
    - verify
    - validate
    - debug
    - benchmark
    - smoke      # Eklendi
    - sanity     # Eklendi
    - integration # Eklendi
```

**Eşleşen script örnekleri**:
- `test_integration.py` → test ("test" içerir)
- `verify_deployment.py` → test ("verify" içerir)
- `validate_data.py` → test ("validate" içerir)
- `benchmark_models.py` → test ("benchmark" içerir)

---

## Örnek Yapılandırmalar

### Minimal Yapılandırma

Çoğunlukla varsayılanları küçük ayarlamalarla kullanmak isteyen projeler için:

```yaml
thresholds:
  small_file_lines: 75  # Varsayılandan biraz daha sıkı

exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
    - vendor  # Üçüncü taraf kod hariç tutma ekle

script_categories:
  production:
    - main.py
    - run.py
```

### Sıkı Yapılandırma

Agresif temizlik isteyen projeler için:

```yaml
thresholds:
  small_file_lines: 50
  large_file_lines: 300
  log_retention_days: 7
  duplicate_similarity: 0.95

exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
    - node_modules
    - .pytest_cache
    - build
    - dist
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "__init__.py"
    - "__main__.py"
    - "setup.py"

script_categories:
  production:
    - train.py
    - evaluate.py
  analysis_keywords:
    - analyze
    - check
    - inspect
    - compare
    - evaluate
    - report
    - visualize
    - plot
    - explore
  maintenance_keywords:
    - migrate
    - update
    - fix
    - clean
    - convert
    - setup
    - install
    - repair
  test_keywords:
    - test
    - verify
    - validate
    - debug
    - benchmark
```

### Hoşgörülü Yapılandırma

Muhafazakar temizlik isteyen projeler için:

```yaml
thresholds:
  small_file_lines: 150
  large_file_lines: 800
  log_retention_days: 90
  duplicate_similarity: 0.75

exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
    - node_modules
    - .pytest_cache
    - .mypy_cache
    - build
    - dist
    - vendor
    - external
    - third_party
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "__init__.py"
    - "__main__.py"
    - "setup.py"
    - "conftest.py"
    - "main.py"
    - "cli.py"
    - "*_config.py"
    - "*_settings.py"

script_categories:
  production:
    - train_models.py
    - run_backtest.py
    - daily_run.py
    - paper_trading_runner.py
    - data_fetcher.py
    - model_evaluator.py
    - feature_engineer.py
  analysis_keywords:
    - analyze
    - check
    - inspect
  maintenance_keywords:
    - migrate
    - update
    - fix
  test_keywords:
    - test
    - verify
```

### Makine Öğrenimi Projesi Yapılandırması

ML/AI projeleri için özelleştirilmiş:

```yaml
thresholds:
  small_file_lines: 100
  large_file_lines: 500
  log_retention_days: 30
  duplicate_similarity: 0.85

exclusions:
  directories:
    - .venv
    - __pycache__
    - .git
    - node_modules
    - .pytest_cache
    - build
    - dist
    - models          # Eğitilmiş model dosyaları
    - data            # Veri dosyaları
    - logs            # Log dosyaları
    - checkpoints     # Eğitim kontrol noktaları
    - tensorboard     # TensorBoard logları
    - mlruns          # MLflow çalıştırmaları
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "__init__.py"
    - "__main__.py"
    - "setup.py"
    - "conftest.py"

script_categories:
  production:
    - train.py
    - evaluate.py
    - predict.py
    - serve.py
  analysis_keywords:
    - analyze
    - visualize
    - plot
    - compare
    - evaluate
    - explore
    - profile
  maintenance_keywords:
    - migrate
    - update
    - fix
    - clean
    - convert
    - preprocess
  test_keywords:
    - test
    - verify
    - validate
    - benchmark
```

---

## Eşik Ayarlama Kılavuzu

### Dosya Boyutu Eşikleri Nasıl Seçilir

**Adım 1: Mevcut kod tabanınızı analiz edin**

```bash
# Mevcut dosya boyutu dağılımını görmek için bir rapor oluşturun
python scripts/maintenance/generate_cleanup_report.py --markdown rapor.md
```

Şunları anlamak için "Dosya Boyutları" bölümünü inceleyin:
- Ortalama dosya boyutu
- Medyan dosya boyutu
- Dosya boyutlarının dağılımı

**Adım 2: Başlangıç eşiklerini ayarlayın**

Proje türünüze göre bu kılavuzları kullanın:

| Proje Türü | Küçük Eşik | Büyük Eşik |
|-------------|------------|------------|
| Mikroservisler | 50-75 | 300-400 |
| Standart Uygulama | 100 | 500 |
| Monolitik Uygulama | 150-200 | 700-1000 |
| Kütüphane/Framework | 75-100 | 400-600 |

**Adım 3: Yineleyin ve iyileştirin**

```bash
# Farklı eşiklerle test edin
python scripts/maintenance/find_small_files.py --threshold 75
python scripts/maintenance/find_small_files.py --threshold 100
python scripts/maintenance/find_small_files.py --threshold 150

# Sonuçları karşılaştırın ve doğru dosyaları tanımlayan eşiği seçin
```

**Adım 4: Doğrulayın**

- Küçük/büyük dosyaların listesini gözden geçirin
- Eşiğin ele almak istediğiniz dosyaları yakaladığından emin olun
- Uygun boyuttaki dosyaları işaretlemediğinden emin olun

### Kopya Benzerlik Eşiği Nasıl Seçilir

**Adım 1: Varsayılanla başlayın (0.85)**

```bash
python scripts/maintenance/find_duplicate_code.py
```

**Adım 2: Sonuçlara göre ayarlayın**

**Çok fazla yanlış pozitif görüyorsanız** (gerçekten kopya olmayan kod):
- Eşiği 0.90 veya 0.95'e yükseltin
- Bu tespiti daha sıkı hale getirir

**Bariz kopyaları kaçırıyorsanız**:
- Eşiği 0.75 veya 0.80'e düşürün
- Bu tespiti daha hoşgörülü hale getirir

**Adım 3: Farklı eşikleri test edin**

```bash
# Sıkı (daha az sonuç, daha yüksek güven)
python scripts/maintenance/find_duplicate_code.py --threshold 0.95

# Varsayılan (dengeli)
python scripts/maintenance/find_duplicate_code.py --threshold 0.85

# Hoşgörülü (daha fazla sonuç, daha fazla inceleme gerektirir)
python scripts/maintenance/find_duplicate_code.py --threshold 0.75
```

**Adım 4: İş akışınıza göre seçin**

- **0.95+**: Yüksek güven istediğinizde ve tüm sonuçlara göre hareket edeceğinizde
- **0.85**: Denge istediğinizde ve sonuçları gözden geçireceğinizde
- **0.75**: Tüm potansiyel kopyaları bulmak istediğinizde ve dikkatlice gözden geçireceğinizde

### Log Saklama Süresi Nasıl Seçilir

**Bu faktörleri göz önünde bulundurun**:

1. **Disk alanı**: Loglar ne kadar alan tüketiyor?
   ```bash
   du -sh logs/
   ```

2. **Hata ayıklama ihtiyaçları**: Tipik olarak ne kadar geriye bakmanız gerekiyor?
   - Aktif geliştirme: 7-14 gün
   - Kararlı üretim: 30-60 gün
   - Uyumluluk gereksinimleri: 90+ gün

3. **Log hacmi**: Loglar ne kadar hızlı birikiyor?
   - Yüksek hacim: Daha kısa saklama (7-14 gün)
   - Düşük hacim: Daha uzun saklama (60-90 gün)

**Önerilen değerler**:
- **7 gün**: Yüksek hacimli loglar, sıkı disk alanı
- **14 gün**: Aktif geliştirme, sık hata ayıklama
- **30 gün**: Varsayılan, çoğu proje için iyi
- **60 gün**: Üretim sistemleri, ara sıra hata ayıklama
- **90+ gün**: Uyumluluk gereksinimleri, arşivleme ihtiyaçları

---

## En İyi Uygulamalar

### Yapılandırma Yönetimi

1. **Sürüm kontrolü**: `cleanup_config.yaml`'ı her zaman git'e commit edin
   ```bash
   git add cleanup_config.yaml
   git commit -m "Temizlik yapılandırması ekle"
   ```

2. **Özelleştirmeleri belgeleyin**: Belirli değerleri neden seçtiğinizi açıklayan yorumlar ekleyin
   ```yaml
   thresholds:
     small_file_lines: 75  # Varsayılandan daha sıkı çünkü birçok yardımcı dosyamız var
     large_file_lines: 600  # Hoşgörülü çünkü modellerimiz karmaşık
   ```

3. **Düzenli olarak gözden geçirin**: Projeniz geliştikçe yapılandırmayı yeniden ziyaret edin
   - Büyük yeniden yapılandırmadan sonra
   - Proje yapısı değiştiğinde
   - Ekip boyutu değiştiğinde

4. **Ekiple paylaşın**: Tüm ekip üyelerinin yapılandırmayı anladığından emin olun
   - README'de belgeleyin
   - Ekip toplantılarında tartışın
   - İşe alıştırmaya dahil edin

### Eşik Seçimi

1. **Muhafazakar başlayın**: Hoşgörülü eşiklerle başlayın ve zamanla sıkılaştırın
   ```yaml
   # İlk yapılandırma
   thresholds:
     small_file_lines: 150  # Hoşgörülü
     large_file_lines: 800  # Hoşgörülü
   
   # Temizlikten sonra
   thresholds:
     small_file_lines: 100  # Daha sıkı
     large_file_lines: 500  # Daha sıkı
   ```

2. **Etkiyi ölçün**: Eşik değişikliklerinden önce ve sonra metrikleri takip edin
   ```bash
   # Önce
   python scripts/maintenance/generate_cleanup_report.py --json once.json
   
   # Eşikleri değiştir
   # ...
   
   # Sonra
   python scripts/maintenance/generate_cleanup_report.py --json sonra.json
   ```

3. **Ekip tercihlerini göz önünde bulundurun**: Eşikleri ekip kodlama standartlarıyla hizalayın
   - Kod incelemelerinde tartışın
   - Stil kılavuzunda referans verin
   - CI/CD'de uygulayın

### Hariç Tutma Yönetimi

1. **Oluşturulan kodu hariç tutun**: Her zaman otomatik oluşturulan dosyaları hariç tutun
   ```yaml
   exclusions:
     directories:
       - generated
       - auto-generated
       - .generated
     patterns:
       - "*_pb2.py"      # Protocol buffers
       - "*_generated.py"
   ```

2. **Üçüncü taraf kodu hariç tutun**: Bakımını yapmadığınız kodu analiz etmeyin
   ```yaml
   exclusions:
     directories:
       - vendor
       - external
       - third_party
       - lib
   ```

3. **Derleme yapıtlarını hariç tutun**: Geçici derleme dosyalarını analiz etmeyin
   ```yaml
   exclusions:
     directories:
       - build
       - dist
       - target
       - out
   ```

4. **Hariç tutmaları periyodik olarak gözden geçirin**: Hariç tutmaların hala ilgili olduğundan emin olun
   - Silinen dizinler için hariç tutmaları kaldırın
   - Yeni oluşturulan kod için hariç tutmalar ekleyin
   - Proje geliştikçe desenleri güncelleyin

### Script Kategorizasyonu

1. **Üretim scriptleri hakkında açık olun**: Tüm üretim scriptlerini açıkça listeleyin
   ```yaml
   script_categories:
     production:
       - train.py
       - evaluate.py
       - predict.py
       - serve.py
       # Yeni üretim scriptlerini buraya ekleyin
   ```

2. **Açıklayıcı script adları kullanın**: Scriptleri kategorizasyon anahtar kelimeleriyle eşleşecek şekilde adlandırın
   - Analiz: `analyze_*.py`, `check_*.py`, `compare_*.py`
   - Bakım: `migrate_*.py`, `update_*.py`, `fix_*.py`
   - Testler: `test_*.py`, `verify_*.py`, `validate_*.py`

3. **Kategorizasyon sonuçlarını gözden geçirin**: Scriptlerin doğru kategorize edildiğini kontrol edin
   ```bash
   python scripts/maintenance/organize_scripts.py
   # Yürütmeden önce çıktıyı gözden geçirin
   ```

---

## Sorun Giderme

### Yapılandırma Yüklenmiyor

**Belirti**: Scriptler yapılandırmanız yerine varsayılan değerleri kullanıyor

**Çözümler**:

1. **Dosya konumunu kontrol edin**:
   ```bash
   ls -la cleanup_config.yaml
   # Proje kökünde olmalı
   ```

2. **Dosya adını kontrol edin**:
   ```bash
   # Doğru: cleanup_config.yaml
   # Yanlış: cleanup-config.yaml, cleanup_config.yml
   ```

3. **Yapılandırma yolunu açıkça belirtin**:
   ```bash
   python scripts/maintenance/find_unused_files.py --config cleanup_config.yaml
   ```

4. **YAML sözdizimini kontrol edin**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('cleanup_config.yaml'))"
   ```

### Geçersiz Eşik Değerleri

**Belirti**: Geçersiz eşik değerleri hakkında hata mesajı

**Çözümler**:

1. **Eşik aralıklarını kontrol edin**:
   ```yaml
   thresholds:
     small_file_lines: 100    # Pozitif tam sayı olmalı
     large_file_lines: 500    # small_file_lines'dan büyük olmalı
     log_retention_days: 30   # Pozitif tam sayı olmalı
     duplicate_similarity: 0.85  # 0.0-1.0 arasında olmalı
   ```

2. **Uygun türleri sağlayın**:
   ```yaml
   # Doğru
   thresholds:
     small_file_lines: 100
   
   # Yanlış
   thresholds:
     small_file_lines: "100"  # Tam sayı yerine string
   ```

3. **Yapılandırmayı doğrulayın**:
   ```bash
   python -c "from scripts.maintenance.core import CleanupConfig; c = CleanupConfig(); print('Geçerli')"
   ```

### Hariç Tutmalar Çalışmıyor

**Belirti**: Hariç tutulan dizinler veya dosyalar hala sonuçlarda görünüyor

**Çözümler**:

1. **Desen sözdizimini kontrol edin**:
   ```yaml
   # Doğru
   patterns:
     - "test_*.py"    # test_foo.py ile eşleşir
     - "*_test.py"    # foo_test.py ile eşleşir
   
   # Yanlış
   patterns:
     - test_*.py      # Tırnak işaretleri eksik
     - "test_.*\.py"  # Regex sözdizimi (desteklenmiyor)
   ```

2. **Dizin yollarını kontrol edin**:
   ```yaml
   # Doğru
   directories:
     - .venv          # Proje kökü göreceli
     - build
     - dist
   
   # Yanlış
   directories:
     - /.venv         # Mutlak yol (önerilmez)
     - ./build        # Gereksiz ./
   ```

3. **Hariç tutmaların yüklendiğini doğrulayın**:
   ```bash
   python -c "from scripts.maintenance.core import CleanupConfig; c = CleanupConfig(); print(c.excluded_dirs)"
   ```

---

## Özet

`cleanup_config.yaml` dosyası, temizlik sistemi için güçlü özelleştirme sağlar:

✅ **Eşikler**: Dosya boyutu ve benzerlik tespitini kontrol edin  
✅ **Hariç Tutmalar**: İlgisiz dizinleri ve dosyaları atlayın  
✅ **Script Kategorileri**: Scriptleri kullanım desenine göre düzenleyin  
✅ **Esneklik**: Varsayılanlarla başlayın, gerektiğinde özelleştirin  
✅ **Güvenlik**: Geçersiz yapılandırma varsayılanlara geri döner  

**Hızlı başlangıç**:
1. Proje kökünden varsayılan yapılandırmayı kopyalayın
2. Eşikleri proje ihtiyaçlarınıza göre özelleştirin
3. Oluşturulan kod ve üçüncü taraf kütüphaneler için hariç tutmalar ekleyin
4. Üretim scriptlerini açıkça listeleyin
5. Yürütmeden önce dry-run moduyla test edin

**Unutmayın**:
- Muhafazakar başlayın, zamanla sıkılaştırın
- Özelleştirmelerinizi belgeleyin
- Yapılandırmayı düzenli olarak gözden geçirin
- Ekibinizle paylaşın

Daha fazla bilgi için bakınız:
- `scripts/maintenance/README_TR.md` - Bakım scriptleri kılavuzu
- `docs/specs/post-development-cleanup/requirements.md` - Gereksinimler
- `docs/specs/post-development-cleanup/design.md` - Tasarım belgesi
