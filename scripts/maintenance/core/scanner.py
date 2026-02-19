"""File scanning utilities for post-development cleanup system.

This module provides the FileInfo dataclass and FileScanner class for scanning
Python files and extracting metadata including line counts, imports, and definitions.
"""

import ast
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from fnmatch import fnmatch

from .config import CleanupConfig


@dataclass
class FileInfo:
    """Metadata about a Python file.
    
    Attributes:
        path: Path to the Python file
        lines: Total number of lines in the file
        blank_lines: Number of blank lines
        comment_lines: Number of comment-only lines
        code_lines: Number of lines containing code
        imports: List of imported module names
        functions: List of function names defined in the file
        classes: List of class names defined in the file
        last_modified: Last modification timestamp
        has_main_block: Whether the file contains if __name__ == "__main__"
    """
    path: Path
    lines: int
    blank_lines: int
    comment_lines: int
    code_lines: int
    imports: List[str]
    functions: List[str]
    classes: List[str]
    last_modified: datetime
    has_main_block: bool = False


class FileScanner:
    """Scans Python files and extracts metadata.
    
    The FileScanner class provides methods to scan individual files or entire
    directories, extracting line counts, imports, and code definitions while
    respecting exclusion patterns from the configuration.
    
    Attributes:
        config: CleanupConfig instance with exclusion patterns and thresholds
    """
    
    def __init__(self, config: CleanupConfig):
        """Initialize the file scanner.
        
        Args:
            config: CleanupConfig instance for exclusion patterns
        """
        self.config = config
    
    def scan_file(self, file_path: Path) -> FileInfo:
        """Scan a single Python file and extract metadata.
        
        Args:
            file_path: Path to the Python file to scan
            
        Returns:
            FileInfo object containing file metadata
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get line counts
        total_lines, blank_lines, comment_lines = self.count_lines(file_path)
        code_lines = total_lines - blank_lines - comment_lines
        
        # Extract imports and definitions
        imports = self.extract_imports(file_path)
        functions, classes = self.extract_definitions(file_path)
        
        # Check for main block
        has_main_block = self.has_main_block(file_path)
        
        # Get last modified time
        last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        return FileInfo(
            path=file_path,
            lines=total_lines,
            blank_lines=blank_lines,
            comment_lines=comment_lines,
            code_lines=code_lines,
            imports=imports,
            functions=functions,
            classes=classes,
            last_modified=last_modified,
            has_main_block=has_main_block
        )
    
    def scan_directory(self, root_path: Path) -> List[FileInfo]:
        """Recursively scan directory for Python files.
        
        Scans the directory tree starting from root_path, finding all Python
        files and extracting their metadata. Respects exclusion patterns from
        the configuration.
        
        Args:
            root_path: Root directory to start scanning from
            
        Returns:
            List of FileInfo objects for all discovered Python files
        """
        file_infos = []
        
        # Find all Python files
        for py_file in root_path.rglob('*.py'):
            # Skip if in excluded directory
            if self._is_excluded_path(py_file):
                continue
            
            # Skip if matches excluded pattern
            if self._matches_excluded_pattern(py_file):
                continue
            
            try:
                file_info = self.scan_file(py_file)
                file_infos.append(file_info)
            except (FileNotFoundError, PermissionError, Exception) as e:
                # Log error but continue scanning
                print(f"Warning: Could not scan {py_file}: {e}")
                continue
        
        return file_infos
    
    def count_lines(self, file_path: Path) -> Tuple[int, int, int]:
        """Count total, blank, and comment lines in a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Tuple of (total_lines, blank_lines, comment_lines)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        
        total_lines = len(lines)
        blank_lines = 0
        comment_lines = 0
        
        in_multiline_string = False
        multiline_delimiter = None
        
        for line in lines:
            stripped = line.strip()
            
            # Check for blank lines
            if not stripped:
                blank_lines += 1
                continue
            
            # Handle multiline strings (docstrings)
            if in_multiline_string:
                if multiline_delimiter in stripped:
                    in_multiline_string = False
                    multiline_delimiter = None
                comment_lines += 1
                continue
            
            # Check for start of multiline string
            if stripped.startswith('"""') or stripped.startswith("'''"):
                delimiter = '"""' if stripped.startswith('"""') else "'''"
                # Check if it's a single-line docstring
                if stripped.count(delimiter) >= 2:
                    comment_lines += 1
                else:
                    in_multiline_string = True
                    multiline_delimiter = delimiter
                    comment_lines += 1
                continue
            
            # Check for single-line comments
            if stripped.startswith('#'):
                comment_lines += 1
                continue
        
        return total_lines, blank_lines, comment_lines
    
    def extract_imports(self, file_path: Path) -> List[str]:
        """Extract all import statements from a Python file.
        
        Uses AST parsing to extract both 'import' and 'from...import' statements.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of imported module names
        """
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        
        except (SyntaxError, UnicodeDecodeError, Exception):
            # If AST parsing fails, return empty list
            pass
        
        return imports
    
    def extract_definitions(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """Extract function and class names from a Python file.
        
        Uses AST parsing to extract top-level function and class definitions.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Tuple of (function_names, class_names)
        """
        functions = []
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.AsyncFunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
        
        except (SyntaxError, UnicodeDecodeError, Exception):
            # If AST parsing fails, return empty lists
            pass
        
        return functions, classes
    
    def has_main_block(self, file_path: Path) -> bool:
        """Check if file contains if __name__ == "__main__" block.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            True if the file contains a main block
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    # Check if this is a __name__ == "__main__" check
                    if isinstance(node.test, ast.Compare):
                        left = node.test.left
                        if isinstance(left, ast.Name) and left.id == '__name__':
                            for comparator in node.test.comparators:
                                if isinstance(comparator, ast.Constant):
                                    if comparator.value == '__main__':
                                        return True
        
        except (SyntaxError, UnicodeDecodeError, Exception):
            pass
        
        return False
    
    def _is_excluded_path(self, file_path: Path) -> bool:
        """Check if a file path is in an excluded directory.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the path is in an excluded directory
        """
        excluded_dirs = self.config.excluded_dirs
        
        for part in file_path.parts:
            if part in excluded_dirs:
                return True
        
        return False
    
    def _matches_excluded_pattern(self, file_path: Path) -> bool:
        """Check if a file matches an excluded pattern.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the filename matches an excluded pattern
        """
        excluded_patterns = self.config.excluded_patterns
        filename = file_path.name
        
        for pattern in excluded_patterns:
            if fnmatch(filename, pattern):
                return True
        
        return False
