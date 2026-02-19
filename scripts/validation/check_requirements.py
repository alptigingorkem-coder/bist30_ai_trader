def check_requirements():
    """
    Tüm import edilen harici paketlerin requirements.txt'de olup olmadığını kontrol et.
    """
    
    print("="*70)
    print("REQUIREMENTS.TXT KONTROLÜ")
    print("="*70)
    
    from pathlib import Path
    import ast
    import sys
    import os
    
    # requirements.txt'i oku
    req_file = Path('requirements.txt')
    if not req_file.exists():
        print("\n❌ requirements.txt dosyası bulunamadı!")
        return False
    
    with open(req_file, 'r') as f:
        requirements = [line.split('==')[0].split('>=')[0].strip().lower() 
                       for line in f if line.strip() and not line.startswith('#')]
    
    print(f"\n📦 requirements.txt'de {len(requirements)} paket tanımlı")
    
    # Tüm Python dosyalarındaki import'ları topla
    project_root = Path.cwd()
    python_files = []
    exclude_dirs = {'.git', '.venv', 'env', 'venv', '__pycache__', 'node_modules', 'ui', 'archive', 'docs'}
    
    for f in project_root.glob("*.py"):
        python_files.append(f)
        
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    
    imported_packages = set()
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        pkg = alias.name.split('.')[0].lower()
                        imported_packages.add(pkg)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        pkg = node.module.split('.')[0].lower()
                        imported_packages.add(pkg)
        
        except:
            pass
    
    # Standart kütüphane paketlerini filtrele
    stdlib = ['os', 'sys', 'json', 'logging', 'datetime', 'pathlib', 
              'typing', 'collections', 'itertools', 'functools', 'math',
              'random', 'time', 'warnings', 'copy', 'ast', 'inspect', 
              'shutil', 'subprocess', 'threading', 'multiprocessing', 
              'concurrent', 'queue', 'contextlib', 'sqlite3', 'pickle', 
              'csv', 're', 'unittest', 'enum', 'abc', 'platform', 'socket',
              'hashlib', 'uuid', 'io', 'base64', 'glob', 'argparse', 'signal', 'traceback',
              'dataclasses', 'numbers', 'statistics', 'operator']
    
    # Mapping for packages where pip name != module name
    pkg_mapping = {
        'pil': 'pillow',
        'sklearn': 'scikit-learn',
        'cv2': 'opencv-python',
        'yaml': 'pyyaml',
        'bs4': 'beautifulsoup4',
        'dotenv': 'python-dotenv'
    }
    
    external_packages = set()
    for pkg in imported_packages:
        if pkg in stdlib: continue
        
        real_name = pkg_mapping.get(pkg, pkg)
        external_packages.add(real_name)
    
    print(f"📚 Projede {len(external_packages)} harici paket import edilmiş")
    
    # Eksik paketleri bul
    req_set = set(requirements)
    
    missing = []
    for pkg in external_packages:
        if pkg not in req_set:
            missing.append(pkg)
            
    # Filter known implicit deps or test tools
    ignore_list = ['tests', 'scripts', 'api', 'core', 'models', 'utils', 'paper_trading', 'config', 'configs', 'research', 'templates', 'ui'] 
    missing = [m for m in missing if m not in ignore_list]

    if missing:
        print(f"\n⚠️ requirements.txt'de EKSİK OLABİLECEK PAKETLER ({len(missing)} adet):")
        for pkg in sorted(missing):
            print(f"  - {pkg}")
        
        print("\n💡 Not: Bazıları proje modülü olabilir veya başka paketlerce kuruluyor olabilir.")
        return True # Just warn
    else:
        print("\n✅ Tüm import edilen paketler requirements.txt'de mevcut")
        return True

if __name__ == "__main__":
    check_requirements()
