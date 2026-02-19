"""Tests for generate_cleanup_report.py CLI script."""

import subprocess
import sys
from pathlib import Path
import json
import tempfile


def test_generate_cleanup_report_help():
    """Test that help option works."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/generate_cleanup_report.py', '--help'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'Generate comprehensive cleanup report' in result.stdout
    assert '--markdown' in result.stdout
    assert '--json' in result.stdout
    assert '--lang' in result.stdout


def test_generate_cleanup_report_basic():
    """Test basic report generation."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/generate_cleanup_report.py', 
         '--root', 'scripts/maintenance/core'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'CLEANUP REPORT SUMMARY' in result.stdout
    assert 'Total Files:' in result.stdout
    assert 'ESTIMATED IMPROVEMENTS' in result.stdout
    assert 'PRIORITIZED ACTIONS' in result.stdout


def test_generate_cleanup_report_json_export():
    """Test JSON export functionality."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json_path = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, 'scripts/maintenance/generate_cleanup_report.py',
             '--root', 'scripts/maintenance/core',
             '--json', json_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert Path(json_path).exists()
        
        # Verify JSON structure
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        assert 'timestamp' in data
        assert 'summary' in data
        assert 'estimated_improvements' in data
        assert 'prioritized_actions' in data
        
        # Verify summary fields
        assert 'total_files' in data['summary']
        assert 'average_file_size' in data['summary']
        assert 'unused_files_count' in data['summary']
        
    finally:
        Path(json_path).unlink(missing_ok=True)


def test_generate_cleanup_report_markdown_export():
    """Test Markdown export functionality."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        md_path = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, 'scripts/maintenance/generate_cleanup_report.py',
             '--root', 'scripts/maintenance/core',
             '--markdown', md_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert Path(md_path).exists()
        
        # Verify Markdown content
        content = Path(md_path).read_text()
        assert '# Cleanup Report' in content
        assert '## Summary' in content
        assert '## Estimated Improvements' in content
        assert '## Prioritized Actions' in content
        
    finally:
        Path(md_path).unlink(missing_ok=True)


def test_generate_cleanup_report_turkish():
    """Test Turkish language option."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        md_path = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, 'scripts/maintenance/generate_cleanup_report.py',
             '--root', 'scripts/maintenance/core',
             '--lang', 'tr',
             '--markdown', md_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert Path(md_path).exists()
        
        # Verify Turkish translations
        content = Path(md_path).read_text()
        assert 'Temizlik Raporu' in content
        assert 'Özet' in content
        assert 'Tahmini İyileştirmeler' in content
        
    finally:
        Path(md_path).unlink(missing_ok=True)


def test_generate_cleanup_report_verbose():
    """Test verbose output option."""
    result = subprocess.run(
        [sys.executable, 'scripts/maintenance/generate_cleanup_report.py',
         '--root', 'scripts/maintenance/core',
         '--verbose'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'DETAILED FINDINGS' in result.stdout


def test_generate_cleanup_report_both_formats():
    """Test exporting to both Markdown and JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        md_path = f.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json_path = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, 'scripts/maintenance/generate_cleanup_report.py',
             '--root', 'scripts/maintenance/core',
             '--markdown', md_path,
             '--json', json_path],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert Path(md_path).exists()
        assert Path(json_path).exists()
        assert 'Markdown report exported' in result.stdout
        assert 'JSON report exported' in result.stdout
        
    finally:
        Path(md_path).unlink(missing_ok=True)
        Path(json_path).unlink(missing_ok=True)
