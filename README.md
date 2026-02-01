# BIST30 AI Trader - Yapay Zeka Destekli Borsa İstanbul Ticaret Terminali

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Paper Trading Ready](https://img.shields.io/badge/Paper%20Trading-Ready-green.svg)](#-paper-trading)

Bu proje, Borsa İstanbul (BIST30) payları için geliştirilmiş, Random Forest ve LSTM modellerini kullanan hibrit bir yapay zeka alım-satım (trading) terminalidir. Sistem, teknik indikatörler ve makroekonomik verileri analiz ederek ticaret sinyalleri üretir ve risk yönetimi modülleri (Macro Gate, Volatilite analizi) ile stratejileri optimize eder.

## ⚠️ YASAL UYARI VE SORUMLULUK REDDİ

**BU YAZILIM YATIRIM TAVSİYESİ DEĞİLDİR.**

1.  **Sorumluluk Reddi:** Bu yazılım "OLDUĞU GİBİ" (AS IS) sunulmaktadır. Geliştiriciler, kullanımdan doğabilecek **HİÇBİR MADDİ VEYA MANEVİ ZARARDAN SORUMLU TUTULAMAZ**.

2.  **Yatırım Riski:** Borsa ve finansal piyasalarda işlem yapmak yüksek risk içerir. Bu Yazılım tarafından sağlanan sinyaller **kesinlikle yatırım tavsiyesi niteliği taşımaz**.

3.  **Kullanıcı Sorumluluğu:** Bu Yazılımı kullanan herkes, oluşabilecek tüm riskleri **kendi üzerine aldığını** beyan eder.

---

## 🚀 Özellikler

| Özellik | Açıklama |
|---------|----------|
| **Hibrit AI Modeli** | Random Forest + LSTM güç birleşimi |
| **Macro Gate** | VIX, USDTRY, Global Risk filtresi |
| **Paper Trading v2.0** | Stateless + Position-Aware simülasyon |
| **Slippage Simülasyonu** | ATR + Volume percentile bazlı |
| **Risk Yönetimi** | Stop-Loss, Take-Profit, Exposure limitleri |
| **Gelişmiş Raporlama** | HTML formatında detaylı analizler |

---

## 📁 Proje Yapısı

```
bist30_ai_trader/
├── core/                           # Çekirdek modüller
│   ├── paper_engine.py             # Shadow Execution (Stateless)
│   ├── paper_portfolio.py          # Portföy state (Slippage)
│   └── paper_logger.py             # JSON logging
│
├── paper_trading_position_aware/   # Position-Aware Paper Trading
│   ├── portfolio_state.py          # Pozisyon takibi
│   ├── position_engine.py          # 6 karar tipi
│   ├── position_runner.py          # Orchestrator
│   └── position_logger.py          # JSON + CSV logging
│
├── models/saved/                   # Eğitilmiş modeller
├── strategies/                     # Ticaret stratejileri
├── configs/                        # Sektör konfigürasyonları
├── docs/                           # Teknik dokümantasyon
└── tools/                          # Yardımcı araçlar
```

---

## 🛠️ Kurulum

**Gereksinimler:** Python 3.8+

```bash
# 1. Depoyu klonlayın
git clone https://github.com/alptigingorkem-coder/bist30_ai_trader.git
cd bist30_ai_trader

# 2. Sanal ortam oluşturun
python -m venv venv
.\venv\Scripts\activate  # Windows

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Konfigürasyonu düzenleyin
copy config.example.py config.py
```

---

## 📖 Kullanım

### Modelleri Eğitmek
```bash
python train_models.py
```

### Günlük Sinyal Üretimi
```bash
python daily_run.py
```

### Backtest
```bash
python run_backtest.py
```

---

## 📊 Paper Trading

Sistem iki katmanlı Paper Trading altyapısı sunar:

### 1. Stateless Paper Trading (Shadow Execution)
```bash
python run_paper.py
```
- Sinyal → Shadow Order → Log
- Slippage simülasyonu (ATR + Volume)
- Macro Gate blokaj takibi

### 2. Position-Aware Paper Trading
```bash
python paper_trading_position_aware/position_runner.py
```
- Pozisyon belleği (açık/kapalı takibi)
- 6 karar tipi: OPEN, HOLD, SCALE_IN, SCALE_OUT, CLOSE, IGNORE
- Exposure ve risk limitleri
- Overtrading koruması

### Analiz Araçları
```bash
# Temel analiz
python analyze_paper.py

# Stress test (En kötü 20 gün)
python analyze_paper.py --stress

# Tam analiz (MAE/MFE dahil)
python analyze_paper.py --full
```

---

## 📈 Eğitilmiş Modeller

| Sektör | Alpha Model | Beta Model |
|--------|-------------|------------|
| Banking | ✅ | ✅ |
| Growth | ✅ | ✅ |
| Holding | ✅ | ✅ |
| Industrial | ✅ | ✅ |

---

## 📊 Performans (Walk-Forward 2023-2024)

**Test Sonuçları (Phase 8 - Final Validation):**
- **Ortalama Getiri (Portfolio):** %6.35 (Backtest 2023-2024 OOS)
- **Sharpe Ratio:** 0.47 (Gerçekçi Komisyon ve Slippage dahil)
- **Yöntem:** Daily Timeframe + LightGBM LambdaRank + Top 5 Allocation
- **Risk Yönetimi:** %0.70 Round-Trip Maliyet + Dinamik Stop-Loss
- **Robustness:** Günlük rebalancing sayesinde piyasa şoklarına anlık tepki.

---

## 📄 Dokümantasyon

| Belge | Açıklama |
|-------|----------|
| [Paper Trading Teknik](docs/PAPER_TRADING_TECHNICAL.md) | Shadow Execution mimarisi |
| [Kullanım Kılavuzu](docs/KULLANIM_KILAVUZU.md) | Adım adım kullanım |
| [Mimari Tasarım](docs/mimari_tasarim.html) | Sistem mimarisi |
| [Sorun Giderme](docs/SORUN_GIDERME.md) | Yaygın hatalar |

---

## 🤝 Katkıda Bulunma

1. Bu depoyu **Fork**'layın
2. Yeni dal oluşturun: `git checkout -b feature/YeniOzellik`
3. Değişiklikleri commit'leyin: `git commit -m 'Yeni özellik'`
4. Push'layın: `git push origin feature/YeniOzellik`
5. **Pull Request** oluşturun

Detaylar için: [CONTRIBUTING.md](docs/CONTRIBUTING.md)

---

## 📄 Lisans

Bu proje **AGPL-3.0** lisansı ile lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakınız.

---

**Son Güncelleme:** 2026-02-01 | **Versiyon:** 2.0
