import os
import subprocess
import pandas as pd
import glob
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def get_metric_from_report(ticker, metric_name):
    """HTML rapor veya loglardan metrik parse etmeye çalışır.
    Daha kolayı: backtest_trades csv'si veya main.py logunu parse etmek.
    Şimdilik main.py'nin son çıktısını parse edelim."""
    return "N/A"

def run_batch():
    tickers = config.TIERS['TIER_1']
    results = []
    
    print(f"Starting Batch Test for {len(tickers)} tickers...")
    
    for ticker in tickers:
        print(f"Running for {ticker}...")
        try:
            # Run main.py
            result = subprocess.run(
                ["python", "main.py", "--ticker", ticker],
                capture_output=True
            )
            
            output = result.stdout.decode('cp1252', errors='replace') # Windows default

            
            # Parse output for metrics
            # Look for: Total Return        : -0.1356
            metrics = {}
            for line in output.split('\n'):
                if ":" in line:
                    parts = line.split(":")
                    key = parts[0].strip()
                    val = parts[1].strip()
                    if key in ['Total Return', 'Sharpe Ratio', 'Max Drawdown', 'Win Rate']:
                        try:
                            metrics[key] = float(val.replace('%', ''))
                        except:
                            metrics[key] = val
                            
            metrics['Ticker'] = ticker
            results.append(metrics)
            
        except Exception as e:
            print(f"Error running {ticker}: {e}")
            
    # Summary
    df = pd.DataFrame(results)
    if not df.empty:
        # Reorder columns
        cols = ['Ticker', 'Total Return', 'Win Rate', 'Max Drawdown', 'Sharpe Ratio']
        df = df[[c for c in cols if c in df.columns]]
        
        print("\n=== BATCH TEST RESULTS ===")
        print(df.to_string(index=False))
        df.to_csv("reports/batch_results.csv", index=False)
        print("\nResults saved to reports/batch_results.csv")
    else:
        print("No results obtained.")

if __name__ == "__main__":
    run_batch()
