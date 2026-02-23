"""
PositionAwareSession: Session management class for position-aware paper trading.

This module implements session management for paper trading by extracting
session initialization, signal generation, trade execution, and finalization
into separate methods.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime
import logging

from paper_trading.portfolio_state import PortfolioState
from core.risk_manager import RiskManager
from paper_trading.position_engine import PositionEngine
from paper_trading.position_logger import PositionLogger
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.regime_detector import RegimeDetector
import config
from utils.db_manager import DBManager

log = logging.getLogger(__name__)
db = DBManager()


class PositionAwareSession:
    """
    Manages position-aware trading session.
    
    This class orchestrates the complete paper trading workflow:
    1. Session initialization (portfolio, risk manager, engine)
    2. Signal generation (data loading, predictions, ranking)
    3. Trade execution (position management)
    4. Session finalization (state saving, reporting)
    """
    
    def __init__(
        self,
        portfolio: Optional[PortfolioState] = None,
        risk_manager: Optional[RiskManager] = None,
        verbose: bool = True
    ):
        """Initialize session with optional components."""
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        self.verbose = verbose
        
        # Components initialized during session
        self.engine = None
        self.trade_logger = None
        self.model = None
        self.regime_detector = None

    
    def run(self) -> Dict[str, Any]:
        """
        Execute complete trading session.
        
        Returns:
            Dictionary with session results (portfolio_value, realized_pnl, stats)
        """
        log.info("=" * 70)
        log.info("POSITION-AWARE PAPER TRADING (v3.0)")
        log.info("Date: %s", datetime.now().strftime('%Y-%m-%d %H:%M'))
        log.info("=" * 70)
        
        # Initialize session
        self._initialize_session()
        
        # Check strategy health
        can_trade, health_msg, health_rec = self._check_strategy_health()
        if not can_trade:
            log.error("Strategy health blocked trading. Session aborted.")
            return {'portfolio_value': 0, 'realized_pnl': 0, 'stats': {}}
        
        # Generate signals
        top_picks, win_rate, win_loss_ratio = self._generate_signals(health_rec)
        
        if top_picks is None or top_picks.empty:
            log.error("No signals generated")
            return {'portfolio_value': 0, 'realized_pnl': 0, 'stats': {}}
        
        # Execute trades
        stats = self._execute_trades(top_picks, win_rate, win_loss_ratio)
        
        # Finalize session
        results = self._finalize_session(stats)
        
        return results

    
    def _initialize_session(self) -> None:
        """Initialize session components."""
        # Load or use provided portfolio
        if self.portfolio is None:
            self.portfolio = PortfolioState.load()
        
        # Initialize or use provided risk manager
        if self.risk_manager is None:
            self.risk_manager = RiskManager()
        
        # Initialize engine and logger
        self.engine = PositionEngine(
            portfolio_state=self.portfolio,
            risk_manager=self.risk_manager
        )
        self.trade_logger = PositionLogger()
        
        # Initialize regime detector
        try:
            self.regime_detector = RegimeDetector(config)
        except Exception as e:
            log.warning(f"Regime detector initialization failed: {e}")
            self.regime_detector = None
        
        if self.verbose:
            log.info("Portfolio State (Start):")
            log.info(f"   Cash           : {self.portfolio.cash:,.0f} TL")
            log.info(f"   Positions      : {self.portfolio.position_count()}")
            log.info(f"   Total Value    : {self.portfolio.total_portfolio_value():,.0f} TL")
            log.info(f"   Exposure       : {self.portfolio.exposure_ratio() * 100:.1f}%")
    
    def _check_strategy_health(self) -> tuple:
        """
        Check strategy health and return trading permission.
        
        Returns:
            Tuple of (can_trade, health_msg, health_rec)
        """
        from paper_trading.strategy_health import check_strategy_health
        
        can_trade, health_msg, health_rec = check_strategy_health(self.portfolio)
        
        if self.verbose:
            log.info("Strategy Health: %s", health_msg)
            log.info("   Can Live Trade : %s", health_rec.get('can_live_trade'))
            log.info("   Paper Only     : %s", health_rec.get('paper_only_mode'))
            log.info("   Pos Size x     : %s", health_rec.get('position_size_multiplier'))
            log.info("   Conf Threshold : %s", health_rec.get('confidence_threshold'))
        
        return can_trade, health_msg, health_rec

    
    def _generate_signals(self, health_rec: Dict) -> tuple:
        """
        Generate trading signals from market data and model predictions.
        
        Args:
            health_rec: Health recommendation dictionary
            
        Returns:
            Tuple of (top_picks DataFrame, win_rate, win_loss_ratio)
        """
        # Load model
        log.info("Loading production model...")
        from paper_trading.position_runner import load_production_model
        self.model = load_production_model()
        
        # Detect market regime
        self._detect_market_regime()
        
        # Download and process market data
        all_data = self._load_market_data()
        
        if not all_data:
            log.error("No data available")
            return None, 0.55, 2.0
        
        log.info("Processed %d symbols", len(all_data))
        
        # Generate predictions
        top_picks = self._generate_predictions(all_data)
        
        # Calculate target weights
        top_picks = self._calculate_target_weights(top_picks, health_rec)
        
        # Calculate dynamic risk parameters
        win_rate, win_loss_ratio = self._calculate_risk_parameters()
        
        if self.verbose:
            self._log_target_portfolio(top_picks)
        
        return top_picks, win_rate, win_loss_ratio
    
    def _detect_market_regime(self) -> None:
        """Detect current market regime."""
        if self.regime_detector is None:
            return
        
        try:
            loader = DataLoader(start_date=config.START_DATE)
            benchmark_data = loader.get_benchmark_data()
            
            if benchmark_data is not None and not benchmark_data.empty:
                regime = self.regime_detector.detect_regime(benchmark_data.iloc[-1])
                log.info(f"🌍 MARKET REGIME: {regime}")
        except Exception as e:
            log.warning(f"Regime detection failed: {e}")
    
    def _load_market_data(self) -> Dict[str, pd.DataFrame]:
        """Load and process market data for all tickers."""
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
                df['Ticker'] = ticker
                all_data[ticker] = df
        
        return all_data

    
    def _generate_predictions(self, all_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Generate model predictions and rank symbols."""
        log.info("Running model predictions...")
        full_df = pd.concat(all_data.values())
        
        # Predict on full dataframe
        scores = self.model.predict(full_df)
        full_df['Score'] = scores
        
        # Get latest data point for each ticker
        temp_df = full_df.reset_index()
        
        # Ensure Ticker column exists
        if 'Ticker' not in temp_df.columns:
            if 'level_1' in temp_df.columns:
                temp_df.rename(columns={'level_1': 'Ticker'}, inplace=True)
            elif 'symbol' in temp_df.columns:
                temp_df.rename(columns={'symbol': 'Ticker'}, inplace=True)
        
        latest = temp_df.groupby('Ticker').tail(1)
        latest = latest.sort_values('Score', ascending=False)
        
        return latest
    
    def _calculate_target_weights(
        self, candidates: pd.DataFrame, health_rec: Dict
    ) -> pd.DataFrame:
        """Calculate target weights for top picks."""
        MAX_POSITIONS = getattr(config, 'PORTFOLIO_SIZE', 5)
        MAX_SECTOR_POS = getattr(config, 'MAX_SECTOR_POSITIONS', 2)
        
        # Check circuit breaker
        current_equity = self.portfolio.total_portfolio_value()
        
        # Initialize peak equity if not exists
        if not hasattr(self.portfolio, 'peak_equity'):
            self.portfolio.peak_equity = current_equity
        
        if current_equity > self.portfolio.peak_equity:
            self.portfolio.peak_equity = current_equity
        
        cb_action, cb_dd = self.risk_manager.check_portfolio_drawdown(
            current_equity, self.portfolio.peak_equity
        )
        
        # Handle circuit breaker
        if cb_action == 'STOP_TRADING':
            log.error(f"⚠️ CIRCUIT BREAKER TRIGGERED! Drawdown: {cb_dd:.2%}. Closing all positions.")
            return self._create_close_all_positions(candidates)
        
        # Select top picks with sector filtering
        top_picks = self._select_top_picks(candidates, MAX_POSITIONS, MAX_SECTOR_POS)
        
        # Apply weighting strategy
        top_picks = self._apply_weighting_strategy(top_picks)
        
        # Reduce exposure if needed
        if cb_action == 'REDUCE_EXPOSURE':
            log.warning(f"⚠️ DRAWDOWN WARNING! Reducing exposure by 50%. Current DD: {cb_dd:.2%}")
            top_picks['target_weight'] *= 0.5
        
        return top_picks

    
    def _create_close_all_positions(self, candidates: pd.DataFrame) -> pd.DataFrame:
        """Create DataFrame to close all open positions."""
        open_symbols = self.portfolio.get_open_symbols()
        top_picks = candidates[candidates['Ticker'].isin(open_symbols)].copy()
        top_picks['target_weight'] = 0.0
        return top_picks
    
    def _select_top_picks(
        self, candidates: pd.DataFrame, max_positions: int, max_sector_pos: int
    ) -> pd.DataFrame:
        """Select top picks with sector filtering."""
        selected_tickers = []
        sector_counts = {}
        
        for _, row in candidates.iterrows():
            if len(selected_tickers) >= max_positions:
                break
            
            ticker = row['Ticker']
            sector = config.get_sector(ticker)
            
            if sector_counts.get(sector, 0) < max_sector_pos:
                selected_tickers.append(ticker)
                sector_counts[sector] = sector_counts.get(sector, 0) + 1
        
        return candidates[candidates['Ticker'].isin(selected_tickers)].copy()
    
    def _apply_weighting_strategy(self, top_picks: pd.DataFrame) -> pd.DataFrame:
        """Apply weighting strategy to top picks."""
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
            import numpy as np
            n = len(top_picks)
            ranks = np.arange(1, n + 1)
            rank_sum = n * (n + 1) / 2
            weights = (n - ranks + 1) / rank_sum
            top_picks['target_weight'] = weights
        
        else:  # Equal weight
            top_picks['target_weight'] = 1.0 / len(top_picks) if len(top_picks) > 0 else 0
        
        return top_picks
    
    def _calculate_risk_parameters(self) -> tuple:
        """Calculate dynamic risk parameters from portfolio statistics."""
        try:
            current_stats = self.portfolio.get_trade_statistics()
            win_rate = current_stats.get('win_rate', 55.0) / 100.0 \
                if current_stats.get('total_trades', 0) > 10 else 0.55
            avg_win = current_stats.get('avg_win', 0)
            avg_loss = abs(current_stats.get('avg_loss', 1))
            win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 2.0
            
            if self.verbose:
                log.info(f"   Dynamic Risk Params: WinRate={win_rate:.2f}, W/L={win_loss_ratio:.2f}")
            
            return win_rate, win_loss_ratio
        except:
            return 0.55, 2.0
    
    def _log_target_portfolio(self, top_picks: pd.DataFrame) -> None:
        """Log target portfolio information."""
        MAX_POSITIONS = getattr(config, 'PORTFOLIO_SIZE', 5)
        log.info("Target Portfolio (Top %d):", MAX_POSITIONS)
        
        for _, row in top_picks.iterrows():
            ticker = row['Ticker']
            score = row['Score']
            weight = row['target_weight']
            price = row['Close']
            log.info("   %s | Score: %.2f | Weight: %5.1f%% | Price: %.2f",
                     ticker, score, weight * 100, price)

    
    def _execute_trades(
        self, top_picks: pd.DataFrame, win_rate: float, win_loss_ratio: float
    ) -> Dict[str, int]:
        """
        Execute trades based on target portfolio.
        
        Returns:
            Dictionary with trade statistics
        """
        log.info("Executing trades...")
        
        stats = {'open': 0, 'scale_in': 0, 'scale_out': 0, 'close': 0, 'hold': 0}
        
        # Execute trades for target positions
        for _, row in top_picks.iterrows():
            ticker = row['Ticker']
            target_weight = row['target_weight']
            confidence = row['Score']
            price = row['Close']
            
            decision = self.engine.process_signal(
                symbol=ticker,
                target_weight=target_weight,
                confidence=confidence,
                price=price,
                win_rate=win_rate,
                win_loss_ratio=win_loss_ratio
            )
            
            action = decision['action']
            stats[action.lower()] = stats.get(action.lower(), 0) + 1
            
            if self.verbose and action != 'HOLD':
                log.info("   %-12s %-10s @ %.2f", action, ticker, price)
            
            # Log trade to database
            self._log_trade_to_db(action, ticker, price, decision)
        
        # Close unwanted positions
        self._close_unwanted_positions(top_picks, stats)
        
        return stats
    
    def _log_trade_to_db(
        self, action: str, ticker: str, price: float, decision: Dict
    ) -> None:
        """Log trade to database."""
        if action not in ['OPEN', 'SCALE_IN', 'SCALE_OUT', 'CLOSE']:
            return
        
        try:
            side = 'BUY' if action in ['OPEN', 'SCALE_IN'] else 'SELL'
            amount = int(decision.get('qty', 0))
            
            with db.connection() as conn:
                if conn:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO trades (time, symbol, side, price, amount, strategy)
                        VALUES (%s, %s, %s, %s, %s, %s);
                    """, (datetime.now(), ticker, side, price, amount, "HybridEnsemble"))
                    conn.commit()
                    cur.close()
        except Exception as e:
            log.warning(f"Failed to log trade to DB: {e}")
    
    def _close_unwanted_positions(
        self, top_picks: pd.DataFrame, stats: Dict[str, int]
    ) -> None:
        """Close positions not in target portfolio."""
        log.info("Cleaning up positions...")
        allowed_symbols = top_picks['Ticker'].tolist()
        current_positions = self.portfolio.get_open_symbols()
        
        for symbol in current_positions:
            if symbol not in allowed_symbols:
                price = self.portfolio.get_last_price(symbol)
                self.engine.process_signal(
                    symbol=symbol,
                    target_weight=0.0,
                    confidence=0.0,
                    price=price
                )
                stats['close'] = stats.get('close', 0) + 1
                
                if self.verbose:
                    log.info("   CLOSE        %-10s @ %.2f", symbol, price)

    def _finalize_session(self, stats: Dict[str, int]) -> Dict[str, Any]:
        """
        Finalize trading session and save results.
        
        Args:
            stats: Trade statistics dictionary
            
        Returns:
            Dictionary with session results
        """
        # Save portfolio state
        self.portfolio.save()
        
        # Calculate final portfolio metrics
        final_value = self.portfolio.total_portfolio_value()
        realized_pnl = self.portfolio.realized_pnl
        
        # Log session summary
        if self.verbose:
            log.info("=" * 70)
            log.info("SESSION SUMMARY")
            log.info("=" * 70)
            log.info("Trade Actions:")
            log.info("   Open       : %d", stats.get('open', 0))
            log.info("   Scale In   : %d", stats.get('scale_in', 0))
            log.info("   Scale Out  : %d", stats.get('scale_out', 0))
            log.info("   Close      : %d", stats.get('close', 0))
            log.info("   Hold       : %d", stats.get('hold', 0))
            log.info("")
            log.info("Portfolio State (End):")
            log.info("   Cash           : %,.0f TL", self.portfolio.cash)
            log.info("   Positions      : %d", self.portfolio.position_count())
            log.info("   Total Value    : %,.0f TL", final_value)
            log.info("   Exposure       : %.1f%%", self.portfolio.exposure_ratio() * 100)
            log.info("   Realized PnL   : %,.0f TL", realized_pnl)
            log.info("=" * 70)
        
        # Save portfolio stats to database
        self._save_portfolio_stats_to_db(final_value, realized_pnl, stats)
        
        # Return results
        return {
            'portfolio_value': final_value,
            'realized_pnl': realized_pnl,
            'stats': stats
        }
    
    def _save_portfolio_stats_to_db(
        self, portfolio_value: float, realized_pnl: float, stats: Dict[str, int]
    ) -> None:
        """Save portfolio statistics to database."""
        try:
            with db.connection() as conn:
                if conn:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO portfolio_stats 
                        (time, total_value, cash, realized_pnl, position_count, 
                         exposure_ratio, open_trades, scale_in_trades, 
                         scale_out_trades, close_trades)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        datetime.now(),
                        portfolio_value,
                        self.portfolio.cash,
                        realized_pnl,
                        self.portfolio.position_count(),
                        self.portfolio.exposure_ratio(),
                        stats.get('open', 0),
                        stats.get('scale_in', 0),
                        stats.get('scale_out', 0),
                        stats.get('close', 0)
                    ))
                    conn.commit()
                    cur.close()
        except Exception as e:
            log.warning(f"Failed to save portfolio stats to DB: {e}")
