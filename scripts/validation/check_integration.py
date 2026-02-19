import os
import ast
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

from scripts.validation.utils import get_python_files

def check_all_imports():
    """
    Tüm Python dosyalarındaki import'ları kontrol et.
    Eksik/kırık import'ları tespit et.
    """
    
    print("="*70)
    print("IMPORT BAĞIMLILIKLARI KONTROLÜ")
    print("="*70)
    
    # Proje kök dizini
    project_root = Path.cwd()
    
    python_files = get_python_files(project_root)
    
    print(f"\n📁 Toplam {len(python_files)} Python dosyası bulundu.")
    print(f"🔍 Import kontrolleri başlatılıyor...\n")
    
    issues = {
        'broken_imports': [],      # Import edilemeyen modüller
        'missing_files': [],        # Dosya yok
        'circular_deps': [],        # Döngüsel bağımlılık
        'unused_imports': [],       # Kullanılmayan import'lar
        'relative_import_issues': [] # Relative import sorunları
    }
    
    for py_file in python_files:
        try:
            rel_path = py_file.relative_to(project_root)
        except ValueError:
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(py_file))
            
            # Import'ları çıkar
            imports = extract_imports(tree)
            
            # Her import'u kontrol et
            for imp in imports:
                module_name = imp['module']
                if not module_name: continue

                # Proje içi modül mü? Harici mi?
                if is_project_module(module_name, project_root):
                    # Proje içi - Dosya var mı kontrol et
                    if not check_module_exists(module_name, project_root):
                        issues['missing_files'].append({
                            'file': str(rel_path),
                            'line': imp['lineno'],
                            'missing_module': module_name
                        })
                else:
                    # Harici paket - import edilebilir mi kontrol et
                    # Sadece kurulu mu diye bakıyoruz
                    if not can_import(module_name):
                        issues['broken_imports'].append({
                            'file': str(rel_path),
                            'line': imp['lineno'],
                            'module': module_name
                        })
        
        except SyntaxError as e:
            print(f"⚠️  Syntax hatası: {rel_path}:{e.lineno}")
        except Exception as e:
            print(f"⚠️  Hata: {rel_path} - {e}")
            
    # ========================================
    # SONUÇ RAPORU
    # ========================================
    print("\n" + "="*70)
    print("IMPORT KONTROLÜ SONUÇLARI")
    print("="*70)
    
    # Eksik dosyalar
    if issues['missing_files']:
        print(f"\n🔴 EKSİK MODÜLLER ({len(issues['missing_files'])} adet):")
        for issue in issues['missing_files'][:10]:  # İlk 10
            print(f"  {issue['file']}:{issue['line']} → '{issue['missing_module']}' bulunamadı")
        if len(issues['missing_files']) > 10:
            print(f"  ... ve {len(issues['missing_files']) - 10} adet daha")
    else:
        print("\n✅ Tüm proje içi modüller mevcut")
    
    # Kırık import'lar (harici paketler)
    if issues['broken_imports']:
        print(f"\n🔴 KIRIK IMPORT'LAR ({len(issues['broken_imports'])} adet):")
        for issue in issues['broken_imports'][:10]:
            print(f"  {issue['file']}:{issue['line']} → '{issue['module']}' import edilemiyor")
        if len(issues['broken_imports']) > 10:
            print(f"  ... ve {len(issues['broken_imports']) - 10} adet daha")
        
        print("\n💡 Çözüm: Eksik paketleri yükleyin:")
        unique_modules = set(i['module'].split('.')[0] for i in issues['broken_imports'])
        print(f"   pip install {' '.join(unique_modules)}")
    else:
        print("\n✅ Tüm harici paketler yüklenmiş")
    
    print("\n" + "="*70)
    
    return issues

def extract_imports(tree: ast.AST) -> List[Dict]:
    """AST'den import'ları çıkar."""
    imports = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    'module': alias.name,
                    'lineno': node.lineno,
                    'type': 'import'
                })
        
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                imports.append({
                    'module': module,
                    'name': alias.name,
                    'full': full_name,
                    'lineno': node.lineno,
                    'type': 'from',
                    'level': node.level  # Relative import seviyesi
                })
    
    return imports

def is_project_module(module_name: str, project_root: Path) -> bool:
    """Modül proje içinde mi?"""
    # Yaygın harici paketler
    external = ['pandas', 'numpy', 'sklearn', 'lightgbm', 'torch', 
                'matplotlib', 'seaborn', 'optuna', 'yfinance', 
                'requests', 'flask', 'fastapi', 'sqlalchemy',
                'pytest', 'logging', 'json', 'os', 'sys', 'pathlib',
                'datetime', 'time', 'math', 'random', 'typing', 
                'collections', 'itertools', 'functools', 'warnings', 
                'copy', 'ast', 'inspect', 'shutil', 'subprocess', 
                'threading', 'multiprocessing', 'concurrent', 'queue',
                'contextlib', 'sqlite3', 'pickle', 'joblib', 'catboost', 
                'shap', 'scipy', 'statsmodels', 'ta', 'pandas_ta', 'mlflow',
                'schedule', 'dateutil', 'urllib', 'uvicorn', 'pydantic', 'psycopg2']
    
    first_part = module_name.split('.')[0]
    
    if first_part in external:
        return False
    
    # Proje içi klasörler
    project_modules = ['core', 'models', 'utils', 'api', 'scripts', 
                      'tests', 'config', 'configs', 'paper_trading',
                      'research', 'templates', 'ui']
    
    return first_part in project_modules

def check_module_exists(module_name: str, project_root: Path) -> bool:
    """Modül dosyası var mı?"""
    # module.submodule.file → module/submodule/file.py
    parts = module_name.split('.')
    
    # __init__.py kontrolü
    path1 = project_root / '/'.join(parts) / '__init__.py'
    if path1.exists():
        return True
    
    # Direkt .py dosyası kontrolü
    path2 = project_root / '/'.join(parts[:-1]) / f"{parts[-1]}.py"
    if path2.exists():
        return True
    
    # Klasör olarak kontrol
    path3 = project_root / '/'.join(parts)
    if path3.is_dir():
        return True
    
    return False

def can_import(module_name: str) -> bool:
    """Modül import edilebilir mi?"""
    try:
        importlib.import_module(module_name.split('.')[0])
        return True
    except (ImportError, ModuleNotFoundError):
        return False

if __name__ == "__main__":
    issues = check_all_imports()
    # Don't fail build, just warn
    sys.exit(0)
