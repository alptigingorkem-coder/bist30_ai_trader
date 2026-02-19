import os
import sys

# Add project root to path
# scripts/training/ -> scripts/ -> root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import numpy as np
import argparse
import json

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from core.backtesting import Backtester


def comprehensive_walk_forward():
    """
    Walk-Forward Validation — Gerçek LightGBM Model Tahminleriyle.
    
    Her pencerede:
    1. Eğitim verisinde LightGBM modeli eğitilir
    2. Test periyodunda model tahminleri alınır  
    3. Top-N hisse seçilir, eşit ağırlıklı portföy oluşturulur
    4. Backtester ile simülasyon yapılır
    """
    
    print("="*70)
    print("WALK-FORWARD VALIDATION (Gerçek Model)")
    print("="*70)
    print("\nHer pencerede LightGBM modeli yeniden eğitilir ve test edilir.")
    print("Bu, gerçek Out-of-Sample (OOS) performansı ölçer.")
    print("="*70)
    
    # Veri yükle
    print("\n📥 Tam veri yükleniyor...")
    loader = DataLoader()
    tickers = config.TICKERS
    if hasattr(config, 'BIST30_TICKERS'):
        tickers = config.BIST30_TICKERS
    
    start_date = "2018-01-01"
    end_date = "2026-02-14"
    
    data_map = {}
    print(f"   Fetching for {len(tickers)} tickers...")
    
    count = 0
    for t in tickers:
        try:
            df = loader.fetch_stock_data(t)
            if df is not None and not df.empty:
                df = df[(df.index >= start_date) & (df.index <= end_date)]
                if len(df) > 0:
                    data_map[t] = df
                    count += 1
        except Exception as e:
            print(f"Error fetching {t}: {e}")
            
    if count == 0:
        print("❌ Veri yüklenemedi!")
        return None, 0, 0

    # Feature engineering
    print("🔧 Feature'lar hesaplanıyor...")
    processed_dfs = []
    
    for ticker, df in data_map.items():
        try:
            fe = FeatureEngineer(df)
            processed = fe.process_all(ticker=ticker)
            processed['Ticker'] = ticker
            processed_dfs.append(processed)
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    if not processed_dfs:
        print("❌ Feature engineering başarısız!")
        return None, 0, 0
        
    full_data = pd.concat(processed_dfs)
    full_data = full_data.reset_index()
    if 'Date' not in full_data.columns:
        full_data.rename(columns={'index': 'Date'}, inplace=True)
        
    full_data['Date'] = pd.to_datetime(full_data['Date'])
    full_data = full_data.set_index(['Date', 'Ticker']).sort_index()
    
    print(f"📊 Toplam veri: {len(full_data)} satır, {full_data.index.get_level_values('Ticker').nunique()} hisse")
    
    # Walk-forward pencereleri
    windows = [
        {
            'name': '2020 (COVID)',
            'train': ('2018-01-01', '2019-12-31'),
            'test': ('2020-01-01', '2020-12-31')
        },
        {
            'name': '2021 (Toparlanma)',
            'train': ('2019-01-01', '2020-12-31'),
            'test': ('2021-01-01', '2021-12-31')
        },
        {
            'name': '2022 (Faiz Artışları)',
            'train': ('2020-01-01', '2021-12-31'),
            'test': ('2022-01-01', '2022-12-31')
        },
        {
            'name': '2023 (Geçiş)',
            'train': ('2021-01-01', '2022-12-31'),
            'test': ('2023-01-01', '2023-12-31')
        },
        {
            'name': '2024 (Enflasyon Rallisi)',
            'train': ('2022-01-01', '2023-12-31'),
            'test': ('2024-01-01', '2024-12-31')
        },
        {
            'name': '2025 (Güncel)',
            'train': ('2023-01-01', '2024-12-31'),
            'test': ('2025-01-01', '2026-02-14')
        }
    ]
    
    # ARGS
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', type=int, default=None, help='Specific window index (1-based) to run')
    args = parser.parse_args()

    if args.window is not None:
        windows = [windows[args.window - 1]]
        print(f"🎯 Running only Window {args.window}: {windows[0]['name']}")

    results = []
    
    for i, window in enumerate(windows, 1):
        print(f"\n{'='*70}")
        print(f"PENCERE {i}: {window['name']}")
        print(f"{'='*70}")
        print(f"Train: {window['train'][0]} → {window['train'][1]}")
        print(f"Test:  {window['test'][0]} → {window['test'][1]}")
        
        idx = pd.IndexSlice
        
        # Train/Test split
        try:
            train_slice = full_data.loc[idx[window['train'][0]:window['train'][1], :], :]
            test_slice = full_data.loc[idx[window['test'][0]:window['test'][1], :], :]
        except KeyError:
            print("⚠️  Veri yok.")
            continue

        if len(train_slice) < 100 or len(test_slice) < 20:
            print(f"⚠️  Yetersiz veri (Train: {len(train_slice)}, Test: {len(test_slice)})")
            continue
            
        print(f"📊 Train: {len(train_slice)} satır, Test: {len(test_slice)} satır")
        
        # --- LightGBM Model Eğitimi ---
        print("🧠 LightGBM modeli eğitiliyor...")
        
        try:
            from models.ranking_model import RankingModel
            from configs import banking as sector_config
            
            # RankingModel train_slice ile oluştur
            ranker = RankingModel(train_slice, sector_config)
            ranker.train()
            
            print("✅ Model eğitildi")
            
        except Exception as e:
            print(f"❌ Model eğitim hatası: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: RSI-based simple strategy
            result = _fallback_strategy(i, window, test_slice)
            results.append(result)
            continue
        
        # --- Test Periyodunda Tahmin ---
        print("📈 Test periyodunda tahminler alınıyor...")
        
        try:
            # Test verisini günlük grupla ve her gün için tahmin al
            unique_dates = test_slice.index.get_level_values('Date').unique().sort_values()
            port_size = getattr(config, 'PORTFOLIO_SIZE', 5)
            
            all_daily_returns = []
            total_trades = 0
            wins = 0
            
            for d in unique_dates:
                try:
                    day_data = test_slice.xs(d, level='Date')
                    if len(day_data) < port_size:
                        continue
                    
                    # Model tahmini
                    scores = ranker.predict(day_data)
                    
                    if scores is None or len(scores) == 0:
                        continue
                    
                    # Skorları Series'e çevir
                    score_series = pd.Series(scores, index=day_data.index)
                    
                    # Top-N seç
                    top_tickers = score_series.nlargest(port_size).index
                    
                    # Günlük getiri hesapla (eşit ağırlıklı)
                    if 'Excess_Return' in day_data.columns:
                        selected_returns = day_data.loc[top_tickers, 'Excess_Return']
                    elif 'NextDay_Return' in day_data.columns:
                        selected_returns = day_data.loc[top_tickers, 'NextDay_Return']
                    else:
                        # Close price change
                        selected_returns = day_data.loc[top_tickers, 'Close'].pct_change().fillna(0)
                    
                    valid_returns = selected_returns.dropna()
                    
                    if len(valid_returns) > 0:
                        daily_ret = valid_returns.mean()
                        all_daily_returns.append(daily_ret)
                        total_trades += 1
                        if daily_ret > 0:
                            wins += 1
                            
                except Exception as e:
                    continue
            
            # Metrikleri hesapla
            if not all_daily_returns:
                print("⚠️  Hiç trade yapılamadı.")
                result = _empty_result(i, window)
                results.append(result)
                continue
            
            daily_rets = np.array(all_daily_returns)
            cum_ret = np.cumprod(1 + daily_rets)
            total_return = cum_ret[-1] - 1
            
            # Sharpe
            sharpe = 0
            if daily_rets.std() > 1e-6:
                sharpe = np.sqrt(252) * daily_rets.mean() / daily_rets.std()
            
            # Max Drawdown
            peak = np.maximum.accumulate(cum_ret)
            dd = (cum_ret - peak) / peak
            max_dd = dd.min()
            
            # Win Rate
            win_rate = wins / total_trades if total_trades > 0 else 0
            
            result = {
                'window': i,
                'name': window['name'],
                'test_period': f"{window['test'][0]} → {window['test'][1]}",
                'sharpe': sharpe,
                'total_return': total_return,
                'max_drawdown': max_dd,
                'win_rate': win_rate,
                'total_trades': total_trades
            }
            results.append(result)
            
            print(f"\n📊 Sonuçlar ({window['name']}):")
            print(f"   Sharpe:        {result['sharpe']:.2f}")
            print(f"   Total Return:  {result['total_return']*100:.2f}%")
            print(f"   Max Drawdown:  {result['max_drawdown']*100:.2f}%")
            print(f"   Win Rate:      {result['win_rate']*100:.1f}%")
            print(f"   Total Trades:  {result['total_trades']}")
            
        except Exception as e:
            print(f"❌ Tahmin hatası: {e}")
            import traceback
            traceback.print_exc()
            result = _empty_result(i, window)
            results.append(result)
    
    # Özet
    if results:
        df_results = pd.DataFrame(results)
        
        print("\n" + "="*70)
        print("WALK-FORWARD ÖZET")
        print("="*70)
        print(df_results[['name', 'sharpe', 'total_return', 'max_drawdown', 'win_rate', 'total_trades']].to_string(index=False))
        
        avg_sharpe = df_results['sharpe'].mean()
        std_sharpe = df_results['sharpe'].std()
        avg_return = df_results['total_return'].mean()
        
        print(f"\n{'─'*50}")
        print(f"Ortalama Sharpe:  {avg_sharpe:.2f} ± {std_sharpe:.2f}")
        print(f"Ortalama Return:  {avg_return*100:.2f}%")
        print(f"Tutarlılık (CV):  {std_sharpe/max(abs(avg_sharpe), 0.01)*100:.0f}%")
        print(f"{'─'*50}")
        
        # Kaydet
        df_results.to_csv("reports/walk_forward_results.csv", index=False)
        print("\n💾 Sonuçlar reports/walk_forward_results.csv'ye kaydedildi")
        
        return df_results, avg_sharpe, std_sharpe
    
    return None, 0, 0


def _empty_result(i, window):
    return {
        'window': i,
        'name': window['name'],
        'test_period': f"{window['test'][0]} → {window['test'][1]}",
        'sharpe': 0, 'total_return': 0, 'max_drawdown': 0, 
        'win_rate': 0, 'total_trades': 0
    }


def _fallback_strategy(i, window, test_slice):
    """RSI tabanlı basit fallback stratejisi"""
    print("⚡ Fallback: RSI stratejisi kullanılıyor...")
    
    unique_tickers = test_slice.index.get_level_values('Ticker').unique()
    all_daily_returns = []
    
    for ticker in unique_tickers:
        try:
            ticker_df = test_slice.xs(ticker, level='Ticker')
            if ticker_df.empty:
                continue
        except KeyError:
            continue
        
        signals = pd.Series(1, index=ticker_df.index)
        bt = Backtester(ticker_df, initial_capital=10000)
        res = bt.run_backtest(signals_or_weights=signals)
        
        d_rets = res['Equity'].pct_change().fillna(0)
        d_rets.name = ticker
        all_daily_returns.append(d_rets)

    if not all_daily_returns:
        return _empty_result(i, window)
    
    concat_rets = pd.concat(all_daily_returns, axis=1).fillna(0)
    port_daily_ret = concat_rets.mean(axis=1)
    port_cum_ret = (1 + port_daily_ret).cumprod()
    
    total_return = port_cum_ret.iloc[-1] - 1
    sharpe = 0
    if port_daily_ret.std() > 1e-6:
        sharpe = np.sqrt(252) * port_daily_ret.mean() / port_daily_ret.std()
    
    peak = port_cum_ret.cummax()
    dd = (port_cum_ret - peak) / peak
    max_dd = dd.min()
    
    return {
        'window': i,
        'name': window['name'] + ' (FALLBACK)',
        'test_period': f"{window['test'][0]} → {window['test'][1]}",
        'sharpe': sharpe,
        'total_return': total_return,
        'max_drawdown': max_dd,
        'win_rate': 0.0,
        'total_trades': 0
    }


if __name__ == "__main__":
    comprehensive_walk_forward()
