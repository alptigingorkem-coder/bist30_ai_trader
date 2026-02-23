"""
Position-Aware Paper Trading Runner - MODERNIZED
Yeni target-weight based PositionEngine ile uyumlu orchestrator
"""

import sys
import os
from datetime import datetime
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging_config import get_logger
from paper_trading.portfolio_state import PortfolioState

log = get_logger(__name__)


def load_production_model():
    """Load HybridEnsemble model"""
    import os
    import joblib
    from models.ensemble_model import HybridEnsemble
    
    ranker = HybridEnsemble()
    
    lgbm_path = "models/saved/global_ranker.pkl"
    tft_path = "models/saved/tft_model.pth"
    tft_config_path = "models/saved/tft_config.joblib"
    catboost_path = "models/saved/global_ranker_catboost.cbm"
    
    tft_config = None
    if os.path.exists(tft_config_path):
         tft_config = joblib.load(tft_config_path)
         
    ranker.load_models(lgbm_path, tft_path, tft_config=tft_config, catboost_path=catboost_path)
    
    log.info("Production Model: HybridEnsemble loaded.")
    return ranker


def run_position_aware_session(verbose: bool = True):
    """
    Modern Position-Aware Paper Trading Session
    
    Delegates to PositionAwareSession class for execution.
    
    Args:
        verbose: Enable verbose logging
        
    Returns:
        Dictionary with session results (portfolio_value, realized_pnl, stats)
    """
    from paper_trading.position_aware_session import PositionAwareSession
    
    # Create and run session
    session = PositionAwareSession(verbose=verbose)
    result = session.run()
    
    return result


def reset_portfolio():
    """Reset portfolio to initial state"""
    portfolio = PortfolioState()
    
    # Clear all positions
    portfolio.positions = {}
    portfolio.cash = portfolio.initial_capital
    portfolio.realized_pnl = 0.0
    portfolio.trade_history = []
    portfolio.closed_trades = []
    
    portfolio.save()
    log.info("Portfolio reset to initial state")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Position-Aware Paper Trading")
    parser.add_argument('--reset', action='store_true', help='Reset portfolio')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode')
    
    args = parser.parse_args()
    
    if args.reset:
        reset_portfolio()
    else:
        run_position_aware_session(verbose=not args.quiet)
