import pkg_resources
import ast
import os
import sys

def get_imports():
    imports = set()
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r', errors='ignore') as f:
                    try:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for n in node.names:
                                    imports.add(n.name.split('.')[0])
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    imports.add(node.module.split('.')[0])
                    except:
                        pass
    return imports

def check_requirements():
    req_file = 'requirements.txt'
    if not os.path.exists(req_file):
        return
    
    with open(req_file, 'r') as f:
        requirements = {line.split('==')[0].split('>=')[0].strip().lower() for line in f if line.strip() and not line.startswith('#')}

    imports = get_imports()
    # Normalize imports
    imports = {i.lower() for i in imports}
    
    # Mapping
    mapping = {'pil': 'pillow', 'cv2': 'opencv-python', 'sklearn': 'scikit-learn', 'yaml': 'pyyaml', 'bs4': 'beautifulsoup4', 'dotenv': 'python-dotenv'}
    
    mapped_imports = set()
    for i in imports:
        mapped_imports.add(mapping.get(i, i))
        
    unused = []
    for r in requirements:
        if r not in mapped_imports:
            # Safe list
            if r not in ['gunicorn', 'uvicorn', 'psycopg2-binary', 'pytest', 'black', 'flake8', 'ipykernel']:
                unused.append(r)
    
    print("UNUSED PACKAGES IN REQUIREMENTS.TXT:")
    for u in unused:
        print(u)

if __name__ == "__main__":
    check_requirements()
