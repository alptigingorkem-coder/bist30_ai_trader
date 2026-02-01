# Sorun Giderme Rehberi (Troubleshooting)

BIST30 AI Trader kullanırken karşılaşabileceğiniz yaygın sorunlar ve çözümleri aşağıda listelenmiştir.

## Sık Karşılaşılan Hatalar

### 1. "ModuleNotFoundError: No module named '...'"
**Sorun:** Gerekli Python kütüphaneleri yüklü değil veya sanal ortam (venv) aktif değil.
**Çözüm:**
1.  Terminalinizde sanal ortamın aktif olduğundan emin olun (satır başında `(venv)` yazmalı).
2.  Bağımlılıkları tekrar yükleyin:
    ```bash
    pip install -r requirements.txt
    ```

### 2. "API connection failed" veya "Data download error"
**Sorun:** İnternet bağlantısı yok veya veri sağlayıcı (Yahoo Finance, TCMB) geçici olarak erişilemez durumda.
**Çözüm:**
- İnternet bağlantınızı kontrol edin.
- `config.py` dosyasındaki API anahtarlarının doğru olduğunu doğrulayın.
- Yahoo Finance bazen çok fazla istek yapıldığında IP adresini geçici olarak engelleyebilir. Bir süre bekleyip tekrar deneyin.

### 3. "Model not trained" hatası
**Sorun:** `daily_run.py` veya backtest çalıştırmadan önce modeller eğitilmemiş.
**Çözüm:**
Önce eğitim betiğini çalıştırın:
```bash
python train_models.py
```

### 4. Raporlar Güncellenmiyor
**Sorun:** `reports/` klasöründeki HTML dosyaları eski tarihli kalıyor.
**Çözüm:**
- `daily_run.py` betiğinin başarıyla tamamlandığından emin olun (Hata mesajı var mı?).
- Dosya izinlerini kontrol edin.
- Klasördeki eski raporları silip tekrar deneyin.

### 5. Windows'ta "Execution Policy" Hatası
**Sorun:** `Activate.ps1` dosyasını çalıştırırken yetki hatası alıyorsunuz.
**Çözüm:**
PowerShell'i yönetici olarak açın ve şu komutu girin:
```bash
Set-ExecutionPolicy RemoteSigned
```

## Hala Sorun Yaşıyorsanız
Lütfen hatanın tam metni ve ekran görüntüsü ile birlikte GitHub üzerinden bir "Issue" açın.
