import os
import ast
import sys

def get_tree(startpath):
    structure = []
    exclude = {'__pycache__', '.git', '.venv', 'venv', 'lightning_logs', 'cache', '.gemini', '.agent', 'mlruns'}
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in exclude]
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        structure.append(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if not f.endswith('.pyc'):
                structure.append(f'{subindent}{f}')
    return "\n".join(structure)

def analyze_file(filepath):
    info = {
        "lines": 0,
        "classes": [],
        "functions": [],
        "imports": [],
        "docstring": ""
    }
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            info["lines"] = len(content.splitlines())
            try:
                tree = ast.parse(content)
                info["docstring"] = ast.get_docstring(tree) or ""
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        info["classes"].append(node.name)
                    elif isinstance(node, ast.FunctionDef):
                        info["functions"].append(node.name)
                    elif isinstance(node, ast.Import):
                        for n in node.names:
                            info["imports"].append(n.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            info["imports"].append(node.module)
            except SyntaxError:
                pass
    except Exception:
        pass
    return info

def main():
    root_dir = os.getcwd()
    report_path = "project_structure_report.md"
    
    critical_files = [
        "config.py",
        "core/backtesting.py",
        "core/risk_manager.py",
        "models/ranking_model.py",
        "models/transformer_model.py",
        "models/ensemble_model.py",
        "utils/feature_engineering.py",
        "scripts/training/train_models.py", 
        "scripts/training/train_tft.py",
        "scripts/analysis/run_backtest.py"
    ]

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# BIST30 AI Trader - Proje Yapısı Raporu\n\n")
        
        # 1. Tam Dizin Ağacı
        f.write("## 1. Tam Dizin Ağacı\n")
        f.write("```bash\n")
        f.write(get_tree(root_dir))
        f.write("\n```\n\n")

        # 2. Python Dosyaları Listesi (İşlevleriyle)
        f.write("## 2. Python Dosyaları Listesi\n")
        f.write("```python\nConfig_Analizi = {\n")
        
        all_files_info = {}
        for root, dirs, files in os.walk(root_dir):
            if any(x in root for x in ['__pycache__', '.git', '.venv']): continue
            for file in files:
                if file.endswith(".py"):
                    rel_path = os.path.relpath(os.path.join(root, file), root_dir)
                    info = analyze_file(os.path.join(root, file))
                    all_files_info[rel_path] = info
                    
                    f.write(f'    "{rel_path}": {{\n')
                    f.write(f'        "Satır": {info["lines"]},\n')
                    f.write(f'        "Sınıflar": {info["classes"]},\n')
                    f.write(f'        "Fonksiyonlar": {info["functions"][:5]}... ,\n')
                    f.write(f'        "Importlar": {info["imports"][:5]}... \n')
                    f.write('    },\n')
        f.write("}\n```\n\n")

        # 3. Kritik Dosyaların İçerik Özeti
        f.write("## 3. Kritik Dosyaların İçerik Özeti\n")
        for cf in critical_files:
            if os.path.exists(cf):
                f.write(f"### {cf}\n")
                f.write("```python\n")
                with open(cf, 'r') as cf_file:
                    head = "".join(cf_file.readlines()[:50])
                    f.write(head)
                f.write("\n```\n")
                info = all_files_info.get(cf, analyze_file(cf))
                f.write(f"**Yapılar:**\n- Sınıflar: {', '.join(info['classes'])}\n- Fonksiyonlar: {', '.join(info['functions'])}\n\n")

        # 4. Bağımlılık Haritası
        f.write("## 4. Bağımlılık Haritası\n")
        f.write("```python\nImport_Graph = {\n")
        for path, info in all_files_info.items():
            if info['imports']:
                # Filter internal imports broadly
                internal_imports = [i for i in info['imports'] if i.startswith(('core', 'models', 'utils', 'config'))]
                if internal_imports:
                     f.write(f'    "{path}": {internal_imports},\n')
        f.write("}\n```\n\n")

        # 5. Config Dosyası Tam İçeriği
        f.write("## 5. Config Dosyası Tam İçeriği\n")
        if os.path.exists("config.py"):
             f.write("```python\n")
             with open("config.py", 'r') as cf:
                 f.write(cf.read())
             f.write("\n```\n\n")
        
        # 6. Eksik/Gereksiz Dosya Tespiti
        f.write("## 6. Dosya Durumu\n")
        missing = []
        if not os.path.exists("models/regime_detector.py"):
            missing.append("models/regime_detector.py (Regime Detection)")
        if not os.path.isdir("tests") or not os.listdir("tests"):
             missing.append("tests/ (Boş veya yok)")
        
        unnecessary = []
        if os.path.exists("scripts/test_pykap.py"): unnecessary.append("scripts/test_pykap.py")
        if os.path.exists("lightning_logs") and len(os.listdir("lightning_logs")) > 10: unnecessary.append("lightning_logs/ (Temizlenmeli)")

        f.write("### Kritik Eksikler\n")
        for m in missing: f.write(f"- {m}\n")
        if not missing: f.write("- Yok\n")
        
        f.write("\n### Gereksiz Dosyalar\n")
        for u in unnecessary: f.write(f"- {u}\n")
        if not unnecessary: f.write("- Yok\n")

if __name__ == "__main__":
    main()
