import os
import ast
import sys
from pathlib import Path

def get_python_files(project_root: Path):
    print("DEBUG: Starting file walk...")
    python_files = []
    # Exclude these directories completely
    exclude_dirs = {'.git', '.venv', 'env', 'venv', '__pycache__', 'node_modules', 'ui', 'archive', 'docs', '.idea', '.vscode'}
    
    # Include root files
    for f in project_root.glob("*.py"):
        python_files.append(f)
        
    # Walk directories
    for root, dirs, files in os.walk(project_root):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # print(f"DEBUG: Visiting {root}") 
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
                
    print(f"DEBUG: Found {len(python_files)} python files.")
    return python_files

if __name__ == "__main__":
    project_root = Path.cwd()
    files = get_python_files(project_root)
    # Just print first 10
    for f in files[:10]:
        print(f"  - {f}")
    sys.exit(0)
