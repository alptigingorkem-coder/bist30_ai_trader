# Değişiklik Günlüğü (Changelog)

Bu dosya, BIST30 AI Trader projesinde yapılan tüm önemli değişiklikleri içerir.
Biçim [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standartlarına dayanmaktadır.

## [2.0.0] - 2026-02-01

### Eklendi
- **Paper Trading v2.0 Altyapısı**
  - `core/paper_engine.py`: Shadow Execution motoru
  - `core/paper_logger.py`: JSON Lines loglama
  - `core/paper_portfolio.py`: ATR + Volume slippage simülasyonu
  - `run_paper.py`: Günlük orchestrator
  - `analyze_paper.py`: MAE/MFE, stress test, forward return analizi

- **Position-Aware Paper Trading (Stateful Phase)**
  - `paper_trading_position_aware/portfolio_state.py`: Pozisyon takibi
  - `paper_trading_position_aware/position_engine.py`: 6 karar tipi
  - `paper_trading_position_aware/position_runner.py`: Orchestrator
  - `paper_trading_position_aware/position_logger.py`: JSON + CSV logging

- **Dokümantasyon**
  - Teknik Paper Trading dokümantasyonu (MD + HTML)
  - Out of Scope ve Live Readiness Checklist bölümleri

### Değiştirildi
- README.md tamamen yenilendi
- Proje yapısı modernize edildi

### Silindi
- `_archive/` eski kod kalıntıları
- `archive/tests_v1/` eski testler
- 120+ eski backtest raporu

---

## [1.1.0] - 2026-01-31

### Eklendi
- Macro Gate v2: VIX, USDTRY, Global Risk entegrasyonu
- Sektör bazlı model eğitimi (Banking, Growth, Holding, Industrial)
- Gelişmiş backtest raporu (HTML formatı)

### Değiştirildi
- Modüler yapıya geçiş (`core/`, `strategies/`, `utils/`)

---

## [1.0.0] - 2026-01-30

### Başlangıç
- Temel veri çekme modülü oluşturuldu
- Random Forest ve LSTM modelleri entegre edildi
- Backtest motoru ve raporlama sistemi eklendi
- Günlük çalıştırma betiği hazırlandı
- Macro Gate sistemi eklendi
- AGPL-3.0 Lisans eklendi
