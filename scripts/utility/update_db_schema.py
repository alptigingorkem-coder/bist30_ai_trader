
import os
import sys
import psycopg2
from psycopg2 import pool

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from utils.logging_config import get_logger

log = get_logger("SchemaUpdater")

def update_schema():
    try:
        conn = psycopg2.connect(
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", "password"),
            host=os.environ.get("DB_HOST", "localhost"),
            port=os.environ.get("DB_PORT", "5432"),
            database=os.environ.get("DB_NAME", "bist30_trader")
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        log.info("Connected to DB. Starting schema update...")
        
        # 1. Check if trades table exists
        cur.execute("SELECT to_regclass('public.trades');")
        if not cur.fetchone()[0]:
            log.error("Trades table does not exist! Run migration first.")
            return

        # 2. Add columns
        columns = [
            ("order_type", "TEXT"),
            ("regime", "TEXT"),
            ("execution_notes", "TEXT")
        ]
        
        for col, dtype in columns:
            try:
                query = f"ALTER TABLE trades ADD COLUMN IF NOT EXISTS {col} {dtype};"
                cur.execute(query)
                log.info(f"✅ Authenticated column: {col}")
            except Exception as e:
                log.warning(f"⚠️ Could not add column {col}: {e}")
                
        log.info("Schema update completed successfully.")
        cur.close()
        conn.close()
        
    except Exception as e:
        log.error(f"❌ Connection or Execution Fail: {e}")

if __name__ == "__main__":
    update_schema()
