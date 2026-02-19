"""Automated cleanup manager for temporary files and artifacts."""

from dataclasses import dataclass
from pathlib import Path
from typing import List
from datetime import datetime, timedelta
import json
import logging


@dataclass
class CleanupOperation:
    """Single cleanup operation."""
    operation_type: str
    target: Path
    reason: str
    size_bytes: int


@dataclass
class CleanupResult:
    """Result of cleanup operations."""
    operations: List[CleanupOperation]
    total_size_freed: int
    dry_run: bool


class AutoCleanupManager:
    """Manages automated cleanup."""
    
    def __init__(self, config):
        self.config = config
        self.log_retention_days = config.log_retention_days
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    
    def find_pycache_dirs(self, root_path: Path) -> List[Path]:
        """Find all __pycache__ directories."""
        pycache_dirs = []
        for path in root_path.rglob('__pycache__'):
            if path.is_dir():
                pycache_dirs.append(path)
        return pycache_dirs
    
    def find_old_logs(self, root_path: Path) -> List[Path]:
        """Find log files older than retention period."""
        old_logs = []
        cutoff_date = datetime.now() - timedelta(days=self.log_retention_days)
        
        for log_file in root_path.rglob('*.log'):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff_date:
                    old_logs.append(log_file)
            except Exception:
                pass
        
        return old_logs
    
    def find_empty_inits(self, root_path: Path) -> List[Path]:
        """Find empty __init__.py files."""
        empty_inits = []
        
        for init_file in root_path.rglob('__init__.py'):
            try:
                # Check if file is empty or only contains whitespace/comments
                content = init_file.read_text().strip()
                if not content or all(line.strip().startswith('#') for line in content.split('\n')):
                    # Check if directory has other Python files
                    directory = init_file.parent
                    other_py_files = [f for f in directory.glob('*.py') if f.name != '__init__.py']
                    if not other_py_files:
                        empty_inits.append(init_file)
            except Exception:
                pass
        
        return empty_inits
    
    def find_temp_files(self, root_path: Path) -> List[Path]:
        """Find temporary files matching patterns."""
        temp_files = []
        patterns = ['*.tmp', '*.bak', '*~', '.DS_Store', '*.pyc']
        
        for pattern in patterns:
            for temp_file in root_path.rglob(pattern):
                if temp_file.is_file():
                    temp_files.append(temp_file)
        
        return temp_files
    
    def execute_cleanup(self, root_path: Path, dry_run: bool = True) -> CleanupResult:
        """Execute cleanup operations."""
        operations = []
        total_size = 0
        
        # Find all cleanup targets
        pycache_dirs = self.find_pycache_dirs(root_path)
        old_logs = self.find_old_logs(root_path)
        empty_inits = self.find_empty_inits(root_path)
        temp_files = self.find_temp_files(root_path)
        
        # Process __pycache__ directories
        for pycache_dir in pycache_dirs:
            try:
                size = sum(f.stat().st_size for f in pycache_dir.rglob('*') if f.is_file())
                operation = CleanupOperation(
                    operation_type='delete_dir',
                    target=pycache_dir,
                    reason='__pycache__ directory',
                    size_bytes=size
                )
                operations.append(operation)
                total_size += size
                
                if not dry_run:
                    import shutil
                    shutil.rmtree(pycache_dir)
                    self.log_operation(operation)
            except Exception as e:
                self.logger.warning(f"Failed to process {pycache_dir}: {e}")
        
        # Process old log files
        for log_file in old_logs:
            try:
                size = log_file.stat().st_size
                operation = CleanupOperation(
                    operation_type='delete_file',
                    target=log_file,
                    reason=f'Log file older than {self.log_retention_days} days',
                    size_bytes=size
                )
                operations.append(operation)
                total_size += size
                
                if not dry_run:
                    log_file.unlink()
                    self.log_operation(operation)
            except Exception as e:
                self.logger.warning(f"Failed to process {log_file}: {e}")
        
        # Process empty __init__.py files
        for init_file in empty_inits:
            try:
                size = init_file.stat().st_size
                operation = CleanupOperation(
                    operation_type='remove_empty_init',
                    target=init_file,
                    reason='Empty __init__.py in directory with no other Python files',
                    size_bytes=size
                )
                operations.append(operation)
                total_size += size
                
                if not dry_run:
                    init_file.unlink()
                    self.log_operation(operation)
            except Exception as e:
                self.logger.warning(f"Failed to process {init_file}: {e}")
        
        # Process temporary files
        for temp_file in temp_files:
            try:
                size = temp_file.stat().st_size
                operation = CleanupOperation(
                    operation_type='delete_file',
                    target=temp_file,
                    reason=f'Temporary file matching pattern',
                    size_bytes=size
                )
                operations.append(operation)
                total_size += size
                
                if not dry_run:
                    temp_file.unlink()
                    self.log_operation(operation)
            except Exception as e:
                self.logger.warning(f"Failed to process {temp_file}: {e}")
        
        return CleanupResult(
            operations=operations,
            total_size_freed=total_size,
            dry_run=dry_run
        )
    
    def log_operation(self, operation: CleanupOperation):
        """Log cleanup operation."""
        self.logger.info(f"{operation.operation_type}: {operation.target} - {operation.reason}")
    
    def export_json(self, result: CleanupResult, output_path: Path):
        """Export results to JSON."""
        data = {
            'operations': [
                {
                    'operation_type': op.operation_type,
                    'target': str(op.target),
                    'reason': op.reason,
                    'size_bytes': op.size_bytes
                }
                for op in result.operations
            ],
            'total_size_freed': result.total_size_freed,
            'dry_run': result.dry_run
        }
        
        output_path.write_text(json.dumps(data, indent=2))
