#!/usr/bin/env python3
"""
Project Structure Validation
Validates that all expected scripts and files exist according to README.
"""

from pathlib import Path


def check_project_structure():
    """README'de belirtilen script yapılanmasını doğrula."""
    print("=" * 70)
    print("1️⃣ PROJE YAPILANMASI KONTROLÜ")
    print("=" * 70)

    # Beklenen yapı (README'den)
    expected_structure = {
        'scripts/analysis/': [
            'run_backtest.py',
            'get_training_metrics.py',
            'run_feature_importance.py'
        ],
        'scripts/training/': [
            'train_models.py',
            'train_catboost.py',
            'train_tft.py',
            'walk_forward_validation.py'
        ],
        'scripts/ops/': [
            'paper_trading_runner.py'
        ],
        'scripts/maintenance/': [
            'find_unused_files.py',
            'find_duplicate_code.py',
            'generate_cleanup_report.py'
        ],
        'scripts/validation/': [
            'check_project_structure.py',  # Bu dosya
        ]
    }

    checks = {}
    print("\n📁 Script Klasörleri:")
    
    for folder, files in expected_structure.items():
        folder_path = Path(folder)
        if not folder_path.exists():
            print(f"  ❌ {folder} BULUNAMADI")
            checks[folder] = False
            continue
            
        print(f"\n  📂 {folder}")
        for file in files:
            file_path = folder_path / file
            exists = file_path.exists()
            status = "✅" if exists else "❌"
            print(f"    {status} {file}")
            checks[f"{folder}{file}"] = exists

    # Sonuç
    all_passed = all(checks.values())
    total = len(checks)
    passed = sum(checks.values())
    
    print(f"\n📊 Toplam: {passed}/{total} dosya mevcut ({passed/total*100:.1f}%)")
    
    if all_passed:
        print("✅ Tüm beklenen dosyalar mevcut")
        return {'status': 'PASS', 'score': 100}
    else:
        missing = [k for k, v in checks.items() if not v]
        print(f"\n⚠️ Eksik dosyalar ({len(missing)} adet):")
        for f in missing[:10]:
            print(f"  - {f}")
        return {
            'status': 'PARTIAL' if passed/total > 0.8 else 'FAIL',
            'score': (passed/total) * 100,
            'missing': missing
        }


if __name__ == "__main__":
    result = check_project_structure()
    print(f"\nFinal Status: {result['status']}")
