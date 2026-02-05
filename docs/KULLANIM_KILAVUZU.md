# BIST30 AI Trader - Kullanım Kılavuzu

Bu belge, BIST30 AI Trader yazılımının kurulumu, yapılandırılması ve etkili kullanımı için hazırlanmıştır. Sistem, hem günlük al/sat sinyalleri üretmek hem de risksiz ortamda stratejileri test etmek (Paper Trading) için gelişmiş araçlar sunar.

---

## 1. Kurulum ve Hazırlık

### Ön Gereksinimler
- **Python 3.8** veya üzeri yüklü olmalı.
- **Git** aracı yüklü olmalı.
- İnternet bağlantısı (Veri çekmek için).

### Hızlı Kurulum
Aşağıdaki komutları sırasıyla terminalde çalıştırarak sistemi hazır hale getirin:

```bash
# 1. Projeyi Klonlayın
git clone https://github.com/alptigingorkem-coder/bist30_ai_trader.git
cd bist30_ai_trader

# 2. Sanal Ortam Oluşturun (Önerilen)
python -m venv venv
.\venv\Scripts\activate

# 3. Kütüphaneleri Yükleyin
pip install -r requirements.txt

# 4. Ayar Dosyasını Oluşturun
copy config.example.py config.py
```

> [!NOTE]
> `config.py` dosyasını açarak API anahtarlarınızı (varsa) ve risk parametrelerini düzenleyebilirsiniz. Herhangi bir ayar yapmadan da varsayılan değerlerle çalışır.

---

## 2. Hangi Komut Ne İşe Yarar?

Sistemi kullanmak için aşağıdaki ana komutları kullanabilirsiniz.

### A. Günlük Sinyal Üretimi (`daily_run.py`)
Yapay zeka modellerini çalıştırarak o gün için al, sat veya tut tavsiyeleri üretir. **Agresif mod aktif: Sistem en iyi 5 hisseye odaklanır (Alpha Odaklı).**

- **Komut:** `python daily_run.py`
- **Ne Yapar?** 
  - **Otomatik Veri Çekme:** `LiveDataEngine` ile güncel fiyatları otomatik çeker (Manuel veri girişine gerek kalmaz).
  - **Veri Fallback:** Eğer otomatik çekim başarısız olursa, manuel giriş moduna geçer.
  - **Top 5 Seçimi:** En yüksek potansiyelli 5 hisseyi belirler (Konsantrasyon: Top 5).
  - **Ağırlıklı Tahsisat:** Risk Parity mantığıyla sermaye dağılımı önerir.
  - Macro Gate (Piyasa Güvenliği) kontrolü yapar (Opsiyonel/Devre Dışı).
  - Sonuçları ekrana yazar ve bir CSV raporu oluşturur.
- **Ne Zaman Çalıştırılmalı?** 
  - **Piyasa Kapandıktan Sonra (18:15+)**: Ertesi gün için plan yapmak amacıyla.
  - **Piyasa Açılmadan Önce (09:00 - 09:55)**: Son kontroller için.

### B. Paper Trading (Simülasyon)
Sistemi gerçek para riske etmeden test etmek için iki farklı mod bulunur.

#### 1. Stateless (Durumsuz) Mod (`run_paper.py`)
Anlık sinyal kalitesini test eder. Geçmiş pozisyonları hatırlamaz, sadece "o anki" sinyalin doğruluğuna ve sistemin engelleme yapıp yapmadığına bakar.

- **Komut:** `python run_paper.py`
- **Kullanım Amacı:** Stratejinin o an sinyal üretip üretmediğini, slippage (fiyat kayması) hesaplarını ve Macro Gate engellerini hızlıca kontrol etmek için.

#### 2. Position-Aware (Pozisyon Takipli) Mod (`position_runner.py`)
Gerçek bir portföy yönetir gibi çalışır. Kasanızdaki nakiti, açık pozisyonlarınızı ve kar/zarar durumunuzu takip eder.

- **Komut:** `python paper_trading/position_runner.py`
- **Ek Özellikler:**
  - `OPEN_POSITION`: Yeni hisse alır.
  - `CLOSE_POSITION`: Mevcut hisseyi satar.
  - `SCALE_IN/OUT`: Pozisyonu büyütür veya küçültür.
  - `HOLD`: Pozisyonu korur.
- **Ne Zaman Çalıştırılmalı?** Her işlem günü **bir kez**, tercihen piyasa kapanışından sonra (18:15+) çalıştırılmalıdır.

### C. Modelleri Eğitmek (`train_models.py`)
Yapay zeka modellerini (Random Forest ve ranker) güncel verilerle yeniden eğitir.

- **Komut:** `python train_models.py`
- **Ne Sıklıkla?** Haftada bir veya piyasada büyük bir değişim olduğunda çalıştırılması önerilir.

---

## 3. Verilerim Nerede?

Sistem ürettiği verileri düzenli bir klasör yapısında saklar. İşte önemli dosyaların yerleri:

### 📁 Paper Trading Verileri (Simülasyon)
Position-Aware modunu kullanırken oluşan tüm portföy verileri burada tutulur.

| Veri Tipi | Dosya Yolu | Açıklama |
|-----------|------------|----------|
| **Portföy Durumu** | `paper_trading/logs/portfolio_state.json` | Anlık nakit, açık hisseler ve maliyetleriniz. (**Bu dosya silinirse portföy sıfırlanır!**) |
| **Günlük Loglar** | `paper_trading/logs/daily/` | Her gün için oluşturulan detaylı işlem kayıtları (JSON). |
| **Özet Raporlar** | `paper_trading/logs/summary/` | Tüm oturumların özet performans tablosu (`all_sessions.csv`). |

### 📁 Stateless (Anlık) Test Logları
`run_paper.py` çalıştırdığınızda oluşan loglar.

- **Konum:** `logs/paper_trading/paper_trades_YYYY-MM-DD.json`

### 📁 Günlük Sinyal Raporları
`daily_run.py` ile üretilen al/sat sinyal listeleri.

- **Konum:** `reports/signals_YYYYMMDD.csv`
- **Format:** Excel ile açılabilir CSV dosyası. İçeriğe Tarih, Hisse, Sinyal, Güven Oranı ve Stop-Loss seviyeleri dahildir.

---

## 4. Sorun Giderme ve İpuçları

> [!TIP]
> **Portföyü Sıfırlamak İstiyorum:**
> Position-Aware modunda baştan başlamak isterseniz şu komutu kullanın:
> `python paper_trading/position_runner.py --reset`

| Sorun | Olası Neden | Çözüm |
|-------|-------------|-------|
| **"System Halted"** | Piyasa çok riskli (VIX yüksek veya sert düşüş). | Agresif modda bu hata nadirdir; `config.py` üzerinden Macro Gate'i kontrol edin. |
| **Sinyal Çıkmıyor** | Strateji kriterleri sağlanmıyor olabilir. | `daily_run.py` çıktısında modellerin güven eşiklerini (Confidence) kontrol edin. |
| **Veri Hatası** | İnternet bağlantısı kesik olabilir. | Bağlantınızı kontrol edip tekrar deneyin. |

---

**Teknik Destek:** Sorun yaşamaya devam ederseniz `logs/` klasöründeki son dosyaları inceleyerek hatanın kaynağını bulabilirsiniz.
