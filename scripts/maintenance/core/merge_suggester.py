"""Merge suggestion module for small files."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict
import json


@dataclass
class MergeSuggestion:
    """Suggestion to merge files."""
    source_files: List[any]  # FileInfo objects
    target_file: Path
    estimated_size: int
    functional_similarity: float
    required_import_updates: List[Tuple[Path, str, str]]


@dataclass
class MergeResult:
    """Result of merge analysis."""
    suggestions: List[MergeSuggestion]
    total_file_reduction: int


class MergeSuggester:
    """Suggests file merges."""
    
    def __init__(self, config, scanner, similarity_threshold=0.5):
        self.config = config
        self.scanner = scanner
        self.small_threshold = config.small_file_threshold
        self.large_threshold = config.large_file_threshold
        self.similarity_threshold = similarity_threshold
    
    def calculate_functional_similarity(self, files: List[any]) -> float:
        """Calculate functional similarity between files."""
        if len(files) < 2:
            return 0.0
        
        # Calculate import similarity
        all_imports = [set(f.imports) for f in files]
        if all_imports:
            common_imports = set.intersection(*all_imports) if len(all_imports) > 1 else all_imports[0]
            total_imports = set.union(*all_imports)
            import_similarity = len(common_imports) / len(total_imports) if total_imports else 0.0
        else:
            import_similarity = 0.0
        
        # Calculate naming similarity (check for common prefixes/suffixes)
        all_functions = [set(f.functions) for f in files]
        naming_similarity = 0.0
        if all_functions:
            # Check for common prefixes
            all_func_names = [name for funcs in all_functions for name in funcs]
            if all_func_names:
                prefixes = set()
                for name in all_func_names:
                    if '_' in name:
                        prefixes.add(name.split('_')[0])
                naming_similarity = len(prefixes) / len(all_func_names) if all_func_names else 0.0
        
        # Calculate class hierarchy similarity
        all_classes = [set(f.classes) for f in files]
        hierarchy_similarity = 0.0
        if all_classes:
            common_classes = set.intersection(*all_classes) if len(all_classes) > 1 else set()
            total_classes = set.union(*all_classes)
            hierarchy_similarity = len(common_classes) / len(total_classes) if total_classes else 0.0
        
        # Weighted score
        return 0.4 * import_similarity + 0.3 * hierarchy_similarity + 0.3 * naming_similarity
    
    def suggest_merges(self, small_files: List[any]) -> MergeResult:
        """Suggest merge opportunities."""
        suggestions = []
        
        # Group files by directory
        by_directory = {}
        for file_info in small_files:
            directory = file_info.path.parent
            if directory not in by_directory:
                by_directory[directory] = []
            by_directory[directory].append(file_info)
        
        # For each directory, find merge candidates
        for directory, files in by_directory.items():
            if len(files) < 2:
                continue
            
            # Calculate similarity for all pairs
            for i in range(len(files)):
                for j in range(i + 1, len(files)):
                    file_group = [files[i], files[j]]
                    similarity = self.calculate_functional_similarity(file_group)
                    
                    # If similarity is high enough, suggest merge
                    if similarity > self.similarity_threshold:
                        estimated_size = self.estimate_merged_size(file_group)
                        
                        # Only suggest if merged size is reasonable
                        if estimated_size <= self.large_threshold:
                            target_file = directory / f"{files[i].path.stem}_{files[j].path.stem}.py"
                            import_updates = self.find_import_updates(file_group, target_file)
                            
                            suggestion = MergeSuggestion(
                                source_files=file_group,
                                target_file=target_file,
                                estimated_size=estimated_size,
                                functional_similarity=similarity,
                                required_import_updates=import_updates
                            )
                            suggestions.append(suggestion)
        
        total_reduction = sum(len(s.source_files) - 1 for s in suggestions)
        
        return MergeResult(
            suggestions=suggestions,
            total_file_reduction=total_reduction
        )
    
    def estimate_merged_size(self, files: List[any]) -> int:
        """Estimate size of merged file."""
        # Sum code lines, accounting for potential duplicate imports
        total_lines = sum(f.code_lines for f in files)
        
        # Estimate import deduplication savings
        all_imports = [set(f.imports) for f in files]
        if all_imports:
            unique_imports = set.union(*all_imports)
            total_imports = sum(len(imports) for imports in all_imports)
            import_savings = total_imports - len(unique_imports)
        else:
            import_savings = 0
        
        return max(0, total_lines - import_savings)
    
    def find_import_updates(self, files: List[any], target_file: Path) -> List[Tuple[Path, str, str]]:
        """Find all imports that need updating."""
        import_updates = []
        
        # Check all Python files in project
        project_root = Path.cwd()
        for py_file in project_root.rglob('*.py'):
            try:
                content = py_file.read_text()
                for file_info in files:
                    module_name = file_info.path.stem
                    target_module = target_file.stem
                    
                    # Check for imports
                    if f'import {module_name}' in content:
                        import_updates.append((py_file, f'import {module_name}', f'import {target_module}'))
                    if f'from {module_name} import' in content:
                        import_updates.append((py_file, f'from {module_name} import', f'from {target_module} import'))
            except Exception:
                pass
        
        return import_updates
    
    def export_json(self, result: MergeResult, output_path: Path):
        """Export results to JSON."""
        data = {
            'suggestions': [
                {
                    'source_files': [str(f.path) for f in s.source_files],
                    'target_file': str(s.target_file),
                    'estimated_size': s.estimated_size,
                    'functional_similarity': s.functional_similarity,
                    'required_import_updates': [[str(f), old, new] for f, old, new in s.required_import_updates]
                }
                for s in result.suggestions
            ],
            'total_file_reduction': result.total_file_reduction
        }
        
        output_path.write_text(json.dumps(data, indent=2))
