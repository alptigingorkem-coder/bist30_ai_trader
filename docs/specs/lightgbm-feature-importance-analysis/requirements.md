# Gereksinim Dokümanı: LightGBM Feature Importance Analizi

## Giriş

Bu özellik, BIST30 AI Trader sisteminde kullanılan LightGBM modelinin performansını artırmak için SHAP (SHapley Additive exPlanations) değerlerine dayalı kapsamlı bir feature importance analizi ve feature selection süreci sağlar. Mevcut NDCG@3 metriğini 0.6217'den 0.65'e yükseltmeyi hedefler.

Sistem, ayırt edici özellikleri (discriminative features) belirleyecek, düşük katkılı özellikleri filtreleyecek ve model performansını optimize edecektir. Analiz sonuçları görselleştirilecek ve otomatik olarak model eğitim sürecine entegre edilecektir.

## Sözlük

- **System**: LightGBM Feature Importance Analysis modülü
- **SHAP_Analyzer**: SHAP değerlerini hesaplayan ve analiz eden bileşen
- **Feature_Selector**: Feature selection işlemlerini gerçekleştiren bileşen
- **Model_Trainer**: LightGBM modelini eğiten bileşen
- **Visualizer**: Analiz sonuçlarını görselleştiren bileşen
- **Configuration_Manager**: Analiz parametrelerini yöneten bileşen
- **NDCG@3**: Normalized Discounted Cumulative Gain at position 3 - ranking kalitesi metriği
- **SHAP_Value**: Bir feature'ın model tahminindeki katkısını gösteren değer
- **Feature_Importance**: Bir feature'ın model performansına olan etkisi
- **Discriminative_Feature**: Hedef değişkeni ayırt etmede yüksek katkı sağlayan özellik
- **Blacklist**: Model eğitiminden çıkarılacak düşük katkılı feature'ların listesi
- **Baseline_Model**: Feature selection öncesi eğitilmiş referans model
- **Optimized_Model**: Feature selection sonrası eğitilmiş optimize edilmiş model

## Gereksinimler

### Gereksinim 1: SHAP Tabanlı Feature Importance Hesaplama

**Kullanıcı Hikayesi:** Bir veri bilimcisi olarak, her feature'ın model tahminlerine olan katkısını anlamak istiyorum, böylece hangi özelliklerin gerçekten değerli olduğunu görebilirim.

#### Kabul Kriterleri

1. WHEN bir LightGBM modeli sağlandığında, THE SHAP_Analyzer SHALL model için TreeExplainer oluşturmalıdır
2. WHEN SHAP değerleri hesaplandığında, THE SHAP_Analyzer SHALL her feature için ortalama mutlak SHAP değerini hesaplamalıdır
3. WHEN veri seti 1000 satırdan fazla olduğunda, THE SHAP_Analyzer SHALL hesaplama hızı için rastgele örnekleme yapmalıdır
4. WHEN SHAP hesaplaması tamamlandığında, THE System SHALL feature'ları importance değerine göre azalan sırada sıralamalıdır
5. THE SHAP_Analyzer SHALL çok sınıflı (multi-class) SHAP çıktılarını doğru şekilde işlemelidir

### Gereksinim 2: Feature Selection ve Blacklist Oluşturma

**Kullanıcı Hikayesi:** Bir model mühendisi olarak, düşük katkılı feature'ları otomatik olarak filtrelemek istiyorum, böylece model daha hızlı ve daha etkili olur.

#### Kabul Kriterleri

1. WHEN feature importance değerleri hesaplandığında, THE Feature_Selector SHALL yapılandırılabilir bir eşik değeri kullanarak düşük katkılı feature'ları belirlemelidir
2. WHEN blacklist oluşturulduğunda, THE Feature_Selector SHALL belirlenen düşük katkılı feature'ları JSON formatında kaydetmelidir
3. THE Feature_Selector SHALL blacklist dosyasını `models/saved/feature_blacklist.json` konumuna kaydetmelidir
4. WHEN blacklist kaydedildiğinde, THE System SHALL kaydedilen feature sayısını ve konumunu loglamalıdır
5. WHERE kullanıcı özel bir eşik değeri belirttiğinde, THE Feature_Selector SHALL varsayılan eşik yerine kullanıcı eşiğini kullanmalıdır

### Gereksinim 3: Baseline ve Optimized Model Karşılaştırması

**Kullanıcı Hikayesi:** Bir performans analisti olarak, feature selection'ın model performansına etkisini ölçmek istiyorum, böylece iyileştirmenin değerini kanıtlayabilirim.

#### Kabul Kriterleri

1. WHEN analiz başlatıldığında, THE Model_Trainer SHALL tüm feature'larla bir baseline model eğitmelidir
2. WHEN baseline model eğitildikten sonra, THE Model_Trainer SHALL blacklist uygulanmış feature'larla optimized model eğitmelidir
3. WHEN her iki model de eğitildikten sonra, THE System SHALL NDCG@3 metriğini her iki model için hesaplamalıdır
4. THE System SHALL baseline ve optimized model arasındaki NDCG@3 farkını yüzde olarak raporlamalıdır
5. WHEN optimized model baseline'dan daha kötü performans gösterdiğinde, THE System SHALL bir uyarı loglamalıdır

### Gereksinim 4: Görselleştirme ve Raporlama

**Kullanıcı Hikayesi:** Bir veri bilimcisi olarak, feature importance sonuçlarını görsel olarak incelemek istiyorum, böylece bulguları hızlıca anlayabilir ve paylaşabilirim.

#### Kabul Kriterleri

1. WHEN SHAP analizi tamamlandığında, THE Visualizer SHALL top-20 feature'ı gösteren bir bar chart oluşturmalıdır
2. WHEN görselleştirme oluşturulduğunda, THE Visualizer SHALL grafiği `reports/feature_importance/` dizinine PNG formatında kaydetmelidir
3. THE Visualizer SHALL SHAP summary plot oluşturmalıdır
4. WHEN analiz tamamlandığında, THE System SHALL özet bir rapor dosyası (Markdown formatında) oluşturmalıdır
5. THE System SHALL raporda şu bilgileri içermelidir: toplam feature sayısı, blacklist'e alınan feature sayısı, baseline NDCG@3, optimized NDCG@3, iyileştirme yüzdesi

### Gereksinim 5: Yapılandırma ve Parametrizasyon

**Kullanıcı Hikayesi:** Bir sistem yöneticisi olarak, analiz parametrelerini kolayca yapılandırmak istiyorum, böylece farklı senaryoları test edebilirim.

#### Kabul Kriterleri

1. THE Configuration_Manager SHALL SHAP örnekleme boyutunu yapılandırılabilir hale getirmelidir
2. THE Configuration_Manager SHALL feature importance eşik değerini yapılandırılabilir hale getirmelidir
3. THE Configuration_Manager SHALL analiz tarih aralığını yapılandırılabilir hale getirmelidir
4. WHERE yapılandırma dosyası mevcut değilse, THE System SHALL varsayılan değerlerle çalışmalıdır
5. WHEN geçersiz bir yapılandırma sağlandığında, THE System SHALL açıklayıcı bir hata mesajı döndürmelidir

### Gereksinim 6: Model Entegrasyonu ve Otomatik Uygulama

**Kullanıcı Hikayesi:** Bir MLOps mühendisi olarak, feature selection sonuçlarının otomatik olarak model eğitim pipeline'ına entegre edilmesini istiyorum, böylece manuel müdahale gerekmez.

#### Kabul Kriterleri

1. WHEN blacklist oluşturulduğunda, THE System SHALL blacklist'i RankingModel sınıfının okuyabileceği formatta kaydetmelidir
2. WHEN RankingModel eğitim için veri hazırladığında, THE System SHALL blacklist'teki feature'ları otomatik olarak filtrelemelidir
3. THE System SHALL blacklist dosyasının varlığını kontrol etmeli ve yoksa tüm feature'ları kullanmalıdır
4. WHEN blacklist güncellendiğinde, THE System SHALL değişiklikleri bir sonraki model eğitiminde otomatik olarak uygulamalıdır
5. THE System SHALL blacklist uygulama durumunu (kaç feature filtrelendi) loglama yapmalıdır

### Gereksinim 7: Performans ve Ölçeklenebilirlik

**Kullanıcı Hikayesi:** Bir sistem mimarı olarak, analizin büyük veri setlerinde de verimli çalışmasını istiyorum, böylece üretim ortamında kullanılabilir.

#### Kabul Kriterleri

1. WHEN veri seti 10,000 satırdan fazla olduğunda, THE SHAP_Analyzer SHALL hesaplama süresini 5 dakikanın altında tutmalıdır
2. THE System SHALL bellek kullanımını veri seti boyutunun 3 katını geçmeyecek şekilde yönetmelidir
3. WHEN çoklu ticker analizi yapıldığında, THE System SHALL her ticker için ilerleme durumunu loglamalıdır
4. THE System SHALL başarısız ticker'ları atlayarak analize devam etmelidir
5. WHEN bir hata oluştuğunda, THE System SHALL hatayı loglayıp diğer işlemlere devam etmelidir

### Gereksinim 8: Validasyon ve Kalite Kontrol

**Kullanıcı Hikayesi:** Bir kalite güvence uzmanı olarak, analiz sonuçlarının güvenilir olduğundan emin olmak istiyorum, böylece yanlış kararlar alınmaz.

#### Kabul Kriterleri

1. WHEN SHAP değerleri hesaplandığında, THE System SHALL tüm feature'lar için geçerli sayısal değerler üretildiğini doğrulamalıdır
2. WHEN blacklist oluşturulduğunda, THE System SHALL blacklist'in toplam feature'ların %80'inden fazlasını içermediğini kontrol etmelidir
3. IF blacklist çok fazla feature içeriyorsa, THEN THE System SHALL bir uyarı vermeli ve eşik değerini ayarlamayı önermelidir
4. THE System SHALL NDCG@3 metriğinin 0 ile 1 arasında olduğunu doğrulamalıdır
5. WHEN model karşılaştırması yapıldığında, THE System SHALL her iki modelin de aynı test verisi üzerinde değerlendirildiğini garanti etmelidir

### Gereksinim 9: Logging ve İzlenebilirlik

**Kullanıcı Hikayesi:** Bir DevOps mühendisi olarak, analiz sürecinin her adımını izleyebilmek istiyorum, böylece sorunları hızlıca tespit edebilirim.

#### Kabul Kriterleri

1. THE System SHALL her önemli adımda (veri yükleme, model eğitimi, SHAP hesaplama, blacklist oluşturma) bilgilendirici log mesajları üretmelidir
2. WHEN bir hata oluştuğunda, THE System SHALL hata mesajını, stack trace'i ve ilgili bağlamı loglamalıdır
3. THE System SHALL analiz başlangıç ve bitiş zamanlarını loglamalıdır
4. THE System SHALL her aşamanın süresini (timing) loglamalıdır
5. WHEN analiz tamamlandığında, THE System SHALL özet istatistikleri (işlenen ticker sayısı, toplam süre, başarı oranı) loglamalıdır

### Gereksinim 10: Sonuç Persistance ve Versiyon Yönetimi

**Kullanıcı Hikayesi:** Bir araştırmacı olarak, farklı analiz sonuçlarını karşılaştırabilmek istiyorum, böylece zaman içindeki değişimleri görebilirim.

#### Kabul Kriterleri

1. WHEN analiz tamamlandığında, THE System SHALL sonuçları timestamp içeren bir dosya adıyla kaydetmelidir
2. THE System SHALL her analiz için metadata (tarih, kullanılan parametreler, veri seti boyutu) kaydetmelidir
3. THE System SHALL önceki analiz sonuçlarını silmeden yeni sonuçları kaydetmelidir
4. WHEN birden fazla analiz sonucu mevcut olduğunda, THE System SHALL en son sonucu varsayılan olarak kullanmalıdır
5. THE System SHALL analiz sonuçlarını JSON formatında yapılandırılmış şekilde kaydetmelidir
