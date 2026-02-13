import torch
import sys
import os

print("="*30)
print("🚀 BIST30 AI TRADER - SİSTEM KONTROLÜ")
print("="*30)

# 1. Python ve Yer Kontrolü
print(f"📂 Çalışma Yolu: {os.getcwd()}")
print(f"🐍 Python Sürümü: {sys.version.split()[0]}")

# 2. GPU Kontrolü (AMD ROCm)
if torch.cuda.is_available():
    device_name = torch.cuda.get_device_name(0)
    print(f"✅ GPU BULUNDU: {device_name}")
    print(f"📊 VRAM Durumu: Harika!")
    
    # Küçük bir stres testi
    try:
        x = torch.rand(5000, 5000).cuda()
        y = torch.rand(5000, 5000).cuda()
        z = torch.matmul(x, y)
        print("⚡ GPU Test İşlemi: BAŞARILI (Matris Çarpımı)")
    except Exception as e:
        print(f"❌ GPU Test Hatası: {e}")
else:
    print("❌ GPU BULUNAMADI! (Sadece CPU çalışıyor)")

print("="*30)

