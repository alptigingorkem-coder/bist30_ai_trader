"""
Banking Sector Batch Test
8 bank hissesini toplu test eder ve sonuçları kaydeder.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import pandas as pd
import re

# Banking hisseleri
BANKS = [
    "AKBNK.IS",   # Akbank (zaten test edildi)
    "GARAN.IS",   # Garanti
    "ISCTR.IS",   # İş Bankası
    "YKBNK.IS",   # Yapı Kredi
    "HALKB.IS",   # Halkbank
    "VAKBN.IS",   # Vakıfbank
    "ALBRK.IS",   # Albaraka
    "SKBNK.IS"    # Şekerbank
]

def parse_output(output):
    """main.py output'undan metrikleri çıkarır"""
    metrics = {
        'Ticker': None,
        'Total Return': None,
        'Sharpe Ratio': None,
        'Max Drawdown': None,
        'Win Rate': None,
        'Num Trades': None,
        'Circuit Breaker': 'No'
    }
    
    # Ticker
    ticker_match = re.search(r'BİST30 AI Trader: (\S+)', output)
    if ticker_match:
        metrics['Ticker'] = ticker_match.group(1)
    
    # Circuit Breaker
    if 'CIRCUIT BREAKER TETİKLENDİ' in output:
        cb_match = re.search(r'CIRCUIT BREAKER TETİKLENDİ \(([^)]+)\)', output)
        if cb_match:
            metrics['Circuit Breaker'] = cb_match.group(1)
    
    # Metrics
    for line in output.split('\n'):
        if 'Total Return' in line:
            val = re.search(r':[\s]+([-]?\d+\.\d+)', line)
            if val:
                metrics['Total Return'] = float(val.group(1))
        elif 'Sharpe Ratio' in line:
            val = re.search(r':[\s]+([-]?\d+\.\d+)', line)
            if val:
                metrics['Sharpe Ratio'] = float(val.group(1))
        elif 'Max Drawdown' in line:
            val = re.search(r':[\s]+([-]?\d+\.\d+)', line)
            if val:
                metrics['Max Drawdown'] = float(val.group(1))
        elif 'Win Rate' in line:
            val = re.search(r':[\s]+([-]?\d+\.\d+)', line)
            if val:
                metrics['Win Rate'] = float(val.group(1))
        elif 'Num Trades' in line:
            val = re.search(r':[\s]+([-]?\d+\.\d+)', line)
            if val:
                metrics['Num Trades'] = int(float(val.group(1)))
    
    return metrics

def run_banking_tests():
    """Tüm bankaları test et"""
    results = []
    
    print("=" * 60)
    print("BANKING SECTOR BATCH TEST")
    print("=" * 60)
    
    for i, ticker in enumerate(BANKS, 1):
        print(f"\n[{i}/{len(BANKS)}] Testing {ticker}...")
        
        try:
            # main.py çalıştır
            result = subprocess.run(
                ['python', 'main.py', '--ticker', ticker],
                capture_output=True,
                text=True,
                timeout=300  # 5 dakika timeout
            )
            
            # Parse output
            output = result.stdout + result.stderr
            metrics = parse_output(output)
            results.append(metrics)
            
            # Özet göster
            if metrics['Sharpe Ratio'] is not None:
                print(f"  ✅ Sharpe: {metrics['Sharpe Ratio']:.2f}, Return: {metrics['Total Return']*100:.1f}%, Trades: {metrics['Num Trades']}")
            else:
                print(f"  ❌ Test başarısız (parse error)")
            
        except subprocess.TimeoutExpired:
            print(f"  ⏱️  Timeout (5 dakika aşıldı)")
            results.append({'Ticker': ticker, 'Error': 'Timeout'})
        except Exception as e:
            print(f"  ❌ Hata: {e}")
            results.append({'Ticker': ticker, 'Error': str(e)})
    
    return results

def save_results(results):
    """Sonuçları CSV'ye kaydet"""
    df = pd.DataFrame(results)
    output_file = 'reports/banking_sector_results.csv'
    df.to_csv(output_file, index=False)
    print(f"\n✅ Sonuçlar kaydedildi: {output_file}")
    
    # Özet istatistikler
    print("\n" + "=" * 60)
    print("BANKING SECTOR ÖZET")
    print("=" * 60)
    
    valid_results = df[df['Sharpe Ratio'].notna()]
    
    if len(valid_results) > 0:
        print(f"\nTest Edilen: {len(valid_results)}/{len(BANKS)} banka")
        print(f"Ortalama Sharpe: {valid_results['Sharpe Ratio'].mean():.2f}")
        print(f"Ortalama Return: {valid_results['Total Return'].mean()*100:.1f}%")
        print(f"Win Rate Ortalaması: {valid_results['Win Rate'].mean()*100:.1f}%")
        
        # En iyi 3
        top3 = valid_results.nlargest(3, 'Sharpe Ratio')
        print("\n🏆 En İyi 3 Banka:")
        for idx, row in top3.iterrows():
            print(f"  {row['Ticker']}: Sharpe {row['Sharpe Ratio']:.2f}, Return {row['Total Return']*100:.1f}%")
        
        # Circuit Breaker
        cb_count = (valid_results['Circuit Breaker'] != 'No').sum()
        print(f"\n⚠️  Circuit Breaker: {cb_count}/{len(valid_results)} banka")
    else:
        print("\n❌ Hiçbir banka başarılı test edilemedi!")
    
    return df

if __name__ == "__main__":
    results = run_banking_tests()
    df = save_results(results)
    
    print("\n✅ Banking sector batch test tamamlandı!")
