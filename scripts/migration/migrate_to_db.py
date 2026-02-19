
import os
import sys
import json
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_manager import DBManager
from core.feature_store import FeatureStore
from utils.logging_config import get_logger

log = get_logger(__name__)

def migrate_tickers():
    """Migrates tickers from tickers.json to SQL 'stocks' table."""
    log.info("--- Migrating Tickers ---")
    
    json_path = os.path.join(os.path.dirname(__file__), '../tickers.json')
    if not os.path.exists(json_path):
        log.error("tickers.json not found!")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    log.info(f"Found {len(data)} tickers in JSON.")
    
    db = DBManager()
    
    # We can handle custom connection here for raw psycopg2.extras
    with db.connection() as conn:
        if not conn:
            log.error("No DB Connection.")
            return
            
        cur = conn.cursor()
        
        # Schema: symbol, sector, exchange, is_active
        # last_updated has default NOW()
        values = [(item['symbol'], item['sector'], 'BIST', True) for item in data]
        
        query = """
            INSERT INTO stocks (symbol, sector, exchange, is_active)
            VALUES %s
            ON CONFLICT (symbol) DO UPDATE
            SET sector = EXCLUDED.sector,
                is_active = EXCLUDED.is_active,
                last_updated = NOW();
        """
        
        try:
            execute_values(cur, query, values)
            conn.commit()
            log.info(f"Successfully migrated {len(values)} tickers to DB.")
        except Exception as e:
            conn.rollback()
            log.error(f"Error migrating tickers: {e}")

def migrate_fundamentals():
    """Migrates fundamental data from FeatureStore (Parquet) to SQL 'fundamental_data' table."""
    log.info("--- Migrating Fundamentals ---")
    
    fs = FeatureStore()
    try:
        df = fs.load_fundamentals() # Could be empty if Parquet doesn't exist
    except ImportError as e:
        log.error(f"Failed to load fundamentals (Dependency Missing): {e}")
        return
    except Exception as e:
        log.error(f"Failed to load fundamentals: {e}")
        return
    
    if df.empty:
        log.warning("No fundamental data found in FeatureStore (fundamentals.parquet). Skipping.")
        return
        
    log.info(f"Loaded {len(df)} rows from Parquet.")
    
    # Ensure columns exist. Expected: Date, Ticker, Metric1, Metric2...
    # Typically FeatureStore saves Ticker, Date, PE, PB, etc.
    if 'Date' not in df.columns or 'Ticker' not in df.columns:
        log.error("Fundamentals dataframe missing required columns (Date, Ticker).")
        return
        
    # Standardize columns
    id_vars = ['Date', 'Ticker']
    
    # Identify value columns (all except Date/Ticker)
    value_cols = [c for c in df.columns if c not in id_vars]
    
    if not value_cols:
        log.warning("No metric columns found in fundamentals data.")
        return

    # Melt dataframe to long format (Time, Symbol, Metric, Value)
    df_long = df.melt(id_vars=id_vars, value_vars=value_cols, var_name='Metric', value_name='Value')
    
    # Remove NaN values and infinity
    df_long = df_long.dropna(subset=['Value'])
    import numpy as np
    df_long = df_long[~df_long['Value'].isin([np.inf, -np.inf])]
    
    log.info(f"Transformed to {len(df_long)} rows (Long Format).")
    
    db = DBManager()
    
    # Process in chunks
    chunk_size = 5000
    total_rows = len(df_long)
    
    with db.connection() as conn:
        if not conn: return
        cur = conn.cursor()
        
        query = """
            INSERT INTO fundamental_data (time, symbol, metric, value)
            VALUES %s
            ON CONFLICT (time, symbol, metric) DO UPDATE
            SET value = EXCLUDED.value;
        """
        
        start_time = time.time()
        
        # Prepare tuples generator
        all_values = list(zip(df_long['Date'], df_long['Ticker'], df_long['Metric'], df_long['Value']))
        
        for i in range(0, total_rows, chunk_size):
            chunk = all_values[i : i+chunk_size]
            
            try:
                execute_values(cur, query, chunk)
                conn.commit()
                if (i + chunk_size) % 10000 == 0:
                     log.info(f"Inserted {min(i + chunk_size, total_rows)} / {total_rows} rows...")
            except Exception as e:
                conn.rollback()
                log.error(f"Error inserting chunk {i}: {e}")
                
        duration = time.time() - start_time
        log.info(f"Migration complete in {duration:.2f}s.")

if __name__ == "__main__":
    migrate_tickers()
    
    try:
        if FeatureStore().load_fundamentals().empty:
             log.warning("Base fundamentals empty. Skipping fundamental migration.")
        else:
             migrate_fundamentals()
    except Exception as e:
        log.warning(f"Skipping Fundamental Migration due to error (likely missing pyarrow/fastparquet): {e}")
