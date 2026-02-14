# BIST30 AI Trader - Gelişmiş Algoritmik Ticaret Platformu

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GPU Support](https://img.shields.io/badge/ROCm-Supported-red.svg)](https://rocm.docs.amd.com/)
[![Build Status](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)]()

**BIST30 AI Trader**, Borsa İstanbul (BIST30) pay piyasası için geliştirilmiş, **Hibrit Yapay Zeka (Ensemble Learning)** modellerini kullanan, modern ve modüler bir algoritmik ticaret sistemidir.

Proje, **LightGBM** (Ranking/Sınıflandırma) ve **TFT - Temporal Fusion Transformer** (Zaman Serisi/Trend) modellerini birleştirerek hisse senetlerini puanlar ve dinamik risk yönetimi kuralları ile portföy yönetir.

---

## 🚀 Öne Çıkan Özellikler

### 🧠 Hibrit AI Mimarisi
- **LightGBM:** Hızlı, ağaç tabanlı model ile hisseler arası sıralama (Learning to Rank) yapar.
- **TFT (Temporal Fusion Transformer):** Derin öğrenme (Deep Learning) ile zaman serisi trendlerini ve mevsimselliği yakalar.
- **Ensemble:** İki modelin çıktılarını dinamik ağırlıklarla birleştirerek (Hybrid Ensemble) karar mekanizmasını güçlendirir.

### 🛡️ Gelişmiş Risk Yönetimi
- **Dinamik Stop-Loss / Take-Profit:** ATR (Average True Range) tabanlı, piyasa volatilitesine göre genişleyen/daralan stop seviyeleri.
- **Rejim Analizi:** Piyasanın Ralli/Yatay/Çöküş (Crash) durumunu tespit eder ve risk parametrelerini (Cash pozisyonu, Stop mesafesi) buna göre ayarlar.
- **Kelly Criterion:** Pozisyon büyüklüğünü matematiksel olasılık formülü (Half-Kelly) ile optimize eder.

### ⚡ Modern Altyapı
- **Merkezi Konfigürasyon:** `settings.yaml` ve `config.py` ile tüm parametrelerin tek noktadan yönetimi ve Environment Variable desteği.
- **Logging:** Python `logging` altyapısı ile yapılandırılmış, dosyaya ve konsola aktarılan detaylı sistem logları.
- **Veri Doğrulama:** `Pydantic` ile canlı veri akışında şema kontrolü ve hata yakalama.
- **GPU Hızlandırma:** AMD ROCm desteği ile TFT modelinin GPU üzerinde hızlı eğitimi.

---

## 📊 Performans Karnesi (Phase 7 - Son 6 Ay)

Projenin **Hybrid Ensemble** modeli ile yapılan son kalite değerlendirmesi (Backtest: 2025-2026):

| Metrik | Değer | Açıklama |
| :--- | :--- | :--- |
| **Rank IC** | `0.0484` | Model puanları ile gerçek getiriler arasındaki korelasyon (Başarılı). |
| **Yıllık Getiri** | `%58.97` | Sistemin yıllıklandırılmış getiri potansiyeli. |
| **Kümülatif Getiri** | `%31.36` | Son 6 ayda elde edilen toplam getiri simülasyonu. |
| **Sharpe Ratio** | `0.61` | Riske göre düzeltilmiş getiri performansı. |
| **Max Drawdown** | `-%21.54` | Görülen en büyük sermaye erimesi (Risk uyarısı içerir). |

> **Not:** Sonuçlar geçmiş verilerle yapılan simülasyonlara dayanır. Gelecek performans garantisi vermez.

---

## 📁 Proje Yapısı

```
bist30_ai_trader/
├── api/                      # FastAPI tabanlı sunucu ve endpointler
├── core/                     # Çekirdek iş mantığı
│   ├── backtest/             # Modüler backtest motoru
│   ├── risk_manager.py       # Risk yönetimi sınıfı
│   └── live_data_engine.py   # Canlı veri akışı ve doğrulama
├── models/                   # AI Modelleri (LightGBM, TFT, Ensemble)
├── paper_trading/            # Sanal işlem (Paper Trading) sistemi
├── scripts/                  # Çalıştırılabilir scriptler (Eğitim, Test, Analiz)
├── tests/                    # Birim testler (Unit Tests)
├── utils/                    # Yardımcı araçlar ve Feature Engineering
│   └── features/             # Teknik, Volatilite ve Makro özellik kütüphaneleri
├── config.py                 # Konfigürasyon yükleyici
└── settings.yaml             # Parametre dosyası
```

---

## 🛠️ Kurulum (Linux / Ubuntu)

**Ön Gereksinimler:** Python 3.10+, pip, (Opsiyonel) AMD GPU için ROCm sürücüleri.

1.  **Depoyu Klonlayın:**
    ```bash
    git clone https://github.com/alptigingorkem-coder/bist30_ai_trader.git
    cd bist30_ai_trader
    ```

2.  **Sanal Ortam Oluşturun:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Bağımlılıkları Yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Not: ROCm için PyTorch sürümünü sisteminize uygun olarak ayrıca kurmanız gerekebilir.)*

4.  **Konfigürasyonu Kontrol Edin:**
    `settings.yaml` dosyasını inceleyin ve risk parametrelerini isteğinize göre düzenleyin.

---

## 📖 Kullanım Kılavuzu

### 1. Modelleri Eğitmek
Sistemi sıfırdan kuruyorsanız veya modelleri güncellemek istiyorsanız:
```bash
# LightGBM ve TFT modellerini eğitir
./run_training.sh
```

### 2. Kalite ve Performans Analizi
Mevcut modellerin durumunu görmek için:
```bash
python scripts/project_evaluation.py
```

### 3. Paper Trading (Sanal İşlem)
Canlı veri ile sistemi izlemek ve işlem simülasyonu yapmak için:
```bash
# Canlı veri akışını ve simülasyonu başlatır
python scripts/paper_trading_runner.py
```

### 4. Backtest (Tarihsel Test)
Geçmiş veriler üzerinde stratejiyi test etmek için:
```bash
python scripts/run_backtest.py
```

---

## ⚠️ YASAL UYARI VE SORUMLULUK REDDİ

**BU YAZILIM YATIRIM TAVSİYESİ DEĞİLDİR.**

1.  **Sorumluluk Reddi:** Bu yazılım eğitim ve araştırma amaçlı geliştirilmiştir. Yazılımın ürettiği sinyaller, finansal kayıplara yol açabilir. Geliştiriciler, kullanımdan doğabilecek **HİÇBİR MADDİ VEYA MANEVİ ZARARDAN SORUMLU TUTULAMAZ.**
2.  **Kendi Araştırmanızı Yapın (DYOR):** Borsa işlemleri yüksek risk içerir. Bu yazılımı bir karar destek sistemi olarak kullanın, tam yetkiyle (otonom) işlem yaptırmadan önce riskleri iyice değerlendirin.

---

**Lisans:** [AGPL-3.0](LICENSE)
**Geliştirici:** Alptigin Görkem
