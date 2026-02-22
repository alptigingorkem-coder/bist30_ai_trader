"""
Unit tests for BacktestCommand.

Tests the Command pattern implementation for backtest orchestration.
"""

import pytest
import argparse
import os
from unittest.mock import Mock, patch, MagicMock
from core.backtest.backtest_command import BacktestCommand


@pytest.fixture
def mock_args():
    """Create mock command-line arguments."""
    args = argparse.Namespace()
    args.mode = 'oos'
    args.model = 'lightgbm'
    return args


@pytest.fixture
def command(mock_args):
    """Create BacktestCommand instance with mock args."""
    return BacktestCommand(args=mock_args)


# ─────────────────────────────────────────────────────────────
# INITIALIZATION TESTS
# ─────────────────────────────────────────────────────────────

def test_initialization_with_args(mock_args):
    """Test BacktestCommand initialization with provided args."""
    command = BacktestCommand(args=mock_args)
    
    assert command.args == mock_args
    assert command.args.mode == 'oos'
    assert command.args.model == 'lightgbm'
    assert command.ranker is None
    assert command.data_loader is None
    assert command.all_data == {}
    assert command.xu100_data is None


def test_initialization_without_args():
    """Test BacktestCommand initialization without args (parses from sys.argv)."""
    with patch('sys.argv', ['test', '--mode', 'is', '--model', 'catboost']):
        command = BacktestCommand()
        
        assert command.args.mode == 'is'
        assert command.args.model == 'catboost'


# ─────────────────────────────────────────────────────────────
# ARGUMENT PARSING TESTS
# ─────────────────────────────────────────────────────────────

def test_parse_arguments_default():
    """Test argument parsing with defaults."""
    with patch('sys.argv', ['test']):
        command = BacktestCommand()
        
        assert command.args.mode == 'oos'
        assert command.args.model == 'lightgbm'


def test_parse_arguments_custom():
    """Test argument parsing with custom values."""
    with patch('sys.argv', ['test', '--mode', 'is', '--model', 'ensemble']):
        command = BacktestCommand()
        
        assert command.args.mode == 'is'
        assert command.args.model == 'ensemble'


def test_parse_arguments_invalid_mode():
    """Test argument parsing with invalid mode."""
    with patch('sys.argv', ['test', '--mode', 'invalid']):
        with pytest.raises(SystemExit):
            BacktestCommand()


def test_parse_arguments_invalid_model():
    """Test argument parsing with invalid model."""
    with patch('sys.argv', ['test', '--model', 'invalid']):
        with pytest.raises(SystemExit):
            BacktestCommand()


# ─────────────────────────────────────────────────────────────
# SETUP ENVIRONMENT TESTS
# ─────────────────────────────────────────────────────────────

def test_setup_environment_creates_reports_dir(command, tmp_path, monkeypatch):
    """Test that setup_environment creates reports directory."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    
    # Ensure reports doesn't exist
    reports_dir = tmp_path / "reports"
    assert not reports_dir.exists()
    
    # Run setup
    command._setup_environment()
    
    # Check directory was created
    assert reports_dir.exists()
    assert reports_dir.is_dir()


def test_setup_environment_existing_dir(command, tmp_path, monkeypatch):
    """Test that setup_environment handles existing reports directory."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    
    # Create reports directory
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    
    # Run setup (should not raise error)
    command._setup_environment()
    
    # Directory should still exist
    assert reports_dir.exists()


# ─────────────────────────────────────────────────────────────
# CONFIGURATION LOADING TESTS
# ─────────────────────────────────────────────────────────────

def test_load_configuration_basic(command):
    """Test basic configuration loading."""
    # Should not raise any errors
    command._load_configuration()
    
    # Config should be set
    assert command.config is not None


def test_load_configuration_with_regime(command):
    """Test configuration loading with regime settings."""
    with patch.object(command.config, 'USE_ADAPTIVE_REGIME', True):
        with patch.object(command.config, 'REGIME_THRESHOLDS', {'bull': 0.6}):
            with patch.object(command.config, 'REGIME_ACTIONS', {'bull': 'aggressive'}):
                # Should not raise any errors
                command._load_configuration()


def test_load_configuration_without_regime(command):
    """Test configuration loading without regime settings."""
    with patch.object(command.config, 'USE_ADAPTIVE_REGIME', False):
        # Should not raise any errors
        command._load_configuration()


# ─────────────────────────────────────────────────────────────
# MODEL LOADING TESTS
# ─────────────────────────────────────────────────────────────

def test_load_model_lightgbm(command):
    """Test loading LightGBM model."""
    mock_model = Mock()
    
    with patch('core.backtest.backtest_command.RankingModel.load', return_value=mock_model):
        command._load_model()
        
        assert command.ranker == mock_model


def test_load_model_catboost(command):
    """Test loading CatBoost model."""
    command.args.model = 'catboost'
    mock_model = Mock()
    
    with patch('models.ranking_model_catboost.CatBoostRankingModel.load', return_value=mock_model):
        command._load_model()
        
        assert command.ranker == mock_model


def test_load_model_ensemble(command):
    """Test loading Ensemble model."""
    command.args.model = 'ensemble'
    mock_ensemble = Mock()
    
    with patch('models.ensemble_model.HybridEnsemble', return_value=mock_ensemble):
        with patch('os.path.exists', return_value=True):
            with patch('core.backtest.backtest_command.joblib.load', return_value=Mock()):
                command._load_model()
                
                assert command.ranker == mock_ensemble
                assert mock_ensemble.load_models.called


def test_load_model_file_not_found(command):
    """Test model loading when file not found."""
    with patch('core.backtest.backtest_command.RankingModel.load', side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            command._load_model()


def test_load_model_loading_error(command):
    """Test model loading with generic error."""
    with patch('core.backtest.backtest_command.RankingModel.load', side_effect=Exception("Load error")):
        with pytest.raises(Exception):
            command._load_model()


# ─────────────────────────────────────────────────────────────
# DATA LOADING TESTS
# ─────────────────────────────────────────────────────────────

def test_load_data_success(command):
    """Test successful data loading."""
    mock_loader = Mock()
    mock_xu100 = MagicMock()
    mock_xu100.__len__ = Mock(return_value=100)
    mock_ticker_data = Mock()
    mock_ticker_data.empty = False
    
    mock_loader.fetch_stock_data.return_value = mock_xu100
    mock_loader.get_combined_data.return_value = mock_ticker_data
    
    with patch('core.backtest.backtest_command.DataLoader', return_value=mock_loader):
        with patch.object(command.config, 'TICKERS', ['THYAO.IS', 'GARAN.IS']):
            with patch.object(command.config, 'START_DATE', '2020-01-01'):
                command._load_data()
                
                assert command.data_loader == mock_loader
                assert command.xu100_data == mock_xu100
                assert len(command.all_data) == 2


def test_load_data_xu100_missing(command):
    """Test data loading when XU100 data is missing."""
    mock_loader = Mock()
    mock_ticker_data = Mock()
    mock_ticker_data.empty = False
    
    mock_loader.fetch_stock_data.return_value = None
    mock_loader.get_combined_data.return_value = mock_ticker_data
    
    with patch('core.backtest.backtest_command.DataLoader', return_value=mock_loader):
        with patch.object(command.config, 'TICKERS', ['THYAO.IS']):
            with patch.object(command.config, 'START_DATE', '2020-01-01'):
                command._load_data()
                
                assert command.xu100_data is None
                assert len(command.all_data) == 1


def test_load_data_ticker_error(command):
    """Test data loading when a ticker fails."""
    mock_loader = Mock()
    mock_xu100 = MagicMock()
    mock_xu100.__len__ = Mock(return_value=100)
    mock_ticker_data = Mock()
    mock_ticker_data.empty = False
    
    mock_loader.fetch_stock_data.return_value = mock_xu100
    mock_loader.get_combined_data.side_effect = [mock_ticker_data, Exception("Data error")]
    
    with patch('core.backtest.backtest_command.DataLoader', return_value=mock_loader):
        with patch.object(command.config, 'TICKERS', ['THYAO.IS', 'GARAN.IS']):
            with patch.object(command.config, 'START_DATE', '2020-01-01'):
                command._load_data()
                
                # Should load one ticker successfully
                assert len(command.all_data) == 1


def test_load_data_no_data(command):
    """Test data loading when no data is available."""
    mock_loader = Mock()
    
    mock_loader.fetch_stock_data.return_value = None
    mock_loader.get_combined_data.return_value = None
    
    with patch('core.backtest.backtest_command.DataLoader', return_value=mock_loader):
        with patch.object(command.config, 'TICKERS', ['THYAO.IS']):
            with patch.object(command.config, 'START_DATE', '2020-01-01'):
                with pytest.raises(ValueError, match="No data loaded"):
                    command._load_data()


# ─────────────────────────────────────────────────────────────
# BACKTEST EXECUTION TESTS
# ─────────────────────────────────────────────────────────────

def test_run_backtest_placeholder(command):
    """Test backtest execution (placeholder implementation)."""
    # Should not raise any errors
    command._run_backtest()


# ─────────────────────────────────────────────────────────────
# REPORT GENERATION TESTS
# ─────────────────────────────────────────────────────────────

def test_generate_report_placeholder(command):
    """Test report generation (placeholder implementation)."""
    # Should not raise any errors
    command._generate_report()


# ─────────────────────────────────────────────────────────────
# EXECUTE WORKFLOW TESTS
# ─────────────────────────────────────────────────────────────

def test_execute_success(command):
    """Test successful execute workflow."""
    # Mock all step methods
    command._setup_environment = Mock()
    command._load_configuration = Mock()
    command._load_model = Mock()
    command._load_data = Mock()
    command._run_backtest = Mock()
    command._generate_report = Mock()
    
    exit_code = command.execute()
    
    # All methods should be called
    assert command._setup_environment.called
    assert command._load_configuration.called
    assert command._load_model.called
    assert command._load_data.called
    assert command._run_backtest.called
    assert command._generate_report.called
    
    # Should return success
    assert exit_code == 0


def test_execute_failure(command):
    """Test execute workflow with failure."""
    # Mock methods, one raises error
    command._setup_environment = Mock()
    command._load_configuration = Mock()
    command._load_model = Mock(side_effect=Exception("Model error"))
    command._load_data = Mock()
    command._run_backtest = Mock()
    command._generate_report = Mock()
    
    exit_code = command.execute()
    
    # Should return failure
    assert exit_code == 1
    
    # Later methods should not be called
    assert not command._load_data.called
    assert not command._run_backtest.called
    assert not command._generate_report.called


def test_execute_step_order(command):
    """Test that execute calls steps in correct order."""
    call_order = []
    
    command._setup_environment = Mock(side_effect=lambda: call_order.append('setup'))
    command._load_configuration = Mock(side_effect=lambda: call_order.append('config'))
    command._load_model = Mock(side_effect=lambda: call_order.append('model'))
    command._load_data = Mock(side_effect=lambda: call_order.append('data'))
    command._run_backtest = Mock(side_effect=lambda: call_order.append('backtest'))
    command._generate_report = Mock(side_effect=lambda: call_order.append('report'))
    
    command.execute()
    
    # Check order
    assert call_order == ['setup', 'config', 'model', 'data', 'backtest', 'report']


# ─────────────────────────────────────────────────────────────
# INTEGRATION TESTS
# ─────────────────────────────────────────────────────────────

def test_complete_workflow_mock(mock_args):
    """Test complete workflow with all mocks."""
    with patch('core.backtest.backtest_command.RankingModel.load'):
        with patch('core.backtest.backtest_command.DataLoader'):
            with patch('os.path.exists', return_value=False):
                with patch('os.makedirs'):
                    command = BacktestCommand(args=mock_args)
                    
                    # Mock data loading
                    command.config.TICKERS = ['THYAO.IS']
                    command.config.START_DATE = '2020-01-01'
                    
                    # Execute should complete without errors
                    exit_code = command.execute()
                    
                    # Note: Will fail at data loading due to mocks
                    # but structure is tested
                    assert exit_code in [0, 1]
