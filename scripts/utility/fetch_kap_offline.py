
import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
import concurrent.futures

# Proje kök dizinini path'e ekle
sys.path.append(os.getcwd())

import config
from utils.kap_data_fetcher import kap_fetcher

def fetch_ticker_history(ticker):
    """Tek bir hisse için tüm geçmişi indirir."""
    try:
        print(f"⏳ {ticker} için geçmiş veriler indiriliyor...")
        
        # Son 10 yıl
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365 * 10)
        
        # 1. Bildirimler (ODA - Özel Durum Açıklaması)
        # Force cache update by implicitly running fetch which saves to cache
        df_disclosures = kap_fetcher.fetch_disclosures(
            ticker, 
            from_date=str(start_date), 
            to_date=str(end_date),
            disclosure_type='ODA',
            use_cache=False # Force download to update cache
        )
        
        # 2. Mali Raporlar (Finansal Raporlar)
        df_financials = kap_fetcher.fetch_financial_reports(
            ticker,
            from_date=str(start_date),
            to_date=str(end_date),
            use_cache=False
        )
        
        count_disc = len(df_disclosures)
        count_fin = len(df_financials)
        
        return f"✅ {ticker}: {count_disc} bildirim, {count_fin} rapor indirildi."
        
    except Exception as e:
        return f"❌ {ticker} HATASI: {e}"

def main():
    print("="*60)
    print("📥 KAP OFFLINE VERİ İNDİRİCİ (CACHE OLUŞTURUCU)")
    print("="*60)
    
    start_time = time.time()
    tickers = config.TICKERS
    print(f"Hedef: {len(tickers)} hisse için son 10 yıllık veri.")
    
    # Paralel indirme (Worker sayısını abartma, KAP banlamasın)
    # PyKap zaten içeride web request yapıyor, 4 worker güvenli.
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_ticker = {executor.submit(fetch_ticker_history, t): t for t in tickers}
        
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                res = future.result()
                print(res)
                results.append(res)
            except Exception as e:
                print(f"❌ {ticker} Thread Hatası: {e}")

    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print(f"🏁 İŞLEM TAMAMLANDI ({elapsed:.1f} saniye)")
    print("="*60)

if __name__ == "__main__":
    main()
