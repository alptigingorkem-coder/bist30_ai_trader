
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

def run_daily_analysis():
    print(f"\n=== BİST30 AI TRADER - GÜNLÜK ANALİZ ({datetime.now().strftime('%Y-%m-%d')}) ===")
    print("Sektörel Stratejiler Devrede: Banking, Holding, Industrial, Growth\n")
    
    tickers = config.TICKERS
    results = []
    
    # FIX 23: Performans kontrolü
    should_stop, reason = perf_tracker.should_stop_trading()
    
    if should_stop:
        print(f"🛑 TİCARET DURDURULDU: {reason}")
        print(f"Metrikler: {perf_tracker.get_current_metrics()}")
        return

    # FIX 13: Önce portföy kontrolü
    dd_check = portfolio_mgr.check_drawdown_limit()
    
    if dd_check['action'] == 'CLOSE_ALL':
        print(f"🚨 EMERGENCY: {dd_check['reason']} - TÜM POZİSYONLAR KAPATILDI")
        return  # Hiç işlem yapma
        
    if dd_check['action'] == 'REDUCE_ALL':
        print(f"⚠️ WARNING: {dd_check['reason']} - POZİSYONLAR KÜÇÜLTÜLDÜ")
        # Tüm position size'ları yarıya indirilecek (strateji içinde değil, burada simüle edilebilir veya config'e flag eklenebilir)
        # Pratik çözüm: strategies'e bir flag göndermek veya global bir çarpan tanımlamak.
        # Şimdilik log basıyoruz, aşağıda size hesaplarken dikkate alacağız.
        GLOBAL_SIZE_MULTIPLIER = 0.5
    else:
        GLOBAL_SIZE_MULTIPLIER = 1.0

    # --- MACRO GATE KONTROLÜ ---
    # Config'den kapatılıp kapatılmadığına bak
    if getattr(config, 'ENABLE_MACRO_GATE', True):
        print(">> Macro Gate (Piyasa Güvenliği) kontrol ediliyor...")
        try:
            loader = DataLoader()
            macro_data = loader.fetch_macro_data()
            
            # Macro veri boşsa veya hata varsa güvenli tarafta kalıp devam edebiliriz veya durabiliriz.
            # Burada veri varsa kontrol edelim.
            if macro_data is not None and not macro_data.empty:
                fe = FeatureEngineer(macro_data)
                macro_status = fe.get_macro_status()
                
                check_fail = False
                fail_reasons = []
                
                if macro_status.get('VIX_HIGH', False):
                    check_fail = True
                    fail_reasons.append("VIX Yüksek")
                    
                if macro_status.get('USDTRY_SHOCK', False):
                    check_fail = True
                    fail_reasons.append("USDTRY Şoku")
                    
                if macro_status.get('GLOBAL_RISK_OFF', False):
                    check_fail = True
                    fail_reasons.append("Global Risk-Off")
                
                if check_fail:
                    print("\n" + "!"*60)
                    print("⚠️  MACRO GATE KAPALI - İŞLEMLER DURDURULDU")
                    print(f"    Tespit Edilen Riskler: {', '.join(fail_reasons)}")
                    print(f"    Detaylı Durum: {macro_status}")
                    print("!"*60 + "\n")
                    return # İŞLEM YAPMA, ÇIK
                else:
                    print(f"   [ONAY] Macro Gate Açık (Piyasa Normal).")
            else:
                print("   [UYARI] Macro veri çekilemedi, varsayılan olarak devam ediliyor.")
                
        except Exception as e:
            print(f"   [HATA] Macro Gate kontrolü sırasında hata: {e}")
            print("   Güvenlik nedeniyle devam ediliyor (Fail-Open) veya durdurulabilir.")
            pass
    else:
        print(">> Macro Gate devre dışı (Config: ENABLE_MACRO_GATE=False).")
    # ---------------------------
    
    # Strateji nesnelerini bir kez oluşturup cacheleyelim (Model yükleme maliyetinden kaçınmak için)
    # Ancak her ticker için 'run' metodu temiz çalışmalı. 
    # BaseStrategy state tutmaz (results haric), güvenli.
    
    strategies = {
        'BANKING': BankingStrategy(),
        'HOLDING': HoldingStrategy(),
        'INDUSTRIAL': IndustrialStrategy(),
        'GROWTH': GrowthStrategy()
    }
    
    for ticker in tickers:
        print(f">> {ticker} analiz ediliyor...", end=" ")
        
        # Sektör bul
        sector = "HOLDING" # Default
        for s, t_list in SECTOR_MAP.items():
            if ticker in t_list:
                sector = s
                break
        
        strategy = strategies.get(sector)
        
        try:
            result = strategy.run(ticker)
            
            if 'error' in result:
                print(f"HATA: {result['error']}")
                continue
                
            prediction = result.get('prediction', 0)
            confidence = result.get('confidence', 0)
            action = result.get('action', 'WAIT')
            regime = result.get('regime', 'Unknown')
            regime = result.get('regime', 'Unknown')
            size = result.get('size', 0)
            
            if GLOBAL_SIZE_MULTIPLIER < 1.0 and size > 0:
                size *= GLOBAL_SIZE_MULTIPLIER
                print(f"   [DD Protection] Pozisyon küçültüldü: {size/GLOBAL_SIZE_MULTIPLIER:.2f} -> {size:.2f}")

            # FIX 18: Sektör limiti kontrolü
            if size > 0:
                allowed_size = sector_alloc.can_add_position(sector, size)
                if allowed_size < size:
                    print(f"  ⚠️ Sektör limiti: {sector} için {size:.1%} -> {allowed_size:.1%}")
                    size = allowed_size
                
                # Eğer hala pozisyon varsa, allocation'ı güncelle (commit)
                if size > 0:
                    sector_alloc.update_allocation(sector, size)

            print(f"[{sector}] {action} (Güven: %{confidence*100:.1f}, Rejim: {regime})")
            
            results.append({
                'Tarih': datetime.now().strftime('%Y-%m-%d'),
                'Hisse': ticker,
                'Sektör': sector,
                'Fiyat': f"{result.get('current_price', 0):.2f}",
                'Rejim': regime,
                'Sinyal': action,
                'Güven': f"%{confidence*100:.1f}",
                'Pozisyon': f"%{size*100:.0f}",
                'Stop-Loss': result.get('stop_loss', '-'),
            })
            
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()

    if results:
        df_res = pd.DataFrame(results)
        print("\n" + "="*80)
        print("GÜNLÜK SİNYAL RAPORU")
        print("="*80)
        print(df_res.to_string(index=False))
        print("="*80)
        
        # CSV Kaydı
        filename = f"reports/signals_{datetime.now().strftime('%Y%m%d')}.csv"
        # Klasör yoksa oluştur
        import os
        if not os.path.exists("reports"): os.makedirs("reports")
        
        df_res.to_csv(filename, index=False)
        print(f"\nRapor kaydedildi: {filename}")
    else:
        print("\nHiçbir strateji sinyal üretemedi.")

if __name__ == "__main__":
    run_daily_analysis()
