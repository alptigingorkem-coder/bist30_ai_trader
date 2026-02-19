"""Unit tests for ScriptCategorizer."""

import pytest
from pathlib import Path
from scripts.maintenance.core.script_categorizer import ScriptCategorizer, ScriptOrganizationResult
from scripts.maintenance.core.config import CleanupConfig


@pytest.fixture
def config():
    """Create test configuration."""
    return CleanupConfig()


@pytest.fixture
def categorizer(config):
    """Create ScriptCategorizer instance."""
    return ScriptCategorizer(config, None)


def test_categorize_analysis_script(categorizer):
    """Test categorization of analysis scripts."""
    script_path = Path('scripts/analyze_data.py')
    category = categorizer.categorize_script(script_path)
    assert category == 'analysis'


def test_categorize_maintenance_script(categorizer):
    """Test categorization of maintenance scripts."""
    script_path = Path('scripts/clean_logs.py')
    category = categorizer.categorize_script(script_path)
    assert category == 'maintenance'


def test_categorize_test_script(categorizer):
    """Test categorization of test scripts."""
    script_path = Path('scripts/test_integration.py')
    category = categorizer.categorize_script(script_path)
    assert category == 'integration_tests'


def test_production_script_detection(categorizer):
    """Test production script detection."""
    # Production scripts should be explicitly listed in config
    categorizer.production_scripts = {'train_model.py'}
    script_path = Path('scripts/train_model.py')
    assert categorizer.is_production_script(script_path) is True


def test_non_production_script(categorizer):
    """Test non-production script detection."""
    script_path = Path('scripts/random_script.py')
    assert categorizer.is_production_script(script_path) is False


def test_export_json(categorizer, tmp_path):
    """Test JSON export."""
    from scripts.maintenance.core.script_categorizer import ScriptCategory
    
    result = ScriptOrganizationResult(
        production=ScriptCategory('production', [], 'scripts/'),
        analysis=ScriptCategory('analysis', [], 'scripts/analysis/'),
        maintenance=ScriptCategory('maintenance', [], 'scripts/maintenance/'),
        integration_tests=ScriptCategory('integration_tests', [], 'scripts/tests/'),
        reorganization_plan=[],
        broken_imports=[]
    )
    
    output_path = tmp_path / 'output.json'
    categorizer.export_json(result, output_path)
    
    assert output_path.exists()
    import json
    data = json.loads(output_path.read_text())
    assert 'production' in data
    assert 'analysis' in data
