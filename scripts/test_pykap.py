import pykap
import pandas as pd

# pykap kullanımı hakkında çok az belge var, genelde 'get_bist_companies' ve 'get_general_info' fonksiyonları bilinir.
# Deneme yanılma ile API keşfi.

try:
    print("Fetching BIST Companies via pykap...")
    # pykap.get_bist_companies() sanırım liste dönüyor
    # Kütüphane yapısını dir() ile görelim önce
    print("pykap dir:", dir(pykap))
    
    # Genelde pykap.KB() veya pykap.bist_companies() gibi class/func vardır.
    # Varsayım: pykap kullanımı (Github examples based)
    
    # 1. Bildirim Çekme Denemesi (KAP)
    # KAP parametreleri karmaşık olabilir.
    
    # Eğer kütüphane class tabanlıysa:
    if hasattr(pykap, 'KAP'):
        kap = pykap.KAP()
        print("Initialized KAP object.")
    
    # Veya fonksiyonel:
    if hasattr(pykap, 'get_bist_companies'):
        comps = pykap.get_bist_companies()
        print("Companies:", comps[:5])

except Exception as e:
    print(f"pykap Error: {e}")

# Alternatif: Eğer pykap çok basic ise, requests ile KAP API public endpointlerini deneyebiliriz.
# https://www.kap.org.tr/tr/api/bistCompanies
