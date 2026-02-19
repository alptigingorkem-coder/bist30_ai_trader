# Implementation Plan: LightGBM Feature Importance Analizi

## Genel Bakış

Bu implementation plan, SHAP tabanlı feature importance analizi ve otomatik feature selection sisteminin adım adım geliştirilmesini tanımlar. Her görev, önceki görevler üzerine inşa edilir ve kod entegrasyonunu sağlar.

## Görevler

- [x] 1. Temel veri yapılarını ve yapılandırma yönetimini oluştur
  - `scripts/analysis/feature_importance_config.py` dosyasını oluştur
  - `AnalysisConfig` ve `AnalysisResult` dataclass'larını tanımla
  - Varsayılan yapılandırma değerlerini ayarla
  - Yapılandırma validasyonu ekle (negatif değerler, geçersiz tarihler için)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 1.1 Yapılandırma yönetimi için property testleri yaz
  - **Property 15: Yapılandırma Override**
  - **Property 16: Geçersiz Yapılandırma Hata İşleme**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [x] 2. SHAP Analyzer bileşenini implement et
  - [x] 2.1 `scripts/analysis/shap_analyzer.py` dosyasını oluştur
    - `SHAPAnalyzer` sınıfını tanımla
    - `__init__` metodunu implement et (model ve sample_size parametreleri)
    - TreeExplainer oluşturma mantığını ekle
    - _Requirements: 1.1_
  
  - [x] 2.2 SHAP değerleri hesaplama metodunu implement et
    - `compute_importance` metodunu yaz
    - Veri örnekleme mantığını ekle (>1000 satır için)
    - Multi-class SHAP çıktı işleme mantığını ekle
    - Ortalama mutlak SHAP değeri hesaplama
    - Feature importance DataFrame oluşturma ve sıralama
    - _Requirements: 1.2, 1.3, 1.4, 1.5_
  
  - [x] 2.3 Hata işleme ve validasyon ekle
    - SHAP kütüphanesi eksikliği kontrolü
    - Bellek yetersizliği durumunda sample size azaltma
    - Geçersiz SHAP değerleri kontrolü (NaN, Inf)
    - _Requirements: 8.1_

- [ ]* 2.4 SHAP Analyzer için property testleri yaz
  - **Property 1: SHAP Analyzer TreeExplainer Oluşturma**
  - **Property 2: SHAP Değerleri Sayısal Geçerlilik**
  - **Property 3: Büyük Veri Setlerinde Örnekleme**
  - **Property 4: Feature Importance Sıralama**
  - **Property 5: Multi-class SHAP Çıktı İşleme**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 8.1**

- [x] 3. Feature Selector bileşenini implement et
  - [x] 3.1 `scripts/analysis/feature_selector.py` dosyasını oluştur
    - `FeatureSelector` sınıfını tanımla
    - `create_blacklist` metodunu implement et (eşik tabanlı filtreleme)
    - _Requirements: 2.1, 2.5_
  
  - [x] 3.2 Blacklist kaydetme ve yükleme metodlarını ekle
    - `save_blacklist` metodunu implement et (JSON formatı)
    - `load_blacklist` metodunu implement et
    - Dosya yolu yönetimi (`models/saved/feature_blacklist.json`)
    - _Requirements: 2.2, 2.3_
  
  - [x] 3.3 Blacklist validasyonu ekle
    - `validate_blacklist` metodunu implement et
    - %80 sınır kontrolü
    - Uyarı mesajı üretme mantığı
    - _Requirements: 8.2, 8.3_
  
  - [x] 3.4 Loglama ekle
    - Blacklist oluşturma logları
    - Kaydetme işlemi logları (feature sayısı, konum)
    - _Requirements: 2.4_

- [ ]* 3.5 Feature Selector için property testleri yaz
  - **Property 6: Eşik Tabanlı Feature Filtreleme**
  - **Property 7: Blacklist Serileştirme Round-trip**
  - **Property 8: Blacklist Boyut Validasyonu**
  - **Validates: Requirements 2.1, 2.2, 2.5, 8.2, 8.3, 10.5**

- [x] 4. Model Comparator bileşenini implement et
  - [x] 4.1 `scripts/analysis/model_comparator.py` dosyasını oluştur
    - `ModelComparator` sınıfını tanımla
    - `compare` metodunu implement et
    - _Requirements: 3.3, 3.4_
  
  - [x] 4.2 NDCG@3 hesaplama metodunu implement et
    - `_calculate_ndcg` private metodunu yaz
    - Model tahminlerini al
    - Günlük ranking oluştur
    - NDCG@3 metriğini hesapla
    - Metrik validasyonu (0-1 aralığı)
    - _Requirements: 3.3, 8.4_
  
  - [x] 4.3 Model karşılaştırma mantığını tamamla
    - İyileştirme yüzdesi hesaplama
    - Feature sayısı karşılaştırma
    - Test veri tutarlılığı kontrolü
    - Performans düşüşü uyarısı
    - _Requirements: 3.4, 3.5, 8.5_

- [ ]* 4.4 Model Comparator için property testleri yaz
  - **Property 9: Model Feature Sayısı Azalması**
  - **Property 10: NDCG Metrik Hesaplama**
  - **Property 11: İyileştirme Yüzdesi Hesaplama**
  - **Property 12: Performans Düşüşü Uyarısı**
  - **Property 20: Test Verisi Tutarlılığı**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 8.4, 8.5**

- [x] 5. Checkpoint - Temel bileşenlerin testi
  - Tüm testlerin başarılı olduğundan emin ol
  - Kullanıcıya sorular varsa sor

- [x] 6. Visualizer bileşenini implement et
  - [x] 6.1 `scripts/analysis/visualizer.py` dosyasını oluştur
    - `FeatureImportanceVisualizer` sınıfını tanımla
    - Output dizini yönetimi
    - _Requirements: 4.2_
  
  - [x] 6.2 Feature importance bar chart metodunu implement et
    - `plot_top_features` metodunu yaz
    - Top-20 feature seçimi
    - Matplotlib ile bar chart oluşturma
    - PNG formatında kaydetme
    - _Requirements: 4.1_
  
  - [x] 6.3 SHAP summary plot metodunu implement et
    - `plot_shap_summary` metodunu yaz
    - SHAP kütüphanesi summary plot kullanımı
    - Dosya kaydetme
    - _Requirements: 4.3_
  
  - [x] 6.4 Model karşılaştırma grafiği metodunu implement et
    - `plot_comparison` metodunu yaz
    - Baseline vs Optimized karşılaştırma grafiği
    - Metrik ve feature sayısı görselleştirme
    - _Requirements: 3.4_

- [ ]* 6.5 Visualizer için property testleri yaz
  - **Property 13: Görselleştirme Dosya Oluşturma**
  - **Validates: Requirements 4.1, 4.2, 4.3**

- [x] 7. Report Generator bileşenini implement et
  - [x] 7.1 `scripts/analysis/report_generator.py` dosyasını oluştur
    - `ReportGenerator` sınıfını tanımla
    - Markdown template oluştur
    - _Requirements: 4.4_
  
  - [x] 7.2 Rapor oluşturma metodunu implement et
    - `generate_report` metodunu yaz
    - Tüm gerekli bilgileri raporda dahil et (toplam feature, blacklist, NDCG'ler, iyileştirme)
    - Timestamp ile dosya adı oluşturma
    - Markdown formatında kaydetme
    - _Requirements: 4.4, 4.5, 10.1_

- [ ]* 7.3 Report Generator için property testleri yaz
  - **Property 14: Rapor İçerik Tamlığı**
  - **Property 22: Sonuç Persistance Timestamp**
  - **Validates: Requirements 4.4, 4.5, 10.1**

- [x] 8. Ana FeatureImportanceAnalyzer orchestrator'ı implement et
  - [x] 8.1 `scripts/analysis/feature_importance_analyzer.py` dosyasını oluştur
    - `FeatureImportanceAnalyzer` sınıfını tanımla
    - `__init__` metodunu implement et (config ve analysis_config parametreleri)
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 8.2 Veri yükleme metodunu implement et
    - `_load_data` private metodunu yaz
    - DataLoader kullanarak ticker verilerini yükle
    - FeatureEngineer ile feature'ları oluştur
    - Veri birleştirme ve hazırlama
    - Hata toleransı (başarısız ticker'ları atla)
    - _Requirements: 7.3, 7.4, 7.5_
  
  - [x] 8.3 Baseline model eğitim metodunu implement et
    - `_train_baseline_model` private metodunu yaz
    - RankingModel kullanarak tüm feature'larla model eğit
    - Model eğitim logları
    - _Requirements: 3.1_
  
  - [x] 8.4 SHAP hesaplama metodunu implement et
    - `_compute_shap_values` private metodunu yaz
    - SHAPAnalyzer kullanarak importance hesapla
    - Hata işleme (fallback: LightGBM native importance)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 8.5 Blacklist oluşturma metodunu implement et
    - `_create_blacklist` private metodunu yaz
    - FeatureSelector kullanarak blacklist oluştur
    - Blacklist validasyonu
    - _Requirements: 2.1, 2.2, 8.2, 8.3_
  
  - [x] 8.6 Optimized model eğitim metodunu implement et
    - `_train_optimized_model` private metodunu yaz
    - Blacklist uygulanmış RankingModel eğit
    - Feature sayısı karşılaştırma
    - _Requirements: 3.2_
  
  - [x] 8.7 Model karşılaştırma metodunu implement et
    - `_compare_models` private metodunu yaz
    - ModelComparator kullanarak karşılaştır
    - Sonuçları döndür
    - _Requirements: 3.3, 3.4, 3.5_
  
  - [x] 8.8 Sonuç kaydetme metodunu implement et
    - `_save_results` private metodunu yaz
    - Blacklist kaydetme
    - Görselleştirmeler oluşturma
    - Rapor oluşturma
    - Metadata kaydetme
    - Önceki sonuçları koruma
    - _Requirements: 2.2, 2.3, 4.1, 4.2, 4.3, 4.4, 4.5, 10.2, 10.3_
  
  - [x] 8.9 Ana run_analysis metodunu implement et
    - Tüm adımları orchestrate et
    - Kapsamlı loglama (başlangıç, bitiş, her adım, timing)
    - Hata işleme
    - AnalysisResult döndürme
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ]* 8.10 FeatureImportanceAnalyzer için property testleri yaz
  - **Property 19: Çoklu Ticker Hata Toleransı**
  - **Property 21: Kapsamlı Loglama**
  - **Property 23: Metadata Kaydetme**
  - **Property 24: Sonuç Dosyası Korunması**
  - **Property 25: En Son Sonuç Seçimi**
  - **Validates: Requirements 7.3, 7.4, 7.5, 9.1, 9.2, 9.3, 9.4, 9.5, 10.2, 10.3, 10.4**

- [x] 9. Checkpoint - Ana orchestrator testi
  - Tüm testlerin başarılı olduğundan emin ol
  - End-to-end analiz akışını test et
  - Kullanıcıya sorular varsa sor

- [x] 10. RankingModel entegrasyonunu implement et
  - [x] 10.1 `models/ranking_model.py` dosyasını güncelle
    - `__init__` metoduna `blacklist_path` parametresi ekle
    - `_load_blacklist` private metodunu ekle
    - Blacklist yükleme mantığı (varsayılan konum: `models/saved/feature_blacklist.json`)
    - Blacklist yoksa boş liste döndür
    - _Requirements: 6.1, 6.3_
  
  - [x] 10.2 `prepare_data` metodunu güncelle
    - Feature listesinden blacklist'teki feature'ları filtrele
    - Filtreleme logları ekle (kaç feature filtrelendi)
    - _Requirements: 6.2, 6.5_
  
  - [x] 10.3 Blacklist güncelleme desteği ekle
    - Her `prepare_data` çağrısında blacklist'i yeniden yükle
    - Değişiklik logları
    - _Requirements: 6.4_

- [ ]* 10.4 RankingModel entegrasyonu için property testleri yaz
  - **Property 17: RankingModel Blacklist Entegrasyonu**
  - **Property 18: Blacklist Yokluğunda Fallback**
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

- [x] 11. CLI arayüzü ve ana script oluştur
  - [x] 11.1 `scripts/analysis/run_feature_importance.py` dosyasını oluştur
    - Argparse ile CLI parametreleri tanımla
    - `--config`: Yapılandırma dosyası yolu
    - `--threshold`: Feature importance eşiği
    - `--sample-size`: SHAP örnekleme boyutu
    - `--start-date`: Analiz başlangıç tarihi
    - `--end-date`: Analiz bitiş tarihi
    - `--tickers`: Analiz edilecek ticker'lar (virgülle ayrılmış)
    - `--output-dir`: Çıktı dizini
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 11.2 Ana execution mantığını implement et
    - Yapılandırma yükleme
    - FeatureImportanceAnalyzer oluşturma
    - Analiz çalıştırma
    - Sonuçları yazdırma
    - Hata işleme ve kullanıcı dostu mesajlar
    - _Requirements: 9.1, 9.2, 9.5_

- [ ]* 11.3 CLI için integration testleri yaz
  - End-to-end analiz akışı testi
  - Farklı yapılandırmalarla test
  - Hata senaryoları testi

- [x] 12. Dokümantasyon ve örnekler oluştur
  - [x] 12.1 `docs/feature_importance_analysis.md` dosyasını oluştur
    - Kullanım kılavuzu
    - Yapılandırma seçenekleri
    - Örnek komutlar
    - Çıktı açıklamaları
  
  - [x] 12.2 Örnek notebook oluştur
    - `notebooks/feature_importance_example.ipynb`
    - Adım adım analiz örneği
    - Görselleştirme örnekleri
    - Sonuç yorumlama

- [x] 13. Final checkpoint - Tüm sistem testi
  - Tüm unit testlerin başarılı olduğundan emin ol
  - Tüm property testlerin başarılı olduğundan emin ol
  - Gerçek veri ile end-to-end test yap
  - Performans testlerini çalıştır (10,000+ satır)
  - Dokümantasyonu gözden geçir
  - Kullanıcıya sorular varsa sor

## Notlar

- `*` ile işaretli görevler opsiyoneldir ve daha hızlı MVP için atlanabilir
- Her görev, önceki görevlerin tamamlanmasını gerektirir
- Property testler, design dokümanındaki property'leri doğrular
- Unit testler, belirli örnekleri ve edge case'leri test eder
- Checkpoint'ler, artımlı doğrulama sağlar
