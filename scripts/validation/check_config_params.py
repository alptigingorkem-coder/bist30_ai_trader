#!/usr/bin/env python3
"""
Configuration Parameters Validation
Checks that config.py has safe parameters for paper trading.
"""


def check_config_parameters():
    """config.py'deki kritik parametreleri kontrol et."""
    print("=" * 70)
    print("6️⃣ CONFIG PARAMETRE KONTROLÜ")
    print("=" * 70)

    try:
        import sys
        from pathlib import Path
        # Add project root to path
        project_root = Path(__file__).parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        import config
    except ImportError as e:
        print(f"❌ config.py import hatası: {e}")
        return {'status': 'FAIL', 'score': 0, 'reason': f'config.py import error: {e}'}

    # Paper trading için güvenli değerler
    safe_params = {
        'RISK_PER_TRADE': {
            'current': getattr(config, 'RISK_PER_TRADE', None),
            'safe_range': (0.01, 0.05),  # %1-5
            'recommended': 0.03
        },
        'MAX_DRAWDOWN_LIMIT': {
            'current': getattr(config, 'MAX_DRAWDOWN_LIMIT', None),
            'safe_range': (0.10, 0.20),  # %10-20
            'recommended': 0.15
        },
        'USE_ADAPTIVE_REGIME': {
            'current': getattr(config, 'USE_ADAPTIVE_REGIME', None),
            'expected': True
        },
        'ENABLE_MACRO_GATE': {
            'current': getattr(config, 'ENABLE_MACRO_GATE', None),
            'expected': True
        }
    }

    checks = {}
    print("\n⚙️ Kritik Parametreler:")
    
    for param, info in safe_params.items():
        current = info['current']
        
        if current is None:
            print(f"  ❌ {param} tanımlı değil!")
            checks[param] = False
            continue
        
        if 'safe_range' in info:
            # Numeric parameter
            min_val, max_val = info['safe_range']
            recommended = info['recommended']
            
            safe = min_val <= current <= max_val
            optimal = abs(current - recommended) / recommended < 0.2  # %20 içinde
            
            if safe and optimal:
                status = "✅"
                checks[param] = True
            elif safe:
                status = "🟡"
                checks[param] = True
            else:
                status = "❌"
                checks[param] = False
            
            print(f"  {status} {param} = {current}")
            print(f"      Güvenli aralık: {min_val} - {max_val}")
            print(f"      Önerilen: {recommended}")
        else:
            # Boolean parameter
            expected = info['expected']
            safe = current == expected
            status = "✅" if safe else "❌"
            checks[param] = safe
            print(f"  {status} {param} = {current} (beklenen: {expected})")

    # Sonuç
    passed = sum(checks.values())
    total = len(checks)
    score = (passed / total) * 100
    
    print(f"\n📊 Config Skoru: {score:.1f}% ({passed}/{total})")
    
    if score == 100:
        return {'status': 'PASS', 'score': 100}
    elif score >= 75:
        return {'status': 'PARTIAL', 'score': score}
    else:
        return {'status': 'FAIL', 'score': score}


if __name__ == "__main__":
    result = check_config_parameters()
    print(f"\nFinal Status: {result['status']}")
