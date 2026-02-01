import requests
import json
import config

API_KEY = config.TCMB_API_KEY
SERIES = "TP.DK.USD.A.YTL" # Dolar Kuru (Alış)
START_DATE = "01-01-2024"
END_DATE = "01-01-2024"

# EVDS API Endpoint
URL = f"https://evds2.tcmb.gov.tr/service/evds/series={SERIES}&startDate={START_DATE}&endDate={END_DATE}&type=json&key={API_KEY}"

print(f"API Key Test Ediliyor: {API_KEY}")
print("-" * 30)

try:
    response = requests.get(URL)
    
    if response.status_code == 200:
        try:
            data = response.json()
            if "error" in data: # Bazen JSON döner ama içinde hata mesajı olur
                 print("API Hatası (JSON):", data["error"])
            # EVDS bazen items yerine totalCount=0 döner hata durumunda
            elif "totalCount" in data and data["totalCount"] == 0:
                 print("Veri dönmedi (Count=0). API Key yetkisi veya parametre hatası olabilir.")
                 print("Raw Response:", data)
            elif "items" in data:
                 print("✅ BAŞARILI! API Key aktif.")
                 print("Örnek Veri:", data["items"][0])
            else:
                 # Farklı bir format olabilir, başarılı sayalım
                 print("✅ BAŞARILI OLABİLİR (Format farklı).")
                 print("Raw Response:", data)
        except json.JSONDecodeError:
            # HTML dönerse hata vardır
            print("❌ BAŞARISIZ. API HTML döndürdü (Muhtemelen Key Hatası veya IP Kısıtlaması).")
            # print(response.text[:200])
    else:
        print(f"❌ HTTP Hatası: {response.status_code}")
        print(response.text[:200])

except Exception as e:
    print(f"❌ Bağlantı Hatası: {e}")
