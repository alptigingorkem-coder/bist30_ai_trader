import sys
import os
import pandas as pd
import yfinance as yf
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from utils.db_manager import DBManager
from utils.logging_config import get_logger

log = get_logger("Migration")

def migrate_market_data(db):
    """Fetches full history for all tickers and saves to DB."""
    log.info("Starting Market Data Migration...")
    
    start_date = "2010-01-01" # Long history
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for ticker in config.TICKERS:
        log.info(f"Migrating {ticker}...")
        try:
            # Download full history
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                log.warning(f"  No data found for {ticker}")
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                 df.columns = df.columns.droplevel(1)
            
            # Rename columns if needed (yfinance usually returns Capitalized)
            # DB expects: Open, High, Low, Close, Volume
            
            # Save to DB
            db.save_data(df, ticker)
            
        except Exception as e:
            log.error(f"  Error migrating {ticker}: {e}")

def migrate_fundamentals(db):
    """Migrates fundamentals.parquet to DB."""
    log.info("Starting Fundamental Data Migration...")
    
    parquet_path = os.path.join(config.DATA_DIR, "feature_store", "fundamentals.parquet")
    if not os.path.exists(parquet_path):
        log.warning(f"  Fundamentals file not found: {parquet_path}")
        return

    try:
        df = pd.read_parquet(parquet_path)
        # Assumes df has: Date/Time, Ticker, Metric columns...
        # Need to inspect parquet structure. 
        # For now, let's assume a generic melt or structure.
        # If structure is wide (Ticker, Date, PE, PB...), melt it.
        
        # Checking loaded parquet structure in previous steps or assuming?
        # Let's inspect it in the script dynamically.
        
        log.info(f"  Loaded {len(df)} rows from parquet.")
        
        # TODO: Implement parquet to DB mapping based on actual structure.
        # Placeholder for now.
        
    except Exception as e:
        log.error(f"  Error migrating fundamentals: {e}")

if __name__ == "__main__":
    db = DBManager()
    
    # 1. Market Data
    migrate_market_data(db)
    
    # 2. Fundamentals
    # migrate_fundamentals(db) # Uncomment after inspecting structure
    
    log.info("Migration Completed.")
