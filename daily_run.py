
import pandas as pd
from datetime import datetime
import config
import sys
import os

# Sektör Stratejileri
from strategies.banking_strategy import BankingStrategy
from strategies.holding_strategy import HoldingStrategy
from strategies.industrial_strategy import IndustrialStrategy
from strategies.growth_strategy import GrowthStrategy
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from utils.portfolio_manager import PortfolioManager
from utils.sector_allocator import SectorAllocator
from utils.performance_tracker import PerformanceTracker

portfolio_mgr = PortfolioManager(initial_capital=100000)
sector_alloc = SectorAllocator(max_concentration=getattr(config, 'MAX_SECTOR_CONCENTRATION', 0.40))
perf_tracker = PerformanceTracker()

# Sektör Konfigürasyonları (Single Source of Truth)
from configs import banking as config_banking
from configs import holding as config_holding
from configs import industrial as config_industrial
from configs import growth as config_growth

# Sektör Haritası (Dinamik)
SECTOR_MAP = {
    'BANKING': config_banking.TICKERS,
    'HOLDING': config_holding.TICKERS,
    'INDUSTRIAL': config_industrial.TICKERS,
    'GROWTH': config_growth.TICKERS
}

def get_strategy_for_ticker(ticker):
    if ticker in SECTOR_MAP['BANKING']: return BankingStrategy()
    if ticker in SECTOR_MAP['HOLDING']: return HoldingStrategy()
    if ticker in SECTOR_MAP['INDUSTRIAL']: return IndustrialStrategy()
    if ticker in SECTOR_MAP['GROWTH']: return GrowthStrategy()
    
    # Bilinmeyenler için varsayılan: Holding (Dengeli)
    return HoldingStrategy()


def get_signal_snapshots(verbose=True):
    """
    Generates trading signal snapshots for all tickers.
    Returns: List of dictionaries (Snapshots).
    """
    if verbose:
        print(f"\n=== BİST30 AI TRADER - GÜNLÜK ANALİZ ({datetime.now().strftime('%Y-%m-%d')}) ===")
        print("Sektörel Stratejiler Devrede: Banking, Holding, Industrial, Growth\n")
    
    tickers = config.TICKERS
    snapshots = []
    
    # FIX 23: Performans kontrolü
    should_stop, reason = perf_tracker.should_stop_trading()
    
    if should_stop:
        if verbose:
            print(f"🛑 TİCARET DURDURULDU: {reason}")
            print(f"Metrikler: {perf_tracker.get_current_metrics()}")
        return [{'error': 'SYSTEM_HALTED', 'reason': reason}]

    # FIX 13: Önce portföy kontrolü
    dd_check = portfolio_mgr.check_drawdown_limit()
    
    global_size_multiplier = 1.0
    system_halted = False
    halt_reason = None
    
    if dd_check['action'] == 'CLOSE_ALL':
        if verbose: print(f"🚨 EMERGENCY: {dd_check['reason']} - TÜM POZİSYONLAR KAPATILDI")
        system_halted = True
        halt_reason = dd_check['reason']
        return [{'error': 'EMERGENCY_CLOSE', 'reason': halt_reason}]
        
    if dd_check['action'] == 'REDUCE_ALL':
        if verbose: print(f"⚠️ WARNING: {dd_check['reason']} - POZİSYONLAR KÜÇÜLTÜLDÜ")
        global_size_multiplier = 0.5

    # --- MACRO GATE KONTROLÜ ---
    macro_blocked = False
    macro_fail_reasons = []
    
    if getattr(config, 'ENABLE_MACRO_GATE', True):
        if verbose: print(">> Macro Gate (Piyasa Güvenliği) kontrol ediliyor...")
        try:
            loader = DataLoader()
            macro_data = loader.fetch_macro_data()
            
            if macro_data is not None and not macro_data.empty:
                fe = FeatureEngineer(macro_data)
                macro_status = fe.get_macro_status()
                
                check_fail = False
                
                if macro_status.get('VIX_HIGH', False):
                    check_fail = True
                    macro_fail_reasons.append("VIX Yüksek")
                    
                if macro_status.get('USDTRY_SHOCK', False):
                    check_fail = True
                    macro_fail_reasons.append("USDTRY Şoku")
                    
                if macro_status.get('GLOBAL_RISK_OFF', False):
                    check_fail = True
                    macro_fail_reasons.append("Global Risk-Off")
                
                if check_fail:
                    macro_blocked = True
                    if verbose:
                        print("\n" + "!"*60)
                        print("⚠️  MACRO GATE KAPALI - İŞLEMLER DURDURULDU")
                        print(f"    Tespit Edilen Riskler: {', '.join(macro_fail_reasons)}")
                        print(f"    Detaylı Durum: {macro_status}")
                        print("!"*60 + "\n")
                else:
                    if verbose: print(f"   [ONAY] Macro Gate Açık (Piyasa Normal).")
            else:
                if verbose: print("   [UYARI] Macro veri çekilemedi, varsayılan olarak devam ediliyor.")
                
        except Exception as e:
            if verbose: print(f"   [HATA] Macro Gate kontrolü sırasında hata: {e}")
            pass
    else:
        if verbose: print(">> Macro Gate devre dışı (Config: ENABLE_MACRO_GATE=False).")
    
    # Macro blocked ise boş dönme, snapshotlarda blocked işaretle.
    
    strategies = {
        'BANKING': BankingStrategy(),
        'HOLDING': HoldingStrategy(),
        'INDUSTRIAL': IndustrialStrategy(),
        'GROWTH': GrowthStrategy()
    }
    
    for ticker in tickers:
        if verbose: print(f">> {ticker} analiz ediliyor...", end=" ")
        
        # Sektör bul
        sector = "HOLDING" # Default
        for s, t_list in SECTOR_MAP.items():
            if ticker in t_list:
                sector = s
                break
        
        strategy = strategies.get(sector)
        snapshot = {
            'ticker': ticker,
            'sector': sector,
            'timestamp': datetime.now().isoformat(),
            'macro_blocked': macro_blocked,
            'macro_reasons': macro_fail_reasons,
            'global_multiplier': global_size_multiplier
        }
        
        try:
            result = strategy.run(ticker)
            
            if 'error' in result:
                if verbose: print(f"HATA: {result['error']}")
                snapshot['error'] = result['error']
                snapshots.append(snapshot)
                continue
                
            snapshot.update({
                'action': result.get('action', 'WAIT'),
                'confidence': result.get('confidence', 0),
                'regime': result.get('regime', 'Unknown'),
                'current_price': result.get('current_price', 0),
                'stop_loss': result.get('stop_loss', 0),
                'raw_size': result.get('size', 0)
            })
            
            size = snapshot['raw_size']
            
            if global_size_multiplier < 1.0 and size > 0:
                size *= global_size_multiplier
                if verbose: print(f"   [DD Protection] Pozisyon küçültüldü: {size/global_size_multiplier:.2f} -> {size:.2f}")

            # Sektör limiti kontrolü
            if size > 0:
                allowed_size = sector_alloc.can_add_position(sector, size)
                if allowed_size < size:
                    if verbose: print(f"  ⚠️ Sektör limiti: {sector} için {size:.1%} -> {allowed_size:.1%}")
                    size = allowed_size
                
                # Eğer simülasyon değilse commit etmeli, ama burada sadece hesaplıyoruz.
                # Paper Trading modunda bu 'update_allocation' çağrısı yapılmalı mı?
                # Evet, çünkü o günkü allocation durumu önemli.
                if size > 0:
                    sector_alloc.update_allocation(sector, size)
            
            snapshot['size'] = size
            
            if verbose: print(f"[{sector}] {snapshot['action']} (Güven: %{snapshot['confidence']*100:.1f}, Rejim: {snapshot['regime']})")
            
            snapshots.append(snapshot)
            
        except Exception as e:
            if verbose: 
                print(f"CRITICAL ERROR: {e}")
            import traceback
            if verbose: traceback.print_exc()
            snapshot['error'] = str(e)
            snapshots.append(snapshot)

    return snapshots

def run_daily_analysis():
    # Wrapper for backward compatibility and console reporting
    results_list = []
    snapshots = get_signal_snapshots(verbose=True)
    
    # Check for System Halt
    if snapshots and 'error' in snapshots[0] and snapshots[0].get('error') in ['SYSTEM_HALTED', 'EMERGENCY_CLOSE']:
        return

    for snap in snapshots:
        if 'error' in snap: continue
        
        # Macro Block override logic for display?
        # daily_run logic used to return early. 
        # Here we continue but action might be blocked essentially.
        # But for Display purposes, we show what the strategy found.
        
        results_list.append({
            'Tarih': datetime.now().strftime('%Y-%m-%d'),
            'Hisse': snap['ticker'],
            'Sektör': snap['sector'],
            'Fiyat': f"{snap.get('current_price', 0):.2f}",
            'Rejim': snap.get('regime', '-'),
            'Sinyal': snap.get('action', '-'),
            'Güven': f"%{snap.get('confidence', 0)*100:.1f}",
            'Pozisyon': f"%{snap.get('size', 0)*100:.0f}",
            'Stop-Loss': normalize_stop(snap.get('stop_loss'))
        })

    if results_list:
        df_res = pd.DataFrame(results_list)
        print("\n" + "="*80)
        print("GÜNLÜK SİNYAL RAPORU")
        print("="*80)
        print(df_res.to_string(index=False))
        print("="*80)
        
        # CSV Kaydı
        filename = f"reports/signals_{datetime.now().strftime('%Y%m%d')}.csv"
        import os
        if not os.path.exists("reports"): os.makedirs("reports")
        
        df_res.to_csv(filename, index=False)
        print(f"\nRapor kaydedildi: {filename}")
    else:
        print("\nHiçbir strateji sinyal üretemedi.")

def normalize_stop(val):
    if val is None: return '-'
    if isinstance(val, (int, float)): return f"{val:.2f}"
    return str(val)

if __name__ == "__main__":
    run_daily_analysis()
