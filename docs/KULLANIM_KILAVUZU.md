# BIST30 AI Trader - Kullanım Kılavuzu

Bu belge, BIST30 AI Trader yazılımının kurulumu, yapılandırılması ve kullanımı hakkında detaylı bilgi içerir.

---

## 1. Kurulum

### Ön Hazırlıklar
- Python 3.8+ yüklü olmalı
- `git` aracı yüklü olmalı

### Adım Adım Kurulum

```bash
# 1. Projeyi indirin
git clone https://github.com/alptigingorkem-coder/bist30_ai_trader.git
cd bist30_ai_trader

# 2. Sanal ortam oluşturun (Windows)
python -m venv venv
.\venv\Scripts\activate

# 3. Kütüphaneleri yükleyin
pip install -r requirements.txt

# 4. Konfigürasyonu hazırlayın
copy config.example.py config.py
```

---

## 2. Yapılandırma (`config.py`)

| Ayar | Açıklama |
|------|----------|
| `API_KEYS` | TCMB, Twitter API anahtarları |
| `MODEL_PARAMS` | RF ve LSTM eğitim parametreleri |
| `STRATEGY_PARAMS` | Stop-Loss, Take-Profit oranları |
| `MACRO_GATE_ENABLED` | Makro filtre aktif/pasif |

---

## 3. Temel Kullanım

### A. Modellerin Eğitimi
```bash
python train_models.py
```
Modeller `models/saved/` klasörüne kaydedilir.

### B. Günlük Sinyal Üretimi
```bash
python daily_run.py
```
Terminalde al/sat önerileri görüntülenir.

### C. Backtest
```bash
python run_backtest.py
```
`reports/` klasöründe HTML rapor oluşturulur.

---

## 4. Paper Trading (Simülasyon)

### Stateless Paper Trading
```bash
python run_paper.py
```
- Shadow execution (gerçek emir yok)
- Slippage simülasyonu
- Macro Gate blokaj takibi

### Position-Aware Paper Trading
```bash
python paper_trading_position_aware/position_runner.py
```
- Pozisyon belleği (açık/kapalı takibi)
- Overtrading koruması
- Exposure limitleri

### Analiz Araçları
```bash
# Temel rapor
python analyze_paper.py

# Stress test (En kötü 20 gün)
python analyze_paper.py --stress

# Tam analiz (MAE/MFE dahil)
python analyze_paper.py --full
```

---

## 5. Karar Tipleri (Position-Aware)

| Karar | Açıklama |
|-------|----------|
| `OPEN_POSITION` | Yeni pozisyon aç |
| `HOLD_EXISTING` | Mevcut pozisyonu tut |
| `SCALE_IN` | Pozisyona ekle |
| `SCALE_OUT` | Pozisyonun bir kısmını sat |
| `CLOSE_POSITION` | Pozisyonu tamamen kapat |
| `IGNORE_SIGNAL` | Sinyali yoksay |

---

## 6. Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| "Module not found" | `pip install -r requirements.txt` |
| Veri hatası | İnternet bağlantısını kontrol edin |
| Model bulunamadı | `python train_models.py` çalıştırın |

---

## 7. Log Dosyaları

| Konum | İçerik |
|-------|--------|
| `logs/paper_trading/` | Stateless paper trading logları |
| `paper_trading_position_aware/logs/daily/` | Position-aware günlük loglar |
| `paper_trading_position_aware/logs/summary/` | Özet CSV |

---

**Son Güncelleme:** 2026-02-01 | **Versiyon:** 2.0
