"""Unused file detection for post-development cleanup system.

This module provides the UnusedFileDetector class for identifying Python files
that are not imported anywhere in the project.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Set

from .config import CleanupConfig
from .scanner import FileScanner, FileInfo


@dataclass
class UnusedFileResult:
    """Result of unused file detection.
    
    Attributes:
        unused_files: List of FileInfo objects for files not imported anywhere
        import_graph: Dictionary mapping file paths to lists of imported file paths
        special_files: List of special file paths that are excluded from unused detection
    """
    unused_files: List[FileInfo]
    import_graph: Dict[str, List[str]]
    special_files: List[str]


class UnusedFileDetector:
    """Detects unused Python files.
    
    The UnusedFileDetector builds an import graph of all Python files in a project
    and identifies files that are not imported by any other file. Special files
    like __init__.py, __main__.py, and setup.py are excluded from the unused list.
    
    Attributes:
        config: CleanupConfig instance with exclusion patterns
        scanner: FileScanner instance for scanning files
    """
    
    def __init__(self, config: CleanupConfig, scanner: FileScanner):
        """Initialize the unused file detector.
        
        Args:
            config: CleanupConfig instance for exclusion patterns
            scanner: FileScanner instance for scanning files
        """
        self.config = config
        self.scanner = scanner
    
    def build_import_graph(self, files: List[FileInfo]) -> Dict[str, List[str]]:
        """Build graph of file imports.
        
        Creates a dictionary mapping each file path to a list of file paths it imports.
        The graph is built by analyzing import statements and resolving them to actual
        file paths in the project.
        
        Args:
            files: List of FileInfo objects to analyze
            
        Returns:
            Dictionary mapping file paths (as strings) to lists of imported file paths
        """
        import_graph = {}
        
        # Create a mapping of module names to file paths for quick lookup
        module_to_file = self._build_module_mapping(files)
        
        for file_info in files:
            file_path_str = str(file_info.path)
            imported_files = []
            
            for import_name in file_info.imports:
                # Try to resolve the import to a file in the project
                resolved_file = self._resolve_import(import_name, file_info.path, module_to_file)
                if resolved_file:
                    imported_files.append(str(resolved_file))
            
            import_graph[file_path_str] = imported_files
        
        return import_graph
    
    def find_unused_files(self, root_path: Path) -> UnusedFileResult:
        """Find all unused Python files.
        
        Scans the project directory, builds an import graph, identifies special files,
        and determines which files are not imported by any other file.
        
        Args:
            root_path: Root directory of the project to analyze
            
        Returns:
            UnusedFileResult containing unused files, import graph, and special files
        """
        # Scan all Python files
        files = self.scanner.scan_directory(root_path)
        
        # Build import graph
        import_graph = self.build_import_graph(files)
        
        # Identify special files
        special_files = [str(f.path) for f in files if self.is_special_file(f)]
        
        # Find all files that are imported (appear in any import list)
        imported_files: Set[str] = set()
        for imported_list in import_graph.values():
            imported_files.update(imported_list)
        
        # Find unused files: not imported and not special
        unused_files = []
        for file_info in files:
            file_path_str = str(file_info.path)
            if file_path_str not in imported_files and file_path_str not in special_files:
                unused_files.append(file_info)
        
        return UnusedFileResult(
            unused_files=unused_files,
            import_graph=import_graph,
            special_files=special_files
        )
    
    def is_special_file(self, file_info) -> bool:
        """Check if file is special and should not be marked as unused.
        
        Special files are excluded from unused file detection because they serve
        special purposes in Python projects:
        - __init__.py: Package initialization
        - __main__.py: Entry point for python -m
        - setup.py: Package installation script
        - Files with if __name__ == "__main__": Entry point scripts
        - Files in tests/ directory: Test files run by pytest
        - Files in api/ directory: API endpoints and servers
        - Files in configs/ directory: Configuration files (may be dynamically imported)
        - Files in examples/ directory: Example scripts
        - Files in scripts/ directory: CLI tools and utilities
        - Files in paper_trading/ directory: Live trading scripts
        
        Args:
            file_info: FileInfo object or Path object to check
            
        Returns:
            True if the file is a special file
        """
        # Handle both FileInfo objects and Path objects
        if isinstance(file_info, Path):
            file_path = file_info
            has_main_block = False  # Can't determine without parsing
        else:
            file_path = file_info.path
            has_main_block = file_info.has_main_block
        
        filename = file_path.name
        
        # Check for special filenames
        if filename in ('__init__.py', '__main__.py', 'setup.py'):
            return True
        
        # Check if file has a main block (entry point)
        if has_main_block:
            return True
        
        # Check if file is in special directories
        parts = file_path.parts
        special_dirs = {
            'tests',           # Test files
            'api',             # API endpoints
            'configs',         # Configuration files
            'examples',        # Example scripts
            'paper_trading',   # Live trading
        }
        
        for special_dir in special_dirs:
            if special_dir in parts:
                return True
        
        # Special case for scripts: only top-level scripts are special
        # scripts/train.py -> special (top-level)
        # scripts/analysis/helper.py -> not special (subdirectory)
        if 'scripts' in parts:
            scripts_index = parts.index('scripts')
            # If there's only one more part after 'scripts', it's top-level
            if len(parts) - scripts_index == 2:  # scripts/filename.py
                return True
        
        return False
    
    def export_json(self, result: UnusedFileResult, output_path: Path) -> None:
        """Export results to JSON.
        
        Exports the unused file detection results to a JSON file with a structured
        format suitable for further processing or reporting.
        
        Args:
            result: UnusedFileResult to export
            output_path: Path where JSON file should be written
        """
        # Convert FileInfo objects to dictionaries
        unused_files_data = []
        for file_info in result.unused_files:
            file_data = {
                'path': str(file_info.path),
                'lines': file_info.lines,
                'code_lines': file_info.code_lines,
                'last_modified': file_info.last_modified.isoformat(),
                'functions': file_info.functions,
                'classes': file_info.classes,
            }
            unused_files_data.append(file_data)
        
        # Build output structure
        output_data = {
            'unused_files': unused_files_data,
            'unused_count': len(result.unused_files),
            'total_files': len(result.import_graph),
            'special_files': result.special_files,
            'import_graph': result.import_graph,
        }
        
        # Write to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def _build_module_mapping(self, files: List[FileInfo]) -> Dict[str, Path]:
        """Build mapping of module names to file paths.
        
        Creates a dictionary that maps Python module names (as they would appear
        in import statements) to their corresponding file paths.
        
        Args:
            files: List of FileInfo objects
            
        Returns:
            Dictionary mapping module names to file paths
        """
        module_to_file = {}
        
        for file_info in files:
            # Convert file path to module name
            # e.g., scripts/analysis/feature_importance.py -> scripts.analysis.feature_importance
            path_parts = file_info.path.parts
            
            # Remove .py extension
            if path_parts[-1].endswith('.py'):
                module_parts = list(path_parts[:-1]) + [path_parts[-1][:-3]]
            else:
                module_parts = list(path_parts)
            
            # Create module name
            module_name = '.'.join(module_parts)
            module_to_file[module_name] = file_info.path
            
            # Also add shorter versions (for relative imports)
            # e.g., analysis.feature_importance, feature_importance
            for i in range(1, len(module_parts)):
                short_module = '.'.join(module_parts[i:])
                if short_module not in module_to_file:
                    module_to_file[short_module] = file_info.path
        
        return module_to_file
    
    def _resolve_import(self, import_name: str, importing_file: Path, 
                       module_to_file: Dict[str, Path]) -> Path | None:
        """Resolve an import statement to a file path.
        
        Attempts to resolve an import name to an actual file path in the project.
        Handles both absolute and relative imports.
        
        Args:
            import_name: Name of the imported module (e.g., 'scripts.analysis.feature_importance')
            importing_file: Path of the file containing the import
            module_to_file: Mapping of module names to file paths
            
        Returns:
            Resolved file path, or None if the import is external or cannot be resolved
        """
        # Try direct lookup
        if import_name in module_to_file:
            return module_to_file[import_name]
        
        # Try with common prefixes removed (for relative imports)
        # e.g., if import is 'core.config' from 'scripts/maintenance/detector.py'
        # try 'scripts.maintenance.core.config'
        importing_dir = importing_file.parent
        dir_parts = importing_dir.parts
        
        for i in range(len(dir_parts), -1, -1):
            prefix = '.'.join(dir_parts[:i])
            if prefix:
                full_module = f"{prefix}.{import_name}"
            else:
                full_module = import_name
            
            if full_module in module_to_file:
                return module_to_file[full_module]
        
        # Could not resolve - likely an external import
        return None
