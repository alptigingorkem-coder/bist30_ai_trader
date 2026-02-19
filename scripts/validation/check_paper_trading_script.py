#!/usr/bin/env python3
"""
Paper Trading Script Validation
Checks if paper trading script exists and can run in dry-run mode.
"""

from pathlib import Path
import subprocess


def check_paper_trading_script():
    """scripts/ops/paper_trading_runner.py script'ini kontrol et ve test et."""
    print("=" * 70)
    print("4️⃣ PAPER TRADING SCRIPT KONTROLÜ")
    print("=" * 70)

    script_path = Path('scripts/ops/paper_trading_runner.py')

    # A. Dosya varlığı
    if not script_path.exists():
        print("❌ Paper trading script BULUNAMADI!")
        return {
            'status': 'FAIL',
            'reason': 'scripts/ops/paper_trading_runner.py eksik'
        }
    
    print(f"✅ Script mevcut: {script_path}")

    # B. Script içeriğini kontrol et
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Kritik bileşenleri kontrol et
    required_components = {
        'RiskManager': 'Risk yönetimi',
        'portfolio': 'Portfolio management',
        'PaperTrader': 'Paper trading class',
        'if __name__': 'Executable script'
    }
    
    # Optional but recommended
    optional_components = {
        'regime': 'Regime detection (önerilir)',
        'def main': 'Main function (önerilir)'
    }

    print("\n🔍 Kritik Bileşenler:")
    component_checks = {}
    for component, desc in required_components.items():
        present = component in content
        status = "✅" if present else "❌"
        print(f"  {status} {component}: {desc}")
        component_checks[component] = present
    
    print("\n🔍 Opsiyonel Bileşenler:")
    optional_checks = {}
    for component, desc in optional_components.items():
        present = component in content
        status = "✅" if present else "⚠️"
        print(f"  {status} {component}: {desc}")
        optional_checks[component] = present

    # C. Dry-run test (python3 kullan)
    print("\n🧪 Dry-Run Test:")
    print("  ⏳ Test başlatılıyor (timeout: 60 saniye)...")
    
    try:
        result = subprocess.run(
            'python3 scripts/ops/paper_trading_runner.py --dry-run --days 1',
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("  ✅ Dry-run başarılı!")
            print(f"  ℹ️ Output: {result.stdout[:200]}...")
            dry_run_success = True
        else:
            print("  ❌ Dry-run BAŞARISIZ!")
            print(f"  Error: {result.stderr[:200]}...")
            dry_run_success = False
            
    except subprocess.TimeoutExpired:
        print("  ⚠️ Timeout (60s aşıldı)")
        dry_run_success = False
    except Exception as e:
        print(f"  ❌ Test hatası: {e}")
        dry_run_success = False

    # Sonuç
    all_components = all(component_checks.values())
    optional_score = sum(optional_checks.values()) / len(optional_checks) if optional_checks else 1.0
    
    # Score: 70% required + 30% optional
    base_score = 100 if all_components else 0
    final_score = base_score * 0.7 + (optional_score * 100 * 0.3)
    
    if all_components and dry_run_success:
        return {
            'status': 'PASS',
            'score': final_score,
            'message': 'Paper trading script hazır'
        }
    elif all_components:
        return {
            'status': 'PARTIAL',
            'score': final_score * 0.8,  # Dry-run fail penalty
            'message': 'Script mevcut ama dry-run başarısız'
        }
    else:
        missing = [k for k, v in component_checks.items() if not v]
        return {
            'status': 'FAIL',
            'score': 0,
            'message': f'Eksik bileşenler: {", ".join(missing)}'
        }


if __name__ == "__main__":
    result = check_paper_trading_script()
    print(f"\nFinal Status: {result['status']}")
