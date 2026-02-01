
import sys
import os
from datetime import datetime
import pandas as pd

# Add root to path
sys.path.append(os.getcwd())

from daily_run import get_signal_snapshots
from core.paper_engine import PaperEngine

def run_paper_trading_session():
    print("\n" + "="*80)
    print(f"🎬 PAPER TRADING SESSION ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("="*80)
    
    # 1. Initialize Engine
    engine = PaperEngine()
    
    # 2. Get Signals (reusing logic from daily_run)
    print("\n[1/3] Sinyal Analizi Başlıyor...")
    try:
        snapshots = get_signal_snapshots(verbose=True)
    except Exception as e:
        print(f"❌ Sinyal üretimi sırasında hata: {e}")
        return

    # Check for System Halt
    if snapshots and 'error' in snapshots[0] and snapshots[0].get('error') in ['SYSTEM_HALTED', 'EMERGENCY_CLOSE']:
        print(f"\n🛑 İŞLEM DURDURULDU: {snapshots[0].get('reason')}")
        return

    # 3. Shadow Execution
    print("\n[2/3] Shadow Execution (Sanal Emir İletimi)...")
    execution_results = []
    
    for snap in snapshots:
        if 'error' in snap:
            print(f"   ⚠️ {snap['ticker']}: Hatalı Sinyal ({snap['error']}) - Atlanıyor.")
            continue
            
        # Execute in Paper Engine
        result = engine.execute_snapshot(snap)
        execution_results.append(result)
        
        # Console Feedback
        status_icon = "✅" if result['executed'] else "⛔"
        action_text = result.get('action_taken', 'BLOCKED')
        reason_text = f"({result['blocked_reason']})" if result['blocked_reason'] else ""
        
        print(f"   {status_icon} {result['ticker']:<10} | {action_text:<15} | Fiyat: {result['simulated_price']:.2f} | Miktar: {result['simulated_quantity']:.2f} {reason_text}")

    # 4. Session Summary
    print("\n[3/3] Oturum Özeti")
    executed_count = sum(1 for r in execution_results if r['executed'])
    blocked_count = sum(1 for r in execution_results if not r['executed'])
    
    print("-" * 40)
    print(f"Toplam Sinyal: {len(execution_results)}")
    print(f"İşleme Dönüşen: {executed_count}")
    print(f"Bloke Edilen : {blocked_count}")
    print("-" * 40)
    
    print(f"\n✅ Tüm kararlar 'logs/paper_trading/' altına kaydedildi.")

if __name__ == "__main__":
    run_paper_trading_session()
