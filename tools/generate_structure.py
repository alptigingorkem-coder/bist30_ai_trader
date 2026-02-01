import os
import sys

def generate_tree(startpath, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for root, dirs, files in os.walk(startpath):
            # Sort directories and files for consistent output
            dirs.sort()
            files.sort()
            
            # Filter out unwanted directories
            # Modifying dirs in-place will prune the search
            dirs[:] = [d for d in dirs if d not in ['.git', 'venv', '__pycache__', '.idea', '.vscode', 'node_modules', 'site-packages']]
            
            level = root.replace(startpath, '').count(os.sep)
            indent = '    ' * level
            f.write('{}{}/\n'.format(indent, os.path.basename(root)))
            
            subindent = '    ' * (level + 1)
            for file in files:
                if file.endswith('.pyc') or file == '.DS_Store':
                    continue
                f.write('{}{}\n'.format(subindent, file))

if __name__ == "__main__":
    project_root = os.getcwd() # Assumes running from project root
    output_filename = "project_structure.txt"
    
    print(f"Generating project structure for: {project_root}")
    generate_tree(project_root, output_filename)
    print(f"Project structure saved to: {output_filename}")
