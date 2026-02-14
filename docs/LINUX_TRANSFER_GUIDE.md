# 🐧 Linux Geçiş ve Devir Teslim Rehberi

Bu belge, **BIST30 AI Trader** projesinin Windows ortamından Linux (AMD ROCm) ortamına taşınması sürecinde, sonraki yapay zeka asistanına ve geliştiriciye (size) rehberlik etmek amacıyla hazırlanmıştır.

## 📅 Mevcut Durum (14.02.2026)
- **Proje Versiyonu:** 2.1.1 (Patch)
- **Son Çalışılan Dal:** `changes` (GitHub: `alptigingorkem-coder/bist30_ai_trader`)
- **Model Durumu:**
    - ✅ **LightGBM (Ranking):** Başarıyla eğitildi ve `models/saved/global_ranker.pkl` olarak kaydedildi.
    - ⏳ **TFT (Transformer):** Windows üzerinde CPU/RAM darboğazı ve "Device Side Assert" hataları nedeniyle eğitimi **yarım kaldı**.
- **Kritik Gelişmeler:**
    - **KAP Entegrasyonu:** Tamamlandı, `utils/kap_data_fetcher.py` stabilize edildi.
    - **Risk Yönetimi:** Agresif moddan güvenli moda geçildi (`RISK_PER_TRADE = 0.05`).

## 🎯 Hedef
TFT (Temporal Fusion Transformer) modelini, AMD GPU gücünden faydalanarak **Linux + ROCm** altyapısında eğitmek ve tüm sistemi canlı simülasyon (Paper Trading) için hazır hale getirmek.

---

## 🛠️ Kurulum Adımları (Linux Tarafında)

Yeni ortama geçtiğinizde (Gemini veya kendiniz), bu sırayı takip ediniz:

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/alptigingorkem-coder/bist30_ai_trader.git
cd bist30_ai_trader
git checkout changes
```

### 2. Sanal Ortam ve Bağımlılıklar
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
# Standart paketler
pip install -r requirements.txt
```

### 3. AMD ROCm Kurulumu (Kritik)
PyTorch'un ROCm sürümünü kurmalısınız. Sisteminizdeki ROCm versiyonuna (örn: 6.0, 6.1) uygun komutu kullanın:
```bash
# Örnek (ROCm 6.0 için):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0
```

### 4. GPU Doğrulaması
Python konsolunda GPU'nun görüldüğünü teyit edin:
```python
import torch
print(torch.cuda.is_available()) # True dönmeli
print(torch.cuda.get_device_name(0)) # AMD Radeon... dönmeli
```

---

## ⚠️ Yapılması Gereken Kod Değişiklikleri

Windows uyumluluğu için yapılan bazı ayarlar Linux'ta performansı düşürebilir. Lütfen aşağıdaki dosyaları güncelleyin:

### 1. `config.py` - Cihaz Tespiti
Mevcut kodda `get_device` fonksiyonu basitleştirilmiş olabilir. ROCm, PyTorch tarafından `cuda` olarak tanınır.

**Kontrol Edin:**
```python
def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")  # ROCm burada 'cuda' olarak geçer
    # Apple Silicon (MPS) Desteği
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")
```

### 2. `models/transformer_model.py` - Veri Yükleme Hızı
Windows'ta `num_workers=0` zorunluluğu vardı. Linux'ta bunu artırarak veri yükleme hızını katlayabilirsiniz.

**Değiştirin:**
```python
# Satır ~132 ve ~135 civarı
train_dataloader = train_dataset.to_dataloader(
    train=True, batch_size=batch_size, num_workers=4 # 0 yerine 4 veya 8 yapın
)
```

---

## 🚀 Eğitimi Başlatma

Her şey hazırsa, eğitimi başlatmak için:

```bash
python train_models.py
```

Bu komut önce LightGBM'i (hızlıca) tekrar eğitecek, ardından TFT model eğitimini başlatacaktır. GPU kullanımı sayesinde eğitimin çok daha hızlı tamamlanması beklenmektedir.

## 📝 Sonraki Asistana Not
> "Merhaba, ben önceki oturumdan Gemini. Kullanıcı projeyi Windows'tan Linux'a taşıdı. En son TFT modeli eğitmeye çalışıyorduk ancak donanım yetersizdi. Lütfen yukarıdaki adımları takip ederek ortamı kurmasına yardımcı ol ve `train_models.py` çalıştırıldığında hata alınıp alınmadığını kontrol et. `config.py` içindeki Makro Feature'lar (`ENABLE_MACRO_IN_MODEL`) kapalı durumda, bu bilinçli bir tercih. Başarılar!"
