"""
Unit tests for PositionAwareSession.

Tests the session management class for position-aware paper trading.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

from paper_trading.position_aware_session import PositionAwareSession


# ─────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_portfolio():
    """Create mock portfolio state."""
    portfolio = Mock()
    portfolio.cash = 100000.0
    portfolio.realized_pnl = 5000.0
    portfolio.peak_equity = 105000.0
    portfolio.position_count = Mock(return_value=3)
    portfolio.total_portfolio_value = Mock(return_value=105000.0)
    portfolio.exposure_ratio = Mock(return_value=0.6)
    portfolio.get_open_symbols = Mock(return_value=['THYAO', 'GARAN', 'ISCTR'])
    portfolio.get_last_price = Mock(return_value=50.0)
    portfolio.get_trade_statistics = Mock(return_value={
        'win_rate': 60.0,
        'total_trades': 20,
        'avg_win': 1500.0,
        'avg_loss': -750.0
    })
    portfolio.save = Mock()
    return portfolio


@pytest.fixture
def mock_risk_manager():
    """Create mock risk manager."""
    manager = Mock()
    manager.check_portfolio_drawdown = Mock(return_value=('CONTINUE', 0.05))
    return manager


@pytest.fixture
def mock_engine():
    """Create mock position engine."""
    engine = Mock()
    engine.process_signal = Mock(return_value={
        'action': 'OPEN',
        'qty': 100,
        'price': 50.0
    })
    return engine


@pytest.fixture
def mock_model():
    """Create mock prediction model."""
    model = Mock()
    model.predict = Mock(return_value=np.array([0.8, 0.7, 0.6, 0.5, 0.4]))
    return model


@pytest.fixture
def sample_market_data():
    """Create sample market data."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'Close': np.random.uniform(40, 60, 100),
        'Volume': np.random.uniform(1000000, 5000000, 100),
        'Volatility_20': np.random.uniform(0.01, 0.05, 100),
        'Ticker': 'THYAO'
    }, index=dates)
    return data


@pytest.fixture
def sample_top_picks():
    """Create sample top picks DataFrame."""
    return pd.DataFrame({
        'Ticker': ['THYAO', 'GARAN', 'ISCTR'],
        'Score': [0.8, 0.7, 0.6],
        'Close': [50.0, 45.0, 40.0],
        'Volatility_20': [0.02, 0.03, 0.025],
        'target_weight': [0.4, 0.35, 0.25]
    })


# ─────────────────────────────────────────────────────────────
# INITIALIZATION TESTS
# ─────────────────────────────────────────────────────────────

def test_initialization_with_components(mock_portfolio, mock_risk_manager):
    """Test initialization with provided components."""
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    
    assert session.portfolio == mock_portfolio
    assert session.risk_manager == mock_risk_manager
    assert session.verbose is False
    assert session.engine is None
    assert session.trade_logger is None
    assert session.model is None
    assert session.regime_detector is None


def test_initialization_without_components():
    """Test initialization without provided components."""
    session = PositionAwareSession(verbose=True)
    
    assert session.portfolio is None
    assert session.risk_manager is None
    assert session.verbose is True


# ─────────────────────────────────────────────────────────────
# SESSION INITIALIZATION TESTS
# ─────────────────────────────────────────────────────────────

@patch('paper_trading.position_aware_session.PositionLogger')
@patch('paper_trading.position_aware_session.PositionEngine')
@patch('paper_trading.position_aware_session.RiskManager')
@patch('paper_trading.position_aware_session.PortfolioState')
@patch('paper_trading.position_aware_session.RegimeDetector')
def test_initialize_session_creates_components(
    mock_regime_cls, mock_portfolio_cls, mock_risk_cls, 
    mock_engine_cls, mock_logger_cls, mock_portfolio
):
    """Test that _initialize_session creates all required components."""
    mock_portfolio_cls.load = Mock(return_value=mock_portfolio)
    
    session = PositionAwareSession(verbose=False)
    session._initialize_session()
    
    # Verify components were created
    mock_portfolio_cls.load.assert_called_once()
    mock_risk_cls.assert_called_once()
    mock_engine_cls.assert_called_once()
    mock_logger_cls.assert_called_once()


@patch('paper_trading.position_aware_session.PositionLogger')
@patch('paper_trading.position_aware_session.PositionEngine')
@patch('paper_trading.position_aware_session.RegimeDetector')
def test_initialize_session_uses_provided_components(
    mock_regime_cls, mock_engine_cls, mock_logger_cls,
    mock_portfolio, mock_risk_manager
):
    """Test that _initialize_session uses provided components."""
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    session._initialize_session()
    
    # Verify provided components are used
    assert session.portfolio == mock_portfolio
    assert session.risk_manager == mock_risk_manager


@patch('paper_trading.position_aware_session.PositionLogger')
@patch('paper_trading.position_aware_session.PositionEngine')
@patch('paper_trading.position_aware_session.RegimeDetector')
def test_initialize_session_handles_regime_detector_failure(
    mock_regime_cls, mock_engine_cls, mock_logger_cls,
    mock_portfolio, mock_risk_manager
):
    """Test that regime detector failure is handled gracefully."""
    mock_regime_cls.side_effect = Exception("Regime detector error")
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    session._initialize_session()
    
    # Session should continue with None regime detector
    assert session.regime_detector is None


# ─────────────────────────────────────────────────────────────
# STRATEGY HEALTH TESTS
# ─────────────────────────────────────────────────────────────

@patch('paper_trading.strategy_health.check_strategy_health')
def test_check_strategy_health_returns_tuple(mock_health, mock_portfolio):
    """Test that _check_strategy_health returns correct tuple."""
    mock_health.return_value = (
        True,
        "Healthy",
        {'can_live_trade': True, 'paper_only_mode': False}
    )
    
    session = PositionAwareSession(portfolio=mock_portfolio, verbose=False)
    can_trade, msg, rec = session._check_strategy_health()
    
    assert can_trade is True
    assert msg == "Healthy"
    assert rec['can_live_trade'] is True


@patch('paper_trading.strategy_health.check_strategy_health')
def test_check_strategy_health_blocks_trading(mock_health, mock_portfolio):
    """Test that unhealthy strategy blocks trading."""
    mock_health.return_value = (
        False,
        "Unhealthy",
        {'can_live_trade': False}
    )
    
    session = PositionAwareSession(portfolio=mock_portfolio, verbose=False)
    can_trade, msg, rec = session._check_strategy_health()
    
    assert can_trade is False


# ─────────────────────────────────────────────────────────────
# MARKET DATA TESTS
# ─────────────────────────────────────────────────────────────

@patch('paper_trading.position_aware_session.FeatureEngineer')
@patch('paper_trading.position_aware_session.DataLoader')
@patch('paper_trading.position_aware_session.config')
def test_load_market_data_success(
    mock_config, mock_loader_cls, mock_fe_cls,
    sample_market_data
):
    """Test successful market data loading."""
    mock_config.START_DATE = '2023-01-01'
    mock_config.TICKERS = ['THYAO', 'GARAN']
    
    mock_loader = Mock()
    mock_loader.get_combined_data = Mock(return_value=sample_market_data)
    mock_loader_cls.return_value = mock_loader
    
    mock_fe = Mock()
    mock_fe.process_all = Mock(return_value=sample_market_data)
    mock_fe_cls.return_value = mock_fe
    
    session = PositionAwareSession(verbose=False)
    result = session._load_market_data()
    
    assert len(result) == 2
    assert 'THYAO' in result
    assert 'GARAN' in result


@patch('paper_trading.position_aware_session.FeatureEngineer')
@patch('paper_trading.position_aware_session.DataLoader')
@patch('paper_trading.position_aware_session.config')
def test_load_market_data_skips_insufficient_data(
    mock_config, mock_loader_cls, mock_fe_cls
):
    """Test that tickers with insufficient data are skipped."""
    mock_config.START_DATE = '2023-01-01'
    mock_config.TICKERS = ['THYAO', 'GARAN']
    
    mock_loader = Mock()
    # THYAO has insufficient data
    mock_loader.get_combined_data = Mock(side_effect=[
        pd.DataFrame({'Close': [50.0] * 50}),  # Only 50 rows
        pd.DataFrame({'Close': [45.0] * 150})  # 150 rows
    ])
    mock_loader_cls.return_value = mock_loader
    
    mock_fe = Mock()
    mock_fe.process_all = Mock(return_value=pd.DataFrame({'Close': [45.0] * 150}))
    mock_fe_cls.return_value = mock_fe
    
    session = PositionAwareSession(verbose=False)
    result = session._load_market_data()
    
    # Only GARAN should be included
    assert len(result) == 1
    assert 'GARAN' in result


# ─────────────────────────────────────────────────────────────
# PREDICTION TESTS
# ─────────────────────────────────────────────────────────────

def test_generate_predictions(mock_model, sample_market_data):
    """Test prediction generation and ranking."""
    # Create 3 separate dataframes with different tickers
    data1 = sample_market_data.copy()
    data1['Ticker'] = 'THYAO'
    data2 = sample_market_data.copy()
    data2['Ticker'] = 'GARAN'
    data3 = sample_market_data.copy()
    data3['Ticker'] = 'ISCTR'
    
    all_data = {
        'THYAO': data1,
        'GARAN': data2,
        'ISCTR': data3
    }
    
    # Mock should return correct length (300 rows total)
    mock_model.predict = Mock(return_value=np.array([0.8] * 300))
    
    session = PositionAwareSession(verbose=False)
    session.model = mock_model
    
    result = session._generate_predictions(all_data)
    
    # Verify predictions were made
    mock_model.predict.assert_called_once()
    
    # Verify result structure
    assert 'Score' in result.columns
    assert 'Ticker' in result.columns
    assert len(result) == 3  # One row per ticker (latest)


def test_generate_predictions_handles_missing_ticker_column(mock_model):
    """Test that missing Ticker column is handled."""
    data = pd.DataFrame({
        'Close': [50.0, 51.0],
        'level_1': ['THYAO', 'THYAO']
    })
    
    all_data = {'THYAO': data}
    
    # Mock should return correct length
    mock_model.predict = Mock(return_value=np.array([0.8, 0.7]))
    
    session = PositionAwareSession(verbose=False)
    session.model = mock_model
    
    result = session._generate_predictions(all_data)
    
    # Should rename level_1 to Ticker
    assert 'Ticker' in result.columns


# ─────────────────────────────────────────────────────────────
# TARGET WEIGHT CALCULATION TESTS
# ─────────────────────────────────────────────────────────────

@patch('paper_trading.position_aware_session.config')
def test_calculate_target_weights_normal(
    mock_config, mock_portfolio, mock_risk_manager, sample_top_picks
):
    """Test target weight calculation under normal conditions."""
    mock_config.PORTFOLIO_SIZE = 5
    mock_config.MAX_SECTOR_POSITIONS = 2
    mock_config.WEIGHTING_STRATEGY = 'Equal'
    mock_config.get_sector = Mock(return_value='Banking')
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    
    health_rec = {}
    result = session._calculate_target_weights(sample_top_picks, health_rec)
    
    assert 'target_weight' in result.columns
    assert len(result) > 0


@patch('paper_trading.position_aware_session.config')
def test_calculate_target_weights_circuit_breaker_stop(
    mock_config, mock_portfolio, mock_risk_manager, sample_top_picks
):
    """Test circuit breaker stops trading."""
    mock_config.PORTFOLIO_SIZE = 5
    mock_config.MAX_SECTOR_POSITIONS = 2
    mock_config.get_sector = Mock(return_value='Banking')
    
    # Circuit breaker triggered
    mock_risk_manager.check_portfolio_drawdown = Mock(
        return_value=('STOP_TRADING', 0.35)
    )
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    
    health_rec = {}
    result = session._calculate_target_weights(sample_top_picks, health_rec)
    
    # All weights should be 0
    assert (result['target_weight'] == 0.0).all()


@patch('paper_trading.position_aware_session.config')
def test_calculate_target_weights_reduce_exposure(
    mock_config, mock_portfolio, mock_risk_manager, sample_top_picks
):
    """Test exposure reduction on drawdown warning."""
    mock_config.PORTFOLIO_SIZE = 5
    mock_config.MAX_SECTOR_POSITIONS = 2
    mock_config.WEIGHTING_STRATEGY = 'Equal'
    mock_config.get_sector = Mock(return_value='Banking')
    
    # Drawdown warning
    mock_risk_manager.check_portfolio_drawdown = Mock(
        return_value=('REDUCE_EXPOSURE', 0.20)
    )
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    
    health_rec = {}
    result = session._calculate_target_weights(sample_top_picks, health_rec)
    
    # Weights should be reduced (but not zero)
    assert (result['target_weight'] > 0).any()
    assert (result['target_weight'] < 0.5).all()  # Reduced by 50%


# ─────────────────────────────────────────────────────────────
# WEIGHTING STRATEGY TESTS
# ─────────────────────────────────────────────────────────────

@patch('paper_trading.position_aware_session.config')
def test_apply_weighting_strategy_equal(mock_config, sample_top_picks):
    """Test equal weighting strategy."""
    mock_config.WEIGHTING_STRATEGY = 'Equal'
    
    session = PositionAwareSession(verbose=False)
    result = session._apply_weighting_strategy(sample_top_picks)
    
    # All weights should be equal
    expected_weight = 1.0 / len(sample_top_picks)
    assert np.allclose(result['target_weight'], expected_weight)


@patch('paper_trading.position_aware_session.config')
def test_apply_weighting_strategy_risk_parity(mock_config, sample_top_picks):
    """Test risk parity weighting strategy."""
    mock_config.WEIGHTING_STRATEGY = 'RiskParity'
    
    session = PositionAwareSession(verbose=False)
    result = session._apply_weighting_strategy(sample_top_picks)
    
    # Weights should sum to 1
    assert np.isclose(result['target_weight'].sum(), 1.0)
    # Lower volatility should get higher weight
    assert result.iloc[0]['target_weight'] > result.iloc[1]['target_weight']


@patch('paper_trading.position_aware_session.config')
def test_apply_weighting_strategy_rank_weighted(mock_config, sample_top_picks):
    """Test rank-weighted strategy."""
    mock_config.WEIGHTING_STRATEGY = 'RankWeighted'
    
    session = PositionAwareSession(verbose=False)
    result = session._apply_weighting_strategy(sample_top_picks)
    
    # Weights should sum to 1
    assert np.isclose(result['target_weight'].sum(), 1.0)
    # First pick should have highest weight
    assert result.iloc[0]['target_weight'] > result.iloc[1]['target_weight']
    assert result.iloc[1]['target_weight'] > result.iloc[2]['target_weight']


# ─────────────────────────────────────────────────────────────
# TRADE EXECUTION TESTS
# ─────────────────────────────────────────────────────────────

def test_execute_trades(mock_portfolio, mock_risk_manager, sample_top_picks):
    """Test trade execution."""
    mock_engine = Mock()
    mock_engine.process_signal = Mock(return_value={
        'action': 'OPEN',
        'qty': 100
    })
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    session.engine = mock_engine
    
    stats = session._execute_trades(sample_top_picks, 0.6, 2.0)
    
    # Verify trades were executed
    assert mock_engine.process_signal.call_count == len(sample_top_picks)
    assert 'open' in stats
    assert stats['open'] == len(sample_top_picks)


def test_execute_trades_with_hold_action(
    mock_portfolio, mock_risk_manager, sample_top_picks
):
    """Test that HOLD actions are counted correctly."""
    mock_engine = Mock()
    mock_engine.process_signal = Mock(return_value={
        'action': 'HOLD',
        'qty': 0
    })
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    session.engine = mock_engine
    
    stats = session._execute_trades(sample_top_picks, 0.6, 2.0)
    
    assert stats['hold'] == len(sample_top_picks)


@patch('paper_trading.position_aware_session.db')
def test_log_trade_to_db(mock_db, mock_portfolio, mock_risk_manager):
    """Test trade logging to database."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor = Mock(return_value=mock_cursor)
    mock_db.connection = Mock(return_value=mock_conn)
    mock_conn.__enter__ = Mock(return_value=mock_conn)
    mock_conn.__exit__ = Mock(return_value=False)
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    
    decision = {'qty': 100}
    session._log_trade_to_db('OPEN', 'THYAO', 50.0, decision)
    
    # Verify database insert was called
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


def test_close_unwanted_positions(
    mock_portfolio, mock_risk_manager, sample_top_picks
):
    """Test closing positions not in target portfolio."""
    mock_portfolio.get_open_symbols = Mock(return_value=['THYAO', 'GARAN', 'AKBNK'])
    
    mock_engine = Mock()
    mock_engine.process_signal = Mock(return_value={'action': 'CLOSE'})
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    session.engine = mock_engine
    
    stats = {'close': 0}
    session._close_unwanted_positions(sample_top_picks, stats)
    
    # AKBNK should be closed (not in top_picks)
    assert stats['close'] == 1


# ─────────────────────────────────────────────────────────────
# SESSION FINALIZATION TESTS
# ─────────────────────────────────────────────────────────────

@patch('paper_trading.position_aware_session.db')
def test_finalize_session(mock_db, mock_portfolio, mock_risk_manager):
    """Test session finalization."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor = Mock(return_value=mock_cursor)
    mock_db.connection = Mock(return_value=mock_conn)
    mock_conn.__enter__ = Mock(return_value=mock_conn)
    mock_conn.__exit__ = Mock(return_value=False)
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    
    stats = {'open': 2, 'close': 1, 'hold': 3}
    result = session._finalize_session(stats)
    
    # Verify portfolio was saved
    mock_portfolio.save.assert_called_once()
    
    # Verify result structure
    assert 'portfolio_value' in result
    assert 'realized_pnl' in result
    assert 'stats' in result
    assert result['portfolio_value'] == 105000.0
    assert result['realized_pnl'] == 5000.0


@patch('paper_trading.position_aware_session.db')
def test_save_portfolio_stats_to_db(mock_db, mock_portfolio, mock_risk_manager):
    """Test saving portfolio stats to database."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor = Mock(return_value=mock_cursor)
    mock_db.connection = Mock(return_value=mock_conn)
    mock_conn.__enter__ = Mock(return_value=mock_conn)
    mock_conn.__exit__ = Mock(return_value=False)
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    
    stats = {'open': 2, 'scale_in': 1, 'scale_out': 1, 'close': 1}
    session._save_portfolio_stats_to_db(105000.0, 5000.0, stats)
    
    # Verify database insert was called
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


# ─────────────────────────────────────────────────────────────
# INTEGRATION TESTS
# ─────────────────────────────────────────────────────────────

@patch('paper_trading.position_runner.load_production_model')
@patch('paper_trading.strategy_health.check_strategy_health')
@patch('paper_trading.position_aware_session.PositionLogger')
@patch('paper_trading.position_aware_session.PositionEngine')
@patch('paper_trading.position_aware_session.RegimeDetector')
def test_run_session_success(
    mock_regime_cls, mock_engine_cls, mock_logger_cls,
    mock_health, mock_load_model,
    mock_portfolio, mock_risk_manager, mock_model
):
    """Test complete session run with success."""
    # Setup mocks
    mock_health.return_value = (True, "Healthy", {})
    mock_load_model.return_value = mock_model
    
    mock_engine = Mock()
    mock_engine.process_signal = Mock(return_value={'action': 'OPEN', 'qty': 100})
    mock_engine_cls.return_value = mock_engine
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    
    # Mock internal methods
    session._load_market_data = Mock(return_value={})
    session._generate_predictions = Mock(return_value=pd.DataFrame())
    session._calculate_target_weights = Mock(return_value=pd.DataFrame())
    
    result = session.run()
    
    # Verify result structure
    assert 'portfolio_value' in result
    assert 'realized_pnl' in result
    assert 'stats' in result


@patch('paper_trading.strategy_health.check_strategy_health')
@patch('paper_trading.position_aware_session.PositionLogger')
@patch('paper_trading.position_aware_session.PositionEngine')
@patch('paper_trading.position_aware_session.RegimeDetector')
def test_run_session_health_blocks_trading(
    mock_regime_cls, mock_engine_cls, mock_logger_cls, mock_health,
    mock_portfolio, mock_risk_manager
):
    """Test that unhealthy strategy blocks session."""
    mock_health.return_value = (False, "Unhealthy", {})
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    
    result = session.run()
    
    # Session should abort
    assert result['portfolio_value'] == 0
    assert result['realized_pnl'] == 0


@patch('paper_trading.position_runner.load_production_model')
@patch('paper_trading.strategy_health.check_strategy_health')
@patch('paper_trading.position_aware_session.PositionLogger')
@patch('paper_trading.position_aware_session.PositionEngine')
@patch('paper_trading.position_aware_session.RegimeDetector')
def test_run_session_no_signals(
    mock_regime_cls, mock_engine_cls, mock_logger_cls,
    mock_health, mock_load_model,
    mock_portfolio, mock_risk_manager, mock_model
):
    """Test session with no signals generated."""
    mock_health.return_value = (True, "Healthy", {})
    mock_load_model.return_value = mock_model
    
    session = PositionAwareSession(
        portfolio=mock_portfolio,
        risk_manager=mock_risk_manager,
        verbose=False
    )
    
    # Mock to return empty data
    session._load_market_data = Mock(return_value={})
    
    result = session.run()
    
    # Session should abort with no signals
    assert result['portfolio_value'] == 0
    assert result['realized_pnl'] == 0
