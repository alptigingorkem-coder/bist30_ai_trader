import os
import psycopg2
from psycopg2 import pool
import contextlib
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

    @contextlib.contextmanager
    def connection(self):
        """Context manager for safe connection handling."""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            self.return_connection(conn)

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
             "SELECT create_hypertable('trades', 'time', if_not_exists => TRUE);",

             # Portfolio Stats Table (NEW)
            """
            CREATE TABLE IF NOT EXISTS portfolio_stats (
                time TIMESTAMPTZ NOT NULL,
                equity DOUBLE PRECISION,
                cash DOUBLE PRECISION,
                position_count INT,
                exposure_ratio DOUBLE PRECISION,
                drawdown DOUBLE PRECISION,
                daily_return DOUBLE PRECISION
            );
            """,
            "SELECT create_hypertable('portfolio_stats', 'time', if_not_exists => TRUE);",

             # Stocks Master Table (NEW)
            """
            CREATE TABLE IF NOT EXISTS stocks (
                symbol TEXT PRIMARY KEY,
                sector TEXT,
                exchange TEXT DEFAULT 'BIST',
                is_active BOOLEAN DEFAULT TRUE,
                last_updated TIMESTAMPTZ DEFAULT NOW(),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        ]

        conn = self.get_connection()
        if conn:
            try:
                cur = conn.cursor()
                for query in queries:
                    cur.execute(query)
                conn.commit()
                cur.close()
                log.info("Database schema initialized with portfolio_stats.")
            except Exception as e:
                log.error(f"Schema initialization error: {e}")
                conn.rollback()
            finally:
                self.return_connection(conn)

    def save_portfolio_stats(self, stats_dict):
        """Saves portfolio performance metrics to DB."""
        if not DBManager._pool: return

        with self.connection() as conn:
            if not conn: return
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO portfolio_stats (time, equity, cash, position_count, exposure_ratio, drawdown, daily_return)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (
                    stats_dict.get('time', pd.Timestamp.now()),
                    stats_dict.get('equity'),
                    stats_dict.get('cash'),
                    stats_dict.get('position_count'),
                    stats_dict.get('exposure_ratio'),
                    stats_dict.get('drawdown'),
                    stats_dict.get('daily_return', 0.0)
                ))
                conn.commit()
                cur.close()
            except Exception as e:
                log.error(f"Error saving portfolio stats: {e}")
                conn.rollback()

    def fetch_data(self, symbol, start_date, end_date):
        """Fetches market data from DB."""
        # Use context manager
        if not DBManager._pool: return None
        
        with self.connection() as conn:
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

    def save_data(self, df, symbol):
        """Upserts market data into DB."""
        if not DBManager._pool or df.empty: return

        with self.connection() as conn:
            if not conn: return
            try:
                cur = conn.cursor()
                
                # Prepare data list of tuples
                data_values = []
                for index, row in df.iterrows():
                    data_values.append((
                        index, symbol, row['Open'], row['High'], row['Low'], row['Close'], row['Volume']
                    ))
                
                # Bulk Insert
                from psycopg2.extras import execute_batch
                
                query = """
                    INSERT INTO market_data (time, symbol, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (time, symbol) DO UPDATE
                    SET open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume;
                """
                
                execute_batch(cur, query, data_values)
                
                conn.commit()
                cur.close()
                log.info(f"Saved {len(df)} records for {symbol} to DB (Bulk).")
            except Exception as e:
                log.error(f"Error saving data for {symbol}: {e}")
                conn.rollback()

    def save_trade(self, trade_dict):
        """Saves a single trade execution to DB (Audit Trail)."""
        if not DBManager._pool: return

        with self.connection() as conn:
            if not conn: return
            try:
                cur = conn.cursor()
                # Ensure columns match schema: 
                # time, symbol, side, price, amount, strategy, order_type, regime, execution_notes
                query = """
                    INSERT INTO trades (time, symbol, side, price, amount, strategy, order_type, regime, execution_notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                cur.execute(query, (
                    trade_dict.get('time', pd.Timestamp.now()),
                    trade_dict.get('symbol'),
                    trade_dict.get('side'),
                    trade_dict.get('price'),
                    trade_dict.get('amount'),
                    trade_dict.get('strategy', 'Unknown'),
                    trade_dict.get('order_type'),    # New
                    trade_dict.get('regime'),        # New
                    trade_dict.get('execution_notes') # New
                ))
                conn.commit()
                cur.close()
            except Exception as e:
                log.error(f"Error saving trade for {trade_dict.get('symbol')}: {e}")
                conn.rollback()

    def register_stock(self, symbol, sector):
        """Upserts stock info into master table."""
        if not DBManager._pool: return

        with self.connection() as conn:
            if not conn: return
            try:
                cur = conn.cursor()
                query = """
                    INSERT INTO stocks (symbol, sector, last_updated)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (symbol) DO UPDATE
                    SET sector = EXCLUDED.sector,
                        last_updated = NOW();
                """
                cur.execute(query, (symbol, sector))
                conn.commit()
                cur.close()
            except Exception as e:
                log.error(f"Error registering stock {symbol}: {e}")
                conn.rollback()

    def get_active_tickers(self):
        """Returns list of active tickers from DB."""
        if not DBManager._pool: return []

        with self.connection() as conn:
            if not conn: return []
            try:
                cur = conn.cursor()
                cur.execute("SELECT symbol FROM stocks WHERE is_active = TRUE;")
                rows = cur.fetchall()
                cur.close()
                return [row[0] for row in rows]
            except Exception as e:
                log.error(f"Error fetching active tickers: {e}")
                return []

    def get_all_stocks(self):
        """Returns list of (symbol, sector) tuples for active stocks."""
        if not DBManager._pool: return []

        with self.connection() as conn:
            if not conn: return []
            try:
                cur = conn.cursor()
                cur.execute("SELECT symbol, sector FROM stocks WHERE is_active = TRUE;")
                rows = cur.fetchall()
                cur.close()
                return rows
            except Exception as e:
                log.error(f"Error fetching all stocks: {e}")
                return []

    def check_missing_data(self, ticker, days=3):
        """
        Checks if the latest data for the ticker is older than 'days'.
        Returns True if data is missing/stale.
        """
        if not DBManager._pool: return True # Assume missing if no DB

        with self.connection() as conn:
            if not conn: return True
            try:
                cur = conn.cursor()
                # Get max time for this symbol
                cur.execute("SELECT MAX(time) FROM market_data WHERE symbol = %s;", (ticker,))
                result = cur.fetchone()
                cur.close()
                
                if result and result[0]:
                    last_date = result[0]
                    # Convert to pd.Timestamp for comparison consistency or use datetime
                    # result[0] is likely datetime
                    import datetime
                    
                    # Naive vs Aware check
                    now = datetime.datetime.now(last_date.tzinfo)
                    diff = now - last_date
                    
                    if diff.days > days:
                        log.info(f"[Gap] {ticker}: Last data {diff.days} days ago ({last_date.date()}).")
                        return True
                    return False
                else:
                    log.info(f"[Gap] {ticker}: No data found in DB.")
                    return True # No data
            except Exception as e:
                log.error(f"Error checking missing data for {ticker}: {e}")
                return True # Default to True (Fetch it)

    def close(self):
        if DBManager._pool:
            DBManager._pool.closeall()
