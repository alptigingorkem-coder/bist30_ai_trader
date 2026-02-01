# BIST30 AI Trader - Yapay Zeka Destekli Borsa İstanbul Ticaret Terminali

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

Bu proje, Borsa İstanbul (BIST30) payları için geliştirilmiş, Random Forest ve LSTM modellerini kullanan hibrit bir yapay zeka alım-satım (trading) terminalidir. Sistem, teknik indikatörler ve makroekonomik verileri analiz ederek ticaret sinyalleri üretir ve risk yönetimi modülleri (Macro Gate, Volatilite analizi) ile stratejileri optimize eder.

## ⚠️ YASAL UYARI VE SORUMLULUK REDDİ (DISCLAIMER)

**BU YAZILIM YATIRIM TAVSİYESİ DEĞİLDİR.**

1.  **Sorumluluk Reddi:** Bu yazılım ("Yazılım"), "OLDUĞU GİBİ" (AS IS) esasına göre sunulmaktadır. Yazılımın geliştiricileri, katkıda bulunanlar veya dağıtıcılar, Yazılımın kullanımından, hatalı çalışmasından, ürettiği sinyallerden veya bu sinyallere dayanarak yapılan işlemlerden doğabilecek **HİÇBİR MADDİ VEYA MANEVİ ZARARDAN**, kar kaybından, veri kaybından veya diğer ticari zararlardan **SORUMLU TUTULAMAZ**.

2.  **Yatırım Riski:** Borsa ve finansal piyasalarda işlem yapmak yüksek risk içerir. Paranızın tamamını veya bir kısmını kaybedebilirsiniz. Bu Yazılım tarafından sağlanan veriler, analizler, tahminler veya sinyaller **kesinlikle yatırım tavsiyesi, alım-satım önerisi veya finansal danışmanlık niteliği taşımaz**. Tüm yatırım kararları, kullanıcının kendi hür iradesine ve risk değerlendirmesine dayanmalıdır.

3.  **Hata Olasılığı:** Yazılım, karmaşık algoritmalar ve matematiksel modeller kullanmaktadır. Yazılımda, veri kaynaklarında veya kullanılan kütüphanelerde hatalar (bug), kesintiler veya öngörülemeyen davranışlar olabilir. Geçmiş performans, gelecekteki sonuçların garantisi değildir.

4.  **Kullanıcı Sorumluluğu:** Bu Yazılımı indiren, kuran veya kullanan herkes, bu feragatnameyi okumuş, anlamış ve kabul etmiş sayılır. Yazılımı kullanarak, oluşabilecek tüm riskleri ve potansiyel zararları **kendi üzerinize aldığınızı** beyan edersiniz.

---

## 🚀 Özellikler

*   **Hibrit AI Modeli:** Random Forest (sınıflandırma) ve LSTM (zaman serisi) modellerinin güç birleşimi.
*   **Macro Gate:** Makroekonomik veriler (Dolar, Altın, Faiz, VIX) ile genel piyasa yönü filtresi.
*   **Risk Yönetimi:** Otomatik Stop-Loss, Take-Profit ve dinamik pozisyon yönetimi.
*   **Gelişmiş Raporlama:** HTML formatında detaylı backtest, paper trading ve performans analiz raporları.
*   **Modüler Mimari:** Kolayca genişletilebilir strateji ve model yapısı.

## 🛠️ Kurulum

Gereksinimler: Python 3.8+

1.  Depoyu klonlayın:
    ```bash
    git clone https://github.com/kullaniciadi/bist30_ai_trader.git
    cd bist30_ai_trader
    ```

2.  Sanal ortam oluşturun ve aktif edin:
    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    ```

3.  Bağımlılıkları yükleyin:
    ```bash
    pip install -r requirements.txt
    ```

4.  Konfigürasyon dosyasını düzenleyin (`config.py`) ve kendi API anahtarlarınızı girin.

## 📖 Kullanım

### Modelleri Eğitmek
Sistemi ilk kez kullanmadan önce modelleri eğitmeniz gerekir:
```bash
python train_models.py
```

### Günlük Analiz (Daily Run)
Günlük sinyalleri almak ve rapor oluşturmak için:
```bash
python daily_run.py
```
Bu komut güncel verileri çeker, analiz eder ve `reports/` klasörüne rapor oluşturur.

### Backtest
Geçmişe dönük performans testi için:
```bash
python run_backtest.py
```

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen önce `docs/CONTRIBUTING.md` dosyasını okuyunuz.

1.  Bu depoyu "Fork"layın.
2.  Yeni bir dal (branch) oluşturun (`git checkout -b feature/YeniOzellik`).
3.  Değişikliklerinizi "Commit"leyin (`git commit -m 'Yeni özellik eklendi'`).
4.  Dalınızı "Push"layın (`git push origin feature/YeniOzellik`).
5.  Bir "Pull Request" oluşturun.

## 📄 Lisans

Bu proje **AGPL-3.0** lisansı ile lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakınız.
