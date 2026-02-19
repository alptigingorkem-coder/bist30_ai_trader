"""Script categorization and organization module."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict
import json
import re


@dataclass
class ScriptCategory:
    """Script category information."""
    name: str
    scripts: List[Path]
    target_directory: str


@dataclass
class ScriptOrganizationResult:
    """Result of script organization analysis."""
    production: ScriptCategory
    analysis: ScriptCategory
    maintenance: ScriptCategory
    integration_tests: ScriptCategory
    reorganization_plan: List[Tuple[Path, Path]]
    broken_imports: List[Tuple[Path, str]]


class ScriptCategorizer:
    """Categorizes and organizes scripts."""
    
    def __init__(self, config, scanner):
        self.config = config
        self.scanner = scanner
        self.production_scripts = set(config.production_scripts)
        self.analysis_keywords = config.analysis_keywords if config.analysis_keywords else ['analyze', 'check', 'inspect', 'compare', 'evaluate']
        self.maintenance_keywords = config.maintenance_keywords if config.maintenance_keywords else ['migrate', 'update', 'fix', 'clean', 'convert']
        self.test_keywords = config.test_keywords if config.test_keywords else ['test', 'verify', 'validate', 'debug']
    
    def categorize_script(self, script_path: Path) -> str:
        """Categorize a single script."""
        if self.is_production_script(script_path):
            return 'production'
        
        script_name = script_path.name.lower()
        
        # Check for test keywords
        if any(keyword in script_name for keyword in self.test_keywords):
            return 'integration_tests'
        
        # Check for analysis keywords
        if any(keyword in script_name for keyword in self.analysis_keywords):
            return 'analysis'
        
        # Check for maintenance keywords
        if any(keyword in script_name for keyword in self.maintenance_keywords):
            return 'maintenance'
        
        # Default to analysis
        return 'analysis'
    
    def is_production_script(self, script_path: Path) -> bool:
        """Check if script is used in production."""
        script_name = script_path.name
        
        # Check if explicitly listed in config
        if script_name in self.production_scripts:
            return True
        
        # Check if referenced in shell scripts
        project_root = Path.cwd()
        for sh_file in project_root.rglob('*.sh'):
            try:
                content = sh_file.read_text()
                if script_name in content:
                    return True
            except Exception:
                pass
        
        # Check if referenced in documentation
        for doc_file in project_root.rglob('*.md'):
            try:
                content = doc_file.read_text()
                if script_name in content:
                    return True
            except Exception:
                pass
        
        return False
    
    def analyze_organization(self, scripts_dir: Path) -> ScriptOrganizationResult:
        """Analyze current organization and propose changes."""
        production_scripts = []
        analysis_scripts = []
        maintenance_scripts = []
        integration_test_scripts = []
        
        # Scan all Python scripts
        for script_path in scripts_dir.rglob('*.py'):
            if script_path.name.startswith('__'):
                continue
            
            category = self.categorize_script(script_path)
            
            if category == 'production':
                production_scripts.append(script_path)
            elif category == 'analysis':
                analysis_scripts.append(script_path)
            elif category == 'maintenance':
                maintenance_scripts.append(script_path)
            elif category == 'integration_tests':
                integration_test_scripts.append(script_path)
        
        # Create categories
        production = ScriptCategory('production', production_scripts, str(scripts_dir))
        analysis = ScriptCategory('analysis', analysis_scripts, str(scripts_dir / 'analysis'))
        maintenance = ScriptCategory('maintenance', maintenance_scripts, str(scripts_dir / 'maintenance'))
        integration_tests = ScriptCategory('integration_tests', integration_test_scripts, str(scripts_dir / 'tests'))
        
        # Generate reorganization plan
        reorganization_plan = []
        for script in analysis_scripts:
            if not str(script).startswith(str(scripts_dir / 'analysis')):
                target = scripts_dir / 'analysis' / script.name
                reorganization_plan.append((script, target))
        
        for script in maintenance_scripts:
            if not str(script).startswith(str(scripts_dir / 'maintenance')):
                target = scripts_dir / 'maintenance' / script.name
                reorganization_plan.append((script, target))
        
        for script in integration_test_scripts:
            if not str(script).startswith(str(scripts_dir / 'tests')):
                target = scripts_dir / 'tests' / script.name
                reorganization_plan.append((script, target))
        
        # Detect broken imports
        broken_imports = self.detect_broken_imports(reorganization_plan)
        
        return ScriptOrganizationResult(
            production=production,
            analysis=analysis,
            maintenance=maintenance,
            integration_tests=integration_tests,
            reorganization_plan=reorganization_plan,
            broken_imports=broken_imports
        )
    
    def detect_broken_imports(self, reorganization_plan: List[Tuple[Path, Path]]) -> List[Tuple[Path, str]]:
        """Detect imports that would break after reorganization."""
        broken_imports = []
        
        # Build mapping of old to new paths
        path_mapping = {str(old): str(new) for old, new in reorganization_plan}
        
        # Check all Python files for imports
        project_root = Path.cwd()
        for py_file in project_root.rglob('*.py'):
            try:
                content = py_file.read_text()
                for old_path_str, new_path_str in path_mapping.items():
                    old_path = Path(old_path_str)
                    # Check for imports of the moved file
                    module_name = old_path.stem
                    import_patterns = [
                        f'import {module_name}',
                        f'from {module_name} import',
                        f'from .{module_name} import',
                        f'from ..{module_name} import'
                    ]
                    for pattern in import_patterns:
                        if pattern in content:
                            broken_imports.append((py_file, pattern))
            except Exception:
                pass
        
        return broken_imports
    
    def export_json(self, result: ScriptOrganizationResult, output_path: Path):
        """Export results to JSON."""
        data = {
            'production': {
                'name': result.production.name,
                'scripts': [str(s) for s in result.production.scripts],
                'target_directory': result.production.target_directory
            },
            'analysis': {
                'name': result.analysis.name,
                'scripts': [str(s) for s in result.analysis.scripts],
                'target_directory': result.analysis.target_directory
            },
            'maintenance': {
                'name': result.maintenance.name,
                'scripts': [str(s) for s in result.maintenance.scripts],
                'target_directory': result.maintenance.target_directory
            },
            'integration_tests': {
                'name': result.integration_tests.name,
                'scripts': [str(s) for s in result.integration_tests.scripts],
                'target_directory': result.integration_tests.target_directory
            },
            'reorganization_plan': [[str(old), str(new)] for old, new in result.reorganization_plan],
            'broken_imports': [[str(f), imp] for f, imp in result.broken_imports]
        }
        
        output_path.write_text(json.dumps(data, indent=2))
