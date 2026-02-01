"""
TCMB API Debug Script
Detaylı error analizi için test scripti
"""

import requests
import json

API_KEY = "cbyXzARc17"
BASE_URL = "https://evds2.tcmb.gov.tr/service/evds"

print("=" * 60)
print("TCMB API Detailed Debug")
print("=" * 60)

# Test 1: API Key validation endpoint
print("\n[Test 1] API Key Validation...")
try:
    url = f"{BASE_URL}/categories/"
    params = {'key': API_KEY, 'type': 'json'}
    response = requests.get(url, params=params, timeout=10)
    
    print(f"  URL: {url}")
    print(f"  Status Code: {response.status_code}")
    print(f"  Response: {response.text[:300]}")
    
    if response.status_code == 200:
        print("  ✅ API Key geçerli!")
    elif response.status_code == 401:
        print("  ❌ API Key geçersiz (401 Unauthorized)")
    elif response.status_code == 403:
        print("  ❌ API Key henüz aktif değil (403 Forbidden)")
    else:
        print(f"  ⚠️  Beklenmeyen status: {response.status_code}")
        
except requests.exceptions.Timeout:
    print("  ⏱️  Timeout - TCMB sunucusu yanıt vermiyor")
except requests.exceptions.ConnectionError as e:
    print(f"  ❌ Bağlantı hatası: {e}")
except Exception as e:
    print(f"  ❌ Hata: {type(e).__name__}: {e}")

# Test 2: Direct data request
print("\n[Test 2] Direct Data Request...")
try:
    url = f"{BASE_URL}/series"
    params = {
        'key': API_KEY,
        'type': 'json',
        'series': 'TP.YSSK.A02',
        'startDate': '01-01-2023',
        'endDate': '01-01-2024'
    }
    response = requests.get(url, params=params, timeout=10)
    
    print(f"  URL: {url}")
    print(f"  Params: {params}")
    print(f"  Status Code: {response.status_code}")
    print(f"  Response: {response.text[:300]}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"  ✅ Veri alındı! {len(data.get('items', []))} kayıt")
        except json.JSONDecodeError:
            print("  ⚠️  JSON parse hatası")
    else:
        print(f"  ❌ Başarısız: Status {response.status_code}")
        
except Exception as e:
    print(f"  ❌ Hata: {type(e).__name__}: {e}")

# Test 3: evds kütüphanesi versiyonu
print("\n[Test 3] evds Library Version...")
try:
    import evds
    print(f"  evds version: {evds.__version__ if hasattr(evds, '__version__') else 'Unknown'}")
    print(f"  evds location: {evds.__file__}")
except Exception as e:
    print(f"  ❌ evds import hatası: {e}")

print("\n" + "=" * 60)
print("Debug tamamlandı")
print("=" * 60)
