"""Tests for suggest_merges.py CLI script."""

import subprocess
import sys
import json
from pathlib import Path
import pytest


def test_suggest_merges_help():
    """Test that help message is displayed."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/suggest_merges.py', '--help'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'Suggest merge opportunities' in result.stdout
    assert '--root' in result.stdout
    assert '--json' in result.stdout
    assert '--threshold' in result.stdout


def test_suggest_merges_basic():
    """Test basic merge suggestion functionality."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/suggest_merges.py', '--root', 'scripts/analysis/'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'MERGE SUGGESTION RESULTS' in result.stdout
    assert 'Small file threshold:' in result.stdout
    assert 'Similarity threshold:' in result.stdout


def test_suggest_merges_json_export(tmp_path):
    """Test JSON export functionality."""
    json_file = tmp_path / 'merge_suggestions.json'
    
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/suggest_merges.py', 
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
    
    assert 'suggestions' in data
    assert 'total_file_reduction' in data
    assert isinstance(data['suggestions'], list)
    assert isinstance(data['total_file_reduction'], int)
    
    # If there are suggestions, verify their structure
    if data['suggestions']:
        suggestion = data['suggestions'][0]
        assert 'source_files' in suggestion
        assert 'target_file' in suggestion
        assert 'estimated_size' in suggestion
        assert 'functional_similarity' in suggestion
        assert 'required_import_updates' in suggestion
        assert isinstance(suggestion['source_files'], list)
        assert len(suggestion['source_files']) >= 2


def test_suggest_merges_custom_threshold():
    """Test with custom similarity threshold."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/suggest_merges.py', 
         '--root', 'scripts/analysis/',
         '--threshold', '0.7'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'Similarity threshold: 70.00%' in result.stdout


def test_suggest_merges_invalid_threshold():
    """Test error handling for invalid threshold."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/suggest_merges.py', 
         '--root', 'scripts/analysis/',
         '--threshold', '1.5'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 1
    assert 'Error: Threshold must be between 0.0 and 1.0' in result.stderr


def test_suggest_merges_with_config(tmp_path):
    """Test with custom configuration file."""
    # Create a test config
    config_file = tmp_path / 'test_config.yaml'
    config_file.write_text("""
thresholds:
  small_file_lines: 80
  large_file_lines: 500

exclusions:
  directories:
    - .venv
    - __pycache__
""")
    
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/suggest_merges.py', 
         '--root', 'scripts/analysis/',
         '--config', str(config_file)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'MERGE SUGGESTION RESULTS' in result.stdout
    assert 'Small file threshold: 80 lines' in result.stdout


def test_suggest_merges_no_small_files(tmp_path):
    """Test with directory containing no small files."""
    # Create a directory with only large files
    test_dir = tmp_path / 'test_scripts'
    test_dir.mkdir()
    
    # Create a large file with actual code (over 100 lines of code)
    large_file = test_dir / 'large_script.py'
    code_lines = ['def func_{}():'.format(i) + '\n    return {}'.format(i) for i in range(300)]
    large_file.write_text('\n'.join(code_lines))
    
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/suggest_merges.py', 
         '--root', str(test_dir)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'No small files found' in result.stdout


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
