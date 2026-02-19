"""Unit tests for AutoCleanupManager."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from scripts.maintenance.core.auto_cleanup import AutoCleanupManager, CleanupResult
from scripts.maintenance.core.config import CleanupConfig


@pytest.fixture
def config():
    """Create test configuration."""
    return CleanupConfig()


@pytest.fixture
def cleanup_manager(config):
    """Create AutoCleanupManager instance."""
    return AutoCleanupManager(config)


@pytest.fixture
def test_structure(tmp_path):
    """Create test directory structure."""
    # Create __pycache__ directory
    pycache = tmp_path / '__pycache__'
    pycache.mkdir()
    (pycache / 'test.pyc').write_text('compiled')
    
    # Create old log file
    old_log = tmp_path / 'old.log'
    old_log.write_text('old log')
    # Set modification time to 40 days ago
    old_time = (datetime.now() - timedelta(days=40)).timestamp()
    import os
    os.utime(old_log, (old_time, old_time))
    
    # Create recent log file
    recent_log = tmp_path / 'recent.log'
    recent_log.write_text('recent log')
    
    # Create empty __init__.py in empty directory
    empty_dir = tmp_path / 'empty_module'
    empty_dir.mkdir()
    (empty_dir / '__init__.py').write_text('')
    
    # Create temp files
    (tmp_path / 'test.tmp').write_text('temp')
    (tmp_path / 'test.bak').write_text('backup')
    
    return tmp_path


def test_find_pycache_dirs(cleanup_manager, test_structure):
    """Test finding __pycache__ directories."""
    pycache_dirs = cleanup_manager.find_pycache_dirs(test_structure)
    assert len(pycache_dirs) == 1
    assert pycache_dirs[0].name == '__pycache__'


def test_find_old_logs(cleanup_manager, test_structure):
    """Test finding old log files."""
    old_logs = cleanup_manager.find_old_logs(test_structure)
    assert len(old_logs) >= 1
    assert any('old.log' in str(log) for log in old_logs)


def test_find_empty_inits(cleanup_manager, test_structure):
    """Test finding empty __init__.py files."""
    empty_inits = cleanup_manager.find_empty_inits(test_structure)
    assert len(empty_inits) >= 1


def test_find_temp_files(cleanup_manager, test_structure):
    """Test finding temporary files."""
    temp_files = cleanup_manager.find_temp_files(test_structure)
    assert len(temp_files) >= 2
    assert any('.tmp' in str(f) for f in temp_files)
    assert any('.bak' in str(f) for f in temp_files)


def test_execute_cleanup_dry_run(cleanup_manager, test_structure):
    """Test cleanup execution in dry-run mode."""
    result = cleanup_manager.execute_cleanup(test_structure, dry_run=True)
    
    assert result.dry_run is True
    assert len(result.operations) > 0
    assert result.total_size_freed >= 0
    
    # Verify files still exist (dry-run)
    assert (test_structure / '__pycache__').exists()
    assert (test_structure / 'test.tmp').exists()


def test_execute_cleanup_actual(cleanup_manager, test_structure):
    """Test actual cleanup execution."""
    result = cleanup_manager.execute_cleanup(test_structure, dry_run=False)
    
    assert result.dry_run is False
    assert len(result.operations) > 0
    
    # Verify files are deleted
    assert not (test_structure / '__pycache__').exists()
    assert not (test_structure / 'test.tmp').exists()
    assert not (test_structure / 'test.bak').exists()


def test_export_json(cleanup_manager, tmp_path):
    """Test JSON export."""
    result = CleanupResult(operations=[], total_size_freed=0, dry_run=True)
    output_path = tmp_path / 'output.json'
    cleanup_manager.export_json(result, output_path)
    
    assert output_path.exists()
    import json
    data = json.loads(output_path.read_text())
    assert 'operations' in data
    assert 'total_size_freed' in data
    assert 'dry_run' in data
