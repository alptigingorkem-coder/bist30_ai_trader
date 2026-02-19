"""Verification utilities for database and trading system validation.

This module provides utility functions for verifying database records,
slippage calculations, and other system validations.
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.db_manager import DBManager
from core.backtest.engine import BacktestEngineMixin


class MockEngine(BacktestEngineMixin):
    """Mock engine for testing slippage calculations."""
    pass


def verify_db_records():
    """Verify database records by displaying recent portfolio stats and trades.
    
    Connects to the database and displays the last 5 records from
    portfolio_stats and trades tables.
    """
    print("="*70)
    print("DATABASE RECORDS VERIFICATION")
    print("="*70)
    
    db = DBManager()
    with db.connection() as conn:
        if conn:
            print("\n--- Portfolio Stats (Last 5) ---")
            df_stats = pd.read_sql(
                "SELECT * FROM portfolio_stats ORDER BY time DESC LIMIT 5;", 
                conn
            )
            print(df_stats)
            
            print("\n--- Trades (Last 5) ---")
            df_trades = pd.read_sql(
                "SELECT * FROM trades ORDER BY time DESC LIMIT 5;", 
                conn
            )
            print(df_trades)
        else:
            print("Failed to connect to DB")


def test_slippage(engine, vol, avg_vol, size):
    """Test slippage calculation for given parameters.
    
    Args:
        engine: BacktestEngineMixin instance with calculate_slippage method
        vol: Current volume
        avg_vol: Average volume
        size: Order size
    """
    slip = engine.calculate_slippage(vol, avg_vol, size)
    impact = size / avg_vol
    print(f"Size: {size:>10}, AvgVol: {avg_vol:>10}, "
          f"ImpactRatio: {impact:>6.2%}, "
          f"Slippage: {slip:.6f} ({slip*10000:.2f} bps)")


def verify_slippage():
    """Verify slippage calculations with various scenarios.
    
    Tests slippage calculation across different liquidity and order size
    scenarios to ensure proper market impact modeling.
    """
    print("="*70)
    print("SLIPPAGE VERIFICATION")
    print("="*70)
    
    engine = MockEngine()
    
    print("\n1. High Liquidity (Small Order)")
    test_slippage(engine, 1e6, 1e7, 1000)  # 0.01% ratio -> Expect 2bps spread
    
    print("\n2. Medium Liquidity (Medium Order)")
    test_slippage(engine, 1e6, 1e7, 400000)  # 4% ratio -> Expect 5bps spread
    
    print("\n3. Low Liquidity (Large Order)")
    test_slippage(engine, 1e6, 1e7, 900000)  # 9% ratio -> Expect 10bps spread
    
    print("\n4. Market Impact Zone (>10%)")
    test_slippage(engine, 1e6, 1e7, 2000000)  # 20% ratio -> Impact zone
    
    print("\n5. Huge Impact")
    test_slippage(engine, 1e6, 1e7, 5000000)  # 50% ratio -> Large impact


def main():
    """Run all verification tests."""
    verify_db_records()
    print("\n")
    verify_slippage()


if __name__ == "__main__":
    main()
