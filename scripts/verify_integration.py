import sys
import os
import torch
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from utils.db_manager import DBManager
from utils.data_loader import DataLoader
from utils.logging_config import get_logger

log = get_logger("IntegrationVerify")

def check_gpu():
    log.info("--- 1. GPU Verification ---")
    if torch.cuda.is_available():
        log.info(f"✅ GPU Available: {torch.cuda.get_device_name(0)}")
        try:
            t = torch.tensor([1.0, 2.0]).cuda()
            log.info("✅ Tensor operation on GPU successful.")
        except Exception as e:
            log.error(f"❌ Tensor operation failed: {e}")
    else:
        log.warning("⚠️ GPU NOT Available (Running on CPU).")

def check_database():
    log.info("--- 2. Database Verification ---")

    try:
        db = DBManager()
        # Simple query to check market_data
        conn = db.get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM market_data;")
                count = cur.fetchone()[0]
            db.return_connection(conn)
            
            if count > 0:
                log.info(f"✅ Database Connection OK. 'market_data' row count: {count}")
            else:
                log.warning("⚠️ Database connected but 'market_data' is EMPTY.")
        else:
            log.error("❌ Failed to get DB connection from pool.")
            return False
            
    except Exception as e:
        log.error(f"❌ Database connection failed: {e}")
        return False
    return True

def check_dataloader():
    log.info("--- 3. DataLoader & Data Flow Verification ---")
    try:
        loader = DataLoader()
        ticker = "GARAN.IS" # Major stock, should exist
        
        # This will test the DB fetch logic we added
        log.info(f"Fetching data for {ticker} via DataLoader (should hit DB)...")
        df = loader.fetch_stock_data(ticker)
        
        if df is not None and not df.empty:
            log.info(f"✅ Data fetched successfully. Shape: {df.shape}")
            log.info(f"   Last date: {df.index[-1]}")
            
            # Check if it came from DB (logic inside DataLoader logs this, but we can infer by speed or logs)
        else:
            log.error(f"❌ DataLoader returned Empty/None for {ticker}")
            
    except Exception as e:
        log.error(f"❌ DataLoader test failed: {e}")

if __name__ == "__main__":
    log.info("Starting Comprehensive Integration Check...")
    check_gpu()
    if check_database():
        check_dataloader()
    log.info("Integration Check Completed.")
