"""File size analysis for post-development cleanup system.

This module provides the FileSizeAnalyzer class for analyzing file sizes,
identifying small and large files, and suggesting split points for large files.
"""

import ast
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional
from statistics import median

from .config import CleanupConfig
from .scanner import FileScanner, FileInfo


@dataclass
class FileSizeResult:
    """Result of file size analysis.
    
    Attributes:
        small_files: List of files below the small file threshold
        large_files: List of files above the large file threshold
        average_size: Average file size in lines of code
        median_size: Median file size in lines of code
        size_distribution: Dictionary mapping size ranges to file counts
    """
    small_files: List[FileInfo]
    large_files: List[FileInfo]
    average_size: float
    median_size: float
    size_distribution: Dict[str, int]


class FileSizeAnalyzer:
    """Analyzes file sizes and identifies small and large files.
    
    The FileSizeAnalyzer class provides methods to analyze file sizes across
    a project, classify files as small or large based on configurable thresholds,
    and suggest logical split points for large files.
    
    Attributes:
        config: CleanupConfig instance with size thresholds
        scanner: FileScanner instance for scanning files
    """
    
    def __init__(self, config: CleanupConfig, scanner: FileScanner):
        """Initialize the file size analyzer.
        
        Args:
            config: CleanupConfig instance with size thresholds
            scanner: FileScanner instance for scanning files
        """
        self.config = config
        self.scanner = scanner
    
    def analyze_sizes(self, root_path: Path) -> FileSizeResult:
        """Analyze file sizes across project.
        
        Scans all Python files in the project and classifies them based on
        size thresholds. Calculates statistics including average and median
        file sizes.
        
        Args:
            root_path: Root directory to analyze
            
        Returns:
            FileSizeResult containing analysis results
        """
        # Scan all files
        all_files = self.scanner.scan_directory(root_path)
        
        if not all_files:
            # Return empty result if no files found
            return FileSizeResult(
                small_files=[],
                large_files=[],
                average_size=0.0,
                median_size=0.0,
                size_distribution={}
            )
        
        # Classify files
        small_files = []
        large_files = []
        
        for file_info in all_files:
            if file_info.code_lines < self.config.small_file_threshold:
                small_files.append(file_info)
            elif file_info.code_lines > self.config.large_file_threshold:
                large_files.append(file_info)
        
        # Calculate statistics
        code_line_counts = [f.code_lines for f in all_files]
        average_size = sum(code_line_counts) / len(code_line_counts)
        median_size = median(code_line_counts)
        
        # Calculate size distribution
        size_distribution = self._calculate_size_distribution(all_files)
        
        return FileSizeResult(
            small_files=small_files,
            large_files=large_files,
            average_size=average_size,
            median_size=median_size,
            size_distribution=size_distribution
        )
    
    def _calculate_size_distribution(self, files: List[FileInfo]) -> Dict[str, int]:
        """Calculate distribution of file sizes.
        
        Groups files into size ranges and counts files in each range.
        
        Args:
            files: List of FileInfo objects
            
        Returns:
            Dictionary mapping size range labels to counts
        """
        distribution = {
            '0-50': 0,
            '51-100': 0,
            '101-200': 0,
            '201-500': 0,
            '501-1000': 0,
            '1000+': 0
        }
        
        for file_info in files:
            lines = file_info.code_lines
            if lines <= 50:
                distribution['0-50'] += 1
            elif lines <= 100:
                distribution['51-100'] += 1
            elif lines <= 200:
                distribution['101-200'] += 1
            elif lines <= 500:
                distribution['201-500'] += 1
            elif lines <= 1000:
                distribution['501-1000'] += 1
            else:
                distribution['1000+'] += 1
        
        return distribution
    
    def group_by_directory(self, files: List[FileInfo]) -> Dict[str, List[FileInfo]]:
        """Group files by directory.
        
        Groups files by their parent directory for easier analysis of
        related files.
        
        Args:
            files: List of FileInfo objects to group
            
        Returns:
            Dictionary mapping directory paths to lists of FileInfo objects
        """
        grouped: Dict[str, List[FileInfo]] = {}
        
        for file_info in files:
            dir_path = str(file_info.path.parent)
            if dir_path not in grouped:
                grouped[dir_path] = []
            grouped[dir_path].append(file_info)
        
        return grouped
    
    def suggest_split_points(self, file_info: FileInfo) -> List[int]:
        """Suggest logical split points for large files.
        
        Analyzes the file structure to identify logical boundaries where
        the file could be split, such as between class definitions or
        groups of functions.
        
        Args:
            file_info: FileInfo object for the file to analyze
            
        Returns:
            List of line numbers representing suggested split points
        """
        split_points = []
        
        try:
            with open(file_info.path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_info.path))
            
            # Find top-level class and function definitions
            definitions = []
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    definitions.append(node.lineno)
            
            if not definitions:
                return split_points
            
            # Sort definitions by line number
            definitions.sort()
            
            # Suggest split points at roughly equal intervals
            # Try to split into files of approximately 300-400 lines each
            target_size = 350
            num_splits = max(1, file_info.code_lines // target_size)
            
            if num_splits <= 1:
                return split_points
            
            # Find definitions closest to ideal split points
            ideal_interval = len(definitions) / (num_splits + 1)
            
            for i in range(1, num_splits + 1):
                ideal_index = int(i * ideal_interval)
                if ideal_index < len(definitions):
                    split_points.append(definitions[ideal_index])
        
        except (SyntaxError, UnicodeDecodeError, Exception):
            # If parsing fails, return empty list
            pass
        
        return split_points
    
    def export_json(self, result: FileSizeResult, output_path: Path) -> None:
        """Export results to JSON format.
        
        Exports the analysis results to a JSON file for machine consumption
        or further processing.
        
        Args:
            result: FileSizeResult to export
            output_path: Path where JSON file should be written
        """
        # Convert FileInfo objects to dictionaries
        data = {
            'small_files': [
                {
                    'path': str(f.path),
                    'code_lines': f.code_lines,
                    'total_lines': f.lines,
                    'last_modified': f.last_modified.isoformat()
                }
                for f in result.small_files
            ],
            'large_files': [
                {
                    'path': str(f.path),
                    'code_lines': f.code_lines,
                    'total_lines': f.lines,
                    'last_modified': f.last_modified.isoformat(),
                    'suggested_split_points': self.suggest_split_points(f)
                }
                for f in result.large_files
            ],
            'statistics': {
                'average_size': round(result.average_size, 2),
                'median_size': round(result.median_size, 2),
                'total_small_files': len(result.small_files),
                'total_large_files': len(result.large_files)
            },
            'size_distribution': result.size_distribution
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
