import ast
import os
import sys
from collections import defaultdict

def check_file(filepath):
    issues = []
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError as e:
            return [f"Syntax Error: {e}"]

    # Check for unused imports (simple heuristic)
    imports = set()
    used_names = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add((n.name, n.asname or n.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for n in node.names:
                    imports.add((f"{node.module}.{n.name}", n.asname or n.name, node.lineno))
        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                used_names.add(node.id)

    # Simple unused check (false positives possible for side-effect imports)
    # for name, asname, lineno in imports:
    #     if asname not in used_names and asname != '*':
    #        issues.append(f"Line {lineno}: Possible unused import '{name}' (as '{asname}')")

    # Check for mutable default args
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for default in node.args.defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    issues.append(f"Line {node.lineno}: Mutable default argument in function '{node.name}'")

    # Check for broad exceptions without doing anything (pass/continue only)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None or (isinstance(node.type, ast.Name) and node.type.id == 'Exception'):
                if len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Continue)):
                     issues.append(f"Line {node.lineno}: Broad exception caught and silenced ({type(node.body[0]).__name__})")

    # Check for hardcoded secrets (heuristic)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if 'API_KEY' in target.id.upper() or 'SECRET' in target.id.upper() or 'PASSWORD' in target.id.upper():
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                             if len(node.value.value) > 5 and 'ENV' not in node.value.value.upper():
                                 issues.append(f"Line {node.lineno}: Potential hardcoded secret in '{target.id}'")

    return issues

def scan_repo(root_dir):
    print(f"Scanning {root_dir}...")
    all_issues = defaultdict(list)
    for root, _, files in os.walk(root_dir):
        if '.venv' in root or '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                file_issues = check_file(path)
                if file_issues:
                    all_issues[path] = file_issues
    
    print("\nAudit Results:")
    for path, issues in all_issues.items():
        rel_path = os.path.relpath(path, root_dir)
        print(f"\n📄 {rel_path}")
        for issue in issues:
            print(f"  ⚠️ {issue}")

if __name__ == "__main__":
    scan_repo(os.getcwd())
