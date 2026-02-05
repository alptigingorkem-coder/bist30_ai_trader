# Proje Dizin Yapısı

```text
bist30_ai_trader/
├── .gitignore                      # Git dışlama kuralları
├── config.py                       # Ana konfigürasyon (gitignore'da)
├── daily_run.py                    # Günlük sinyal üretimi
├── run_backtest.py                 # Backtest çalıştırıcı
├── train_models.py                 # Model eğitim scripti
├── train_catboost.py               # CatBoost model eğitimi
├── start_paper_trading.bat         # Windows batch başlatıcı
├── LICENSE                         # AGPL-3.0 Lisans
├── README.md                       # Proje dokümantasyonu
├── requirements.txt                # Python bağımlılıkları
├── PROJECT_STRUCTURE.md            # Bu dosya
├── SYSTEM_SUMMARY.md               # Sistem özeti
│
├── api/                            # API katmanı
│
├── cache/                          # Önbellek dosyaları
│
├── configs/                        # Sektör konfigürasyonları
│   ├── banking.py
│   ├── growth.py
│   ├── holding.py
│   ├── industrial.py
│   └── __init__.py
│
├── core/                           # Çekirdek modüller
│   ├── backtesting.py              # Backtest motoru
│   ├── dynamic_backtest.py         # Dinamik backtest
│   ├── live_data_engine.py         # Canlı veri motoru
│   ├── portfolio_manager.py        # Portföy yöneticisi
│   ├── risk_manager.py             # Risk yönetimi
│   ├── feature_store.py            # Özellik deposu
│   ├── augmented_feature_generator.py  # Artırılmış özellik üreteci
│   └── __init__.py
│
├── data/                           # Veri dosyaları
│
├── docs/                           # Dokümantasyon
│   ├── CHANGELOG.md                # Değişiklik günlüğü
│   ├── CODE_OF_CONDUCT.md          # Davranış kuralları
│   ├── CONTRIBUTING.md             # Katkı rehberi
│   ├── GUVENLIK.md                 # Güvenlik politikası
│   ├── KULLANIM_KILAVUZU.html      # Kullanım kılavuzu (HTML)
│   ├── KULLANIM_KILAVUZU.md        # Kullanım kılavuzu (MD)
│   ├── PAPER_TRADING_TECHNICAL.html # Paper Trading teknik doküman (HTML)
│   ├── PAPER_TRADING_TECHNICAL.md  # Paper Trading teknik doküman (MD)
│   ├── SORUN_GIDERME.md            # Sorun giderme rehberi
│   ├── dagitim_rehberi.html        # Dağıtım rehberi
│   ├── mimari_tasarim.html         # Sistem mimarisi
│   └── development_logs/           # Geliştirme günlükleri
│
├── logs/                           # Log dosyaları (gitignore'da)
│
├── models/                         # Eğitilmiş ML modelleri (büyük dosyalar gitignore'da)
│
├── paper_trading/                  # Paper Trading sistemi
│   ├── portfolio_state.py          # Pozisyon ve portföy takibi
│   ├── position_engine.py          # 6 karar tipi motoru
│   ├── position_runner.py          # Günlük orchestrator
│   ├── position_logger.py          # JSON + CSV loglama
│   ├── strategy_health.py          # Strateji sağlık monitörü
│   ├── live_execution.py           # Simülasyon motoru
│   └── __init__.py
│
├── reports/                        # Üretilen raporlar (gitignore'da)
│
├── research/                       # Araştırma ve optimizasyon
│   ├── auto_tune.py                # Otomatik parametre ayarlama
│   ├── batch_runner.py             # Toplu çalıştırıcı
│   ├── benchmark_architectures.py  # Mimari kıyaslama
│   ├── fetch_fundamentals.py       # Temel veri çekme
│   ├── model_experiments.py        # Model deneyleri
│   ├── monte_carlo.py              # Monte Carlo simülasyonu
│   ├── optuna_nested_walk_forward.py # Optuna optimizasyonu
│   └── ...
│
├── scripts/                        # Yardımcı scriptler
│
├── templates/                      # HTML şablonları
│
├── tests/                          # Birim testleri
│   ├── test_paper_trading.py
│   ├── test_portfolio.py
│   ├── test_regime_ml.py
│   ├── test_risk_model.py
│   ├── test_strategy_health.py
│   └── __init__.py
│
├── ui/                             # Web arayüzü
│
└── utils/                          # Yardımcı modüller
    ├── data_loader.py              # Veri yükleyici
    ├── feature_engineering.py      # Özellik mühendisliği
    ├── performance_tracker.py      # Performans takibi
    ├── portfolio_manager.py        # Portföy yönetimi
    ├── sector_allocator.py         # Sektör tahsisi
    └── __init__.py
```

## Klasör Açıklamaları

| Klasör | Açıklama |
|--------|----------|
| `core/` | Backtest motoru, risk yönetimi, canlı veri işleme |
| `paper_trading/` | Pozisyon takipli Paper Trading altyapısı |
| `models/` | LightGBM, CatBoost vb. eğitilmiş modeller |
| `research/` | Monte Carlo, Optuna, parametre optimizasyonu |
| `ui/` | Flask/Streamlit tabanlı web arayüzü |
| `tests/` | pytest ile yazılmış birim testleri |
| `docs/` | Teknik dokümantasyon ve geliştirme günlükleri |

---

**Son Güncelleme:** 2026-02-05
