import ast
from pathlib import Path
import sys
import os
from typing import List

# Add project root to sys.path
sys.path.append(os.getcwd())

import config
from scripts.validation.utils import get_python_files

def check_config_usage():
    """
    Config'deki tüm değişkenlerin proje genelinde kullanılıp kullanılmadığını kontrol et.
    """
    
    print("="*70)
    print("CONFIG ENTEGRASYONU KONTROLÜ")
    print("="*70)
    
    # Config'deki tüm değişkenleri al
    config_vars = [attr for attr in dir(config) 
                   if not attr.startswith('_') and attr.isupper()]
    
    print(f"\n📊 Config'de {len(config_vars)} değişken tanımlı")
    
    # Tüm Python dosyalarında kullanımı ara
    project_root = Path.cwd()
    python_files = get_python_files(project_root)
    # Remove config.py itself from check list to avoid self, reference
    python_files = [f for f in python_files if 'config.py' not in str(f)]
    
    usage_count = {var: 0 for var in config_vars}
    usage_locations = {var: [] for var in config_vars}
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for var in config_vars:
                # config.VARIABLE veya CONFIG.VARIABLE veya cfg.VARIABLE
                patterns = [
                    f"config.{var}",
                    f"CONFIG.{var}",
                    f"cfg.{var}",
                    f"cfg.get('{var}'",
                    f'cfg.get("{var}"'
                ]
                
                for pattern in patterns:
                    if pattern in content:
                        usage_count[var] += content.count(pattern)
                        rel_path = py_file.relative_to(project_root)
                        if rel_path not in usage_locations[var]:
                            usage_locations[var].append(str(rel_path))
        except Exception:
             continue
    
    # ========================================
    # KULLANILMAYAN DEĞİŞKENLER
    # ========================================
    unused = [var for var, count in usage_count.items() if count == 0]
    
    print("\n" + "="*70)
    print("KULLANIM ANALİZİ")
    print("="*70)
    
    if unused:
        print(f"\n⚠️ KULLANILMAYAN CONFIG DEĞİŞKENLERİ ({len(unused)} adet):")
        for var in unused[:20]:
            print(f"  • {var}")
        if len(unused) > 20:
            print(f"  ... ve {len(unused) - 20} adet daha")
        
        print("\n💡 Bu değişkenler silinebilir veya kullanılmalı")
    else:
        print("\n✅ Tüm config değişkenleri kullanılıyor")
    
    # ========================================
    # YENİ EKLENMİŞ (REGIME) DEĞİŞKENLERİ
    # ========================================
    print("\n" + "="*70)
    print("YENİ EKLENMİŞ PARAMETRELERİN KULLANIMI")
    print("="*70)
    
    new_params = [
        'REGIME_THRESHOLDS',
        'REGIME_ACTIONS',
        'USE_ADAPTIVE_REGIME',
    ]
    
    for param in new_params:
        if param in usage_count:
            count = usage_count[param]
            locations = usage_locations[param]
            
            if count > 0:
                print(f"\n✅ {param}:")
                print(f"   Kullanım sayısı: {count}")
                print(f"   Kullanıldığı dosyalar: {', '.join(locations[:3])}")
            else:
                print(f"\n🔴 {param}:")
                print(f"   ❌ HİÇ KULLANILMAMIŞ!")
                print(f"   ⚠️ Entegrasyon EKSİK - models/regime_detector.py kontrol et")
        else:
             print(f"\n🔴 {param} config.py içinde TANIMLI DEĞİL!")

    # ========================================
    # KRİTİK PARAMETRELERİN DEĞERLERİ
    # ========================================
    print("\n" + "="*70)
    print("KRİTİK PARAMETRE DEĞERLERİ")
    print("="*70)
    
    critical_params = {
        'RISK_PER_TRADE': ('0.03', 'Risk per trade (hedef: 0.03)'),
        'MAX_DRAWDOWN_LIMIT': ('0.15', 'Max drawdown limit (hedef: 0.15)'),
        'ATR_STOP_LOSS_MULTIPLIER': ('1.5', 'Stop-loss multiplier (hedef: 1.5)'),
        'USE_ADAPTIVE_REGIME': ('True', 'Adaptive regime (hedef: True)'),
        'ENABLE_MACRO_GATE': ('True', 'Macro gate (hedef: True)'),
    }
    
    for param, (target, desc) in critical_params.items():
        if hasattr(config, param):
            actual = str(getattr(config, param))
            status = "✅" if actual == target else "⚠️"
            print(f"{status} {param:30s}: {actual:10s} (hedef: {target}) - {desc}")
        else:
            print(f"❌ {param:30s}: EKSİK!")
    
    print("\n" + "="*70)
    
    return usage_count, unused

if __name__ == "__main__":
    check_config_usage()
