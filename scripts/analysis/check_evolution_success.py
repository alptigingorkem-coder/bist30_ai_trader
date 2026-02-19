
import sys
import os
import random
import logging

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.execution import ExecutionManager, SmartOrderRouter, Urgency, OrderType
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger("EvolutionCheck")

def check_evolution():
    print(f"\n{'='*60}")
    print(f"🚀 ARCHITECTURAL EVOLUTION: SUCCESS CHECK")
    print(f"{'='*60}\n")
    
    failures = []
    
    # --- TEST 1: DYNAMIC ENSEMBLE REGIMES ---
    print(f"🔍 TEST 1: Dynamic Ensemble Weights (Regime Bridge)")
    regimes = ['TREND_UP', 'SIDEWAYS', 'CRISIS', 'VOLATILE', 'NORMAL']
    
    # Config existence check
    if not hasattr(config, 'ENSEMBLE_REGIME_WEIGHTS'):
        failures.append("❌ Config missing 'ENSEMBLE_REGIME_WEIGHTS'")
        print("❌ Config missing 'ENSEMBLE_REGIME_WEIGHTS'")
    else:
        print(f"✅ Config found. Simulating 5 Random Regimes:")
        
        for i in range(5):
            r = random.choice(regimes)
            weights = config.ENSEMBLE_REGIME_WEIGHTS.get(r, "DEFAULT")
            
            # Check logic
            status = "UNKNOWN"
            if r == 'CRISIS':
                # Expect High LGBM
                if weights.get('lgbm', 0) > 0.8: status = "✅ PASS (Crisis Mode)"
                else: status = "❌ FAIL (Crisis should favor LGBM)"
            elif r == 'TREND_UP':
                # Expect High TFT
                if weights.get('tft', 0) > 0.4: status = "✅ PASS (Trend Mode)"
                else: status = "❌ FAIL (Trend should favor TFT)"
            else:
                status = "✅ PASS (Standard Mode)"
                
            print(f"   - Regime: {r:<10} -> Weights: {str(weights):<40} {status}")
            if "FAIL" in status: failures.append(f"Regime Logic Fail: {r}")


    # --- TEST 2: SMART ORDER ROUTER (SOR) ---
    print(f"\n🔍 TEST 2: Smart Order Router (Execution Upgrade)")
    
    exec_manager = ExecutionManager(commission_rate=0.001)
    sor = SmartOrderRouter(exec_manager)
    
    sides = ['BUY', 'SELL']
    urgencies = list(Urgency)
    
    print(f"✅ SOR Initialized. Generating 10 Random Orders:")
    
    for i in range(10):
        side = random.choice(sides)
        urgency = random.choice(urgencies)
        base_price = 100.0
        qty = 10
        
        order = sor.generate_order("TEST", side, base_price, qty, urgency)
        
        # Validation
        p_diff = order['price'] - base_price
        p_pct = (p_diff / base_price) * 100
        
        notes = order.get('note', '')
        otype = order.get('type')
        
        validation = "UNKNOWN"
        if urgency == Urgency.HIGH:
            if otype == OrderType.MARKET: validation = "✅ PASS (Market/High)"
            else: validation = "❌ FAIL (High should be Market)"
        elif urgency == Urgency.NORMAL:
            if otype == OrderType.LIMIT and abs(p_pct) < 0.001: validation = "✅ PASS (Limit/Normal)"
            else: validation = "❌ FAIL (Normal should be Limit@Market)"
        elif urgency == Urgency.LOW:
            # Check price improvement
            if side == 'BUY' and p_diff < 0: validation = "✅ PASS (Passive Buy)"
            elif side == 'SELL' and p_diff > 0: validation = "✅ PASS (Passive Sell)"
            else: validation = "❌ FAIL (Low Urgency should improve price)"
            
        print(f"   - {i+1}. {side:<4} {urgency.name:<6} -> Type: {otype.name:<6} | Price: {order['price']:.4f} ({p_pct:+.2f}%) | {validation}")
        if "FAIL" in validation: failures.append(f"SOR Fail: {urgency.name}")


    # --- FINAL REPORT ---
    print(f"\n{'='*60}")
    if not failures:
        print(f"🏆 SONUÇ: BAŞARILI (SUCCESS)")
        print(f"   Tüm mimari gereksinimler doğrulanmıştır.")
    else:
        print(f"⚠️ SONUÇ: BAŞARISIZ (FAILURE)")
        print(f"   Hatalar:")
        for f in failures:
            print(f"   - {f}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    check_evolution()
