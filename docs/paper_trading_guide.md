# 📊 BIST30 AI Trader - Paper Trading Rehberi

> **Paper Trading Süreci**: Gerçek para kullanmadan, canlı piyasa verisiyle sistemin performansını test etme

## 🎯 Amaç

Paper trading, algoritmik trading sisteminin gerçek piyasa koşullarında nasıl performans gösterdiğini test etmek için kritik bir aşamadır. Bu süreçte:

- ✅ Gerçek piyasa verisi kullanılır
- ✅ Gerçek işlem mantığı çalışır
- ❌ Gerçek para harcanmaz
- ✅ Tüm işlemler kaydedilir ve analiz edilir

## 📅 Süreç Takvimi

### Faz 1: Başlangıç (Gün 1)
- Sistemi başlat
- İlk sinyalleri gözlemle
- Log sistemini kontrol et

### Faz 2: İlk Hafta (Gün 1-7)
- Günlük performans takibi
- Anomali tespiti
- Küçük ayarlamalar

### Faz 3: İkinci Hafta (Gün 8-14)
- Performans analizi
- Sharpe ratio hesaplama
- GO/NO-GO kararı

---

## 🚀 Başlangıç: Paper Trading'i Başlatma

### Adım 1: Sistem Kontrolü

```bash
# Validation script'ini çalıştır
python3 scripts/validation/paper_trading_readiness.py

# Skor %75+ olmalı
```

### Adım 2: Paper Trading'i Başlat

```bash
# Terminal 1: Paper Trading Runner
python3 scripts/ops/paper_trading_runner.py

# Çıktı:
# 🚀 Paper Trader Başlatıldı (Sanal Bakiye: 10,000.00 TL)
# ✅ Model yüklendi: models/saved/global_ranker.pkl
# 🕒 Gün Sonu (EOD) Trader Modu Başlatıldı.
# ℹ️  Sistem her gün saat 18:05'te işlem yapacak.
```

### Adım 3: Log Takibi

```bash
# Terminal 2: Log takibi
tail -f logs/paper_trading_$(date +%Y%m%d).log

# Veya tüm logları izle
tail -f logs/*.log
```

---

## 📊 Günlük Rutin (Her Gün Yapılacaklar)

### 🌅 Sabah Rutini (09:00 - 10:00)

#### 1. Sistem Durumu Kontrolü

```bash
# Paper trading hala çalışıyor mu?
ps aux | grep paper_trading_runner

# Log dosyası büyüklüğü
ls -lh logs/paper_trading_*.log
```

#### 2. Dünkü İşlemleri İncele

```bash
# Son 24 saatin loglarını oku
tail -100 logs/paper_trading_$(date +%Y%m%d).log | grep "ALIM\|SATIŞ"

# Örnek çıktı:
# 🟢 ALIM YAPILDI: THYAO.IS x 100 @ 45.50 (Tutar: 4,561.25)
# 🔴 SATIŞ YAPILDI: EREGL.IS x 50 @ 38.20 (Gelir: 1,905.00)
```

#### 3. Portfolio Durumu

```python
# scripts/analysis/check_portfolio_status.py (yeni oluşturacağız)
python3 scripts/analysis/check_portfolio_status.py

# Çıktı:
# 💰 Nakit: 5,438.75 TL
# 📈 Pozisyonlar: 3 adet
#    - THYAO.IS: 100 hisse (4,550 TL)
#    - AKBNK.IS: 200 hisse (3,200 TL)
#    - EREGL.IS: 50 hisse (1,910 TL)
# 💼 Toplam Değer: 15,098.75 TL
# 📊 Günlük Getiri: +2.3%
```

### 🌆 Akşam Rutini (18:00 - 19:00)

#### 1. Piyasa Kapanışını İzle

```bash
# 18:05'te sistem otomatik çalışacak
# Log'u canlı izle
tail -f logs/paper_trading_$(date +%Y%m%d).log
```

#### 2. İşlem Sonuçlarını Kaydet

```bash
# Günlük rapor oluştur
python3 scripts/analysis/generate_daily_report.py --date $(date +%Y-%m-%d)

# Rapor: reports/daily/2026-02-19.md
```

#### 3. Performans Metrikleri

```bash
# Günlük Sharpe hesapla
python3 scripts/analysis/calculate_daily_sharpe.py

# Çıktı:
# 📊 Günlük Sharpe: 1.85
# 📈 Kümülatif Getiri: +12.5%
# 📉 Max Drawdown: -3.2%
```

---

## 📈 Haftalık Analiz (Her Pazar)

### Haftalık Rapor Oluşturma

```bash
# Haftalık performans raporu
python3 scripts/analysis/generate_weekly_report.py \
    --start-date 2026-02-13 \
    --end-date 2026-02-19

# Rapor: reports/weekly/week_2026_W08.md
```

### Kontrol Edilecek Metrikler

#### 1. Sharpe Ratio
```python
# Hedef: >1.5
# Mevcut: ?
# Durum: ✅ / ⚠️ / ❌
```

#### 2. Max Drawdown
```python
# Hedef: <-15%
# Mevcut: ?
# Durum: ✅ / ⚠️ / ❌
```

#### 3. Win Rate
```python
# Hedef: >55%
# Mevcut: ?
# Durum: ✅ / ⚠️ / ❌
```

#### 4. İşlem Sayısı
```python
# Beklenen: 10-20 işlem/hafta
# Gerçekleşen: ?
# Durum: ✅ / ⚠️ / ❌
```

---

## 🔍 İzlenecek Kritik Noktalar

### ⚠️ Kırmızı Bayraklar (Hemen Müdahale Gerek)

#### 1. Sistem Durdu
```bash
# Kontrol
ps aux | grep paper_trading_runner

# Yoksa yeniden başlat
nohup python3 scripts/ops/paper_trading_runner.py > logs/paper_trading.out 2>&1 &
```

#### 2. Günlük Kayıp >%5
```bash
# Günlük getiri kontrolü
python3 scripts/analysis/check_daily_loss.py

# Eğer >%5 kayıp varsa:
# 1. Sistemi durdur
# 2. Logları incele
# 3. Sorunu tespit et
# 4. Düzelt ve yeniden başlat
```

#### 3. Aşırı İşlem (>10 işlem/gün)
```bash
# İşlem sayısı kontrolü
grep -c "ALIM\|SATIŞ" logs/paper_trading_$(date +%Y%m%d).log

# Eğer >10 ise:
# - Model çok agresif
# - Confidence threshold'u yükselt
```

#### 4. Hiç İşlem Yok (>3 gün)
```bash
# Son 3 günün işlemlerini kontrol et
for i in {0..2}; do
    date=$(date -d "$i days ago" +%Y%m%d)
    echo "=== $date ==="
    grep -c "ALIM\|SATIŞ" logs/paper_trading_$date.log || echo "0"
done

# Eğer 3 gün 0 ise:
# - Piyasa çok volatil olabilir (VOLATILE/CRISIS rejimi)
# - Confidence threshold çok yüksek olabilir
```

### 🟡 Sarı Bayraklar (Gözlem Gerek)

#### 1. Sharpe <1.0
- Performans beklentinin altında
- Haftalık analiz yap
- Parametreleri gözden geçir

#### 2. Drawdown >-10%
- Risk yönetimi çalışıyor ama sınıra yaklaşıyor
- Pozisyon boyutlarını küçült

#### 3. Win Rate <50%
- Model tahminleri zayıf
- Feature importance analizi yap

---

## 📋 Günlük Kontrol Listesi

### ✅ Her Sabah (09:00)

- [ ] Sistem çalışıyor mu? (`ps aux | grep paper_trading`)
- [ ] Dünkü işlemler kaydedilmiş mi?
- [ ] Portfolio durumu normal mi?
- [ ] Log dosyası hata içeriyor mu?

### ✅ Her Akşam (18:30)

- [ ] Bugünkü işlemler tamamlandı mı?
- [ ] Günlük rapor oluşturuldu mu?
- [ ] Performans metrikleri hesaplandı mı?
- [ ] Anomali var mı?

### ✅ Her Pazar

- [ ] Haftalık rapor oluşturuldu mu?
- [ ] Sharpe ratio hedefte mi?
- [ ] Drawdown limitte mi?
- [ ] İşlem sayısı normal mi?

---

## 🛠️ Sorun Giderme

### Problem 1: Sistem Çöktü

```bash
# 1. Log'u kontrol et
tail -100 logs/paper_trading_$(date +%Y%m%d).log

# 2. Hata mesajını bul
grep "ERROR\|Exception" logs/paper_trading_*.log

# 3. Yeniden başlat
python3 scripts/ops/paper_trading_runner.py
```

### Problem 2: Model Yüklenemiyor

```bash
# 1. Model dosyası var mı?
ls -lh models/saved/global_ranker.pkl

# 2. Yoksa yeniden eğit
python3 scripts/training/train_models.py

# 3. Varsa izinleri kontrol et
chmod 644 models/saved/global_ranker.pkl
```

### Problem 3: Veri Çekilemiyor

```bash
# 1. İnternet bağlantısı var mı?
ping -c 3 yahoo.com

# 2. yfinance çalışıyor mu?
python3 -c "import yfinance as yf; print(yf.download('THYAO.IS', period='1d'))"

# 3. API limiti aşıldı mı?
# Birkaç dakika bekle ve tekrar dene
```

---

## 📊 Performans Değerlendirme (2 Hafta Sonra)

### Karar Matrisi

| Metrik | Hedef | Gerçekleşen | Durum |
|--------|-------|-------------|-------|
| Sharpe Ratio | >1.5 | ? | ? |
| Max Drawdown | <-15% | ? | ? |
| Win Rate | >55% | ? | ? |
| Toplam Getiri | >0% | ? | ? |
| İşlem Sayısı | 20-40 | ? | ? |

### GO/NO-GO Kararı

#### 🟢 GO (Canlıya Geç)
**Kriterler:**
- ✅ Sharpe >1.5
- ✅ Drawdown <-15%
- ✅ Win Rate >55%
- ✅ Toplam Getiri >0%

**Aksiyon:**
```bash
# 1. Son validation
python3 scripts/validation/paper_trading_readiness.py

# 2. Küçük sermaye ile başla (10,000 TL)
# 3. İlk ay günlük takip
# 4. Başarılı olursa sermayeyi artır
```

#### 🟡 CONDITIONAL GO (1 Ay Daha Paper Trading)
**Kriterler:**
- 🟡 Sharpe 1.0-1.5
- ✅ Drawdown <-15%
- 🟡 Win Rate 50-55%

**Aksiyon:**
```bash
# 1. Parametreleri optimize et
# 2. 1 ay daha paper trading
# 3. Tekrar değerlendir
```

#### 🔴 NO-GO (Model Revizyonu)
**Kriterler:**
- ❌ Sharpe <1.0
- ❌ Drawdown >-15%
- ❌ Win Rate <50%

**Aksiyon:**
```bash
# 1. Model yeniden eğit
python3 scripts/training/train_models.py

# 2. Feature importance analizi
python3 scripts/analysis/run_feature_importance.py

# 3. Walk-forward validation
python3 scripts/training/walk_forward_validation.py

# 4. Paper trading'e geri dön
```

---

## 📁 Dosya Yapısı

### Log Dosyaları
```
logs/
├── paper_trading_20260219.log    # Günlük log
├── paper_trading_20260220.log
└── paper_trading.out              # Sistem çıktısı
```

### Raporlar
```
reports/
├── daily/
│   ├── 2026-02-19.md             # Günlük rapor
│   └── 2026-02-20.md
├── weekly/
│   ├── week_2026_W08.md          # Haftalık rapor
│   └── week_2026_W09.md
└── final/
    └── paper_trading_final_report.md  # 2 haftalık final rapor
```

### Portfolio Durumu
```
data/
└── paper_trading/
    ├── portfolio_state.json       # Güncel portfolio
    ├── trade_history.csv          # İşlem geçmişi
    └── daily_performance.csv      # Günlük performans
```

---

## 🎓 İpuçları ve En İyi Uygulamalar

### 1. Sabırlı Ol
- İlk hafta düşük performans normal
- Sistem piyasayı öğreniyor
- En az 2 hafta bekle

### 2. Günlük Takip Yap
- Her gün logları kontrol et
- Anomalileri hemen tespit et
- Küçük sorunlar büyümeden çöz

### 3. Notlar Tut
```markdown
# Paper Trading Günlüğü

## 2026-02-19
- Sistem başlatıldı
- İlk işlem: THYAO.IS alım
- Gözlem: Model çok agresif, threshold yükseltilmeli

## 2026-02-20
- Confidence threshold 0.8 → 0.85
- İşlem sayısı azaldı (iyi)
- Sharpe: 1.2 (yükseliyor)
```

### 4. Piyasa Koşullarını İzle
- Volatil günlerde sistem durabilir (VOLATILE rejimi)
- Bu normal ve güvenlik özelliği
- Rejim değişikliklerini logla

### 5. Yedekleme
```bash
# Her hafta sonu yedek al
tar -czf backup_$(date +%Y%m%d).tar.gz \
    logs/ \
    reports/ \
    data/paper_trading/ \
    models/saved/

# Yedekleri sakla
mv backup_*.tar.gz ~/backups/
```

---

## 🚨 Acil Durum Prosedürleri

### Senaryo 1: Sistem Kontrolden Çıktı (>%10 Günlük Kayıp)

```bash
# 1. HEMEN DURDUR
pkill -f paper_trading_runner

# 2. Logları kaydet
cp logs/paper_trading_$(date +%Y%m%d).log logs/emergency_$(date +%Y%m%d_%H%M%S).log

# 3. Analiz yap
python3 scripts/analysis/emergency_analysis.py

# 4. Sorunu çöz
# 5. Validation yap
# 6. Yeniden başlat
```

### Senaryo 2: Veri Kaynağı Çöktü

```bash
# 1. Alternatif veri kaynağına geç
# config.py'de DATA_SOURCE değiştir

# 2. Sistemi yeniden başlat
python3 scripts/ops/paper_trading_runner.py
```

### Senaryo 3: Model Bozuldu

```bash
# 1. Yedek modeli yükle
cp models/saved/backup/global_ranker.pkl models/saved/

# 2. Veya yeniden eğit
python3 scripts/training/train_models.py

# 3. Validation yap
python3 scripts/validation/check_models.py
```

---

## 📞 Destek ve Kaynaklar

### Dokümantasyon
- [README.md](../README.md) - Genel bakış
- [Architecture](architecture.md) - Sistem mimarisi
- [API Documentation](api.md) - API referansı

### Validation Scripts
```bash
# Sistem sağlığı
python3 scripts/validation/paper_trading_readiness.py

# Model kontrolü
python3 scripts/validation/check_models.py

# Altyapı kontrolü
python3 scripts/validation/check_infrastructure.py
```

### Analiz Tools
```bash
# Performans analizi
python3 scripts/analysis/get_training_metrics.py

# Feature importance
python3 scripts/analysis/run_feature_importance.py

# Backtest karşılaştırma
python3 scripts/analysis/compare_improvements.py
```

---

## ✅ Başarı Kriterleri Özeti

### Minimum Gereksinimler (2 Hafta)
- ✅ Sistem 14 gün kesintisiz çalıştı
- ✅ Sharpe Ratio >1.0
- ✅ Max Drawdown <-20%
- ✅ Hiç kritik hata olmadı

### İdeal Hedefler
- 🎯 Sharpe Ratio >1.5
- 🎯 Max Drawdown <-15%
- 🎯 Win Rate >55%
- 🎯 Toplam Getiri >5%

### Canlıya Geçiş Hazırlığı
- 🚀 Tüm metrikler hedefte
- 🚀 2 hafta stabil performans
- 🚀 Validation score >90%
- 🚀 Risk yönetimi test edildi

---

**Başarılar! Paper trading sürecinde bol şans! 🚀📈**

*Son güncelleme: 2026-02-19*
