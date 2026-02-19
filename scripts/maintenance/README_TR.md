# Bakım Scriptleri - Kullanıcı Kılavuzu

BIST30 AI Trader projesinde kod kalitesi sorunlarını analiz etmek, tespit etmek ve düzeltmek için kapsamlı otomatik araçlar.

## İçindekiler

- [Genel Bakış](#genel-bakış)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Script Referansı](#script-referansı)
  - [1. find_unused_files.py](#1-find_unused_filespy)
  - [2. find_small_files.py](#2-find_small_filespy)
  - [3. find_large_files.py](#3-find_large_filespy)
  - [4. find_duplicate_code.py](#4-find_duplicate_codepy)
  - [5. organize_scripts.py](#5-organize_scriptspy)
  - [6. suggest_merges.py](#6-suggest_mergespy)
  - [7. auto_cleanup.py](#7-auto_cleanuppy)
  - [8. generate_cleanup_report.py](#8-generate_cleanup_reportpy)
- [Yapılandırma](#yapılandırma)
- [Güvenlik Özellikleri](#güvenlik-özellikleri)
- [En İyi Uygulamalar](#en-iyi-uygulamalar)
- [Sorun Giderme](#sorun-giderme)

## Genel Bakış

Bakım scriptleri, kod tabanınızı temiz, düzenli ve sürdürülebilir tutmak için kapsamlı bir araç seti sağlar. Her script, kod kalitesinin belirli bir yönüne odaklanır:

- **Tespit**: Kullanılmayan dosyaları, boyut sorunlarını ve kopyaları tanımlama
- **Analiz**: Script organizasyonunu ve birleştirme fırsatlarını analiz etme
- **Temizlik**: Geçici dosyaların ve yapıtların otomatik kaldırılması
- **Raporlama**: Kapsamlı temizlik raporları oluşturma

## Hızlı Başlangıç

1. **Bağımlılıkları yükleyin**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Kapsamlı bir rapor oluşturun** (önerilen ilk adım):
   ```bash
   python scripts/maintenance/generate_cleanup_report.py --markdown rapor.md
   ```

3. **Belirli sorunları inceleyin**:
   ```bash
   # Kullanılmayan dosyaları bulun
   python scripts/maintenance/find_unused_files.py
   
   # Kopya kodu bulun
   python scripts/maintenance/find_duplicate_code.py
   ```

4. **Temizlik işlemini gerçekleştirin** (her zaman önce dry-run kullanın):
   ```bash
   # Temizliği önizleyin
   python scripts/maintenance/auto_cleanup.py
   
   # Temizliği gerçekleştirin
   python scripts/maintenance/auto_cleanup.py --execute
   ```

## Script Referansı

### 1. find_unused_files.py

**Amaç**: Projede hiçbir yerde import edilmeyen Python dosyalarını tanımlar ve ölü kodu bulmanıza yardımcı olur.

**Kullanım**:
```bash
python scripts/maintenance/find_unused_files.py [SEÇENEKLER]
```

**Seçenekler**:
- `--root YOL` - Taranacak kök dizin (varsayılan: mevcut dizin)
- `--config DOSYA` - Temizlik yapılandırma dosyasının yolu
- `--json DOSYA` - Sonuçları JSON dosyasına aktar

**Örnekler**:

```bash
# Mevcut dizini tara
python scripts/maintenance/find_unused_files.py

# Belirli bir dizini tara
python scripts/maintenance/find_unused_files.py --root scripts/

# Sonuçları JSON'a aktar
python scripts/maintenance/find_unused_files.py --json kullanilmayan_dosyalar.json

# Özel yapılandırma kullan
python scripts/maintenance/find_unused_files.py --config yapilandirmam.yaml
```

**Çıktı**:
- Satır sayıları ve son değişiklik tarihleriyle kullanılmayan dosyaların listesi
- Her kullanılmayan dosyada tanımlanan fonksiyonlar ve sınıflar
- Projedeki kullanılmayan dosyaların yüzdesi
- Özel dosyalar (\_\_init\_\_.py, \_\_main\_\_.py, setup.py) otomatik olarak hariç tutulur

**Ne zaman kullanılır**:
- Büyük yeniden yapılandırmadan sonra yetim dosyaları tanımlamak için
- Sürümlerden önce ölü kodu kaldırmak için
- Kod incelemelerinde proje temizliğini değerlendirmek için

**Güvenlik notları**:
- Dosyalar "kullanılmıyor" olabilir ancak yine de bir amaca hizmet edebilir (örn. bağımsız scriptler)
- Dosyaları silmeden önce her zaman listeyi gözden geçirin
- Dosyaların dokümantasyonda veya shell scriptlerinde referans edilip edilmediğini kontrol edin

---

### 2. find_small_files.py

**Amaç**: 100 satırdan az kod içeren dosyaları tanımlar (yapılandırılabilir). Küçük dosyalar, kod bütünlüğünü iyileştirmek için birleştirme adayı olabilir.

**Kullanım**:
```bash
python scripts/maintenance/find_small_files.py [SEÇENEKLER]
```

**Seçenekler**:
- `--root YOL` - Taranacak kök dizin (varsayılan: mevcut dizin)
- `--config DOSYA` - Temizlik yapılandırma dosyasının yolu
- `--json DOSYA` - Sonuçları JSON dosyasına aktar
- `--threshold N` - Küçük dosya eşiği (satır cinsinden, yapılandırmayı geçersiz kılar)

**Örnekler**:

```bash
# Varsayılan eşikle tara (100 satır)
python scripts/maintenance/find_small_files.py

# Özel eşik kullan
python scripts/maintenance/find_small_files.py --threshold 150

# Belirli dizini tara ve aktar
python scripts/maintenance/find_small_files.py --root src/ --json kucuk_dosyalar.json
```

**Çıktı**:
- Dizine göre gruplandırılmış küçük dosyalar
- En küçükten en büyüğe sıralanmış dosya boyutları
- Dizin başına toplam dosya ve satır sayısı
- Dosya boyutu dağılım histogramı
- Birden fazla küçük dosyası olan dizinler (birleştirme adayları)

**Ne zaman kullanılır**:
- Kod konsolidasyonu planlarken
- Parçalanmış modülleri tanımlamak için
- Birleştirme önermeden önce (suggest_merges.py ile birlikte kullanın)

**En iyi uygulamalar**:
- Tüm küçük dosyalar birleştirilmemelidir (örn. \_\_init\_\_.py)
- Sadece dosya boyutunu değil, fonksiyonel bütünlüğü de göz önünde bulundurun
- Akıllı birleştirme önerileri için suggest_merges.py kullanın

---

### 3. find_large_files.py

**Amaç**: 500 satırdan fazla kod içeren dosyaları tanımlar (yapılandırılabilir). Büyük dosyalar, sürdürülebilirliği iyileştirmek için bölme adayı olabilir.

**Kullanım**:
```bash
python scripts/maintenance/find_large_files.py [SEÇENEKLER]
```

**Seçenekler**:
- `--root YOL` - Taranacak kök dizin (varsayılan: mevcut dizin)
- `--config DOSYA` - Temizlik yapılandırma dosyasının yolu
- `--json DOSYA` - Sonuçları JSON dosyasına aktar
- `--threshold N` - Büyük dosya eşiği (satır cinsinden, yapılandırmayı geçersiz kılar)

**Örnekler**:

```bash
# Varsayılan eşikle tara (500 satır)
python scripts/maintenance/find_large_files.py

# Özel eşik kullan
python scripts/maintenance/find_large_files.py --threshold 600

# Belirli dizini tara
python scripts/maintenance/find_large_files.py --root src/

# Bölme önerileriyle aktar
python scripts/maintenance/find_large_files.py --json buyuk_dosyalar.json
```

**Çıktı**:
- Boyuta göre sıralanmış büyük dosyalar (en büyükten başlayarak)
- Sınıf/fonksiyon sınırlarına dayalı önerilen bölme noktaları (satır numaraları)
- Bölmeden sonra yaklaşık segment boyutları
- Dosya yapısı özeti (sınıflar ve fonksiyonlar)
- Dosya boyutu dağılım histogramı

**Ne zaman kullanılır**:
- Dosyaların bakımı zorlaştığında
- Yeniden yapılandırma planlaması sırasında
- Kod gezinilebilirliğini iyileştirmek için

**Bölme noktası önerileri**:
- Sınıf ve fonksiyon sınırlarına dayanır
- Mantıksal bütünlüğü göz önünde bulundurur
- Dengeli segment boyutları hedefler
- Bölmeden önce manuel inceleme önerilir

---

### 4. find_duplicate_code.py

**Amaç**: Birden fazla dosyada özdeş veya neredeyse özdeş uygulamalara sahip fonksiyonları tanımlar. Fazlalığı ortadan kaldırmaya ve paylaşılan yardımcı programlar oluşturmaya yardımcı olur.

**Kullanım**:
```bash
python scripts/maintenance/find_duplicate_code.py [SEÇENEKLER]
```

**Seçenekler**:
- `--root YOL` - Taranacak kök dizin (varsayılan: mevcut dizin)
- `--config DOSYA` - Temizlik yapılandırma dosyasının yolu
- `--json DOSYA` - Sonuçları JSON dosyasına aktar
- `--threshold FLOAT` - Benzerlik eşiği 0.0-1.0 (varsayılan yapılandırmadan: 0.85)

**Örnekler**:

```bash
# Varsayılan eşikle tara (%85 benzerlik)
python scripts/maintenance/find_duplicate_code.py

# Daha sıkı eşik kullan (%95 benzerlik)
python scripts/maintenance/find_duplicate_code.py --threshold 0.95

# Daha gevşek eşik kullan (%70 benzerlik)
python scripts/maintenance/find_duplicate_code.py --threshold 0.70

# Belirli dizini tara
python scripts/maintenance/find_duplicate_code.py --root scripts/

# Sonuçları aktar
python scripts/maintenance/find_duplicate_code.py --json kopyalar.json
```

**Çıktı**:
- Fonksiyon adlarıyla kopya grupları
- Her grup için benzerlik yüzdesi
- Tüm dosya konumları ve satır numaraları
- Karşılaştırma için kod parçacıkları
- Önerilen paylaşılan yardımcı program konumu

**Nasıl çalışır**:
- Python dosyalarından tüm fonksiyonları çıkarır
- Kodu normalleştirir (boşlukları ve yorumları kaldırır)
- Dizi eşleştirme kullanarak benzerliği hesaplar
- Benzerlik eşiğinin üzerindeki fonksiyonları gruplar

**Ne zaman kullanılır**:
- Kopyala-yapıştır kodlama oturumlarından sonra
- Yardımcı programları birleştirmek için yeniden yapılandırma sırasında
- Paylaşılan kütüphaneler oluşturmadan önce

**En iyi uygulamalar**:
- Kodu taşımadan önce önerilen konumları gözden geçirin
- Paylaşılan fonksiyonlar için bir utils modülü oluşturmayı düşünün
- Birleştirmeden sonra tüm referansları güncelleyin
- Birleştirilmiş fonksiyon için testler ekleyin

---

### 5. organize_scripts.py

**Amaç**: Scriptleri kullanım desenine göre kategorize eder (üretim, analiz, bakım, entegrasyon testleri) ve uygun alt dizinlere yeniden düzenleme önerir.

**Kullanım**:
```bash
python scripts/maintenance/organize_scripts.py [SEÇENEKLER]
```

**Seçenekler**:
- `--root YOL` - Kök scriptler dizini (varsayılan: scripts/)
- `--config DOSYA` - Temizlik yapılandırma dosyasının yolu
- `--json DOSYA` - Sonuçları JSON dosyasına aktar
- `--execute` - Yeniden düzenlemeyi gerçekleştir (varsayılan dry-run'dır)

**Örnekler**:

```bash
# Organizasyonu analiz et (dry-run)
python scripts/maintenance/organize_scripts.py

# Belirli dizini analiz et
python scripts/maintenance/organize_scripts.py --root scripts/

# Yeniden düzenleme planını aktar
python scripts/maintenance/organize_scripts.py --json organizasyon.json

# Yeniden düzenlemeyi gerçekleştir (dosyaları taşır)
python scripts/maintenance/organize_scripts.py --execute
```

**Çıktı**:
- Sayılarla script kategorileri
- Her kategori için hedef dizinler
- Yeniden düzenleme planı (kaynak → hedef)
- Bozuk import uyarıları
- Yürütmeden önce onay istemi

**Kategoriler**:
- **Üretim**: Üretim/geliştirme iş akışlarında düzenli olarak kullanılan scriptler
- **Analiz**: Seyrek analiz veya hata ayıklama için scriptler
- **Bakım**: Tek seferlik veya seyrek kurulum/geçiş scriptleri
- **Entegrasyon Testleri**: Bileşenler arası entegrasyonu test eden scriptler

**Kategorizasyon mantığı**:
1. Üretim scriptleri: Shell scriptlerinde, dokümanlarda referans edilen veya yapılandırmada açıkça listelenen
2. Analiz scriptleri: Anahtar kelimeler içerir (analyze, check, inspect, compare, evaluate)
3. Bakım scriptleri: Anahtar kelimeler içerir (migrate, update, fix, clean, convert)
4. Entegrasyon testleri: Anahtar kelimeler içerir (test, verify, validate, debug)

**Ne zaman kullanılır**:
- Scriptler dizini karmaşıklaştığında
- Birçok yeni script ekledikten sonra
- Proje organizasyonunu iyileştirmek için

**⚠️ UYARI**:
- Her zaman önce dry-run modunda çalıştırın
- Bozuk import uyarılarını dikkatlice gözden geçirin
- Yeniden düzenlemeden sonra importları güncelleyin
- Dosyaları taşıdıktan sonra kapsamlı test yapın
- --no-git-check'i yalnızca ne yaptığınızı biliyorsanız kullanmayı düşünün

---

### 6. suggest_merges.py

**Amaç**: Küçük ilgili dosyaları analiz eder ve fonksiyonel benzerliğe dayalı birleştirme fırsatları önerir. Kod bütünlüğünü iyileştirmeye yardımcı olur.

**Kullanım**:
```bash
python scripts/maintenance/suggest_merges.py [SEÇENEKLER]
```

**Seçenekler**:
- `--root YOL` - Taranacak kök dizin (varsayılan: mevcut dizin)
- `--config DOSYA` - Temizlik yapılandırma dosyasının yolu
- `--json DOSYA` - Sonuçları JSON dosyasına aktar
- `--threshold FLOAT` - Benzerlik eşiği 0.0-1.0 (varsayılan: 0.5)

**Örnekler**:

```bash
# Varsayılan eşikle birleştirme öner (%50 benzerlik)
python scripts/maintenance/suggest_merges.py

# Daha sıkı eşik kullan (%70 benzerlik)
python scripts/maintenance/suggest_merges.py --threshold 0.7

# Daha gevşek eşik kullan (%30 benzerlik)
python scripts/maintenance/suggest_merges.py --threshold 0.3

# Belirli dizini tara
python scripts/maintenance/suggest_merges.py --root src/utils/

# Önerileri aktar
python scripts/maintenance/suggest_merges.py --json birlestirme_onerileri.json
```

**Çıktı**:
- Fonksiyonel benzerlik skorlarıyla birleştirme önerileri
- Kaynak dosyalar ve tahmini birleştirilmiş boyut
- Hedef dosya yolu
- Gerekli import güncellemeleri
- Potansiyel dosya sayısı azaltması

**Fonksiyonel benzerlik hesaplaması**:
- Import desenleri (%40): Paylaşılan importlar ilgili işlevselliği gösterir
- Sınıf hiyerarşileri (%30): Kalıtım ilişkileri
- Fonksiyon adlandırma (%30): Benzer önekler/sonekler

**Ne zaman kullanılır**:
- Küçük dosyaları tanımladıktan sonra (önce find_small_files.py kullanın)
- Kod konsolidasyonu planlarken
- Modül bütünlüğünü iyileştirmek için

**En iyi uygulamalar**:
- Yalnızca yüksek fonksiyonel benzerliğe sahip dosyaları birleştirin (>%60)
- Birleştirilmiş dosya boyutunun 500 satırın altında kaldığını doğrulayın
- Birleştirmeden sonra tüm importları güncelleyin
- Birleştirmeden sonra testleri çalıştırın
- Bir kaynak dosya kullanmak yerine yeni bir modül adı oluşturmayı düşünün

---

### 7. auto_cleanup.py

**Amaç**: Geçici dosyaların, \_\_pycache\_\_ dizinlerinin, eski log dosyalarının, boş \_\_init\_\_.py dosyalarının ve diğer yapıtların otomatik temizliği.

**Kullanım**:
```bash
python scripts/maintenance/auto_cleanup.py [SEÇENEKLER]
```

**Seçenekler**:
- `--root YOL` - Taranacak kök dizin (varsayılan: mevcut dizin)
- `--config DOSYA` - Temizlik yapılandırma dosyasının yolu
- `--execute` - Temizliği gerçekleştir (varsayılan dry-run'dır)
- `--json DOSYA` - Sonuçları JSON dosyasına aktar
- `--no-git-check` - Git güvenlik kontrollerini atla (önerilmez)

**Örnekler**:

```bash
# Dry-run modu (temizliği önizle)
python scripts/maintenance/auto_cleanup.py

# Temizliği gerçekleştir (onay gerektirir)
python scripts/maintenance/auto_cleanup.py --execute

# Belirli dizini tara
python scripts/maintenance/auto_cleanup.py --root scripts/

# Temizlik planını aktar
python scripts/maintenance/auto_cleanup.py --json temizlik_plani.json

# Git kontrollerini atla (önerilmez)
python scripts/maintenance/auto_cleanup.py --execute --no-git-check
```

**Neyi temizler**:
- \_\_pycache\_\_ dizinleri ve .pyc dosyaları
- Saklama süresinden eski log dosyaları (varsayılan: 30 gün)
- Başka Python dosyası olmayan dizinlerdeki boş \_\_init\_\_.py dosyaları
- Geçici dosyalar (*.tmp, *.bak, *~, .DS_Store)

**Çıktı**:
- Türe göre gruplandırılmış işlemler
- Boşaltılacak dosya boyutları
- Yürütmeden önce onay istemi
- Git branch oluşturma ve commit mesajları

**Güvenlik özellikleri**:
- Varsayılan olarak dry-run modu
- Git deposu kontrolü (temiz çalışma dizini gerektirir)
- Yürütmeden önce zaman damgalı temizlik branch'i oluşturur
- Dosyaları silmeden önce onay istemi
- Tüm işlemler zaman damgalarıyla kaydedilir
- Geri alma talimatları sağlanır

**Ne zaman kullanılır**:
- Sürümlerden önce yapıtları temizlemek için
- Geliştirme sprintlerinden sonra
- Disk alanı azaldığında
- Düzenli bakımın bir parçası olarak

**⚠️ KRİTİK UYARILAR**:
- HER ZAMAN önce dry-run modunda çalıştırın
- Silinecek dosyaların listesini gözden geçirin
- Git çalışma dizininin temiz olduğundan emin olun
- Yürütmeden önce önemli dosyaları yedekleyin
- Kesinlikle gerekli olmadıkça --no-git-check kullanmayın
- Temizlikten sonra kapsamlı test yapın

**Geri alma**:
```bash
# Temizlik gerçekleştirildiyse, şununla geri alın:
git checkout <orijinal-branch>
git branch -D <temizlik-branch>
```

---

### 8. generate_cleanup_report.py

**Amaç**: Tüm analiz sonuçlarını önceliklendirilmiş eylem öğeleriyle tek bir belgede toplayan kapsamlı bir temizlik raporu oluşturur.

**Kullanım**:
```bash
python scripts/maintenance/generate_cleanup_report.py [SEÇENEKLER]
```

**Seçenekler**:
- `--root YOL` - Analiz edilecek kök dizin (varsayılan: mevcut dizin)
- `--config DOSYA` - Temizlik yapılandırma dosyasının yolu
- `--markdown DOSYA` - Raporu Markdown dosyasına aktar
- `--json DOSYA` - Raporu JSON dosyasına aktar
- `--lang DIL` - Rapor dili: en (İngilizce) veya tr (Türkçe)
- `--scripts-dir YOL` - Organizasyon analizi için scriptler dizini
- `--verbose` - Ayrıntılı ilerleme bilgisi göster

**Örnekler**:

```bash
# Mevcut dizin için rapor oluştur
python scripts/maintenance/generate_cleanup_report.py

# Markdown raporu oluştur
python scripts/maintenance/generate_cleanup_report.py --markdown temizlik_raporu.md

# JSON raporu oluştur
python scripts/maintenance/generate_cleanup_report.py --json temizlik_raporu.json

# Her iki formatı da oluştur
python scripts/maintenance/generate_cleanup_report.py --markdown rapor.md --json rapor.json

# Türkçe rapor oluştur
python scripts/maintenance/generate_cleanup_report.py --lang tr --markdown rapor.md

# Ayrıntılı çıktıyla belirli dizini analiz et
python scripts/maintenance/generate_cleanup_report.py --root /yol/proje --verbose

# Özel scriptler dizini
python scripts/maintenance/generate_cleanup_report.py --scripts-dir ozel_scriptler/
```

**Rapor bölümleri**:
1. **Özet**: Toplam dosyalar, ortalama boyut, sorun sayıları
2. **Kullanılmayan Dosyalar**: Hiçbir yerde import edilmeyen dosyaların listesi
3. **Dosya Boyutları**: Küçük ve büyük dosyalar analizi
4. **Kopya Kod**: Kopya fonksiyon grupları
5. **Script Organizasyonu**: Mevcut vs. önerilen yapı
6. **Birleştirme Önerileri**: Dosyaları birleştirme fırsatları
7. **Tahmini İyileştirmeler**: Temizliğin öngörülen etkisi
8. **Önceliklendirilmiş Eylemler**: Etki ve çabaya göre sıralanmış

**Çıktı formatları**:
- **Konsol**: Temel bulgularla biçimlendirilmiş özet
- **Markdown**: Tüm ayrıntılarla kapsamlı rapor
- **JSON**: Otomasyon için makine tarafından okunabilir format

**Tahmini iyileştirmeler**:
- Dosya sayısı azaltma yüzdesi
- Ortalama dosya boyutu artış yüzdesi
- Sürdürülebilirlik iyileştirme skoru (0-100)

**Önceliklendirilmiş eylemler** (etki/çabaya göre sıralanmış):
1. Kullanılmayan dosyaları kaldır (yüksek etki, düşük çaba)
2. Kopya kodu ortadan kaldır (yüksek etki, orta çaba)
3. Küçük dosyaları birleştir (orta etki, orta çaba)
4. Büyük dosyaları böl (orta etki, yüksek çaba)
5. Scriptleri yeniden düzenle (düşük etki, düşük çaba)

**Ne zaman kullanılır**:
- Temizlik planlamasında ilk adım olarak
- Büyük yeniden yapılandırmadan önce
- Proje sağlığı değerlendirmeleri için
- Zaman içinde temizlik ilerlemesini takip etmek için
- Kod kalitesi hakkında ekip tartışmaları için

**En iyi uygulamalar**:
- Düzenli olarak raporlar oluşturun (haftalık/aylık)
- İyileştirmeleri takip etmek için raporları zaman içinde karşılaştırın
- Raporları ekiple paylaşın
- Sprint planlaması için girdi olarak kullanın
- Hem Markdown'a (insanlar için) hem de JSON'a (otomasyon için) aktarın

**Türkçe dil desteği**:
- Bölüm başlıkları çevrilmiş
- Eylem öğeleri çevrilmiş
- Öneriler çevrilmiş
- Aynı yapı ve veri korunur

---

## Yapılandırma

Temizlik sistemi, proje kökündeki `cleanup_config.yaml` aracılığıyla yapılandırılır.

**Yapılandırma dosyası yapısı**:

```yaml
thresholds:
  small_file_lines: 100        # Bundan küçük dosyalar "küçük"tür
  large_file_lines: 500        # Bundan büyük dosyalar "büyük"tür
  log_retention_days: 30       # Logları bu kadar gün sakla
  duplicate_similarity: 0.85   # Kopyalar için benzerlik eşiği (0.0-1.0)

exclusions:
  directories:                 # Analizden hariç tutulacak dizinler
    - .venv
    - __pycache__
    - .git
    - node_modules
    - .pytest_cache
  patterns:                    # Hariç tutulacak dosya desenleri
    - "test_*.py"
    - "*_test.py"
    - "__init__.py"
    - "setup.py"

script_categories:
  production:                  # Üretim scriptlerini açıkça listele
    - train_models.py
    - run_backtest.py
    - daily_run.py
    - paper_trading_runner.py
  
  analysis_keywords:           # Analiz scriptleri için anahtar kelimeler
    - analyze
    - check
    - inspect
    - compare
    - evaluate
  
  maintenance_keywords:        # Bakım scriptleri için anahtar kelimeler
    - migrate
    - update
    - fix
    - clean
    - convert
  
  test_keywords:              # Test scriptleri için anahtar kelimeler
    - test
    - verify
    - validate
    - debug
```

**Özel yapılandırma kullanma**:

```bash
# Tüm scriptler --config seçeneğini destekler
python scripts/maintenance/find_small_files.py --config yapilandirmam.yaml
python scripts/maintenance/generate_cleanup_report.py --config yapilandirmam.yaml
```

Daha fazla bilgi için `docs/cleanup_config_guide_TR.md` dosyasına bakın.

---

## Güvenlik Özellikleri

Tüm temizlik işlemleri birden fazla güvenlik katmanı içerir:

### 1. Dry-Run Modu (Varsayılan)
- Tüm yıkıcı işlemler varsayılan olarak dry-run modundadır
- Yürütmeden önce değişiklikleri önizleyin
- Dry-run modunda hiçbir dosya değiştirilmez veya silinmez
- Gerçek işlemleri gerçekleştirmek için `--execute` bayrağını kullanın

### 2. Git Entegrasyonu
- Yürütmeden önce temiz çalışma dizinini kontrol eder
- Commit edilmemiş değişiklikler varsa devam etmeyi reddeder
- Zaman damgalı temizlik branch'i oluşturur (cleanup-YYYYMMDD-HHMMSS)
- Değişiklikleri açıklayıcı mesajlarla aşamalı olarak commit eder
- Geri alma talimatları sağlar

### 3. Onay İstemleri
- Dosyaları silmeden önce açık onay gerektirir
- Etkilenecek dosyaların listesini gösterir
- Herhangi bir noktada iptal etmeye izin verir

### 4. Aşamalı İşlemler
- Değişiklikler mantıksal gruplarda commit edilir
- Neyin değiştiğini tanımlamak kolaydır
- Gerekirse geri almayı basitleştirir

### 5. Kapsamlı Kayıt Tutma
- Tüm işlemler zaman damgalarıyla kaydedilir
- Dosya yolları ve nedenler kaydedilir
- Hatalar bağlamla birlikte kaydedilir

### 6. Geri Alma Desteği
```bash
# Temizlik işlemlerini geri al
git checkout <orijinal-branch>
git branch -D <temizlik-branch>

# Script yeniden düzenlemesini geri al
git checkout <orijinal-branch>
git branch -D <yeniden-duzenleme-branch>
```

---

## En İyi Uygulamalar

### Genel İş Akışı

1. **Bir raporla başlayın**:
   ```bash
   python scripts/maintenance/generate_cleanup_report.py --markdown rapor.md
   ```

2. **Belirli sorunları inceleyin**:
   ```bash
   python scripts/maintenance/find_unused_files.py
   python scripts/maintenance/find_duplicate_code.py
   ```

3. **Temizliğinizi planlayın**:
   - Rapordaki önceliklendirilmiş eylemleri gözden geçirin
   - Hızlı kazanımları tanımlayın (kullanılmayan dosyalar, kopyalar)
   - Daha büyük yeniden yapılandırmayı planlayın (birleştirmeler, bölmeler)

4. **Aşamalı olarak yürütün**:
   - Düşük riskli işlemlerle başlayın (auto_cleanup)
   - Orta riskli işlemlere geçin (kullanılmayan dosyaları kaldırma)
   - Yüksek riskli işlemlerle bitirin (birleştirmeler, yeniden düzenleme)

5. **Kapsamlı test yapın**:
   - Her temizlik işleminden sonra testleri çalıştırın
   - İşlevselliğin değişmediğini doğrulayın
   - Bozuk importları kontrol edin

### Sıklık Önerileri

- **Günlük**: Otomatik temizlik (dry-run)
- **Haftalık**: Temizlik raporu oluştur
- **Aylık**: Rapor bulgularını incele ve harekete geç
- **Üç aylık**: Büyük yeniden yapılandırma (birleştirmeler, bölmeler, yeniden düzenleme)
- **Sürümlerden önce**: Tam temizlik döngüsü

---

## Sorun Giderme

### Yaygın Sorunlar

**Sorun**: "Hata: Dizin bulunamadı"
```bash
# Çözüm: Yolun var olduğunu doğrulayın
ls -la /yol/dizin
# Veya mutlak yol kullanın
python scripts/maintenance/find_unused_files.py --root /mutlak/yol
```

**Sorun**: "Hata: Commit edilmemiş değişiklikler tespit edildi"
```bash
# Çözüm: Değişiklikleri commit edin veya stash'leyin
git status
git add .
git commit -m "Temizlikten önce çalışmayı kaydet"
# Veya stash
git stash
```

**Sorun**: "Hata: Eşik pozitif olmalıdır"
```bash
# Çözüm: Geçerli eşik değerleri kullanın
python scripts/maintenance/find_small_files.py --threshold 100  # Geçerli
python scripts/maintenance/find_small_files.py --threshold -50  # Geçersiz
```

**Sorun**: "Uyarı: Bozuk importlar tespit edildi"
```bash
# Çözüm: Yeniden düzenlemeden sonra importları inceleyin ve güncelleyin
# 1. Çıktıdan bozuk importları not edin
# 2. Etkilenen dosyalardaki import ifadelerini güncelleyin
# 3. Doğrulamak için testleri çalıştırın
pytest
```

**Sorun**: "'scripts.maintenance.core' modülü bulunamadı"
```bash
# Çözüm: Proje kökünden çalıştırın
cd /yol/proje/kok
python scripts/maintenance/find_unused_files.py
```

### Yardım Alma

**Script yardımını görüntüle**:
```bash
python scripts/maintenance/find_unused_files.py --help
python scripts/maintenance/auto_cleanup.py --help
```

**Yapılandırmayı kontrol et**:
```bash
# Yapılandırmanın geçerli olduğunu doğrulayın
python -c "from scripts.maintenance.core import CleanupConfig; c = CleanupConfig(); print('Yapılandırma OK')"
```

**Git durumunu doğrula**:
```bash
git status
git log --oneline -5
```

---

## Özet

Bakım scriptleri, kod tabanınızı temiz ve sürdürülebilir tutmak için kapsamlı bir araç seti sağlar. Önemli noktalar:

✅ **Her zaman bir raporla başlayın** mevcut durumu anlamak için
✅ **Dry-run modunu kullanın** yıkıcı işlemleri yürütmeden önce
✅ **Dikkatlice inceleyin** dosyaları silmeden veya taşımadan önce
✅ **Kapsamlı test yapın** her temizlik işleminden sonra
✅ **Aşamalı commit edin** geri almayı kolaylaştırmak için
✅ **Düzenli çalıştırın** teknik borç birikimini önlemek için

Sorular veya sorunlar için tasarım belgesine bakın veya scriptleri `--help` bayrağıyla çalıştırın.
