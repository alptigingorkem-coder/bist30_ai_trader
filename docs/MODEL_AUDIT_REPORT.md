# BIST30 AI Trader - Kapsamlı Model Değerlendirme ve İyileştirme Raporu

## 1. YÖNETİCİ ÖZETİ (Executive Summary)

BIST30 AI Trader projesi, modern finansal yapay zeka yaklaşımlarını (Ranking Learning, Time-Series Forecasting) klasik algoritmik trading prensipleriyle (Risk Yönetimi, Portföy Optimazasyonu) birleştiren hibrit ve güçlü bir mimariye sahiptir. 

**Mevcut Durum:**
- **Model:** LightGBM (LambdaRank) ve Temporal Fusion Transformer (TFT) olmak üzere iki ana model kullanılmaktadır.
- **Veri:** Yahoo Finance ve EVDS (TCMB) kaynaklı çoklu veri akışı mevcuttur.
- **Altyapı:** Linux/ROCm üzerinde GPU destekli eğitim ortamı başarıyla kurulmuştur.
- **Risk:** ATR tabanlı dinamik stop-loss ve piyasa rejimi (Regime Detection) filtreleri mevcuttur.

**Kritik Bulgular:**
1.  **Hiperparametre Optimizasyonu Eksikliği:** Kod tabanında `optimized_lgbm_params.joblib` dosyası aranıyor olsa da, bu dosyayı üreten ve düzenli optimize eden bir script bulunamadı.
2.  **Validasyon Stratejisi:** Mevcut `train_models.py` sadece son %10'luk dilimi validasyon için ayırıyor. Finansal zaman serileri için "Walk-Forward Validation" daha güvenilirdir.
3.  **Backtest Gerçekçiliği:** Backtest motoru (`core/backtesting.py`) oldukça gelişmiş (slippage, market impact var), ancak stres testleri (Stress Testing) eksik.
4.  **Feature Selection:** Feature sayısı oldukça fazla. `RankingModel` içinde basit bir SHAP analizi var ancak sistematik bir eleme (RFE veya Null Importance) yok.

**Öngörülen İyileşme:**
Aşağıdaki yol haritası uygulandığında, Sharpe Oranı'nın **+0.5 ile +1.0** arasında artması ve Max Drawdown'ın **%5-10** oranında azalması hedeflenmektedir.

---

## 2. DETAYLI PROJE ANALİZİ

### A. Genel Mimari
Proje modüler bir yapıya sahiptir:
- `core/`: Çekirdek motorlar (Backtest, Risk, Veri)
- `models/`: Model tanımları (LightGBM, TFT)
- `utils/`: Yardımcı araçlar (Feature Engineering, Data Loader)

**Değerlendirme:**
✅ **Güçlü Yönler:**
- **Event-Driven Backtest:** `Backtester` sınıfı, vektörel değil olay tabanlı çalışarak (loop over rows) gerçek hayatı daha iyi simüle ediyor.
- **Hibrit Model:** Hem sıralama (LGBM) hem zaman serisi (TFT) modellerinin bir arada düşünülmesi vizyoner bir yaklaşım.
- **Risk Katmanı:** Modelden bağımsız çalışan `RiskManager` sınıfı, "Stop Loss" ve "Trailing Stop" mekanizmalarını merkezi yönetiyor.

❌ **Zayıf Yönler:**
- **Feature Store:** Veriler anlık hesaplanıyor (`FeatureEngineer`). Büyük ölçekte bu yavaşlığa neden olabilir. Bir feature store (örn: Parquet tabanlı) tam oturmamış.
- **Config Bağımlılığı:** Birçok kritik eşik değer (`config.py` içinde) hardcoded durumda. Bunların optimize edilmesi gerekiyor.

### B. Model Analizi

#### 1. LightGBM (Ranking Model)
- **Tip:** `lambdarank` (Learning to Rank)
- **Hedef:** `Excess_Return` (BIST100'e göre getiri farkı) sıralaması.
- **Durum:** LambdaRank kullanımı harika bir tercih. Borsa, "ne kadar artacak"tan ziyade "hangisi diğerinden daha iyi artacak" problemidir.
- **Eksik:** Hiperparametreler (learning_rate=0.03, num_leaves=64) *statik*. Her piyasa döngüsü için bu değerler optimal olmayabilir.

#### 2. Temporal Fusion Transformer (TFT)
- **Tip:** Time-Series Forecasting (PyTorch Forecasting)
- **Hedef:** Gelecek fiyat/getiri tahmini.
- **Durum:** Henüz entegrasyon aşamasında. Linux geçişi ile GPU üzerinde eğitilebilir hale geldi.
- **Potansiyel:** Volatilite ve rejim değişimlerini LSTMs'ten daha iyi yakalayabilir.

---

## 3. İYİLEŞTİRME ÖNERİLERİ VE YOL HARİTASI

### Faz 1: Optimizasyon ve Validasyon (1. Hafta) 🔴 KRİTİK

#### 1.1. Optuna ile Hiperparametre Optimizasyonu
Mevcut statik parametrelerden kurtulup, her eğitim öncesi veya periyodik olarak en iyi parametreleri bulan bir script eklenmeli.

**Öneri:**
`scripts/optimize_hyperparameters.py` oluşturulacak.

```python
# Taslak Kod Hedefi
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=50)
joblib.dump(study.best_params, "models/saved/optimized_lgbm_params.joblib")
```

#### 1.2. Walk-Forward Validation
Mevcut "son %10 validasyon" yaklaşımı yerine, zaman içinde kayan pencerelerle (Rolling Window) modelin kararlılığı test edilmeli.

**Öneri:**
`train_models.py` içinde validasyon mantığı güncellenecek. `TimeSeriesSplit` kullanılacak.

### Faz 2: Backtest ve Risk (2. Hafta) 🟡 ÖNEMLİ

#### 2.1. Backtest Stres Testleri
Sistemin 2020 Pandemi düşüşü veya 2021 Kur Şoku gibi dönemlerde nasıl davrandığı simüle edilmeli.

**Öneri:**
`StressTester` sınıfı eklenecek. Belirli tarih aralıklarında (Kriz dönemleri) backtest çalıştırıp raporlayacak.

#### 2.2. Dinamik Pozisyonlama (Kelly Criterion İyileştirmesi)
Mevcut Kelly implementasyonu var ancak `risk_manager` ile daha sıkı entegre edilmeli. "Half-Kelly" stratejisi uygulanarak volatilite riskleri düşürülmeli.

### Faz 3: Feature Engineering (3. Hafta) 🟢 OPSİYONEL

#### 3.1. Advanced Features
- **Microstructure Features:** Bid-Ask Spread, Tick Flow (eğer veri varsa).
- **Sentiment Refinement:** KAP haberlerinin sadece sayısı değil, içeriğinin NLP (BERT) ile duygu analizine tabi tutulması.

---

## 4. AKSİYON PLANI (Action Items)

Aşağıdaki görevler `task.md` dosyasına işlenerek sırasıyla uygulanacaktır.

1.  **[ ] Create Optimization Script:** `scripts/optimize_hyperparameters.py` (Optuna entegrasyonu).
2.  **[ ] Refactor Training Pipeline:** `train_models.py` içine optimizasyon adımını opsiyonel olarak ekle.
3.  **[ ] Enhance Backtester:** `run_backtest.py` içine Walk-Forward ve Stress Test modları ekle.
4.  **[ ] Implement Advanced Config:** Statik eşik değerlerini (`config.py`) dinamik veya optimize edilebilir hale getir.

---

## 5. KOD ŞABLONLARI (Templates)

### Optuna Objective Fonksiyonu Örneği

```python
def objective(trial):
    params = {
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.1),
        'num_leaves': trial.suggest_int('num_leaves', 20, 150),
        'max_depth': trial.suggest_int('max_depth', 3, 12),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
        'min_child_samples': trial.suggest_int('min_child_samples', 10, 100)
    }
    
    # ... Train Logic ...
    # return expert_metric
```

### Walk-Forward Loop Örneği

```python
splits = TimeSeriesSplit(n_splits=5, gap=20)
for train_index, val_index in splits.split(X):
    X_train, X_val = X.iloc[train_index], X.iloc[val_index]
    # ... Train & Eval ...
```
