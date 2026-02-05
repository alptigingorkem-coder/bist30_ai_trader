from pykap.bist import BISTCompany
import pandas as pd

try:
    print("Testing BISTCompany class for AKBNK...")
    # Dokümantasyona göre kullanım: comp = BISTCompany(ticker='AKBNK')
    akbnk = BISTCompany(ticker='AKBNK')
    
    # 1. Bildirimleri Al
    # get_disclosure_summary gibi metodlar olabilir.
    print("Fetching disclosures...")
    # Tarih aralığı verelim
    disclosures = akbnk.get_latests_disclosure_announcements(count=5)
    print("Disclosures:", disclosures)
    
    # 2. Mali Tablolar?
    # Bu kütüphane genelde sadece KAP duyurularını çeker.
    # Financial report çekme özelliği var mı bakalım.
    print("Available methods:", dir(akbnk))

except Exception as e:
    print(f"BISTCompany Error: {e}")
