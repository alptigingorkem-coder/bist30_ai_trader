"""Duplicate code detection for post-development cleanup system.

This module provides the DuplicateCodeDetector class for identifying duplicate
or near-duplicate function implementations across Python files.
"""

import ast
import json
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Tuple, Dict

from .config import CleanupConfig
from .scanner import FileScanner


@dataclass
class DuplicateGroup:
    """Group of duplicate functions.
    
    Attributes:
        function_name: Name of the duplicated function
        locations: List of (file_path, line_number) tuples where function appears
        similarity: Similarity score (0.0 to 1.0)
        code_snippet: Representative code snippet from one instance
        suggested_location: Suggested location for shared utility
    """
    function_name: str
    locations: List[Tuple[str, int]]  # (file_path, line_number)
    similarity: float
    code_snippet: str
    suggested_location: str


@dataclass
class DuplicateResult:
    """Result of duplicate detection.
    
    Attributes:
        duplicate_groups: List of duplicate function groups
        total_duplicates: Total number of duplicate instances found
    """
    duplicate_groups: List[DuplicateGroup]
    total_duplicates: int


class DuplicateCodeDetector:
    """Detects duplicate code across Python files.
    
    The DuplicateCodeDetector identifies functions with identical or near-identical
    implementations across multiple files. It normalizes code (removing whitespace
    and comments) before comparison and groups duplicates together.
    
    Attributes:
        config: CleanupConfig instance with duplicate similarity threshold
        scanner: FileScanner instance for file analysis
    """
    
    def __init__(self, config: CleanupConfig, scanner: FileScanner):
        """Initialize the duplicate code detector.
        
        Args:
            config: CleanupConfig instance with similarity threshold
            scanner: FileScanner instance for file scanning
        """
        self.config = config
        self.scanner = scanner
    
    def extract_functions(self, file_path: Path) -> List[Tuple[str, str, int]]:
        """Extract function name, body, and line number from a file.
        
        Uses AST parsing to extract all function definitions including their
        source code and line numbers.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of (function_name, function_body, line_number) tuples
        """
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            lines = content.splitlines()
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Extract function name and line number
                    func_name = node.name
                    line_number = node.lineno
                    
                    # Extract function body source code
                    # Get the range of lines for this function
                    start_line = node.lineno - 1  # Convert to 0-indexed
                    
                    # Find the end line by looking at the last statement
                    if node.body:
                        end_line = node.body[-1].end_lineno
                    else:
                        end_line = node.lineno
                    
                    # Extract the function source
                    if end_line and start_line < len(lines):
                        func_body = '\n'.join(lines[start_line:end_line])
                        functions.append((func_name, func_body, line_number))
        
        except (SyntaxError, UnicodeDecodeError, Exception) as e:
            # If parsing fails, return empty list
            pass
        
        return functions
    
    def normalize_code(self, code: str) -> str:
        """Normalize whitespace and comments from code.
        
        Removes leading/trailing whitespace, normalizes internal whitespace,
        and removes comments to enable accurate similarity comparison.
        
        Args:
            code: Source code string
            
        Returns:
            Normalized code string
        """
        lines = code.split('\n')
        normalized_lines = []
        
        for line in lines:
            # Remove leading/trailing whitespace
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
            
            # Skip comment-only lines
            if stripped.startswith('#'):
                continue
            
            # Remove inline comments (but be careful with strings)
            # Simple approach: remove # and everything after if not in string
            # This is a simplified version - a full implementation would need
            # proper string literal detection
            if '#' in stripped:
                # Check if # is in a string literal
                in_string = False
                string_char = None
                result = []
                
                for i, char in enumerate(stripped):
                    if char in ('"', "'") and (i == 0 or stripped[i-1] != '\\'):
                        if not in_string:
                            in_string = True
                            string_char = char
                        elif char == string_char:
                            in_string = False
                            string_char = None
                    
                    if char == '#' and not in_string:
                        break
                    
                    result.append(char)
                
                stripped = ''.join(result).strip()
            
            # Normalize whitespace within the line
            # Replace multiple spaces with single space
            normalized = ' '.join(stripped.split())
            
            if normalized:
                normalized_lines.append(normalized)
        
        return '\n'.join(normalized_lines)
    
    def calculate_similarity(self, code1: str, code2: str) -> float:
        """Calculate similarity between two code blocks.
        
        Uses difflib.SequenceMatcher to calculate similarity ratio between
        normalized code blocks.
        
        Args:
            code1: First code block
            code2: Second code block
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Normalize both code blocks
        norm1 = self.normalize_code(code1)
        norm2 = self.normalize_code(code2)
        
        # Calculate similarity using SequenceMatcher
        matcher = SequenceMatcher(None, norm1, norm2)
        similarity = matcher.ratio()
        
        return similarity
    
    def find_duplicates(self, root_path: Path) -> DuplicateResult:
        """Find all duplicate code in the project.
        
        Scans all Python files in the project, extracts functions, normalizes
        them, and groups duplicates based on similarity threshold.
        
        Args:
            root_path: Root directory to scan
            
        Returns:
            DuplicateResult containing all duplicate groups
        """
        # Scan all files
        file_infos = self.scanner.scan_directory(root_path)
        
        # Extract all functions from all files
        all_functions: List[Tuple[str, str, Path, int]] = []
        # (function_name, function_body, file_path, line_number)
        
        for file_info in file_infos:
            functions = self.extract_functions(file_info.path)
            for func_name, func_body, line_num in functions:
                all_functions.append((func_name, func_body, file_info.path, line_num))
        
        # Group functions by name (only compare functions with same name)
        functions_by_name: Dict[str, List[Tuple[str, Path, int]]] = {}
        # {function_name: [(function_body, file_path, line_number), ...]}
        
        for func_name, func_body, file_path, line_num in all_functions:
            if func_name not in functions_by_name:
                functions_by_name[func_name] = []
            functions_by_name[func_name].append((func_body, file_path, line_num))
        
        # Find duplicates within each function name group
        duplicate_groups = []
        threshold = self.config.duplicate_similarity
        
        for func_name, instances in functions_by_name.items():
            # Skip if only one instance
            if len(instances) < 2:
                continue
            
            # Compare all pairs and group similar ones
            processed = set()
            
            for i, (body1, path1, line1) in enumerate(instances):
                if i in processed:
                    continue
                
                # Start a new group with this instance
                group_instances = [(path1, line1)]
                group_bodies = [body1]
                processed.add(i)
                
                # Find all similar instances
                for j, (body2, path2, line2) in enumerate(instances):
                    if j <= i or j in processed:
                        continue
                    
                    similarity = self.calculate_similarity(body1, body2)
                    
                    if similarity >= threshold:
                        group_instances.append((path2, line2))
                        group_bodies.append(body2)
                        processed.add(j)
                
                # Only create a group if we found duplicates
                if len(group_instances) > 1:
                    # Calculate average similarity for the group
                    similarities = []
                    for k in range(len(group_bodies)):
                        for m in range(k + 1, len(group_bodies)):
                            sim = self.calculate_similarity(group_bodies[k], group_bodies[m])
                            similarities.append(sim)
                    
                    avg_similarity = sum(similarities) / len(similarities) if similarities else 1.0
                    
                    # Use the first instance as the code snippet
                    code_snippet = group_bodies[0][:200]  # First 200 chars
                    if len(group_bodies[0]) > 200:
                        code_snippet += "..."
                    
                    # Suggest shared location
                    suggested_location = self.suggest_shared_location(
                        DuplicateGroup(
                            function_name=func_name,
                            locations=[(str(p), ln) for p, ln in group_instances],
                            similarity=avg_similarity,
                            code_snippet=code_snippet,
                            suggested_location=""
                        )
                    )
                    
                    duplicate_group = DuplicateGroup(
                        function_name=func_name,
                        locations=[(str(p), ln) for p, ln in group_instances],
                        similarity=avg_similarity,
                        code_snippet=code_snippet,
                        suggested_location=suggested_location
                    )
                    
                    duplicate_groups.append(duplicate_group)
        
        # Calculate total duplicates
        total_duplicates = sum(len(group.locations) for group in duplicate_groups)
        
        return DuplicateResult(
            duplicate_groups=duplicate_groups,
            total_duplicates=total_duplicates
        )
    
    def suggest_shared_location(self, group: DuplicateGroup) -> str:
        """Suggest where to place shared utility for a duplicate group.
        
        Analyzes the file locations of duplicates and suggests an appropriate
        shared utility location based on common directory structure.
        
        Args:
            group: DuplicateGroup to analyze
            
        Returns:
            Suggested file path for shared utility
        """
        if not group.locations:
            return "utils/common.py"
        
        # Get all file paths
        paths = [Path(loc[0]) for loc in group.locations]
        
        # Find common parent directory
        if len(paths) == 1:
            # Single location - suggest utils in same directory
            parent = paths[0].parent
            return str(parent / "utils.py")
        
        # Find common ancestor
        common_parts = []
        path_parts = [list(p.parts) for p in paths]
        
        if path_parts:
            min_length = min(len(parts) for parts in path_parts)
            
            for i in range(min_length):
                part = path_parts[0][i]
                if all(parts[i] == part for parts in path_parts):
                    common_parts.append(part)
                else:
                    break
        
        # Build suggested location
        if common_parts:
            common_path = Path(*common_parts)
            
            # If common path is a specific module directory, suggest utils there
            if len(common_parts) > 1:
                return str(common_path / "utils.py")
            else:
                return str(common_path / "common" / "utils.py")
        
        # Default suggestion
        return "utils/common.py"
    
    def export_json(self, result: DuplicateResult, output_path: Path) -> None:
        """Export duplicate detection results to JSON.
        
        Args:
            result: DuplicateResult to export
            output_path: Path to output JSON file
        """
        # Convert result to dictionary
        data = {
            'total_duplicates': result.total_duplicates,
            'duplicate_groups': [
                {
                    'function_name': group.function_name,
                    'locations': [
                        {'file': loc[0], 'line': loc[1]}
                        for loc in group.locations
                    ],
                    'similarity': group.similarity,
                    'code_snippet': group.code_snippet,
                    'suggested_location': group.suggested_location
                }
                for group in result.duplicate_groups
            ]
        }
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
