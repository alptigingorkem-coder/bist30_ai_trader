
import sys
import os
import pandas as pd
import numpy as np
import math

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.execution import ExecutionManager

def run_stress_test():
    print("="*60)
    print("🧪 MICRO-CAP STRESS TEST (Capital: 10,000 TL)")
    print("="*60)
    
    CAPITAL = 10000.0
    PORTFOLIO_SIZE = 3
    TARGET_ALLOCATION = CAPITAL / PORTFOLIO_SIZE # 3,333 TL per stock
    
    exec_manager = ExecutionManager(commission_rate=0.0025)
    
    # Mock efficient BIST30 Prices (Low, Medium, High)
    use_cases = [
        {'Symbol': 'EREGL', 'Price': 50.0},   # Low Price (Good granularity)
        {'Symbol': 'THYAO', 'Price': 300.0},  # Mid Price
        {'Symbol': 'FROTO', 'Price': 1000.0}  # High Price (Bad granularity)
    ]
    
    print(f"🎯 Target Allocation per Stock: {TARGET_ALLOCATION:.2f} TL\n")
    
    total_invested = 0
    total_commission = 0
    
    for case in use_cases:
        sym = case['Symbol']
        p = case['Price']
        
        # 1. Calculate Lots
        # ExecutionManager logic: lots = floor(cash / (price * (1+comm)))
        lots = exec_manager.calculate_optimal_lots(p, TARGET_ALLOCATION)
        
        # 2. Actual Cost
        raw_cost = lots * p
        comm = raw_cost * 0.0025
        total_cost = raw_cost + comm
        
        # 3. Deviations
        unused_cash = TARGET_ALLOCATION - total_cost
        deviation_pct = (unused_cash / TARGET_ALLOCATION) * 100
        
        total_invested += total_cost
        total_commission += comm
        
        print(f"🛒 {sym:<6} @ {p:>7.2f} TL")
        print(f"   Lots: {lots} | Cost: {total_cost:.2f} TL | Comm: {comm:.2f} TL")
        print(f"   Unused: {unused_cash:.2f} TL ({deviation_pct:.2f}% Error)")
        print("-" * 30)

    # Portfolio Level Stats
    total_unused = CAPITAL - total_invested
    unused_pct = (total_unused / CAPITAL) * 100
    
    print("\n📊 PORTFOLIO SUMMARY")
    print(f"Total Invested:   {total_invested:.2f} TL")
    print(f"Total Commission: {total_commission:.2f} TL (Immediate Loss)")
    print(f"Total Cash Drag:  {total_unused:.2f} TL ({unused_pct:.2f}%)")
    
    if unused_pct > 5.0:
        print("\n❌ CRITICAL FAIL: Cash Drag > 5%. Inefficient for Micro-Cap.")
        print("   Reason: High stock prices relative to capital prevent efficient allocation.")
    elif unused_pct > 2.0:
        print("\n⚠️ WARNING: Assessable Cash Drag (2-5%). Acceptable but suboptimal.")
    else:
        print("\n✅ PASS: Efficient Allocation (<2% Drag).")
        
    # Check Minimum Trade Viability (Rebalancing)
    print("\n🔄 REBALANCING CHECK")
    # Assume we need to trim 10% of FROTO (High Price)
    # FROTO Holding: 3 Lots * 1000 = 3000 TL.
    # Trim 10% = 300 TL.
    # Share Price = 1000 TL.
    # We cannot sell 0.3 shares. We sell 0. 
    # Result: We cannot rebalance small deviations.
    
    froto_price = 1000.0
    holding_val = 3000.0
    target_trim = 0.10 # 10% trim
    trim_val = holding_val * target_trim # 300 TL
    
    can_trim = trim_val >= froto_price
    print(f"Scenario: Trim 10% of FROTO ({trim_val:.0f} TL needed)")
    if not can_trim:
        print(f"❌ FAIL: Cannot rebalance. Share price ({froto_price}) > Trim Value ({trim_val}).")
        print("   Risk: Portfolio will drift significantly without correction.")
    else:
        print("✅ PASS: Rebalancing possible.")

if __name__ == "__main__":
    run_stress_test()
