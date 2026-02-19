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
from utils.db_manager import DBManager
from models.regime_detector import RegimeDetector

log = get_logger(__name__)
db = DBManager()


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
        log.info(f"   Cash           : {portfolio.cash:,.0f} TL")
        log.info(f"   Positions      : {portfolio.position_count()}")
        log.info(f"   Total Value    : {portfolio.total_portfolio_value():,.0f} TL")
        log.info(f"   Exposure       : {portfolio.exposure_ratio() * 100:.1f}%")
    
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

    # Regime Detection
    try:
        regime_detector = RegimeDetector(config)
        # We need some market data for regime. Usually VIX and Benchmark.
        # DataLoader fetches them during get_combined_data implicitly or explicit macro fetch?
        # Let's simple fetch benchmark to detect regime
        benchmark_data = loader.get_benchmark_data()
        if benchmark_data is not None and not benchmark_data.empty:
             regime = regime_detector.detect_regime(benchmark_data.iloc[-1])
             log.info(f"🌍 MARKET REGIME: {regime}")
        else:
             log.warning("Regime detection skipped: No benchmark data")
    except Exception as e:
        log.warning(f"Regime detection failed: {e}")
    
    all_data = {}
    for ticker in tickers:
        raw = loader.get_combined_data(ticker)
        if raw is None or len(raw) < 100:
            continue
        
        fe = FeatureEngineer(raw)
        df = fe.process_all(ticker)
        
        if not df.empty:
            df['Ticker'] = ticker # Ensure Ticker column exists
            all_data[ticker] = df
    
    if not all_data:
        log.error("No data available")
        return
    
    log.info("Processed %d symbols", len(all_data))
    
    # 5. Predict & Rank
    log.info("Running model predictions...")
    full_df = pd.concat(all_data.values())
    
    # Predict on FULL dataframe to enable TFT/LSTM context
    scores = model.predict(full_df)
    full_df['Score'] = scores
    
    # Get latest data point for each ticker
    # Fix: Ensure Ticker is a column if it was in index
    temp_df = full_df.reset_index()
    if 'Ticker' not in temp_df.columns:
        # Check if it was renamed to level_1 or similar by index reset
        # Or look for any level that looks like a ticker (all CAPS etc) - simpler just to rename index before reset
        log.debug(f"DEBUG: temp_df columns: {temp_df.columns.tolist()}")
        # Force name if possible
        if 'level_1' in temp_df.columns: temp_df.rename(columns={'level_1': 'Ticker'}, inplace=True)
        elif 'symbol' in temp_df.columns: temp_df.rename(columns={'symbol': 'Ticker'}, inplace=True)

    latest = temp_df.groupby('Ticker').tail(1)
    latest = latest.sort_values('Score', ascending=False)
    
    # 6. Calculate Target Weights (Top 5) & Update Risk Params
    MAX_POSITIONS = getattr(config, 'PORTFOLIO_SIZE', 5)
    MAX_SECTOR_POS = getattr(config, 'MAX_SECTOR_POSITIONS', 2)
    
    # --- CIRCUIT BREAKER (Drawdown Control) ---
    current_equity = portfolio.total_portfolio_value()
    # Calculate Peak Equity (Basitçe geçmiş loglardan veya mevcut değerden)
    # PortfolioState içinde 'peak_equity' yoksa şu anki ile başla veya historyden bul
    # Şimdilik basitlik adına: Eğer kayıtlı varsa kullan, yoksa current_equity
    if not hasattr(portfolio, 'peak_equity'):
        # Geçmiş işleme bakarak tahmini peak bulmaya çalışabiliriz ama riskli.
        # En güvenlisi: Kaydetmeye başla.
        portfolio.peak_equity = current_equity
    
    if current_equity > portfolio.peak_equity:
        portfolio.peak_equity = current_equity
        
    cb_action, cb_dd = risk_manager.check_portfolio_drawdown(current_equity, portfolio.peak_equity)
    
    if cb_action == 'STOP_TRADING':
        log.error(f"⚠️ CIRCUIT BREAKER TETİKLENDİ! Drawdown: {cb_dd:.2%}. Tüm pozisyonlar kapatılacak.")
        # Target weights 0 -> Engine hepsini satar
        top_picks = pd.DataFrame() 
        # Boş df dönersek aşağısı patlayabilir. 
        # Mevcut latest df'in kopyasını alıp weight=0 yapalım ki engine 'CLOSE' çalıştırsın.
        top_picks = latest.head(len(latest)).copy()
        top_picks['target_weight'] = 0.0
        
        # Sadece açık pozisyonları listeye eklemek yeterli
        open_symbols = portfolio.get_open_symbols()
        top_picks = top_picks[top_picks['Ticker'].isin(open_symbols)]
        
    else:
        # --- Normal Seçim (Sektör Filtreli) ---
        candidates = latest.sort_values('Score', ascending=False)
        selected_tickers = []
        sector_counts = {}
        
        for _, row in candidates.iterrows():
            if len(selected_tickers) >= MAX_POSITIONS:
                break
            
            ticker = row['Ticker']
            sector = config.get_sector(ticker)
            
            if sector_counts.get(sector, 0) < MAX_SECTOR_POS:
                selected_tickers.append(ticker)
                sector_counts[sector] = sector_counts.get(sector, 0) + 1
                
        top_picks = candidates[candidates['Ticker'].isin(selected_tickers)].copy()
        
        # A. Dinamik Risk Parametreleri (Sharpe Optimizer)
        try:
            current_stats = portfolio.get_trade_statistics()
            win_rate = current_stats.get('win_rate', 55.0) / 100.0 if current_stats.get('total_trades', 0) > 10 else 0.55
            avg_win = current_stats.get('avg_win', 0)
            avg_loss = abs(current_stats.get('avg_loss', 1)) 
            win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 2.0
            log.info(f"   Dynamic Risk Params: WinRate={win_rate:.2f}, W/L={win_loss_ratio:.2f}")
        except:
            win_rate, win_loss_ratio = 0.55, 2.0

        MIN_CONFIDENCE = float(health_rec.get("confidence_threshold", 0.55))
        
        # B. Weighting Strategy
        strategy = getattr(config, 'WEIGHTING_STRATEGY', 'RiskParity')
        
        if strategy == 'RiskParity':
            if 'Volatility_20' in top_picks.columns:
                inv_vol = 1.0 / (top_picks['Volatility_20'].replace(0, 0.01))
                total_inv_vol = inv_vol.sum()
                weights = inv_vol / total_inv_vol
                top_picks['target_weight'] = weights
            else:
                top_picks['target_weight'] = 1.0 / len(top_picks) if len(top_picks) > 0 else 0
                
        elif strategy == 'RankWeighted':
            n = len(top_picks)
            ranks = np.arange(1, n + 1)
            rank_sum = n * (n + 1) / 2
            weights = (n - ranks + 1) / rank_sum
            top_picks['target_weight'] = weights
            
        else:
             # Equal
             top_picks['target_weight'] = 1.0 / len(top_picks) if len(top_picks) > 0 else 0

        # Eğer Drawdown 'REDUCE_EXPOSURE' ise ağırlıkları düşür
        if cb_action == 'REDUCE_EXPOSURE':
            log.warning(f"⚠️ DRAWDOWN WARNING! Exposure azaltılıyor (%50). Mevcut DD: {cb_dd:.2%}")
            top_picks['target_weight'] *= 0.5
    
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
            price=price,
            win_rate=win_rate,
            win_loss_ratio=win_loss_ratio
        )
        
        action = decision['action']
        stats[action.lower()] = stats.get(action.lower(), 0) + 1
        
        if verbose and action != 'HOLD':
            log.info("   %-12s %-10s @ %.2f", action, ticker, price)
            
            # DB Log for trade
            if action in ['OPEN', 'SCALE_IN', 'SCALE_OUT', 'CLOSE']:
                side = 'BUY' if action in ['OPEN', 'SCALE_IN'] else 'SELL'
                amount = int(decision.get('qty', 0))
                db.save_data_raw = None # Skip existing save_data logic for trades
                with db.connection() as conn:
                    if conn:
                        cur = conn.cursor()
                        cur.execute("""
                            INSERT INTO trades (time, symbol, side, price, amount, strategy)
                            VALUES (%s, %s, %s, %s, %s, %s);
                        """, (datetime.now(), ticker, side, price, amount, "HybridEnsemble"))
                        conn.commit()
                        cur.close()
    
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
    log.info(f"   Portfolio: Cash={portfolio.cash:,.0f} TL | Positions={portfolio.position_count()} | Total={final_value:,.0f} TL | PnL={realized_pnl:,.2f} TL")
             
    # DB Log for Portfolio Stats
    db.save_portfolio_stats({
        'time': datetime.now(),
        'equity': final_value,
        'cash': portfolio.cash,
        'position_count': portfolio.position_count(),
        'exposure_ratio': portfolio.exposure_ratio(),
        'drawdown': cb_dd,
        'daily_return': (final_value / portfolio.initial_capital) - 1.0 # Simple return for now
    })
    
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
