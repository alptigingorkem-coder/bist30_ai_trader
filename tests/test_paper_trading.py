"""
Position-Aware Paper Trading - Quick Test
OPEN → HOLD → CLOSE akışını test eder.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_trading.portfolio_state import PortfolioState
from paper_trading.position_engine import PositionEngine
from core.risk_manager import RiskManager

def test_position_flow():
    print("="*60)
    print("🧪 POSITION-AWARE TEST: OPEN → HOLD → CLOSE")
    print("="*60)
    
    # Fresh portfolio
    portfolio = PortfolioState(initial_capital=100000)
    risk_manager = RiskManager()
    
    engine = PositionEngine(portfolio, risk_manager)
    
    # Test 1: OPEN POSITION
    print("\n1️⃣ TEST: Target weight 0.05 → OPEN")
    decision1 = engine.process_signal(
        symbol='ASELS.IS',
        target_weight=0.05,  # 5% portfolio weight
        confidence=0.75,
        price=150.0
    )
    print(f"   Karar: {decision1['action']}")
    print(f"   Sebep: {decision1['reason']}")
    print(f"   Pozisyon var mı: {portfolio.has_position('ASELS.IS')}")
    
    assert decision1['action'] == engine.OPEN, "OPEN bekleniyor"
    assert portfolio.has_position('ASELS.IS'), "Pozisyon açılmalıydı"
    print("   ✅ PASS")
    
    # Test 2: HOLD (minimal weight change)
    print("\n2️⃣ TEST: Target weight 0.051 → HOLD (minimal change)")
    decision2 = engine.process_signal(
        symbol='ASELS.IS',
        target_weight=0.051,  # Very small change
        confidence=0.65,
        price=155.0
    )
    print(f"   Karar: {decision2['action']}")
    print(f"   Sebep: {decision2['reason']}")
    
    assert decision2['action'] == engine.HOLD, "HOLD bekleniyor"
    print("   ✅ PASS")
    
    # Test 3: SCALE_IN
    print("\n3️⃣ TEST: Target weight 0.08 → SCALE_IN")
    decision3 = engine.process_signal(
        symbol='ASELS.IS',
        target_weight=0.08,  # Increase to 8%
        confidence=0.80,
        price=160.0
    )
    print(f"   Karar: {decision3['action']}")
    print(f"   Sebep: {decision3['reason']}")
    
    assert decision3['action'] == engine.SCALE_IN, "SCALE_IN bekleniyor"
    print("   ✅ PASS")
    
    # Test 4: CLOSE
    print("\n4️⃣ TEST: Target weight 0 → CLOSE")
    decision4 = engine.process_signal(
        symbol='ASELS.IS',
        target_weight=0.0,  # Close position
        confidence=0.80,
        price=165.0
    )
    print(f"   Karar: {decision4['action']}")
    print(f"   Sebep: {decision4['reason']}")
    print(f"   Pozisyon var mı: {portfolio.has_position('ASELS.IS')}")
    
    assert decision4['action'] == engine.CLOSE, "CLOSE bekleniyor"
    assert not portfolio.has_position('ASELS.IS'), "Pozisyon kapanmalıydı"
    print("   ✅ PASS")
    
    # Özet
    print("\n" + "="*60)
    print("🎉 TÜM TESTLER GEÇTİ!")
    print(f"\n📊 Final Portföy:")
    print(f"   Nakit: {portfolio.cash:,.0f} TL")
    print(f"   Pozisyon: {portfolio.position_count()}")
    print(f"   Realized PnL: {portfolio.realized_pnl:,.2f} TL")
    print("="*60)

if __name__ == "__main__":
    test_position_flow()
