"""Tests for auto_cleanup.py CLI script."""

import subprocess
import sys
from pathlib import Path
import json
import tempfile


def test_auto_cleanup_help():
    """Test that auto_cleanup.py --help works."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/auto_cleanup.py', '--help'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'Automated cleanup' in result.stdout
    assert '--execute' in result.stdout
    assert '--json' in result.stdout


def test_auto_cleanup_dry_run():
    """Test that auto_cleanup.py runs in dry-run mode by default."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/auto_cleanup.py', '--root', 'scripts/'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'DRY-RUN MODE' in result.stdout
    assert 'CLEANUP RESULTS' in result.stdout
    assert 'No files were deleted' in result.stdout


def test_auto_cleanup_json_export():
    """Test that auto_cleanup.py can export to JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json_path = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, 'scripts/maintenance/auto_cleanup.py', 
             '--root', 'scripts/', '--json', json_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert Path(json_path).exists()
        
        # Verify JSON structure
        with open(json_path) as f:
            data = json.load(f)
        
        assert 'operations' in data
        assert 'total_size_freed' in data
        assert 'dry_run' in data
        assert data['dry_run'] is True
        assert isinstance(data['operations'], list)
        
        # Verify operation structure if any operations found
        if data['operations']:
            op = data['operations'][0]
            assert 'operation_type' in op
            assert 'target' in op
            assert 'reason' in op
            assert 'size_bytes' in op
    
    finally:
        Path(json_path).unlink(missing_ok=True)


def test_auto_cleanup_no_git_check():
    """Test that auto_cleanup.py can skip git checks."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/auto_cleanup.py', 
         '--root', 'scripts/', '--no-git-check'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    # Should not see git safety check messages
    assert 'git safety checks' not in result.stdout.lower()
