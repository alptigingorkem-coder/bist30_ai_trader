"""Unit tests for ReportGenerator."""

import pytest
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from scripts.maintenance.core.report_generator import ReportGenerator, CleanupReport
from scripts.maintenance.core.config import CleanupConfig


@dataclass
class MockUnusedResult:
    """Mock unused files result."""
    unused_files: list


@dataclass
class MockSizeResult:
    """Mock file size result."""
    small_files: list
    large_files: list
    average_size: float


@dataclass
class MockDuplicateResult:
    """Mock duplicate result."""
    duplicate_groups: list


@dataclass
class MockScriptResult:
    """Mock script organization result."""
    production: any
    reorganization_plan: list


@dataclass
class MockCategory:
    """Mock script category."""
    scripts: list


@dataclass
class MockMergeResult:
    """Mock merge result."""
    suggestions: list
    total_file_reduction: int


@dataclass
class MockSuggestion:
    """Mock merge suggestion."""
    estimated_size: int


@pytest.fixture
def config():
    """Create test configuration."""
    return CleanupConfig()


@pytest.fixture
def generator(config):
    """Create ReportGenerator instance."""
    return ReportGenerator(config)


@pytest.fixture
def mock_data():
    """Create mock data for testing."""
    unused = MockUnusedResult(unused_files=[1, 2, 3])
    sizes = MockSizeResult(small_files=[1, 2], large_files=[1], average_size=150.0)
    duplicates = MockDuplicateResult(duplicate_groups=[1, 2])
    scripts = MockScriptResult(
        production=MockCategory(scripts=[1, 2]),
        reorganization_plan=[(1, 2)]
    )
    merges = MockMergeResult(
        suggestions=[MockSuggestion(estimated_size=200)],
        total_file_reduction=2
    )
    return unused, sizes, duplicates, scripts, merges


def test_generate_report(generator, mock_data):
    """Test report generation."""
    unused, sizes, duplicates, scripts, merges = mock_data
    
    report = generator.generate_report(unused, sizes, duplicates, scripts, merges)
    
    assert isinstance(report, CleanupReport)
    assert report.total_files > 0
    assert report.average_file_size == 150.0
    assert len(report.estimated_improvements) > 0
    assert len(report.prioritized_actions) > 0


def test_calculate_improvements(generator, mock_data):
    """Test improvement calculations."""
    unused, sizes, duplicates, scripts, merges = mock_data
    report = generator.generate_report(unused, sizes, duplicates, scripts, merges)
    
    improvements = report.estimated_improvements
    
    assert 'file_count_reduction_percent' in improvements
    assert 'avg_file_size_increase_percent' in improvements
    assert 'maintainability_improvement_score' in improvements
    assert improvements['unused_files_count'] == 3
    assert improvements['files_to_merge'] == 2


def test_prioritize_actions(generator, mock_data):
    """Test action prioritization."""
    unused, sizes, duplicates, scripts, merges = mock_data
    report = generator.generate_report(unused, sizes, duplicates, scripts, merges)
    
    actions = report.prioritized_actions
    
    assert len(actions) > 0
    # Actions should be tuples of (action_name, impact, effort)
    for action in actions:
        assert len(action) == 3
        assert isinstance(action[0], str)
        assert isinstance(action[1], int)
        assert isinstance(action[2], int)
    
    # Verify actions are sorted by impact (descending)
    impacts = [action[1] for action in actions]
    assert impacts == sorted(impacts, reverse=True)


def test_export_markdown(generator, mock_data, tmp_path):
    """Test Markdown export."""
    unused, sizes, duplicates, scripts, merges = mock_data
    report = generator.generate_report(unused, sizes, duplicates, scripts, merges)
    
    output_path = tmp_path / 'report.md'
    generator.export_markdown(report, output_path)
    
    assert output_path.exists()
    content = output_path.read_text()
    assert 'Cleanup Report' in content
    assert 'Summary' in content
    assert 'Total Files' in content


def test_export_markdown_turkish(generator, mock_data, tmp_path):
    """Test Markdown export with Turkish translation."""
    unused, sizes, duplicates, scripts, merges = mock_data
    report = generator.generate_report(unused, sizes, duplicates, scripts, merges)
    
    output_path = tmp_path / 'report_tr.md'
    generator.export_markdown(report, output_path, turkish=True)
    
    assert output_path.exists()
    content = output_path.read_text()
    assert 'Temizlik Raporu' in content
    assert 'Özet' in content


def test_export_json(generator, mock_data, tmp_path):
    """Test JSON export."""
    unused, sizes, duplicates, scripts, merges = mock_data
    report = generator.generate_report(unused, sizes, duplicates, scripts, merges)
    
    output_path = tmp_path / 'report.json'
    generator.export_json(report, output_path)
    
    assert output_path.exists()
    import json
    data = json.loads(output_path.read_text())
    assert 'timestamp' in data
    assert 'summary' in data
    assert 'estimated_improvements' in data
    assert 'prioritized_actions' in data
