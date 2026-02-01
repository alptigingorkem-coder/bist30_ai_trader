
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.getcwd())

from core.paper_logger import PaperLogger
from utils.data_loader import DataLoader

# ═══════════════════════════════════════════════════════════════════════════════
# FORWARD RETURN & EXCURSION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def get_dynamic_holding_period(regime, confidence):
    """
    Rejim ve güven skoruna göre dinamik holding period belirle.
    """
    base_period = 5
    
    # Rejim bazlı ayarlama
    if regime == 'Trend_Up':
        base_period = 7  # Trend'de daha uzun tut
    elif regime == 'Crash_Bear':
        base_period = 3  # Kriz döneminde kısa tut
    elif regime == 'Sideways':
        base_period = 5
    
    # Confidence bazlı ayarlama
    if confidence > 0.8:
        base_period += 2  # Yüksek güven = daha uzun tutma
    elif confidence < 0.5:
        base_period -= 1  # Düşük güven = kısa tutma
    
    return max(2, min(base_period, 10))  # 2-10 gün arası

def calculate_mae_mfe(ticker, trade_date, holding_days, action='BUY'):
    """
    MAE (Max Adverse Excursion) ve MFE (Max Favorable Excursion) hesapla.
    MAE: Pozisyon süresince en kötü çekilme
    MFE: Pozisyon süresince kaçırılan en iyi fırsat
    """
    try:
        loader = DataLoader()
        df = loader.fetch_stock_data(ticker)
        
        if df is None or df.empty:
            return None, None
            
        df = df.sort_index()
        trade_date = pd.to_datetime(trade_date).tz_localize(None)
        
        future_dates = df.index[df.index >= trade_date]
        if len(future_dates) < holding_days + 1:
            return None, None
        
        entry_price = df.loc[future_dates[0], 'Close']
        
        # Holding period boyunca fiyatlar
        holding_prices = df.loc[future_dates[:holding_days+1], 'Close'].values
        
        if action == 'BUY':
            # Long pozisyon için
            returns = (holding_prices - entry_price) / entry_price
            mae = returns.min()  # En kötü düşüş
            mfe = returns.max()  # En iyi yükseliş
        else:
            # Short pozisyon için (tersi)
            returns = (entry_price - holding_prices) / entry_price
            mae = returns.min()
            mfe = returns.max()
        
        return mae, mfe
        
    except Exception:
        return None, None

def calculate_forward_return_dynamic(ticker, trade_date, regime, confidence):
    """
    Dinamik holding period ile forward return hesapla.
    """
    holding_days = get_dynamic_holding_period(regime, confidence)
    
    try:
        loader = DataLoader()
        df = loader.fetch_stock_data(ticker)
        
        if df is None or df.empty:
            return None, holding_days
            
        df = df.sort_index()
        trade_date = pd.to_datetime(trade_date).tz_localize(None)
        
        future_dates = df.index[df.index >= trade_date]
        if len(future_dates) < holding_days + 1:
            return None, holding_days
            
        entry_price = df.loc[future_dates[0], 'Close']
        exit_price = df.loc[future_dates[min(holding_days, len(future_dates)-1)], 'Close']
        
        return (exit_price - entry_price) / entry_price, holding_days
        
    except Exception:
        return None, holding_days

# ═══════════════════════════════════════════════════════════════════════════════
# STRESS TEST - WORST 20 DAY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_worst_n_days(df, n=20):
    """
    Rolling worst-N-day PnL hesapla.
    Sistemin en kötü dönemde nasıl davrandığını analiz eder.
    """
    if 'timestamp' not in df.columns or df.empty:
        return None
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    # Günlük PnL (slippage dahil)
    daily_pnl = df.groupby('date').apply(
        lambda x: x[x['executed'] == True]['simulated_quantity'].sum() * 0.01  # Simplified
    )
    
    if len(daily_pnl) < n:
        return {
            'worst_period_return': 0,
            'worst_start_date': None,
            'worst_end_date': None,
            'total_days': len(daily_pnl)
        }
    
    # Rolling sum
    rolling_sum = daily_pnl.rolling(window=n).sum()
    worst_idx = rolling_sum.idxmin()
    
    return {
        'worst_period_return': rolling_sum.min(),
        'worst_end_date': worst_idx,
        'worst_start_date': daily_pnl.index[max(0, list(daily_pnl.index).index(worst_idx) - n + 1)] if worst_idx else None,
        'total_days': len(daily_pnl)
    }

def compare_macro_gate_impact(df):
    """
    Macro Gate açık/kapalı karşılaştırması.
    """
    if df.empty:
        return None
    
    macro_blocked = df[df['blocked_reason'] == 'MACRO_GATE_BLOCK']
    executed = df[df['executed'] == True]
    
    return {
        'macro_blocked_count': len(macro_blocked),
        'executed_count': len(executed),
        'block_ratio': len(macro_blocked) / len(df) if len(df) > 0 else 0
    }

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_paper_performance(calculate_pnl=False, run_stress_test=False):
    logger = PaperLogger()
    df = logger.load_logs()
    
    print("\n" + "="*70)
    print("📊 PAPER TRADING PERFORMANS RAPORU v2.0")
    print("="*70)
    
    if df.empty:
        print("⚠️ Henüz kayıtlı paper trading verisi bulunamadı.")
        return

    # Filter out test data
    df = df[~df['ticker'].str.startswith('TEST')]
    
    if df.empty:
        print("⚠️ Gerçek ticker verisi bulunamadı (sadece test verileri mevcut).")
        return

    # 1. Genel Özet
    total_decisions = len(df)
    executed = df[df['executed'] == True]
    blocked = df[df['executed'] == False]
    
    print(f"\n1️⃣  GENEL DURUM")
    print(f"   Toplam Karar Sayısı : {total_decisions}")
    print(f"   İşleme Dönüşen      : {len(executed)} (%{len(executed)/total_decisions*100:.1f})")
    print(f"   Bloke Edilen        : {len(blocked)} (%{len(blocked)/total_decisions*100:.1f})")
    
    # Slippage bilgisi (yeni)
    if 'slippage_pct' in df.columns:
        avg_slippage = df['slippage_pct'].mean() * 100
        print(f"   Ort. Slippage       : %{avg_slippage:.3f}")
    
    # 2. Blokaj Nedenleri
    if not blocked.empty:
        print(f"\n2️⃣  BLOKAJ ANALİZİ")
        reasons = blocked['blocked_reason'].value_counts()
        for reason, count in reasons.items():
            pct = count / len(blocked) * 100
            print(f"   • {reason}: {count} (%{pct:.1f})")
        
        macro_blocks = blocked[blocked['blocked_reason'] == 'MACRO_GATE_BLOCK']
        if not macro_blocks.empty:
            print(f"\n   🔴 MACRO GATE: {len(macro_blocks)} işlem engellendi")
    
    # 3. Rejim Bazlı Dağılım
    print(f"\n3️⃣  REJİM BAZLI DAĞILIM")
    if 'regime' in df.columns:
        regime_dist = df.groupby('regime').agg({
            'executed': ['count', 'sum']
        }).round(2)
        regime_dist.columns = ['Toplam', 'Executed']
        regime_dist['Blocked'] = regime_dist['Toplam'] - regime_dist['Executed']
        print(regime_dist.to_string())
    
    # 4. Sessiz Gün Analizi
    print(f"\n4️⃣  SESSİZ GÜN ANALİZİ")
    if 'timestamp' in df.columns:
        df_temp = df.copy()
        df_temp['date'] = pd.to_datetime(df_temp['timestamp']).dt.date
        daily_summary = df_temp.groupby('date').agg({
            'executed': 'sum',
            'ticker': 'count'
        })
        daily_summary.columns = ['Executed', 'Total']
        
        silent_days = daily_summary[daily_summary['Executed'] == 0]
        active_days = daily_summary[daily_summary['Executed'] > 0]
        
        print(f"   Toplam Gün       : {len(daily_summary)}")
        print(f"   Sessiz Günler    : {len(silent_days)} (%{len(silent_days)/len(daily_summary)*100:.1f})")
        print(f"   Aktif Günler     : {len(active_days)} (%{len(active_days)/len(daily_summary)*100:.1f})")
    
    # 5. Stress Test (Yeni)
    if run_stress_test:
        print(f"\n5️⃣  STRESS TEST (En Kötü 20 Günlük Dönem)")
        worst = calculate_worst_n_days(df, n=20)
        if worst and worst['worst_start_date']:
            print(f"   Dönem          : {worst['worst_start_date']} → {worst['worst_end_date']}")
            print(f"   Kümülatif Etki : {worst['worst_period_return']:.2f}")
        else:
            print(f"   ⚠️ Yeterli veri yok (min 20 gün gerekli)")
        
        # Macro Gate Impact
        macro_impact = compare_macro_gate_impact(df)
        if macro_impact:
            print(f"\n   [MACRO GATE ETKİSİ]")
            print(f"   Engellenen: {macro_impact['macro_blocked_count']}")
            print(f"   Geçen     : {macro_impact['executed_count']}")
            print(f"   Blok Oranı: %{macro_impact['block_ratio']*100:.1f}")
    else:
        print(f"\n5️⃣  STRESS TEST (Devre Dışı)")
        print("   💡 Aktifleştirmek için: python analyze_paper.py --stress")
    
    # 6. Forward Return Analizi (Opsiyonel - Yavaş)
    if calculate_pnl:
        print(f"\n6️⃣  FORWARD RETURN & EXCURSION ANALİZİ")
        print("   ⏳ Veri çekiliyor, bu işlem birkaç dakika sürebilir...")
        
        # Executed Trades PnL with MAE/MFE
        if not executed.empty:
            print(f"\n   [İŞLEM YAPILAN - DİNAMİK HOLDİNG]")
            
            results = []
            for _, row in executed.head(10).iterrows():  # İlk 10 için (hız)
                regime = row.get('regime', 'Sideways')
                confidence = row.get('confidence', 0.5)
                
                fwd_ret, hold_period = calculate_forward_return_dynamic(
                    row['ticker'], row['timestamp'], regime, confidence
                )
                mae, mfe = calculate_mae_mfe(row['ticker'], row['timestamp'], hold_period)
                
                if fwd_ret is not None:
                    results.append({
                        'ticker': row['ticker'],
                        'return': fwd_ret,
                        'holding': hold_period,
                        'mae': mae or 0,
                        'mfe': mfe or 0
                    })
            
            if results:
                res_df = pd.DataFrame(results)
                print(f"   Analiz Edilen  : {len(results)} trade")
                print(f"   Ort. Return    : %{res_df['return'].mean()*100:.2f}")
                print(f"   Ort. Holding   : {res_df['holding'].mean():.1f} gün")
                print(f"   Ort. MAE       : %{res_df['mae'].mean()*100:.2f} (en kötü çekilme)")
                print(f"   Ort. MFE       : %{res_df['mfe'].mean()*100:.2f} (kaçırılan kar)")
                
                win_rate = (res_df['return'] > 0).sum() / len(res_df) * 100
                print(f"   Win Rate       : %{win_rate:.1f}")
        
        # Blocked Trades (What If?)
        blocked_with_signal = blocked[blocked['blocked_reason'] == 'MACRO_GATE_BLOCK']
        if not blocked_with_signal.empty:
            print(f"\n   [MACRO GATE ENGELLİ - GİRİLSEYDİ NE OLURDU?]")
            fwd_returns = []
            for _, row in blocked_with_signal.head(5).iterrows():  # İlk 5
                regime = row.get('regime', 'Sideways')
                confidence = row.get('confidence', 0.5)
                ret, _ = calculate_forward_return_dynamic(row['ticker'], row['timestamp'], regime, confidence)
                if ret is not None:
                    fwd_returns.append(ret)
            
            if fwd_returns:
                avg_ret = np.mean(fwd_returns)
                print(f"   Ortalama Getiri: %{avg_ret*100:.2f}")
                
                if avg_ret < 0:
                    print(f"\n   ✅ MACRO GATE: Doğru çalışıyor! Zarardan korudu.")
                else:
                    print(f"\n   ⚠️ MACRO GATE: Fırsat kaçırılmış olabilir.")
    else:
        print(f"\n6️⃣  FORWARD RETURN (Devre Dışı)")
        print("   💡 Aktifleştirmek için: python analyze_paper.py --pnl")

    print("\n" + "="*70)
    print("✅ Analiz tamamlandı.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pnl', action='store_true', help='Calculate forward PnL with MAE/MFE (slow)')
    parser.add_argument('--stress', action='store_true', help='Run stress test (worst 20 days)')
    parser.add_argument('--full', action='store_true', help='Run all analyses')
    args = parser.parse_args()
    
    if args.full:
        analyze_paper_performance(calculate_pnl=True, run_stress_test=True)
    else:
        analyze_paper_performance(calculate_pnl=args.pnl, run_stress_test=args.stress)

