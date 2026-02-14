"""
Position-Aware Paper Trading Runner - MODERNIZED
Yeni target-weight based PositionEngine ile uyumlu orchestrator
"""

import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from utils.logging_config import get_logger
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from paper_trading.portfolio_state import PortfolioState
from paper_trading.position_engine import PositionEngine
from paper_trading.position_logger import PositionLogger
from core.risk_manager import RiskManager
from paper_trading.strategy_health import check_strategy_health

log = get_logger(__name__)


def load_production_model():
    """Load best available model"""
    import os
    import joblib
    
    # Try CatBoost first
    catboost_path = "models/saved/global_ranker_catboost.cbm"
    if os.path.exists(catboost_path):
        from catboost import CatBoostClassifier
        model = CatBoostClassifier()
        model.load_model(catboost_path)
        log.info("CatBoost model loaded: %s", catboost_path)
        return model
    
    # Fallback to LightGBM
    lgbm_path = "models/saved/global_ranker.pkl"
    if os.path.exists(lgbm_path):
        model = joblib.load(lgbm_path)
        log.info("LightGBM model loaded: %s", lgbm_path)
        return model
    
    raise FileNotFoundError("No production model found")


def run_position_aware_session(verbose: bool = True):
    """
    Modern Position-Aware Paper Trading Session
    
    1. Load portfolio state
    2. Download market data
    3. Generate model predictions
    4. Calculate target weights (Top 5)
    5. Execute trades via PositionEngine
    6. Log and save state
    """
    
    log.info("=" * 70)
    log.info("POSITION-AWARE PAPER TRADING (v3.0)")
    log.info("Date: %s", datetime.now().strftime('%Y-%m-%d %H:%M'))
    log.info("=" * 70)
    
    # 1. Initialize modules
    portfolio = PortfolioState.load()
    risk_manager = RiskManager()
    engine = PositionEngine(portfolio_state=portfolio, risk_manager=risk_manager)
    trade_logger = PositionLogger()
    
    if verbose:
        log.info("Portfolio State (Start):")
        log.info("   Cash           : %,.0f TL", portfolio.cash)
        log.info("   Positions      : %d", portfolio.position_count())
        log.info("   Total Value    : %,.0f TL", portfolio.total_portfolio_value())
        log.info("   Exposure       : %.1f%%", portfolio.exposure_ratio() * 100)
    
    # 2. Load model
    log.info("Loading production model...")
    model = load_production_model()
    
    # 3. Strategy health check (kill-switch & position sizing hints)
    can_trade, health_msg, health_rec = check_strategy_health(portfolio)
    if verbose:
        log.info("Strategy Health: %s", health_msg)
        log.info("   Can Live Trade : %s", health_rec.get('can_live_trade'))
        log.info("   Paper Only     : %s", health_rec.get('paper_only_mode'))
        log.info("   Pos Size x     : %s", health_rec.get('position_size_multiplier'))
        log.info("   Conf Threshold : %s", health_rec.get('confidence_threshold'))

    # Eğer canlı trade modunda ve strateji izin vermiyorsa, oturumu sonlandır
    if not can_trade:
        log.error("Strategy health blocked trading. Session aborted.")
        return

    # 4. Download market data
    log.info("Downloading market data...")
    loader = DataLoader(start_date=config.START_DATE)
    tickers = config.TICKERS
    
    all_data = {}
    for ticker in tickers:
        raw = loader.get_combined_data(ticker)
        if raw is None or len(raw) < 100:
            continue
        
        fe = FeatureEngineer(raw)
        df = fe.process_all(ticker)
        
        if not df.empty:
            all_data[ticker] = df
    
    if not all_data:
        log.error("No data available")
        return
    
    log.info("Processed %d symbols", len(all_data))
    
    # 5. Predict & Rank
    log.info("Running model predictions...")
    full_df = pd.concat(all_data.values())
    
    # Get latest data point for each ticker
    latest = full_df.groupby('Ticker').tail(1)
    
    # Predict
    scores = model.predict(latest)
    latest['Score'] = scores
    latest = latest.sort_values('Score', ascending=False)
    
    # 6. Calculate Target Weights (Top 5)
    MAX_POSITIONS = getattr(config, 'PORTFOLIO_SIZE', 5)
    MIN_CONFIDENCE = float(health_rec.get("confidence_threshold", 0.55))
    
    top_picks = latest.head(MAX_POSITIONS)
    
    # Simple equal weighting for Top N
    total_score = top_picks['Score'].sum()
    top_picks['target_weight'] = top_picks['Score'] / total_score if total_score > 0 else 1.0 / len(top_picks)
    
    if verbose:
        log.info("Target Portfolio (Top %d):", MAX_POSITIONS)
        for _, row in top_picks.iterrows():
            ticker = row['Ticker']
            score = row['Score']
            weight = row['target_weight']
            price = row['Close']
            log.info("   %s | Score: %.2f | Weight: %5.1f%% | Price: %.2f",
                     ticker, score, weight * 100, price)
    
    # 7. Execute Trades
    log.info("Executing trades...")
    
    stats = {'open': 0, 'scale_in': 0, 'scale_out': 0, 'close': 0, 'hold': 0}
    
    for _, row in top_picks.iterrows():
        ticker = row['Ticker']
        target_weight = row['target_weight']
        confidence = row['Score']
        price = row['Close']
        
        decision = engine.process_signal(
            symbol=ticker,
            target_weight=target_weight,
            confidence=confidence,
            price=price
        )
        
        action = decision['action']
        stats[action.lower()] = stats.get(action.lower(), 0) + 1
        
        if verbose and action != 'HOLD':
            log.info("   %-12s %-10s @ %.2f", action, ticker, price)
    
    # 8. Close unwanted positions
    log.info("Cleaning up positions...")
    allowed_symbols = top_picks['Ticker'].tolist()
    current_positions = portfolio.get_open_symbols()
    
    for symbol in current_positions:
        if symbol not in allowed_symbols:
            price = portfolio.get_last_price(symbol)
            engine.process_signal(
                symbol=symbol,
                target_weight=0.0,
                confidence=0.0,
                price=price
            )
            stats['close'] = stats.get('close', 0) + 1
            if verbose:
                log.info("   CLOSE        %-10s @ %.2f", symbol, price)
    
    # 9. Save state
    portfolio.save()
    
    # 10. Summary
    final_value = portfolio.total_portfolio_value()
    realized_pnl = portfolio.realized_pnl
    
    log.info("-" * 70)
    log.info("SESSION SUMMARY")
    log.info("-" * 70)
    log.info("   Actions: Open=%d Close=%d ScaleIn=%d ScaleOut=%d Hold=%d",
             stats.get('open', 0), stats.get('close', 0),
             stats.get('scale_in', 0), stats.get('scale_out', 0),
             stats.get('hold', 0))
    log.info("   Portfolio: Cash=%,.0f TL | Positions=%d | Total=%,.0f TL | PnL=%,.2f TL",
             portfolio.cash, portfolio.position_count(), final_value, realized_pnl)
    log.info("Session completed")
    log.info("=" * 70)
    
    return {
        'portfolio_value': final_value,
        'realized_pnl': realized_pnl,
        'stats': stats
    }


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
