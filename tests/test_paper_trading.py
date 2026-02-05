"""
Position-Aware Paper Trading - Quick Test
OPEN → HOLD → CLOSE akışını test eder.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_trading.portfolio_state import PortfolioState
from paper_trading.position_engine import PositionExecutionEngine

def test_position_flow():
    print("="*60)
    print("🧪 POSITION-AWARE TEST: OPEN → HOLD → CLOSE")
    print("="*60)
    
    # Fresh portfolio
    portfolio = PortfolioState(initial_capital=100000)
    portfolio.reset()
    
    engine = PositionExecutionEngine(default_position_size=0.05)
    
    # Test 1: OPEN POSITION
    print("\n1️⃣ TEST: BUY sinyali → OPEN_POSITION")
    snapshot1 = {
        'ticker': 'ASELS.IS',
        'action': 'BUY',
        'confidence': 0.75,
        'regime': 'Trend_Up',
        'macro_blocked': False,
        'current_price': 150.0
    }
    
    decision1 = engine.decide(snapshot1, portfolio)
    print(f"   Karar: {decision1['action']}")
    print(f"   Sebep: {decision1['reason']}")
    
    result1 = portfolio.apply_trade_decision(decision1)
    print(f"   Sonuç: {result1['message']}")
    print(f"   Pozisyon var mı: {portfolio.has_position('ASELS.IS')}")
    
    assert decision1['action'] == 'OPEN_POSITION', "OPEN_POSITION bekleniyor"
    assert portfolio.has_position('ASELS.IS'), "Pozisyon açılmalıydı"
    print("   ✅ PASS")
    
    # Test 2: HOLD (aynı sinyal tekrar)
    print("\n2️⃣ TEST: BUY sinyali tekrar → HOLD_EXISTING")
    snapshot2 = {
        'ticker': 'ASELS.IS',
        'action': 'BUY',
        'confidence': 0.65,  # Düşük güven - scale in olmaz
        'regime': 'Trend_Up',
        'macro_blocked': False,
        'current_price': 155.0
    }
    
    decision2 = engine.decide(snapshot2, portfolio)
    print(f"   Karar: {decision2['action']}")
    print(f"   Sebep: {decision2['reason']}")
    
    assert decision2['action'] == 'HOLD_EXISTING', "HOLD_EXISTING bekleniyor"
    print("   ✅ PASS")
    
    # Test 3: CLOSE
    print("\n3️⃣ TEST: SELL sinyali → CLOSE_POSITION")
    snapshot3 = {
        'ticker': 'ASELS.IS',
        'action': 'SELL',
        'confidence': 0.80,  # Yüksek güven - tam kapat
        'regime': 'Crash_Bear',
        'macro_blocked': False,
        'current_price': 160.0
    }
    
    decision3 = engine.decide(snapshot3, portfolio)
    print(f"   Karar: {decision3['action']}")
    print(f"   Sebep: {decision3['reason']}")
    
    result3 = portfolio.apply_trade_decision(decision3)
    print(f"   Sonuç: {result3['message']}")
    print(f"   Realized PnL: {result3.get('realized_pnl', 0):.2f} TL")
    print(f"   Pozisyon var mı: {portfolio.has_position('ASELS.IS')}")
    
    assert decision3['action'] == 'CLOSE_POSITION', "CLOSE_POSITION bekleniyor"
    assert not portfolio.has_position('ASELS.IS'), "Pozisyon kapanmalıydı"
    print("   ✅ PASS")
    
    # Test 4: MACRO GATE with position
    print("\n4️⃣ TEST: Macro Gate + mevcut pozisyon → HOLD")
    
    # Önce yeni pozisyon aç
    portfolio.apply_trade_decision({
        'action': 'OPEN_POSITION',
        'symbol': 'THYAO.IS',
        'price': 200.0,
        'quantity': 25,
        'side': 'LONG'
    })
    
    snapshot4 = {
        'ticker': 'THYAO.IS',
        'action': 'BUY',
        'confidence': 0.70,
        'regime': 'Sideways',
        'macro_blocked': True,  # Macro gate aktif
        'current_price': 210.0
    }
    
    decision4 = engine.decide(snapshot4, portfolio)
    print(f"   Karar: {decision4['action']}")
    print(f"   Sebep: {decision4['reason']}")
    
    assert decision4['action'] == 'HOLD_EXISTING', "Macro gate ile HOLD bekleniyor"
    print("   ✅ PASS")
    
    # Özet
    print("\n" + "="*60)
    print("🎉 TÜM TESTLER GEÇTİ!")
    summary = portfolio.get_summary()
    print(f"\n📊 Final Portföy:")
    print(f"   Nakit: {summary['cash']:,.0f} TL")
    print(f"   Pozisyon: {summary['positions_count']}")
    print(f"   Realized PnL: {summary['realized_pnl']:,.2f} TL")
    print("="*60)

if __name__ == "__main__":
    test_position_flow()
