import sys
import os
import pandas as pd

# Proje ana dizinini path'e ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.kap_data_fetcher import kap_fetcher

def test_kap_integration():
    ticker = "AKBNK.IS"
    print(f"Testing KAP integration for {ticker}...")
    
    # 1. Fetch Disclosures (Force Live)
    print("\n[Step 1] Fetching disclosures (Force Live)...")
    try:
        # Son 30 günlük veri çekelim (Timeout riskine karşı 3 güne düşürüldü)
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=3)
        
        df = kap_fetcher.fetch_disclosures(
            ticker=ticker,
            from_date=str(start_date),
            to_date=str(end_date),
            force_live=True # Canlı veri zorla
        )
        
        if not df.empty:
            print(f"SUCCESS: Fetched {len(df)} disclosures.")
            print(df.head())
        else:
            print("WARNING: No disclosures found (might be normal if no news).")
            
    except Exception as e:
        print(f"FAILED: {e}")
        return

    # 2. Create Event Features
    print("\n[Step 2] Creating event features...")
    try:
        # Mock price data
        dates = pd.date_range(end=date.today(), periods=10)
        price_df = pd.DataFrame({'Close': [10]*10}, index=dates)
        
        feature_df = kap_fetcher.create_event_features(ticker, price_df)
        
        print("Feature DF columns:", feature_df.columns.tolist())
        print(feature_df[['days_since_disclosure', 'disclosure_count_30d']].tail())
        
        if 'days_since_disclosure' in feature_df.columns:
            print("SUCCESS: Features created.")
        else:
            print("FAILED: Features missing.")
            
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_kap_integration()
