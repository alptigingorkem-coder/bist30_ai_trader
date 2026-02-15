import os
import psycopg2
from psycopg2 import pool
import pandas as pd
from utils.logging_config import get_logger

log = get_logger(__name__)

class DBManager:
    _pool = None

    def __init__(self):
        self._initialize_pool()

    def _initialize_pool(self):
        if DBManager._pool is None:
            try:
                DBManager._pool = psycopg2.pool.SimpleConnectionPool(
                    1, 20,
                    user=os.environ.get("DB_USER", "postgres"),
                    password=os.environ.get("DB_PASSWORD", "password"),
                    host=os.environ.get("DB_HOST", "localhost"),
                    port=os.environ.get("DB_PORT", "5432"),
                    database=os.environ.get("DB_NAME", "bist30_trader")
                )
                log.info("Database connection pool created.")
                self._init_schema()
            except Exception as e:
                log.error(f"Error creating connection pool: {e}")
                DBManager._pool = None

    def get_connection(self):
        if DBManager._pool:
            return DBManager._pool.getconn()
        return None

    def return_connection(self, conn):
        if DBManager._pool and conn:
            DBManager._pool.putconn(conn)

    def _init_schema(self):
        """Initializes TimescaleDB schema and hypertables."""
        queries = [
            # Enable TimescaleDB extension
            "CREATE EXTENSION IF NOT EXISTS timescaledb;",
            
            # Market Data Table
            """
            CREATE TABLE IF NOT EXISTS market_data (
                time TIMESTAMPTZ NOT NULL,
                symbol TEXT NOT NULL,
                open DOUBLE PRECISION,
                high DOUBLE PRECISION,
                low DOUBLE PRECISION,
                close DOUBLE PRECISION,
                volume DOUBLE PRECISION,
                UNIQUE (time, symbol)
            );
            """,
            
            # Create Hypertable for market_data
            "SELECT create_hypertable('market_data', 'time', if_not_exists => TRUE);",
            
            # Fundamental Data Table
            """
            CREATE TABLE IF NOT EXISTS fundamental_data (
                time TIMESTAMPTZ NOT NULL,
                symbol TEXT NOT NULL,
                metric TEXT NOT NULL,
                value DOUBLE PRECISION,
                UNIQUE (time, symbol, metric)
            );
            """,
             "SELECT create_hypertable('fundamental_data', 'time', if_not_exists => TRUE);",

             # Trades Table
            """
            CREATE TABLE IF NOT EXISTS trades (
                time TIMESTAMPTZ NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                price DOUBLE PRECISION,
                amount INT,
                strategy TEXT
            );
            """,
             "SELECT create_hypertable('trades', 'time', if_not_exists => TRUE);"
        ]

        conn = self.get_connection()
        if conn:
            try:
                cur = conn.cursor()
                for query in queries:
                    cur.execute(query)
                conn.commit()
                cur.close()
                log.info("Database schema initialized.")
            except Exception as e:
                log.error(f"Schema initialization error: {e}")
                conn.rollback()
            finally:
                self.return_connection(conn)

    def fetch_data(self, symbol, start_date, end_date):
        """Fetches market data from DB."""
        conn = self.get_connection()
        if not conn: return None

        query = """
            SELECT time, open, high, low, close, volume
            FROM market_data
            WHERE symbol = %s AND time >= %s AND time <= %s
            ORDER BY time ASC;
        """
        try:
            df = pd.read_sql(query, conn, params=(symbol, start_date, end_date))
            if not df.empty:
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
                # Rename index to Date to match existing logic if needed, or keep time
                df.index.name = 'Date' 
            return df
        except Exception as e:
            log.error(f"Error fetching data for {symbol}: {e}")
            return None
        finally:
            self.return_connection(conn)

    def save_data(self, df, symbol):
        """Upserts market data into DB."""
        conn = self.get_connection()
        if not conn or df.empty: return

        try:
            cur = conn.cursor()
            # Prepare data
            # Assumes df index is datetime (Date)
            for index, row in df.iterrows():
                cur.execute("""
                    INSERT INTO market_data (time, symbol, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (time, symbol) DO UPDATE
                    SET open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume;
                """, (index, symbol, row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))
            
            conn.commit()
            cur.close()
            log.info(f"Saved {len(df)} records for {symbol} to DB.")
        except Exception as e:
            log.error(f"Error saving data for {symbol}: {e}")
            conn.rollback()
        finally:
            self.return_connection(conn)

    def close(self):
        if DBManager._pool:
            DBManager._pool.closeall()
