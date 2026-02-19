"""Tests for organize_scripts.py CLI script."""

import subprocess
import sys
import json
from pathlib import Path
import pytest


def test_organize_scripts_help():
    """Test that help message is displayed."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/organize_scripts.py', '--help'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'Organize scripts by usage pattern' in result.stdout
    assert '--root' in result.stdout
    assert '--json' in result.stdout
    assert '--execute' in result.stdout


def test_organize_scripts_dry_run():
    """Test dry-run mode (default)."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/organize_scripts.py', '--root', 'scripts/analysis/'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'SCRIPT ORGANIZATION ANALYSIS' in result.stdout
    assert 'Mode: DRY-RUN' in result.stdout
    assert 'PRODUCTION' in result.stdout
    assert 'ANALYSIS' in result.stdout
    assert 'MAINTENANCE' in result.stdout


def test_organize_scripts_json_export(tmp_path):
    """Test JSON export functionality."""
    json_file = tmp_path / 'organization.json'
    
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/organize_scripts.py', 
         '--root', 'scripts/analysis/', 
         '--json', str(json_file)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert json_file.exists()
    
    # Verify JSON structure
    with open(json_file) as f:
        data = json.load(f)
    
    assert 'production' in data
    assert 'analysis' in data
    assert 'maintenance' in data
    assert 'integration_tests' in data
    assert 'reorganization_plan' in data
    assert 'broken_imports' in data
    
    # Verify structure of categories
    for category in ['production', 'analysis', 'maintenance', 'integration_tests']:
        assert 'name' in data[category]
        assert 'scripts' in data[category]
        assert 'target_directory' in data[category]
        assert isinstance(data[category]['scripts'], list)


def test_organize_scripts_invalid_directory():
    """Test error handling for non-existent directory."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/organize_scripts.py', 
         '--root', '/nonexistent/path/'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 1
    assert 'Error: Directory not found' in result.stderr


def test_organize_scripts_with_config(tmp_path):
    """Test with custom configuration file."""
    # Create a test config
    config_file = tmp_path / 'test_config.yaml'
    config_file.write_text("""
thresholds:
  small_file_lines: 100
  large_file_lines: 500

script_categories:
  production:
    - train_models.py
    - run_backtest.py
""")
    
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/organize_scripts.py', 
         '--root', 'scripts/analysis/',
         '--config', str(config_file)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'SCRIPT ORGANIZATION ANALYSIS' in result.stdout


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
