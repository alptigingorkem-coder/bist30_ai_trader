
from pykap.bist import BISTCompany
import pandas as pd
from datetime import datetime, timedelta

def test_pykap_detailed():
    print("=== PyKap Detaylı Test ===\n")
    
    ticker = 'AKBNK'
    akbnk = BISTCompany(ticker=ticker)
    
    # 1. Şirket Bilgileri
    print(f"1. Şirket: {akbnk.name}")
    print(f"   Şehir: {akbnk.city}")
    print(f"   Denetçi: {akbnk.auditor}")
    print(f"   Company ID: {akbnk.company_id}")
    
    # 2. Özet Sayfa
    print("\n2. Summary Page:")
    try:
        summary = akbnk.summary_page
        print(f"   Type: {type(summary)}")
        if isinstance(summary, dict):
            for k, v in list(summary.items())[:5]:
                print(f"   {k}: {v}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Geçmiş Bildirimler (Son 30 gün)
    print("\n3. Historical Disclosures (last 30 days):")
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        disclosures = akbnk.get_historical_disclosure_list(start_date=start_date, end_date=end_date)
        print(f"   Type: {type(disclosures)}")
        if disclosures:
            print(f"   Count: {len(disclosures)}")
            if isinstance(disclosures, list) and len(disclosures) > 0:
                print(f"   First Item Keys: {disclosures[0].keys() if isinstance(disclosures[0], dict) else 'N/A'}")
                print(f"   Sample: {disclosures[0]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Mali Raporlar
    print("\n4. Financial Reports:")
    try:
        reports = akbnk.get_financial_reports()
        print(f"   Type: {type(reports)}")
        if reports:
            print(f"   Count: {len(reports)}")
            if isinstance(reports, list) and len(reports) > 0:
                print(f"   First Item: {reports[0]}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_pykap_detailed()
