
import os
import sys
import pandas as pd
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_manager import DBManager
from utils.logging_config import get_logger

log = get_logger(__name__)

def verify_db():
    log.info("--- Verifying Database Integrity ---")
    
    db = DBManager()
    
    # 1. Verify Stocks Table
    stocks = db.get_active_tickers()
    log.info(f"Active Tickers in DB: {len(stocks)}")
    
    if len(stocks) == 0:
        log.error("❌ No stocks found in DB! Migration failed?")
    else:
        log.info(f"✅ Stocks table populated. Sample: {stocks[:5]}")
        
    # 2. Verify Market Data (for a sample ticker)
    ticker = "THYAO.IS"
    if ticker in stocks:
        with db.connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM market_data WHERE symbol = %s", (ticker,))
            count = cur.fetchone()[0]
            log.info(f"Market Data Rows for {ticker}: {count}")
            if count > 0:
                log.info(f"✅ Market Data present for {ticker}.")
            else:
                log.warning(f"⚠️ No market data for {ticker}.")
                
    # 3. Verify Fundamentals
    with db.connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM fundamental_data")
        count = cur.fetchone()[0]
        log.info(f"Total Fundamental Data Rows: {count}")
        
        if count > 0:
             log.info("✅ Fundamental Data present.")
        else:
             log.warning("⚠️ Fundamental Data table is empty.")

if __name__ == "__main__":
    verify_db()
