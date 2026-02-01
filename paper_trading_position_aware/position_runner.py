"""
Position-Aware Paper Trading - Main Orchestrator
Günlük çalıştırılan ana script.
"""

import sys
import os
from datetime import datetime

# Root'u path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from daily_run import get_signal_snapshots
from paper_trading_position_aware.portfolio_state import PortfolioState
from paper_trading_position_aware.position_engine import PositionExecutionEngine
from paper_trading_position_aware.position_logger import PositionLogger

def run_position_aware_session(verbose: bool = True):
    """
    Position-Aware Paper Trading oturumu çalıştır.
    
    1. Portföy state'ini yükle
    2. Sinyal snapshot'larını al
    3. Her sinyal için pozisyon kararı üret
    4. Kararları uygula ve logla
    5. Oturum özetini kaydet
    """
    
    print("\n" + "="*70)
    print("🎯 POSITION-AWARE PAPER TRADING OTURUMU")
    print(f"📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    # 1. Modülleri başlat
    portfolio = PortfolioState()
    engine = PositionExecutionEngine()
    logger = PositionLogger()
    
    if verbose:
        print(f"\n📊 Portföy Durumu (Başlangıç):")
        summary = portfolio.get_summary()
        print(f"   Nakit          : {summary['cash']:,.0f} TL")
        print(f"   Pozisyon Sayısı: {summary['positions_count']}")
        print(f"   Toplam Değer   : {summary['total_portfolio_value']:,.0f} TL")
        print(f"   Exposure       : %{summary['exposure_ratio']*100:.1f}")
    
    # 2. Sinyalleri al
    print(f"\n⏳ Sinyal snapshot'ları alınıyor...")
    try:
        snapshots = get_signal_snapshots(verbose=verbose)
    except Exception as e:
        print(f"❌ Sinyal alınamadı: {e}")
        return
    
    if not snapshots:
        print("⚠️ Hiç sinyal alınamadı.")
        return
    
    print(f"✅ {len(snapshots)} sinyal alındı.")
    
    # 3. Her sinyal için karar üret ve uygula
    print(f"\n🔄 Kararlar işleniyor...")
    
    stats = {
        'open': 0, 'close': 0, 'hold': 0,
        'scale_in': 0, 'scale_out': 0, 'ignore': 0
    }
    
    for i, snapshot in enumerate(snapshots):
        ticker = snapshot.get('ticker', 'UNKNOWN')
        signal = snapshot.get('action', 'WAIT')
        
        # Portföy durumu (öncesi)
        portfolio_before = portfolio.get_summary()
        
        # Karar üret
        decision = engine.decide(snapshot, portfolio)
        action = decision.get('action', 'IGNORE_SIGNAL')
        
        # Kararı uygula
        execution_result = portfolio.apply_trade_decision(decision)
        
        # Portföy durumu (sonrası)
        portfolio_after = portfolio.get_summary()
        
        # Logla
        logger.log_decision(
            snapshot=snapshot,
            decision=decision,
            portfolio_before=portfolio_before,
            portfolio_after=portfolio_after,
            execution_result=execution_result
        )
        
        # İstatistik güncelle
        if action == 'OPEN_POSITION':
            stats['open'] += 1
        elif action == 'CLOSE_POSITION':
            stats['close'] += 1
        elif action == 'HOLD_EXISTING':
            stats['hold'] += 1
        elif action == 'SCALE_IN':
            stats['scale_in'] += 1
        elif action == 'SCALE_OUT':
            stats['scale_out'] += 1
        else:
            stats['ignore'] += 1
        
        if verbose:
            action_emoji = {
                'OPEN_POSITION': '🟢',
                'CLOSE_POSITION': '🔴',
                'HOLD_EXISTING': '🟡',
                'SCALE_IN': '⬆️',
                'SCALE_OUT': '⬇️',
                'IGNORE_SIGNAL': '⚪'
            }
            emoji = action_emoji.get(action, '⚪')
            print(f"   [{i+1:2d}] {ticker:12s} | {signal:4s} → {emoji} {action}")
    
    # 4. Oturum özeti
    final_summary = portfolio.get_summary()
    
    print(f"\n" + "-"*70)
    print(f"📊 OTURUM ÖZETİ")
    print(f"-"*70)
    print(f"   Toplam Karar     : {len(snapshots)}")
    print(f"   Açılan Pozisyon  : {stats['open']}")
    print(f"   Kapatılan        : {stats['close']}")
    print(f"   Tutulan          : {stats['hold']}")
    print(f"   Scale In         : {stats['scale_in']}")
    print(f"   Scale Out        : {stats['scale_out']}")
    print(f"   Yoksayılan       : {stats['ignore']}")
    print(f"\n📈 PORTFÖY DURUMU (Son)")
    print(f"   Nakit            : {final_summary['cash']:,.0f} TL")
    print(f"   Pozisyon Sayısı  : {final_summary['positions_count']}")
    print(f"   Toplam Değer     : {final_summary['total_portfolio_value']:,.0f} TL")
    print(f"   Exposure         : %{final_summary['exposure_ratio']*100:.1f}")
    print(f"   Gerçekleşen PnL  : {final_summary['realized_pnl']:,.2f} TL")
    print(f"   Gerçekleşmemiş   : {final_summary['unrealized_pnl']:,.2f} TL")
    
    # 5. Özeti kaydet
    session_metrics = {
        'open_positions': stats['open'],
        'close_positions': stats['close'],
        'hold_existing': stats['hold'],
        'scale_in': stats['scale_in'],
        'scale_out': stats['scale_out'],
        'ignore_signals': stats['ignore'],
        'realized_pnl': final_summary['realized_pnl'],
        'unrealized_pnl': final_summary['unrealized_pnl'],
        'total_exposure': final_summary['total_exposure'],
        'portfolio_value': final_summary['total_portfolio_value']
    }
    
    logger.flush_session_summary(session_metrics)
    
    print(f"\n✅ Oturum tamamlandı. Loglar kaydedildi.")
    print("="*70)
    
    return final_summary

def reset_portfolio():
    """Portföyü sıfırla (test için)."""
    portfolio = PortfolioState()
    portfolio.reset()
    print("✅ Portföy sıfırlandı.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Position-Aware Paper Trading")
    parser.add_argument('--reset', action='store_true', help='Portföyü sıfırla')
    parser.add_argument('--quiet', action='store_true', help='Sessiz mod')
    
    args = parser.parse_args()
    
    if args.reset:
        reset_portfolio()
    else:
        run_position_aware_session(verbose=not args.quiet)
