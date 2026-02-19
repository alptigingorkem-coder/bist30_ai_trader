
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dynamic_backtest import run_dynamic_backtest
from utils.logging_config import get_logger
import config

log = get_logger(__name__)

def run_walk_forward_optimization(
    start_year: int = 2018, 
    end_year: int = 2025,
    train_months: int = 24,
    test_months: int = 3,
    step_months: int = 3
):
    """
    Kayan pencereli Walk-Forward Optimizasyonu ve Backtesti.
    
    Parameters:
        start_year (int): İlk eğitim setinin başlangıç yılı
        end_year (int): Testlerin biteceği yıl
        train_months (int): Eğitim penceresi uzunluğu (ay)
        test_months (int): Test penceresi uzunluğu (ay)
        step_months (int): Pencere kaydırma adımı (ay)
    """
    
    print("\n" + "="*70)
    print("WALK-FORWARD OPTIMIZATION (ROLLING WINDOW)")
    print("="*70)
    print(f"Start Year: {start_year}")
    print(f"End Year:   {end_year}")
    print(f"Train Size: {train_months} months")
    print(f"Test Size:  {test_months} months")
    print(f"Step Size:  {step_months} months")
    print("-" * 70)
    
    # Initialize Dates
    current_start = datetime(start_year, 1, 1)
    max_date = datetime(end_year, 12, 31)
    # Limit visualization to today
    if max_date > datetime.now():
        max_date = datetime.now()
        
    results = []
    equity_curves = []
    
    # Loop
    window_id = 1
    
    while True:
        # Define Window Dates
        train_start = current_start
        train_end = train_start + relativedelta(months=train_months)
        test_end = train_end + relativedelta(months=test_months)
        
        # Stop condition
        if test_end > max_date:
            break
            
        # Format strings
        s_date_train = train_start.strftime("%Y-%m-%d")
        e_date_train = train_end.strftime("%Y-%m-%d")
        e_date_test = test_end.strftime("%Y-%m-%d")
        
        print(f"\n🔄 Window {window_id}: Train[{s_date_train} -> {e_date_train}] Test[{e_date_train} -> {e_date_test}]")
        
        # Run Backtest (using dynamic_backtest core)
        # Force re-train? dynamic_backtest trains a new model every time.
        # Ensure use_cache=True for data fetching, but model is retrained.
        
        result = run_dynamic_backtest(
            train_start=s_date_train,
            train_end=e_date_train,
            test_end=e_date_test,
            initial_capital=100000, # Notional, we aggregate returns
            use_cache=True
        )
        
        if result['success']:
            metrics = result['metrics']
            print(f"   ✅ Sharpe: {metrics['sharpeRatio']:.2f} | Return: {metrics['totalReturn']:.2f}% | MaxDD: {metrics['maxDrawdown']:.2f}%")
            
            # Extract daily equity curve (implied from result structure, dynamic_backtest needs update to return daily or we use monthly)
            # Result has 'equityCurve' which is monthly points with date.
            
            # Store Metrics
            results.append({
                'window': window_id,
                'train_start': s_date_train,
                'train_end': e_date_train,
                'test_end': e_date_test,
                'sharpe': metrics['sharpeRatio'],
                'return': metrics['totalReturn'],
                'max_dd': metrics['maxDrawdown'],
                'trades': metrics['totalTrades']
            })
            
            # Store Equity segments for stitching? 
            # Ideally we perform a full stitched backtest.
            # But simple aggregation of metrics is a good start.
            
        else:
            print(f"   ❌ Failed: {result.get('error')}")
        
        # Shift
        current_start += relativedelta(months=step_months)
        window_id += 1
        
    # Aggregate Results
    if not results:
        print("No results generated.")
        return

    df_res = pd.DataFrame(results)
    print("\n" + "="*70)
    print("ALL WINDOWS SUMMARY")
    print("="*70)
    print(df_res.to_string(index=False))
    
    print("\n" + "-"*30)
    print("OVERALL STATISTICS")
    print("-"*30)
    print(f"Average Sharpe: {df_res['sharpe'].mean():.2f}")
    print(f"Average Return: {df_res['return'].mean():.2f}%")
    print(f"Worst Drawdown: {df_res['max_dd'].min():.2f}% (Metric min is negative)")
    print(f"Total Windows : {len(df_res)}")
    
    # Save
    if not os.path.exists('reports'): os.makedirs('reports')
    df_res.to_csv('reports/walk_forward_optimization_results.csv', index=False)
    print("\n💾 Saved to reports/walk_forward_optimization_results.csv")

if __name__ == "__main__":
    run_walk_forward_optimization()
