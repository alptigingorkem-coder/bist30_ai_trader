
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.analysis.utils import calculate_max_drawdown, calculate_sharpe_ratio

def compare_benchmark():
    print("="*70)
    print("BENCHMARK KARŞILAŞTIRMASI")
    print("="*70)
    
    # 1. Load Strategy Returns
    try:
        if os.path.exists('reports/daily_returns_concatenated.csv'):
            # This contains individual stock returns? Or portfolio?
            # User previous script 'analyze_portfolio.py' assumed 'daily_returns_concatenated.csv'
            # Let's use that or 'walk_forward_results.csv' if available?
            # Actually, let's look for a portfolio equity curve or return series.
            # analyze_portfolio.py calculated it. 
            pass
            
        # Let's try to load the 'portfolio_values.csv' if it exists (from backtest)
        # Or re-calculate from results
        
        # For this script, let's assume we use the last run's metrics 
        # OR we fetch XU30 and ask user for Strategy Return (as per user prompt "strategy_return = 211.52")
        
        # User prompt logic:
        # "Manuel giriş (benchmark scriptinden)"
        # "strategy_return = 211.52"
        # "bist30_return = float(input(...))"
        
        # We can automate fetching BIST30 return for the same period.
        
        start_date = "2024-01-01"
        end_date = "2024-12-31" # Adjust as needed based on actual backtest
        
        print(f"Period: {start_date} to {end_date}")
        
        # Fetch XU030 using DataLoader (handles fallback)
        from utils.data_loader import DataLoader
        loader = DataLoader()
        
        ticker = "XU030.IS"
        print(f"Fetching {ticker}...")
        try:
             df = loader.fetch_stock_data(ticker)
             # If failed or empty, try XU100
             if df is None or df.empty:
                 print("⚠️ XU030 alınamadı, XU100 deneniyor...")
                 df = loader.fetch_stock_data("XU100.IS")
        except Exception as e:
             print(f"Error fetching benchmark: {e}")
             df = None
             
        # Filter date
        if df is not None and not df.empty:
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            
        if df is None or df.empty:
            print("❌ Benchmark verisi yok!")
            bist_return = 0
            max_dd = 0
            sharpe = 0
            # Try to fetch via fallback manually if loader failed to fallback for index?
            # efficient-loader handles it.
        else:
            # Calculate metrics
            df['Return'] = df['Close'].pct_change()
            cum_ret = (1 + df['Return']).cumprod()
            bist_return = (cum_ret.iloc[-1] - 1) * 100
            
            max_dd = calculate_max_drawdown(cum_ret) * 100
            sharpe = calculate_sharpe_ratio(df['Return'])
            
            print(f"\n📊 BIST30 ({ticker}) Performansı:")
            print(f"   Toplam Getiri: {bist_return:.2f}%")
            print(f"   Max Drawdown:  {max_dd:.2f}%")
            print(f"   Sharpe Ratio:  {sharpe:.2f}")
            
        # Strategy Metrics — Backtest sonuçlarından oku
        strategy_return = 0.0
        
        if os.path.exists('reports/final_backtest_results.csv'):
            try:
                bt_results = pd.read_csv('reports/final_backtest_results.csv')
                if 'Total Return' in bt_results.columns:
                    # Total Return zaten yüzde olarak kayıtlı
                    strategy_return = bt_results['Total Return'].mean() * 100
                    print(f"   Strateji getirisi backtest sonuçlarından hesaplandı: {strategy_return:.2f}%")
            except Exception as e:
                print(f"⚠️ Backtest sonuçları okunamadı: {e}")
        
        if strategy_return == 0.0:
            # Fallback: daily_returns_concatenated.csv'den hesapla
            if os.path.exists('reports/daily_returns_concatenated.csv'):
                try:
                    daily_rets = pd.read_csv('reports/daily_returns_concatenated.csv', index_col=0, parse_dates=True)
                    port_ret = daily_rets.mean(axis=1)
                    strategy_return = float(((1 + port_ret).cumprod().iloc[-1] - 1) * 100)
                    print(f"   Strateji getirisi günlük getirilerden hesaplandı: {strategy_return:.2f}%")
                except Exception as e:
                    print(f"⚠️ Günlük getiriler okunamadı: {e}")
        
        if strategy_return == 0.0:
            print("⚠️ Strateji getirisi hesaplanamadı! Önce backtest çalıştırın.")
             
        alpha = strategy_return - bist_return
        
        print(f"\n🚀 STRATEJİ vs BENCHMARK:")
        print(f"   Strateji Getirisi: {strategy_return:.2f}%")
        print(f"   BIST30 Getirisi:   {bist_return:.2f}%")
        print(f"   ALPHA:             {alpha:.2f}%")
        
        # Save
        results = {
            'strategy_return': strategy_return,
            'benchmark_return': bist_return,
            'alpha': alpha,
            'benchmark_sharpe': sharpe,
            'benchmark_dd': max_dd
        }
        
        import json
        with open('reports/benchmark_results.json', 'w') as f:
            json.dump(results, f)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    compare_benchmark()
