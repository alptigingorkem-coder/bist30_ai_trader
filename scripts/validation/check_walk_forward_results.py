#!/usr/bin/env python3
"""
Walk-Forward Validation Results Check
Validates that walk-forward validation has been run and results meet criteria.
"""

from pathlib import Path


def check_walk_forward_results():
    """Walk-forward validation sonuçlarını kontrol et."""
    print("=" * 70)
    print("5️⃣ WALK-FORWARD VALIDATION KONTROLÜ")
    print("=" * 70)

    # Sonuç dosyasını ara
    possible_files = [
        'walk_forward_optimization_results.csv',
        'reports/walk_forward_results.csv',
        'results/walk_forward.csv'
    ]
    
    result_file = None
    for f in possible_files:
        if Path(f).exists():
            result_file = Path(f)
            break
    
    if not result_file:
        print("❌ Walk-forward sonuçları bulunamadı!")
        print("\n💡 Çalıştırın:")
        print("   python scripts/training/walk_forward_validation.py")
        return {
            'status': 'FAIL',
            'reason': 'Walk-forward results eksik'
        }
    
    print(f"✅ Sonuç dosyası bulundu: {result_file}")

    # Sonuçları analiz et
    try:
        import pandas as pd
        df = pd.read_csv(result_file)
        
        # Metrikleri hesapla
        avg_sharpe = df['sharpe'].mean()
        std_sharpe = df['sharpe'].std()
        # max_dd veya max_drawdown kolonunu kullan
        dd_col = 'max_dd' if 'max_dd' in df.columns else 'max_drawdown'
        max_dd = df[dd_col].min()
        win_rate = (df['sharpe'] > 0).sum() / len(df) * 100
        
        print(f"\n📊 Walk-Forward Metrikleri:")
        print(f"  Pencere Sayısı: {len(df)}")
        print(f"  Ortalama Sharpe: {avg_sharpe:.2f}")
        print(f"  Sharpe Std Dev: {std_sharpe:.2f}")
        print(f"  Max Drawdown: {max_dd*100:.1f}%")
        print(f"  Win Rate: {win_rate:.1f}%")
        
        # Değerlendirme
        criteria = {
            'Sharpe >1.5': (avg_sharpe, 1.5, avg_sharpe >= 1.5),
            'Sharpe Std <1.0': (std_sharpe, 1.0, std_sharpe < 1.0),
            'Max DD <-20%': (max_dd, -0.20, max_dd > -0.20),
            'Win Rate >55%': (win_rate, 55.0, win_rate > 55.0)
        }
        
        print(f"\n✔️ Kriter Kontrolü:")
        passed = 0
        total = len(criteria)
        
        for name, (value, threshold, passed_check) in criteria.items():
            status = "✅" if passed_check else "❌"
            print(f"  {status} {name}: {value:.2f} (hedef: {threshold:.2f})")
            if passed_check:
                passed += 1
        
        score = (passed / total) * 100
        print(f"\n📊 Walk-Forward Skoru: {score:.1f}% ({passed}/{total})")
        
        if score >= 75:
            return {
                'status': 'PASS',
                'score': score,
                'metrics': {
                    'avg_sharpe': avg_sharpe,
                    'max_dd': max_dd,
                    'win_rate': win_rate
                }
            }
        else:
            return {
                'status': 'FAIL',
                'score': score,
                'reason': f'Sadece {passed}/{total} kriter geçildi'
            }
            
    except Exception as e:
        print(f"❌ Sonuç dosyası okunamadı: {e}")
        return {
            'status': 'FAIL',
            'reason': f'Dosya okuma hatası: {e}'
        }


if __name__ == "__main__":
    result = check_walk_forward_results()
    print(f"\nFinal Status: {result['status']}")
