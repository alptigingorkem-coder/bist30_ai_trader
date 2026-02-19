"""Unit tests for the FileSizeAnalyzer class."""

import tempfile
import json
from pathlib import Path
import pytest

from scripts.maintenance.core.size_analyzer import FileSizeAnalyzer, FileSizeResult
from scripts.maintenance.core.scanner import FileScanner, FileInfo
from scripts.maintenance.core.config import CleanupConfig


@pytest.fixture
def config():
    """Create a CleanupConfig instance for testing."""
    return CleanupConfig()


@pytest.fixture
def scanner(config):
    """Create a FileScanner instance for testing."""
    return FileScanner(config)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def create_test_file(path: Path, num_lines: int):
    """Helper to create a test file with specified number of code lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create content with the specified number of code lines
    lines = []
    lines.append("# Test file\n")  # Comment
    lines.append("\n")  # Blank
    
    for i in range(num_lines):
        if i % 10 == 0:
            lines.append(f"def func_{i}():\n")
        else:
            lines.append(f"    x = {i}\n")
    
    path.write_text("".join(lines), encoding='utf-8')


class TestFileSizeAnalyzer:
    """Tests for the FileSizeAnalyzer class."""
    
    def test_analyzer_initialization(self, config, scanner):
        """Test that FileSizeAnalyzer can be initialized."""
        analyzer = FileSizeAnalyzer(config, scanner)
        assert analyzer.config == config
        assert analyzer.scanner == scanner
    
    def test_analyze_sizes_empty_directory(self, config, scanner, temp_dir):
        """Test analyzing an empty directory."""
        analyzer = FileSizeAnalyzer(config, scanner)
        result = analyzer.analyze_sizes(temp_dir)
        
        assert result.small_files == []
        assert result.large_files == []
        assert result.average_size == 0.0
        assert result.median_size == 0.0
        assert result.size_distribution == {}
    
    def test_classify_small_files(self, config, scanner, temp_dir):
        """Test that files under 100 lines are classified as small."""
        # Create files with different sizes
        small_file1 = temp_dir / "small1.py"
        small_file2 = temp_dir / "small2.py"
        
        create_test_file(small_file1, 50)  # 50 code lines
        create_test_file(small_file2, 99)  # 99 code lines (boundary)
        
        analyzer = FileSizeAnalyzer(config, scanner)
        result = analyzer.analyze_sizes(temp_dir)
        
        assert len(result.small_files) == 2
        paths = [f.path for f in result.small_files]
        assert small_file1 in paths
        assert small_file2 in paths
    
    def test_classify_large_files(self, config, scanner, temp_dir):
        """Test that files over 500 lines are classified as large."""
        # Create files with different sizes
        large_file1 = temp_dir / "large1.py"
        large_file2 = temp_dir / "large2.py"
        
        create_test_file(large_file1, 501)  # 501 code lines (boundary)
        create_test_file(large_file2, 1000)  # 1000 code lines
        
        analyzer = FileSizeAnalyzer(config, scanner)
        result = analyzer.analyze_sizes(temp_dir)
        
        assert len(result.large_files) == 2
        paths = [f.path for f in result.large_files]
        assert large_file1 in paths
        assert large_file2 in paths
    
    def test_boundary_cases(self, config, scanner, temp_dir):
        """Test boundary cases for file classification."""
        # Create files at exact boundaries
        file_99 = temp_dir / "file_99.py"
        file_100 = temp_dir / "file_100.py"
        file_500 = temp_dir / "file_500.py"
        file_501 = temp_dir / "file_501.py"
        
        create_test_file(file_99, 99)   # Small (< 100)
        create_test_file(file_100, 100) # Medium (>= 100, <= 500)
        create_test_file(file_500, 500) # Medium (>= 100, <= 500)
        create_test_file(file_501, 501) # Large (> 500)
        
        analyzer = FileSizeAnalyzer(config, scanner)
        result = analyzer.analyze_sizes(temp_dir)
        
        # Check small files
        small_paths = [f.path for f in result.small_files]
        assert file_99 in small_paths
        assert file_100 not in small_paths
        
        # Check large files
        large_paths = [f.path for f in result.large_files]
        assert file_501 in large_paths
        assert file_500 not in large_paths
    
    def test_average_calculation(self, config, scanner, temp_dir):
        """Test that average file size is calculated correctly."""
        # Create files with known sizes
        file1 = temp_dir / "file1.py"
        file2 = temp_dir / "file2.py"
        file3 = temp_dir / "file3.py"
        
        create_test_file(file1, 100)
        create_test_file(file2, 200)
        create_test_file(file3, 300)
        
        analyzer = FileSizeAnalyzer(config, scanner)
        result = analyzer.analyze_sizes(temp_dir)
        
        # Average should be (100 + 200 + 300) / 3 = 200
        expected_avg = 200.0
        assert abs(result.average_size - expected_avg) < 1.0
    
    def test_median_calculation(self, config, scanner, temp_dir):
        """Test that median file size is calculated correctly."""
        # Create files with known sizes
        file1 = temp_dir / "file1.py"
        file2 = temp_dir / "file2.py"
        file3 = temp_dir / "file3.py"
        file4 = temp_dir / "file4.py"
        file5 = temp_dir / "file5.py"
        
        create_test_file(file1, 100)
        create_test_file(file2, 200)
        create_test_file(file3, 300)
        create_test_file(file4, 400)
        create_test_file(file5, 500)
        
        analyzer = FileSizeAnalyzer(config, scanner)
        result = analyzer.analyze_sizes(temp_dir)
        
        # Median should be 300 (middle value)
        expected_median = 300.0
        assert abs(result.median_size - expected_median) < 1.0
    
    def test_size_distribution(self, config, scanner, temp_dir):
        """Test that size distribution is calculated correctly."""
        # Create files in different size ranges
        create_test_file(temp_dir / "file_25.py", 25)    # 0-50
        create_test_file(temp_dir / "file_75.py", 75)    # 51-100
        create_test_file(temp_dir / "file_150.py", 150)  # 101-200
        create_test_file(temp_dir / "file_350.py", 350)  # 201-500
        create_test_file(temp_dir / "file_750.py", 750)  # 501-1000
        create_test_file(temp_dir / "file_1500.py", 1500) # 1000+
        
        analyzer = FileSizeAnalyzer(config, scanner)
        result = analyzer.analyze_sizes(temp_dir)
        
        assert result.size_distribution['0-50'] == 1
        assert result.size_distribution['51-100'] == 1
        assert result.size_distribution['101-200'] == 1
        assert result.size_distribution['201-500'] == 1
        assert result.size_distribution['501-1000'] == 1
        assert result.size_distribution['1000+'] == 1
    
    def test_group_by_directory(self, config, scanner, temp_dir):
        """Test grouping files by directory."""
        # Create files in different directories
        dir1 = temp_dir / "dir1"
        dir2 = temp_dir / "dir2"
        
        file1 = dir1 / "file1.py"
        file2 = dir1 / "file2.py"
        file3 = dir2 / "file3.py"
        
        create_test_file(file1, 50)
        create_test_file(file2, 60)
        create_test_file(file3, 70)
        
        analyzer = FileSizeAnalyzer(config, scanner)
        result = analyzer.analyze_sizes(temp_dir)
        
        grouped = analyzer.group_by_directory(result.small_files)
        
        assert str(dir1) in grouped
        assert str(dir2) in grouped
        assert len(grouped[str(dir1)]) == 2
        assert len(grouped[str(dir2)]) == 1
    
    def test_suggest_split_points_large_file(self, config, scanner, temp_dir):
        """Test suggesting split points for a large file."""
        large_file = temp_dir / "large.py"
        
        # Create a file with multiple classes and enough lines to trigger splits
        classes = []
        for i in range(10):
            classes.append(f"""
class Class{i}:
    def method{i}(self):
        pass
    
    def another_method{i}(self):
        pass
""")
        
        content = "# Large file\n\n" + "\n".join(classes)
        # Add more lines to make it large enough (> 700 lines to trigger 2 splits)
        content += "\n" + "\n".join([f"x_{i} = {i}" for i in range(700)])
        
        large_file.write_text(content, encoding='utf-8')
        
        analyzer = FileSizeAnalyzer(config, scanner)
        file_info = scanner.scan_file(large_file)
        
        split_points = analyzer.suggest_split_points(file_info)
        
        # Should suggest at least one split point for a file this large
        assert len(split_points) > 0
        # Split points should be line numbers
        assert all(isinstance(sp, int) for sp in split_points)
    
    def test_suggest_split_points_no_definitions(self, config, scanner, temp_dir):
        """Test split point suggestion for file with no class/function definitions."""
        file = temp_dir / "no_defs.py"
        
        # Create a file with only variable assignments
        content = "\n".join([f"x_{i} = {i}" for i in range(600)])
        file.write_text(content, encoding='utf-8')
        
        analyzer = FileSizeAnalyzer(config, scanner)
        file_info = scanner.scan_file(file)
        
        split_points = analyzer.suggest_split_points(file_info)
        
        # Should return empty list if no logical split points
        assert split_points == []
    
    def test_export_json(self, config, scanner, temp_dir):
        """Test exporting results to JSON."""
        # Create test files
        small_file = temp_dir / "small.py"
        large_file = temp_dir / "large.py"
        
        create_test_file(small_file, 50)
        create_test_file(large_file, 600)
        
        analyzer = FileSizeAnalyzer(config, scanner)
        result = analyzer.analyze_sizes(temp_dir)
        
        # Export to JSON
        output_file = temp_dir / "output.json"
        analyzer.export_json(result, output_file)
        
        # Verify JSON file was created
        assert output_file.exists()
        
        # Load and verify JSON content
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'small_files' in data
        assert 'large_files' in data
        assert 'statistics' in data
        assert 'size_distribution' in data
        
        assert len(data['small_files']) == 1
        assert len(data['large_files']) == 1
        
        assert 'average_size' in data['statistics']
        assert 'median_size' in data['statistics']
        assert 'total_small_files' in data['statistics']
        assert 'total_large_files' in data['statistics']
    
    def test_export_json_with_split_points(self, config, scanner, temp_dir):
        """Test that JSON export includes split point suggestions for large files."""
        large_file = temp_dir / "large.py"
        
        # Create a large file with classes
        content = """
class Class1:
    pass

class Class2:
    pass
"""
        content += "\n".join([f"x = {i}" for i in range(600)])
        large_file.write_text(content, encoding='utf-8')
        
        analyzer = FileSizeAnalyzer(config, scanner)
        result = analyzer.analyze_sizes(temp_dir)
        
        # Export to JSON
        output_file = temp_dir / "output.json"
        analyzer.export_json(result, output_file)
        
        # Load and verify JSON content
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Large files should have suggested_split_points
        assert len(data['large_files']) == 1
        assert 'suggested_split_points' in data['large_files'][0]
    
    def test_mixed_file_sizes(self, config, scanner, temp_dir):
        """Test analyzing a directory with mixed file sizes."""
        # Create files of various sizes
        create_test_file(temp_dir / "tiny.py", 10)      # Small
        create_test_file(temp_dir / "small.py", 80)     # Small
        create_test_file(temp_dir / "medium.py", 250)   # Medium (neither small nor large)
        create_test_file(temp_dir / "large.py", 600)    # Large
        create_test_file(temp_dir / "huge.py", 1200)    # Large
        
        analyzer = FileSizeAnalyzer(config, scanner)
        result = analyzer.analyze_sizes(temp_dir)
        
        # Should have 2 small files
        assert len(result.small_files) == 2
        
        # Should have 2 large files
        assert len(result.large_files) == 2
        
        # Average should be calculated across all 5 files
        expected_avg = (10 + 80 + 250 + 600 + 1200) / 5
        assert abs(result.average_size - expected_avg) < 1.0
