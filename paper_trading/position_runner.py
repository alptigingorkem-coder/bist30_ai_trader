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
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from paper_trading.portfolio_state import PortfolioState
from paper_trading.position_engine import PositionEngine
from paper_trading.position_logger import PositionLogger
from core.risk_manager import RiskManager


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
        print(f"✅ CatBoost model loaded: {catboost_path}")
        return model
    
    # Fallback to LightGBM
    lgbm_path = "models/saved/global_ranker.pkl"
    if os.path.exists(lgbm_path):
        model = joblib.load(lgbm_path)
        print(f"✅ LightGBM model loaded: {lgbm_path}")
        return model
    
    raise FileNotFoundError("❌ No production model found")


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
    
    print("\n" + "="*70)
    print("🎯 POSITION-AWARE PAPER TRADING (v3.0)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    # 1. Initialize modules
    portfolio = PortfolioState.load()
    risk_manager = RiskManager()
    engine = PositionEngine(portfolio_state=portfolio, risk_manager=risk_manager)
    logger = PositionLogger()
    
    if verbose:
        print(f"\n📊 Portfolio State (Start):")
        print(f"   Cash           : {portfolio.cash:,.0f} TL")
        print(f"   Positions      : {portfolio.position_count()}")
        print(f"   Total Value    : {portfolio.total_portfolio_value():,.0f} TL")
        print(f"   Exposure       : {portfolio.exposure_ratio()*100:.1f}%")
    
    # 2. Load model
    print(f"\n⏳ Loading production model...")
    model = load_production_model()
    
    # 3. Download market data
    print(f"⏳ Downloading market data...")
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
        print("❌ No data available")
        return
    
    print(f"✅ Processed {len(all_data)} symbols")
    
    # 4. Predict & Rank
    print(f"⏳ Running model predictions...")
    full_df = pd.concat(all_data.values())
    
    # Get latest data point for each ticker
    latest = full_df.groupby('Ticker').tail(1)
    
    # Predict
    scores = model.predict(latest)
    latest['Score'] = scores
    latest = latest.sort_values('Score', ascending=False)
    
    # 5. Calculate Target Weights (Top 5)
    MAX_POSITIONS = getattr(config, 'PORTFOLIO_SIZE', 5)
    MIN_CONFIDENCE = 0.55
    
    top_picks = latest.head(MAX_POSITIONS)
    
    # Simple equal weighting for Top N
    total_score = top_picks['Score'].sum()
    top_picks['target_weight'] = top_picks['Score'] / total_score if total_score > 0 else 1.0 / len(top_picks)
    
    if verbose:
        print(f"\n🎯 Target Portfolio (Top {MAX_POSITIONS}):")
        for _, row in top_picks.iterrows():
            ticker = row['Ticker']
            score = row['Score']
            weight = row['target_weight']
            price = row['Close']
            print(f"   {ticker:<10} | Score: {score:.2f} | Weight: {weight*100:>5.1f}% | Price: {price:.2f}")
    
    # 6. Execute Trades
    print(f"\n⚙️ Executing trades...")
    
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
            print(f"   {action:<12} {ticker:<10} @ {price:.2f}")
    
    # 7. Close unwanted positions
    print(f"\n🧹 Cleaning up positions...")
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
                print(f"   CLOSE        {symbol:<10} @ {price:.2f}")
    
    # 8. Save state
    portfolio.save()
    
    # 9. Summary
    final_value = portfolio.total_portfolio_value()
    realized_pnl = portfolio.realized_pnl
    
    print(f"\n" + "-"*70)
    print(f"📊 SESSION SUMMARY")
    print(f"-"*70)
    print(f"   Actions:")
    print(f"     Open       : {stats.get('open', 0)}")
    print(f"     Close      : {stats.get('close', 0)}")
    print(f"     Scale In   : {stats.get('scale_in', 0)}")
    print(f"     Scale Out  : {stats.get('scale_out', 0)}")
    print(f"     Hold       : {stats.get('hold', 0)}")
    print(f"\n   Portfolio:")
    print(f"     Cash       : {portfolio.cash:,.0f} TL")
    print(f"     Positions  : {portfolio.position_count()}")
    print(f"     Total Value: {final_value:,.0f} TL")
    print(f"     Realized PnL: {realized_pnl:,.2f} TL")
    print(f"\n✅ Session completed")
    print("="*70)
    
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
    print("✅ Portfolio reset to initial state")


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
