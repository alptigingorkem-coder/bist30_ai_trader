"""Unit tests for UnusedFileDetector class.

Tests the unused file detection functionality including import graph building,
special file detection, and unused file identification.
"""

import pytest
from pathlib import Path
from datetime import datetime
from scripts.maintenance.core.config import CleanupConfig
from scripts.maintenance.core.scanner import FileScanner, FileInfo
from scripts.maintenance.core.unused_detector import UnusedFileDetector, UnusedFileResult


class TestUnusedFileDetector:
    """Test suite for UnusedFileDetector class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return CleanupConfig()
    
    @pytest.fixture
    def scanner(self, config):
        """Create a test file scanner."""
        return FileScanner(config)
    
    @pytest.fixture
    def detector(self, config, scanner):
        """Create a test unused file detector."""
        return UnusedFileDetector(config, scanner)
    
    def test_is_special_file_init(self, detector):
        """Test that __init__.py is recognized as a special file."""
        path = Path("scripts/analysis/__init__.py")
        assert detector.is_special_file(path) is True
    
    def test_is_special_file_main(self, detector):
        """Test that __main__.py is recognized as a special file."""
        path = Path("scripts/__main__.py")
        assert detector.is_special_file(path) is True
    
    def test_is_special_file_setup(self, detector):
        """Test that setup.py is recognized as a special file."""
        path = Path("setup.py")
        assert detector.is_special_file(path) is True
    
    def test_is_special_file_top_level_script(self, detector):
        """Test that top-level scripts in scripts/ are recognized as special."""
        path = Path("scripts/train_model.py")
        assert detector.is_special_file(path) is True
    
    def test_is_not_special_file_subdirectory_script(self, detector):
        """Test that scripts in subdirectories are not special."""
        path = Path("scripts/analysis/feature_importance.py")
        assert detector.is_special_file(path) is False
    
    def test_is_not_special_file_regular(self, detector):
        """Test that regular files are not special."""
        path = Path("scripts/analysis/helper.py")
        assert detector.is_special_file(path) is False
    
    def test_build_import_graph_empty(self, detector):
        """Test building import graph with no files."""
        files = []
        graph = detector.build_import_graph(files)
        assert graph == {}
    
    def test_build_import_graph_no_imports(self, detector):
        """Test building import graph with files that have no imports."""
        files = [
            FileInfo(
                path=Path("test1.py"),
                lines=10,
                blank_lines=2,
                comment_lines=1,
                code_lines=7,
                imports=[],
                functions=["func1"],
                classes=[],
                last_modified=datetime.now()
            )
        ]
        graph = detector.build_import_graph(files)
        assert "test1.py" in graph
        assert graph["test1.py"] == []
    
    def test_build_import_graph_with_imports(self, detector):
        """Test building import graph with files that import each other."""
        file1 = FileInfo(
            path=Path("module1.py"),
            lines=10,
            blank_lines=2,
            comment_lines=1,
            code_lines=7,
            imports=["module2"],
            functions=["func1"],
            classes=[],
            last_modified=datetime.now()
        )
        file2 = FileInfo(
            path=Path("module2.py"),
            lines=10,
            blank_lines=2,
            comment_lines=1,
            code_lines=7,
            imports=[],
            functions=["func2"],
            classes=[],
            last_modified=datetime.now()
        )
        
        files = [file1, file2]
        graph = detector.build_import_graph(files)
        
        assert "module1.py" in graph
        assert "module2.py" in graph
        # module1 should import module2
        assert "module2.py" in graph["module1.py"]
        # module2 should have no imports
        assert graph["module2.py"] == []
    
    def test_export_json(self, detector, tmp_path):
        """Test exporting results to JSON."""
        unused_file = FileInfo(
            path=Path("unused.py"),
            lines=10,
            blank_lines=2,
            comment_lines=1,
            code_lines=7,
            imports=[],
            functions=["func1"],
            classes=["Class1"],
            last_modified=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        result = UnusedFileResult(
            unused_files=[unused_file],
            import_graph={"unused.py": [], "used.py": ["unused.py"]},
            special_files=["__init__.py"]
        )
        
        output_path = tmp_path / "output.json"
        detector.export_json(result, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify content
        import json
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['unused_count'] == 1
        assert data['total_files'] == 2
        assert len(data['unused_files']) == 1
        assert data['unused_files'][0]['path'] == 'unused.py'
        assert data['unused_files'][0]['code_lines'] == 7
        assert data['special_files'] == ["__init__.py"]
    
    def test_module_mapping_basic(self, detector):
        """Test building module name to file path mapping."""
        files = [
            FileInfo(
                path=Path("scripts/analysis/feature_importance.py"),
                lines=10,
                blank_lines=2,
                comment_lines=1,
                code_lines=7,
                imports=[],
                functions=[],
                classes=[],
                last_modified=datetime.now()
            )
        ]
        
        mapping = detector._build_module_mapping(files)
        
        # Should have multiple entries for different module name variations
        assert Path("scripts/analysis/feature_importance.py") in mapping.values()
        # Check that at least one key exists
        assert len(mapping) > 0
    
    def test_resolve_import_direct(self, detector):
        """Test resolving a direct import."""
        module_to_file = {
            "module1": Path("module1.py"),
            "module2": Path("module2.py")
        }
        
        resolved = detector._resolve_import("module1", Path("test.py"), module_to_file)
        assert resolved == Path("module1.py")
    
    def test_resolve_import_not_found(self, detector):
        """Test resolving an import that doesn't exist in the project."""
        module_to_file = {
            "module1": Path("module1.py")
        }
        
        resolved = detector._resolve_import("external_module", Path("test.py"), module_to_file)
        assert resolved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
