"""Unit tests for the FileScanner and FileInfo classes."""

import tempfile
from pathlib import Path
from datetime import datetime
import pytest

from scripts.maintenance.core.scanner import FileScanner, FileInfo
from scripts.maintenance.core.config import CleanupConfig


@pytest.fixture
def config():
    """Create a CleanupConfig instance for testing."""
    return CleanupConfig()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def create_test_file(path: Path, content: str):
    """Helper to create a test file with content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


class TestFileInfo:
    """Tests for the FileInfo dataclass."""
    
    def test_fileinfo_creation(self):
        """Test that FileInfo can be created with all required fields."""
        file_info = FileInfo(
            path=Path("test.py"),
            lines=10,
            blank_lines=2,
            comment_lines=3,
            code_lines=5,
            imports=["os", "sys"],
            functions=["foo", "bar"],
            classes=["MyClass"],
            last_modified=datetime.now()
        )
        
        assert file_info.path == Path("test.py")
        assert file_info.lines == 10
        assert file_info.blank_lines == 2
        assert file_info.comment_lines == 3
        assert file_info.code_lines == 5
        assert file_info.imports == ["os", "sys"]
        assert file_info.functions == ["foo", "bar"]
        assert file_info.classes == ["MyClass"]
        assert isinstance(file_info.last_modified, datetime)


class TestFileScanner:
    """Tests for the FileScanner class."""
    
    def test_scanner_initialization(self, config):
        """Test that FileScanner can be initialized with a config."""
        scanner = FileScanner(config)
        assert scanner.config == config
    
    def test_count_lines_simple(self, config, temp_dir):
        """Test line counting for a simple file."""
        test_file = temp_dir / "test.py"
        content = """# This is a comment
import os

def foo():
    pass

"""
        create_test_file(test_file, content)
        
        scanner = FileScanner(config)
        total, blank, comment = scanner.count_lines(test_file)
        
        assert total == 6
        assert blank == 2
        assert comment == 1
    
    def test_count_lines_with_docstring(self, config, temp_dir):
        """Test line counting with docstrings."""
        test_file = temp_dir / "test.py"
        content = '''"""
This is a module docstring.
It spans multiple lines.
"""

def foo():
    """Function docstring."""
    pass
'''
        create_test_file(test_file, content)
        
        scanner = FileScanner(config)
        total, blank, comment = scanner.count_lines(test_file)
        
        # Docstrings should be counted as comments
        assert total == 8
        assert blank == 1
        assert comment == 5  # 4 lines of module docstring + 1 line function docstring
    
    def test_count_lines_empty_file(self, config, temp_dir):
        """Test line counting for an empty file."""
        test_file = temp_dir / "empty.py"
        create_test_file(test_file, "")
        
        scanner = FileScanner(config)
        total, blank, comment = scanner.count_lines(test_file)
        
        assert total == 0
        assert blank == 0
        assert comment == 0
    
    def test_extract_imports(self, config, temp_dir):
        """Test import extraction."""
        test_file = temp_dir / "test.py"
        content = """import os
import sys
from pathlib import Path
from typing import List, Dict
"""
        create_test_file(test_file, content)
        
        scanner = FileScanner(config)
        imports = scanner.extract_imports(test_file)
        
        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports
        assert "typing" in imports
    
    def test_extract_definitions(self, config, temp_dir):
        """Test function and class extraction."""
        test_file = temp_dir / "test.py"
        content = """
def foo():
    pass

async def bar():
    pass

class MyClass:
    pass

class AnotherClass:
    def method(self):
        pass
"""
        create_test_file(test_file, content)
        
        scanner = FileScanner(config)
        functions, classes = scanner.extract_definitions(test_file)
        
        assert "foo" in functions
        assert "bar" in functions
        assert "MyClass" in classes
        assert "AnotherClass" in classes
        # Method should not be in top-level functions
        assert "method" not in functions
    
    def test_scan_file(self, config, temp_dir):
        """Test scanning a complete file."""
        test_file = temp_dir / "test.py"
        content = """# Test file
import os

def foo():
    pass

class Bar:
    pass
"""
        create_test_file(test_file, content)
        
        scanner = FileScanner(config)
        file_info = scanner.scan_file(test_file)
        
        assert file_info.path == test_file
        assert file_info.lines == 8
        assert file_info.code_lines > 0
        assert "os" in file_info.imports
        assert "foo" in file_info.functions
        assert "Bar" in file_info.classes
        assert isinstance(file_info.last_modified, datetime)
    
    def test_scan_file_not_found(self, config):
        """Test scanning a non-existent file raises FileNotFoundError."""
        scanner = FileScanner(config)
        
        with pytest.raises(FileNotFoundError):
            scanner.scan_file(Path("nonexistent.py"))
    
    def test_scan_directory(self, config, temp_dir):
        """Test scanning a directory."""
        # Create multiple test files
        file1 = temp_dir / "file1.py"
        file2 = temp_dir / "subdir" / "file2.py"
        file3 = temp_dir / "file3.py"
        
        create_test_file(file1, "import os\n")
        create_test_file(file2, "import sys\n")
        create_test_file(file3, "def foo(): pass\n")
        
        scanner = FileScanner(config)
        file_infos = scanner.scan_directory(temp_dir)
        
        assert len(file_infos) == 3
        paths = [fi.path for fi in file_infos]
        assert file1 in paths
        assert file2 in paths
        assert file3 in paths
    
    def test_scan_directory_with_exclusions(self, config, temp_dir):
        """Test that excluded directories are skipped."""
        # Create files in excluded directory
        excluded_dir = temp_dir / "__pycache__"
        excluded_file = excluded_dir / "test.py"
        normal_file = temp_dir / "normal.py"
        
        create_test_file(excluded_file, "import os\n")
        create_test_file(normal_file, "import sys\n")
        
        scanner = FileScanner(config)
        file_infos = scanner.scan_directory(temp_dir)
        
        # Should only find the normal file
        assert len(file_infos) == 1
        assert file_infos[0].path == normal_file
    
    def test_scan_directory_with_pattern_exclusions(self, config, temp_dir):
        """Test that files matching excluded patterns are skipped."""
        # Create test files
        test_file = temp_dir / "test_something.py"
        normal_file = temp_dir / "normal.py"
        
        create_test_file(test_file, "import os\n")
        create_test_file(normal_file, "import sys\n")
        
        scanner = FileScanner(config)
        file_infos = scanner.scan_directory(temp_dir)
        
        # test_*.py should be excluded by default
        paths = [fi.path for fi in file_infos]
        assert test_file not in paths
        assert normal_file in paths
    
    def test_scan_file_with_syntax_error(self, config, temp_dir):
        """Test that files with syntax errors are handled gracefully."""
        test_file = temp_dir / "bad_syntax.py"
        content = """
def foo(
    # Missing closing parenthesis
    pass
"""
        create_test_file(test_file, content)
        
        scanner = FileScanner(config)
        file_info = scanner.scan_file(test_file)
        
        # Should still count lines even if AST parsing fails
        assert file_info.lines > 0
        # But imports and definitions will be empty
        assert file_info.imports == []
        assert file_info.functions == []
        assert file_info.classes == []
    
    def test_code_lines_calculation(self, config, temp_dir):
        """Test that code_lines = total - blank - comment."""
        test_file = temp_dir / "test.py"
        content = """# Comment line

import os

def foo():
    pass
"""
        create_test_file(test_file, content)
        
        scanner = FileScanner(config)
        file_info = scanner.scan_file(test_file)
        
        # Verify the relationship
        assert file_info.code_lines == (
            file_info.lines - file_info.blank_lines - file_info.comment_lines
        )
