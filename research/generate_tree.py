import os

def generate_tree(startpath, exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = []
    
    tree_str = "# Proje Dizin Yapısı\n\n```text\n"
    
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = '│   ' * (level)
        
        if level == 0:
            tree_str += f"{os.path.basename(root)}/\n"
        else:
            tree_str += f"{indent}├── {os.path.basename(root)}/\n"
            
        subindent = '│   ' * (level + 1)
        
        for i, f in enumerate(files):
            if f in ['generate_tree.py']: continue # Exclude self
            if f.endswith('.pyc'): continue
            
            tree_str += f"{subindent}├── {f}\n"
                 
    tree_str += "```\n"
    return tree_str

if __name__ == "__main__":
    excludes = ['.git', 'venv', '__pycache__', '.idea', '.vscode', '.gemini']
    content = generate_tree(os.getcwd(), excludes)
    
    with open('PROJECT_STRUCTURE.md', 'w', encoding='utf-8') as f:
        f.write(content)
