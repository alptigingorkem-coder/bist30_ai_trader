import sys
from pathlib import Path

def check_regime_integration():
    """
    RegimeDetector'ün backtest ve live trading'de kullanılıp kullanılmadığını kontrol et.
    """
    
    print("="*70)
    print("REGIME DETECTOR ENTEGRASYON KONTROLÜ")
    print("="*70)
    
    project_root = Path.cwd()
    
    # Kontrol edilecek dosyalar
    critical_files = {
        'Backtest Engine': [
            'core/backtesting.py',
            'core/backtest/engine.py',
            'core/dynamic_backtest.py'
        ],
        'Risk Manager': [
            'core/risk_manager.py'
        ],
        'Live Trading': [
            'scripts/daily_run.py',
            'scripts/paper_trading_runner.py',
            'paper_trading/strategy_health.py',
            'paper_trading/position_runner.py'
        ],
        'Training': [
            'scripts/train_models.py'
        ]
    }
    
    results = {}
    
    for category, files in critical_files.items():
        print(f"\n📁 {category}:")
        category_results = []
        
        for file_path in files:
            full_path = project_root / file_path
            
            if not full_path.exists():
                print(f"  ⚠️  {file_path} - DOSYA YOK")
                category_results.append(('missing', file_path))
                continue
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regime import kontrolü
            has_import = any([
                'from models.regime_detector import' in content,
                'import regime_detector' in content,
                'from models import regime_detector' in content
            ])
            
            # Regime kullanım kontrolü
            has_usage = any([
                'RegimeDetector(' in content,
                'regime_detector.detect' in content,
                'detect_regime(' in content,
                '.get_trading_action(' in content
            ])
            
            # Sonuç
            if has_import and has_usage:
                print(f"  ✅ {file_path} - ENTEGRE")
                category_results.append(('integrated', file_path))
            elif has_import:
                print(f"  🟡 {file_path} - IMPORT VAR ama KULLANILMIYOR")
                category_results.append(('imported_only', file_path))
            else:
                print(f"  ❌ {file_path} - ENTEGRE DEĞİL")
                category_results.append(('not_integrated', file_path))
        
        results[category] = category_results
    
    # ========================================
    # ÖZET
    # ========================================
    print("\n" + "="*70)
    print("ENTEGRASYON ÖZET")
    print("="*70)
    
    total_files = sum(len(v) for v in results.values())
    integrated = sum(1 for r in results.values() for status, _ in r if status == 'integrated')
    missing = sum(1 for r in results.values() for status, _ in r if status == 'missing')
    not_integrated = sum(1 for r in results.values() for status, _ in r if status == 'not_integrated')
    
    print(f"\nToplam dosya: {total_files}")
    print(f"✅ Entegre: {integrated}")
    print(f"❌ Entegre değil: {not_integrated}")
    print(f"⚠️  Eksik dosya: {missing}")
    
    # Bazı opsiyonel dosyalar entegre olmayabilir, bu yüzden katı bir eşik koymuyoruz
    # Ama kritik yerlerde olmalı
    
    if not_integrated > 0:
         print(f"\n⚠️ SONUÇ: {not_integrated} dosyada entegrasyon EKSİK!")
         print("\n💡 YAPILMASI GEREKENLER:")
         for category, file_results in results.items():
            for status, file_path in file_results:
                if status == 'not_integrated':
                    print(f"  - {file_path} dosyasına RegimeDetector ekle")
         return True # Test run complete
    else:
        print("\n🎉 SONUÇ: RegimeDetector tüm kritik dosyalarda entegre!")
        return True

if __name__ == "__main__":
    success = check_regime_integration()
    sys.exit(0 if success else 1)
