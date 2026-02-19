"""Shared utility functions for validation scripts.

This module contains common helper functions used across
multiple validation scripts.
"""

from pathlib import Path
from typing import List


def get_python_files(project_root: Path) -> List[Path]:
    """Efficiently find Python files excluding specific directories.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        List of Path objects for Python files
    """
    python_files = []
    exclude_dirs = {'.git', '.venv', 'env', 'venv', '__pycache__', '.pytest_cache', 
                    'node_modules', '.hypothesis', 'lightning_logs', 'mlruns', 
                    'catboost_info', 'cache'}
    
    for py_file in project_root.rglob('*.py'):
        # Check if any parent directory is in exclude list
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        python_files.append(py_file)
    
    return python_files
