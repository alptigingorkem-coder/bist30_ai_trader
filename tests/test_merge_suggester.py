"""Unit tests for MergeSuggester."""

import pytest
from pathlib import Path
from dataclasses import dataclass
from scripts.maintenance.core.merge_suggester import MergeSuggester, MergeResult
from scripts.maintenance.core.config import CleanupConfig


@dataclass
class MockFileInfo:
    """Mock FileInfo for testing."""
    path: Path
    code_lines: int
    imports: list
    functions: list
    classes: list


@pytest.fixture
def config():
    """Create test configuration."""
    return CleanupConfig()


@pytest.fixture
def suggester(config):
    """Create MergeSuggester instance."""
    return MergeSuggester(config, None)


def test_functional_similarity_high(suggester):
    """Test functional similarity calculation with similar files."""
    file1 = MockFileInfo(
        path=Path('test1.py'),
        code_lines=50,
        imports=['os', 'sys', 'json'],
        functions=['func1', 'func2'],
        classes=['ClassA']
    )
    file2 = MockFileInfo(
        path=Path('test2.py'),
        code_lines=60,
        imports=['os', 'sys', 'json'],
        functions=['func3', 'func4'],
        classes=['ClassA']
    )
    
    similarity = suggester.calculate_functional_similarity([file1, file2])
    assert similarity > 0.5


def test_functional_similarity_low(suggester):
    """Test functional similarity calculation with different files."""
    file1 = MockFileInfo(
        path=Path('test1.py'),
        code_lines=50,
        imports=['os'],
        functions=['func1'],
        classes=[]
    )
    file2 = MockFileInfo(
        path=Path('test2.py'),
        code_lines=60,
        imports=['numpy', 'pandas'],
        functions=['func2'],
        classes=['ClassB']
    )
    
    similarity = suggester.calculate_functional_similarity([file1, file2])
    assert similarity < 0.5


def test_estimate_merged_size(suggester):
    """Test merged size estimation."""
    file1 = MockFileInfo(
        path=Path('test1.py'),
        code_lines=50,
        imports=['os', 'sys'],
        functions=[],
        classes=[]
    )
    file2 = MockFileInfo(
        path=Path('test2.py'),
        code_lines=60,
        imports=['os', 'json'],
        functions=[],
        classes=[]
    )
    
    estimated_size = suggester.estimate_merged_size([file1, file2])
    # Should be less than sum due to import deduplication
    assert estimated_size <= 110
    assert estimated_size > 0


def test_suggest_merges_empty(suggester):
    """Test merge suggestions with no files."""
    result = suggester.suggest_merges([])
    assert len(result.suggestions) == 0
    assert result.total_file_reduction == 0


def test_export_json(suggester, tmp_path):
    """Test JSON export."""
    result = MergeResult(suggestions=[], total_file_reduction=0)
    output_path = tmp_path / 'output.json'
    suggester.export_json(result, output_path)
    
    assert output_path.exists()
    import json
    data = json.loads(output_path.read_text())
    assert 'suggestions' in data
    assert 'total_file_reduction' in data
