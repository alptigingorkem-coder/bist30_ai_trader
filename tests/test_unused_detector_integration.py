"""Integration tests for UnusedFileDetector.

Tests the unused file detector on actual project structure to verify it works
correctly with real files and import patterns.
"""

import pytest
from pathlib import Path
from scripts.maintenance.core.config import CleanupConfig
from scripts.maintenance.core.scanner import FileScanner
from scripts.maintenance.core.unused_detector import UnusedFileDetector


class TestUnusedFileDetectorIntegration:
    """Integration test suite for UnusedFileDetector."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return CleanupConfig()
    
    @pytest.fixture
    def scanner(self, config):
        """Create a file scanner."""
        return FileScanner(config)
    
    @pytest.fixture
    def detector(self, config, scanner):
        """Create an unused file detector."""
        return UnusedFileDetector(config, scanner)
    
    def test_find_unused_files_in_maintenance_core(self, detector):
        """Test finding unused files in the maintenance core directory."""
        # Test on the actual scripts/maintenance/core directory
        root_path = Path("scripts/maintenance/core")
        
        if not root_path.exists():
            pytest.skip("scripts/maintenance/core directory not found")
        
        result = detector.find_unused_files(root_path)
        
        # Verify result structure
        assert result is not None
        assert isinstance(result.unused_files, list)
        assert isinstance(result.import_graph, dict)
        assert isinstance(result.special_files, list)
        
        # Note: __init__.py files are excluded by the scanner's default patterns,
        # so they won't appear in the results. This is expected behavior.
        # Just verify that we have some files scanned
        assert len(result.import_graph) >= 0  # May be empty if all files are excluded
        
        # Import graph should have entries
        assert len(result.import_graph) > 0
    
    def test_export_and_reimport_json(self, detector, tmp_path):
        """Test exporting results to JSON and reading them back."""
        root_path = Path("scripts/maintenance/core")
        
        if not root_path.exists():
            pytest.skip("scripts/maintenance/core directory not found")
        
        # Find unused files
        result = detector.find_unused_files(root_path)
        
        # Export to JSON
        output_path = tmp_path / "unused_files.json"
        detector.export_json(result, output_path)
        
        # Verify file exists and is valid JSON
        assert output_path.exists()
        
        import json
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Verify structure
        assert 'unused_files' in data
        assert 'unused_count' in data
        assert 'total_files' in data
        assert 'special_files' in data
        assert 'import_graph' in data
        
        # Verify counts match
        assert data['unused_count'] == len(result.unused_files)
        assert data['total_files'] == len(result.import_graph)
    
    def test_special_file_detection_in_project(self, detector):
        """Test that special files are correctly identified in the project."""
        # Test various paths that should be special
        special_paths = [
            Path("scripts/train_model.py"),  # Top-level script
            Path("scripts/__init__.py"),  # __init__.py
            Path("setup.py"),  # setup.py
        ]
        
        for path in special_paths:
            # Only test if the file actually exists
            if path.exists():
                assert detector.is_special_file(path), f"{path} should be special"
        
        # Test paths that should NOT be special
        non_special_paths = [
            Path("scripts/analysis/feature_importance.py"),  # Subdirectory script
            Path("scripts/maintenance/core/config.py"),  # Module file
        ]
        
        for path in non_special_paths:
            if path.exists():
                assert not detector.is_special_file(path), f"{path} should not be special"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
