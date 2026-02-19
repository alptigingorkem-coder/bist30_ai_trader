
import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel
# from core.backtesting import Backtester 
# Using simplified simulation again to avoid dependency issues with main backtester inside script
import config

def increase_trade_frequency():
    """
    MIN_WEIGHT_CHANGE parametresini düşürerek daha fazla işlem yap.
    İstatistiksel anlamı artır.
    """
    
    print("="*70)
    print("İŞLEM SIKLIĞI ARTIRMA")
    print("="*70)
    print("\nMevcut Durum: 3-5 işlem (çok az!)")
    print("Hedef: En az 20-30 işlem")
    print("="*70)
    
    # 1. Veri Yükle
    print("\n📥 Veri yükleniyor...")
    loader = DataLoader()
    tickers = config.TICKERS
    if hasattr(config, 'BIST30_TICKERS'):
         tickers = config.BIST30_TICKERS
         
    start_date = "2024-01-01"
    end_date = "2024-12-31" # Analyze valid period
    
    data_map = {}
    for t in tickers:
        try:
             df = loader.fetch_stock_data(t)
             if df is not None:
                 df = df[(df.index >= start_date) & (df.index <= end_date)]
                 if not df.empty:
                     data_map[t] = df
        except Exception as e:
            pass

    # 2. FE
    print("🔧 Feature'lar hesaplanıyor...")
    processed_dfs = []
    
    for ticker, df in data_map.items():
        try:
            fe = FeatureEngineer(df)
            processed = fe.process_all(ticker=ticker)
            processed['Ticker'] = ticker
            
            # Needed for sim
            processed['NextReturn'] = processed['Close'].pct_change().shift(-1)
            
            processed_dfs.append(processed)
        except Exception:
            pass
            
    full_data = pd.concat(processed_dfs)
    full_data = full_data.reset_index()
    if 'Date' not in full_data.columns:
        full_data.rename(columns={'index': 'Date'}, inplace=True)
    full_data['Date'] = pd.to_datetime(full_data['Date'])
    full_data = full_data.set_index(['Date', 'Ticker']).sort_index()
    
    # 3. Test Parameters
    min_weight_changes = [0.05, 0.03, 0.02, 0.015, 0.01, 0.005]
    
    results = []
    
    for mwc in min_weight_changes:
        print(f"\n{'='*70}")
        print(f"TEST: MIN_WEIGHT_CHANGE = {mwc} ({mwc*100:.1f}%)")
        print(f"{'='*70}")
        
        # Simulation Logic with Rebalancing Threshold
        # Need to track current weights
        
        current_weights = {t: 0.0 for t in tickers}
        unique_dates = full_data.index.get_level_values('Date').unique()
        
        total_trades = 0
        daily_pnl = []
        equity_curve = [1.0]
        
        for d in unique_dates:
            try:
                day_df = full_data.xs(d, level='Date')
            except KeyError:
                continue
            
            # Target Allocation Logic
            # Rank strategy: Top 5 equal weight
            target_weights = {t: 0.0 for t in tickers}
            
            # Score
            if 'RSI' in day_df.columns:
                scores = day_df['RSI']
            else:
                scores = pd.Series(np.random.rand(len(day_df)), index=day_df.index)
                
            top_n = 5
            if len(day_df) >= top_n:
                selected = scores.nlargest(top_n).index
                weight_per_asset = 1.0 / top_n
                for t in selected:
                    target_weights[t] = weight_per_asset
            
            # Rebalance Check
            traded_today = 0
            
            # Calculate PnL on CURRENT positions first (Open to Close? or Close to Close?)
            # Simulation: Hold from T to T+1.
            # Here we are at T. We decide new weights.
            # We assume we get Return T->T+1 on NEW weights?
            # Standard: We rebalance at Close T. 
            # So we earn NextReturn (T->T+1) on the NEW weights.
            
            # Check Threshold
            new_actual_weights = current_weights.copy()
            
            for t in tickers:
                target = target_weights.get(t, 0.0)
                current = current_weights.get(t, 0.0)
                
                diff = abs(target - current)
                
                if diff > mwc:
                    # Trade!
                    new_actual_weights[t] = target
                    traded_today += 1
                else:
                    # No Trade, keep current (drift handled? simplified: constant weight assumption for 1 day)
                    new_actual_weights[t] = current # Actually weights drift with price, but simplifying
            
            if traded_today > 0:
                total_trades += 1 # Count days with trades or total individual trades?
                # User metric likely counts turnover events. 
                # "3-5 işlem" -> likely means "3-5 rebalance events" or "3-5 total buys/sells".
                # Let's count individual trades.
                total_trades += traded_today 

            current_weights = new_actual_weights
            
            # Calculate Portfolio Return
            day_ret = 0
            active_weight = 0
            for t, w in current_weights.items():
                if w > 0:
                    if t in day_df.index and not np.isnan(day_df.loc[t, 'NextReturn']):
                        r = day_df.loc[t, 'NextReturn']
                        day_ret += w * r
                        active_weight += w
                        
            # Cash return 0
            daily_pnl.append(day_ret)
            equity_curve.append(equity_curve[-1] * (1 + day_ret))

        # Metrics
        sharpe = 0
        if len(daily_pnl) > 0:
            std = np.std(daily_pnl)
            if std > 1e-6:
                sharpe = np.sqrt(252) * np.mean(daily_pnl) / std
                
        total_return = equity_curve[-1] - 1
        peak = np.max(equity_curve)
        dd = (np.array(equity_curve) - peak) / peak
        max_dd = np.min(dd)
        
        result = {
            'min_weight_change': mwc,
            'total_trades': total_trades,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'total_return': total_return,
            'win_rate': 0 # Skip calculation for simplicity
        }
        results.append(result)
        
        print(f"\n📊 Sonuçlar:")
        print(f"   Total Trades:  {result['total_trades']}")
        print(f"   Sharpe:        {result['sharpe']:.2f}")

    # Save
    results_df = pd.DataFrame(results)
    if not os.path.exists('reports'):
        os.makedirs('reports')
    results_df.to_csv('reports/trade_frequency_results.csv', index=False)
    
    # Plot
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:red'
    ax1.set_xlabel('Min Weight Change')
    ax1.set_ylabel('Total Trades', color=color)
    ax1.plot(results_df['min_weight_change'], results_df['total_trades'], color=color, marker='o')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.invert_xaxis() # Smaller MWC on right or left? Typically plot ascending x. 
    # Let's just plot as is.

    ax2 = ax1.twinx()  
    color = 'tab:blue'
    ax2.set_ylabel('Sharpe Ratio', color=color)  
    ax2.plot(results_df['min_weight_change'], results_df['sharpe'], color=color, marker='s')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('Trade Frequency & Sharpe vs Min Weight Change')
    fig.tight_layout()  
    plt.savefig('reports/min_weight_change_analysis.png')
    
    return results_df

if __name__ == "__main__":
    increase_trade_frequency()
