# BIST30 AI Trader - Kullanım Kılavuzu

Bu belge, BIST30 AI Trader yazılımının kurulumu, yapılandırılması ve kullanımı hakkında detaylı bilgi içerir.

## 1. Kurulum (Detaylı)

### Ön Hazırlıklar
- Python 3.8 veya daha yeni bir sürümün yüklü olduğundan emin olun (`python --version`).
- `git` aracının yüklü olduğundan emin olun.
- Bir terminal veya komut istemi (CMD/PowerShell) açın.

### Adım Adım Kurulum
1.  **Projeyi İndirin:**
    ```bash
    git clone https://github.com/kullaniciadi/bist30_ai_trader.git
    cd bist30_ai_trader
    ```

2.  **Sanal Ortam (Virtual Environment) Oluşturun:**
    Python projelerinde bağımlılıkların çakışmaması için sanal ortam kullanılması önerilir.
    
    *Windows:*
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
    
    *Linux/macOS:*
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    
    Aktif olduğunda komut satırınızın başında `(venv)` ibaresini görmelisiniz.

3.  **Kütüphaneleri Yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```

## 2. Yapılandırma (`config.py`)

Projenin tüm ayarları `config.py` dosyasında bulunur. Önemli ayarlar:

*   **API Anahtarları:** Eğer TCMB (EVDS) veya Twitter API kullanacaksanız ilgili alanları doldurun.
*   **MODEL_PARAMS:** Random Forest ve LSTM modellerinin eğitim parametreleri.
*   **STRATEGY_PARAMS:** `STOP_LOSS_PCT`, `TAKE_PROFIT_PCT` gibi risk yönetimi ayarları.
*   **DATA_SOURCE:** Veri kaynağı seçimi (yfinance vb.).

## 3. Çalıştırma

### A. Modellerin Eğitimi (`train_models.py`)
Sistemi ilk kez kurduğunuzda veya veri setini güncellediğinizde modelleri eğitmelisiniz.
```bash
python train_models.py
```
Bu işlem verileri indirir, işler ve modelleri eğitip `models/` klasörüne kaydeder.

### B. Günlük Analiz (`daily_run.py`)
Borsa kapandıktan sonra veya gün içinde sinyal üretmek için kullanılır.
```bash
python daily_run.py
```
Çıktılar:
- Terminalde al/sat önerileri.
- `reports/` klasöründe tarihli HTML raporu.

### C. Geçmiş Veri Testi (`run_backtest.py`)
Stratejinin geçmiş performansını görmek için kullanılır.
```bash
python run_backtest.py
```
Bu işlem detaylı bir simülasyon yapar ve HTML raporu üretir.

## 4. Sorun Giderme

- **"Module not found" hatası:** `pip install -r requirements.txt` komutunu `(venv)` aktifken çalıştırdığınızdan emin olun.
- **Veri hatası:** İnternet bağlantınızı kontrol edin. Yahoo Finance bazen geçici olarak erişilemez olabilir.

## 5. Raporları Okuma

`reports/` klasöründe üretilen HTML dosyalarını tarayıcınızla açarak detaylı grafikleri inceleyebilirsiniz. Raporlar şunları içerir:
- Kümülatif Getiri Grafiği
- İşlem Günlüğü (Trade Log)
- Aylık Getiri Tablosu
- Risk Metrikleri (Sharpe, Max Drawdown)
