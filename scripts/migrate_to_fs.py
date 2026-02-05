import sys
import os
sys.path.append(os.getcwd())
from core.feature_store import feature_store
import time

def migrate():
    start = time.time()
    try:
        df = feature_store.import_from_excel('data/fundamental_data.xlsx')
        print(f"Migration successful! Imported {len(df)} rows.")
        
        # Test Read
        t1 = time.time()
        df_read = feature_store.load_fundamentals()
        t2 = time.time()
        print(f"Read Perf Test: Loaded {len(df_read)} rows in {t2-t1:.4f} seconds.")
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
