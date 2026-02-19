import ast
import inspect
from pathlib import Path
import sys
import os
from typing import List

from scripts.validation.utils import get_python_files

def check_function_signature_compatibility():
    """
    Güncellenmiş fonksiyonların tüm çağrı noktalarında uyumluluğunu kontrol et.
    """
    
    print("="*70)
    print("FONKSİYON İMZA UYUMLULUK KONTROLÜ")
    print("="*70)
    
    # Güncellenmiş fonksiyonlar (manuel liste)
    updated_functions = {
        'calculate_stop_loss': {
            'file': 'core/risk_manager.py',
            'class': 'RiskManager',
            'old_params': ['self', 'entry_price', 'atr'],
            'new_params': ['self', 'entry_price', 'atr', 'regime'],
            'new_defaults': {'regime': '"NORMAL"'}
        },
        
        # Diğer güncellenmiş fonksiyonları buraya ekle
    }
    
    project_root = Path.cwd()
    python_files = get_python_files(project_root)
    
    issues = []
    
    for func_name, func_info in updated_functions.items():
        print(f"\n🔍 Kontrol ediliyor: {func_name}()")
        
        # Tüm dosyalarda bu fonksiyonun çağrılarını bul
        for py_file in python_files:
            if func_info['file'] in str(py_file):
                continue  # Tanım dosyasını atla
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basit string arama (AST ile de yapılabilir)
                if f"{func_name}(" in content:
                    # Bu dosyada kullanılıyor
                    rel_path = py_file.relative_to(project_root)
                    
                    # Parametreleri kontrol et (basit heuristic)
                    # Eğer 'regime' parametresi kullanılmamışsa sorun olabilir
                    if f"{func_name}(" in content and 'regime=' not in content:
                        # Potansiyel sorun
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if func_name in line and 'def ' not in line:
                                # Burada false-positive olabilir (positional argument)
                                # Ama yine de uyarı verelim
                                issues.append({
                                    'file': str(rel_path),
                                    'line': i,
                                    'function': func_name,
                                    'issue': f"'{func_name}' çağrısı yeni 'regime' parametresini kullanmıyor olabilir"
                                })
                                print(f"  ⚠️  {rel_path}:{i} - 'regime' parametresi eksik olabilir")
            except Exception:
                continue
    
    # Özet
    print("\n" + "="*70)
    print("SONUÇ")
    print("="*70)
    
    if not issues:
        print("\n✅ Tüm fonksiyon çağrıları güncel imzalarla uyumlu")
    else:
        print(f"\n⚠️ {len(issues)} potansiyel uyumsuzluk tespit edildi")
        print("\n💡 Manuel kontrol gerekli:")
        for issue in issues[:10]:
            print(f"  {issue['file']}:{issue['line']} - {issue['issue']}")
    
    return issues

if __name__ == "__main__":
    check_function_signature_compatibility()
