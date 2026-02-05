"""
Batch Testing Script - Tüm Hisseleri Test Et
"""
import subprocess
import config
import pandas as pd

results = []

print("="*60)
print("TOPLU BACKTEST BAŞLIYOR")
print(f"Test Edilecek Hisseler: {len(config.TICKERS)}")
print("="*60)

for ticker in config.TICKERS:
    print(f"\n>>> {ticker} test ediliyor...")
    
    try:
        # main.py'yi çalıştır
        result = subprocess.run(
            ['python', 'main.py', '--ticker', ticker],
            capture_output=True,
            text=True,
            timeout=300  # 5 dakika timeout
        )
        
        # Çıktıyı parse et
        output = result.stdout
        
        # Metrics'i çıkar
        metrics = {}
        if "BACKTEST SONUÇLARI" in output:
            lines = output.split('\n')
            for line in lines:
                if ':' in line and any(m in line for m in ['Total Return', 'Sharpe', 'Drawdown', 'Win Rate', 'Num Trades']):
                    parts = line.split(':')
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        try:
                            metrics[key] = float(value)
                        except:
                            metrics[key] = value
        
        # Circuit Breaker kontrolü
        circuit_breaker = "CIRCUIT BREAKER" in output
        
        results.append({
            'Ticker': ticker,
            'Total_Return': metrics.get('Total Return', None),
            'Sharpe': metrics.get('Sharpe Ratio', None),
            'Max_DD': metrics.get('Max Drawdown', None),
            'Win_Rate': metrics.get('Win Rate', None),
            'Num_Trades': metrics.get('Num Trades', None),
            'Circuit_Breaker': circuit_breaker,
            'Status': 'SUCCESS' if result.returncode == 0 else 'FAILED'
        })
        
        print(f"✓ {ticker} tamamlandı")
        
    except subprocess.TimeoutExpired:
        print(f"✗ {ticker} TIMEOUT (5 dk aşıldı)")
        results.append({
            'Ticker': ticker,
            'Status': 'TIMEOUT'
        })
    except Exception as e:
        print(f"✗ {ticker} HATA: {e}")
        results.append({
            'Ticker': ticker,
            'Status': f'ERROR: {e}'
        })

# Sonuçları kaydet
df_results = pd.DataFrame(results)
df_results.to_csv('reports/batch_test_results.csv', index=False)

# Özet yazdır
print("\n" + "="*60)
print("TOPLU TEST SONUÇLARI")
print("="*60)
print(df_results.to_string(index=False))
print(f"\nDetaylı sonuçlar: reports/batch_test_results.csv")
