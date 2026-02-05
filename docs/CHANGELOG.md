# Değişiklik Günlüğü (Changelog)

Bu dosya, BIST30 AI Trader projesinde yapılan tüm önemli değişiklikleri içerir.
Biçim [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standartlarına dayanmaktadır.

## [3.0.0] - 2026-02-05

### Yeni Özellikler (Otomasyon)
- **LiveDataEngine Entegrasyonu**
  - `daily_run.py` artık tam otomatik çalışıyor.
  - Canlı veri çekilemediğinde "Manuel Fallback" mekanizması devreye giriyor.
  - `yfinance` ve `DataUnavailabilityError` yönetimi güçlendirildi.

### Değişiklikler
- **KAP Entegrasyonu:** Backtest performansını artırmak için varsayılan olarak `False` yapıldı.
- **Sistem Mimarisi:** Manuel müdahale gereksinimi minimuma indirildi. Only trade on execution.
- **Bağımlılıklar:** `pykap`, `selenium`, `webdriver-manager` requirements.txt'ye eklendi.

### Dokümantasyon
- Kullanım kılavuzu otomasyon detaylarıyla güncellendi.
- Sorun giderme rehberine API ve veri hataları eklendi.

---

## [2.2.0] - 2026-02-05

### Eklendi
- **GitHub Yayınlama Hazırlığı**
  - Proje yapısı dokümantasyonu güncellendi
  - README.md güncel klasör yapısıyla eşleştirildi
  - Tüm docs/ dosyaları gözden geçirildi

### Değiştirildi
- PROJECT_STRUCTURE.md tamamen yeniden yazıldı
- KULLANIM_KILAVUZU.md güncel yollarla güncellendi
- PAPER_TRADING_TECHNICAL.md Top 5 mimarisiyle güncellendi

---

## [2.1.0] - 2026-02-03

### İyileştirildi
- **Risk Yönetimi (Max DD Hedefi)**
  - Trend_Up rejimi için Trailing Stop gevşetildi (3.0x), Crash modu sıkılaştırıldı (1.0x).
  - Rejim belirsizliğinde Fallback stratejisi 'Agresif' (Trend_Up) olarak güncellendi.
  
- **Alpha ve Portföy**
  - Portföy büyüklüğü 7'den 5'e düşürüldü (Konsantrasyon artışı).
  - Macro Gate eşikleri gevşetildi (VIX > 40, USDTRY > %5).
  - Beta 0.94'e çekildi, Alpha (Jensen) %10.7 seviyesine çıkarıldı.

- **Sinyal Verimliliği**
  - Güven eşiği (Confidence Threshold) 0.60'tan 0.50'ye düşürüldü.
  - Sharpe tabanlı pozisyon sizing eşiği 0.6'dan 0.3'e çekildi (Daha fazla işlem sinyali).

---

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
