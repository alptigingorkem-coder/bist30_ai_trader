"""
BacktestCommand - Command pattern for backtest orchestration.

This module implements the Command pattern to orchestrate backtest execution.
It breaks down the complex main() function into manageable, testable components.
"""

import os
import sys
import argparse
import joblib
import pandas as pd
import torch
from typing import Dict, Optional, Tuple, Any

import config
from core.backtesting import Backtester
from core.macro_gate import vectorized_macro_gate
from models.ranking_model import RankingModel
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from utils.logging_config import get_logger

log = get_logger(__name__)


class BacktestCommand:
    """
    Command class for orchestrating backtest execution.
    
    Responsibilities:
    - Parse command-line arguments
    - Load configuration
    - Load models
    - Load and process data
    - Execute backtest
    - Generate reports
    
    This class follows the Command pattern to encapsulate backtest execution
    as a single operation with clear steps.
    """
    
    def __init__(self, args: Optional[argparse.Namespace] = None):
        """
        Initialize BacktestCommand.
        
        Args:
            args: Parsed command-line arguments (optional, will parse if None)
        """
        self.args = args or self._parse_arguments()
        self.config = config
        self.ranker = None
        self.data_loader = None
        self.all_data = {}
        self.xu100_data = None
        
        log.info(f"BacktestCommand initialized: mode={self.args.mode}, model={self.args.model}")
    
    def execute(self) -> int:
        """
        Execute the backtest command.
        
        This is the main entry point that orchestrates all steps.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            log.info("="*50)
            log.info(f"BIST30 AI TRADER - DAILY RANKING BACKTEST ({self.args.mode.upper()})")
            log.info(f"Model: {self.args.model.upper()}")
            log.info("="*50)
            
            # Execute steps in sequence
            self._setup_environment()
            self._load_configuration()
            self._load_model()
            self._load_data()
            self._run_backtest()
            self._generate_report()
            
            log.info("✅ Backtest completed successfully")
            return 0
            
        except Exception as e:
            log.error(f"❌ Backtest failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    # ─────────────────────────────────────────────────────────────
    # PRIVATE STEP METHODS
    # ─────────────────────────────────────────────────────────────
    
    def _parse_arguments(self) -> argparse.Namespace:
        """
        Parse command-line arguments.
        
        Returns:
            Parsed arguments
        """
        parser = argparse.ArgumentParser(description='Run BIST30 AI Trader Backtest')
        parser.add_argument(
            '--mode', 
            type=str, 
            default='oos', 
            choices=['oos', 'is'],
            help='Backtest mode: oos (out-of-sample) or is (in-sample)'
        )
        parser.add_argument(
            '--model', 
            type=str, 
            default='lightgbm', 
            choices=['lightgbm', 'catboost', 'ensemble'],
            help='Model type to use'
        )
        return parser.parse_args()
    
    def _setup_environment(self):
        """Setup environment (create directories, etc.)."""
        if not os.path.exists("reports"):
            os.makedirs("reports")
            log.info("Created reports directory")
    
    def _load_configuration(self):
        """
        Load and validate configuration.
        
        Logs configuration details for debugging.
        """
        log.info("✅ Config loaded")
        
        # Log regime system configuration
        use_adaptive = getattr(self.config, 'USE_ADAPTIVE_REGIME', False)
        thresholds = getattr(self.config, 'REGIME_THRESHOLDS', {})
        actions = getattr(self.config, 'REGIME_ACTIONS', {})
        
        log.info(f"🔍 Adaptive Regime: {use_adaptive}")
        log.info(f"📊 Regime Thresholds: {thresholds}")
        log.info(f"⚙️ Regime Actions: {actions}")
        
        if use_adaptive:
            log.info("✅ Regime-based risk management ACTIVE")
        else:
            log.warning("⚠️ WARNING: Regime detection disabled!")
    
    def _load_model(self):
        """
        Load the ranking model based on args.model.
        
        Raises:
            FileNotFoundError: If model file not found
            Exception: If model loading fails
        """
        log.info(f"Loading {self.args.model.upper()} model...")
        
        try:
            if self.args.model == 'lightgbm':
                self.ranker = RankingModel.load(
                    "models/saved/global_ranker.pkl", 
                    self.config
                )
                
            elif self.args.model == 'catboost':
                from models.ranking_model_catboost import CatBoostRankingModel
                self.ranker = CatBoostRankingModel.load(
                    "models/saved/global_ranker_catboost.cbm", 
                    self.config
                )
                
            elif self.args.model == 'ensemble':
                from models.ensemble_model import HybridEnsemble
                self.ranker = HybridEnsemble()
                
                # Model paths
                lgbm_path = "models/saved/global_ranker.pkl"
                tft_path = "models/saved/tft_model.pth"
                tft_config_path = "models/saved/tft_config.joblib"
                catboost_path = "models/saved/global_ranker_catboost.cbm"
                
                # Load TFT config
                tft_config = None
                if os.path.exists(tft_config_path):
                    tft_config = joblib.load(tft_config_path)
                else:
                    tft_config = self.config
                
                # Load all models
                self.ranker.load_models(
                    lgbm_path, 
                    tft_path, 
                    tft_config=tft_config, 
                    catboost_path=catboost_path
                )
                log.info("✅ Hybrid Ensemble (LightGBM + TFT + CatBoost) loaded")
            
            if self.ranker is None:
                raise FileNotFoundError(f"Model {self.args.model} not found")
            
            log.info(f"✅ {self.args.model.upper()} Ranking Model loaded")
            
        except Exception as e:
            log.error(f"❌ {self.args.model.upper()} Model loading failed: {e}")
            raise
    
    def _load_data(self):
        """
        Load and process all required data.
        
        This includes:
        - Stock data for all tickers
        - Benchmark data (XU100)
        - Macro data
        - Feature engineering
        """
        log.info("Loading data...")
        
        tickers = self.config.TICKERS
        self.data_loader = DataLoader(start_date=self.config.START_DATE)
        
        # Load benchmark data
        self.xu100_data = self.data_loader.fetch_stock_data("XU100.IS")
        if self.xu100_data is not None:
            log.info(f"✅ XU100 benchmark loaded: {len(self.xu100_data)} rows")
        else:
            log.warning("⚠️ XU100 benchmark data not available")
        
        # Load stock data for all tickers
        log.info(f"Loading data for {len(tickers)} tickers...")
        for ticker in tickers:
            try:
                data = self.data_loader.get_combined_data(ticker)
                if data is not None and not data.empty:
                    self.all_data[ticker] = data
                    log.debug(f"✅ {ticker}: {len(data)} rows")
                else:
                    log.warning(f"⚠️ {ticker}: No data")
            except Exception as e:
                log.error(f"❌ {ticker}: Error loading data: {e}")
        
        log.info(f"✅ Data loaded for {len(self.all_data)}/{len(tickers)} tickers")
        
        if not self.all_data:
            raise ValueError("No data loaded for any ticker")
    
    def _run_backtest(self):
        """
        Run the backtest.
        
        This is a placeholder for the actual backtest logic.
        The full implementation would include:
        - Regime detection
        - Score prediction
        - Portfolio allocation
        - Backtest execution
        """
        log.info("Running backtest...")
        
        # TODO: Implement full backtest logic
        # This would include:
        # 1. Detect market regimes
        # 2. Predict scores (regime-conditional)
        # 3. Allocate portfolio (top N)
        # 4. Filter weights based on frequency
        # 5. Run backtests
        # 6. Aggregate results
        
        log.warning("⚠️ Backtest logic not yet implemented in BacktestCommand")
        log.info("This is a refactored structure - full logic to be migrated")
    
    def _generate_report(self):
        """
        Generate backtest report.
        
        This is a placeholder for report generation logic.
        """
        log.info("Generating report...")
        
        # TODO: Implement report generation
        # This would include:
        # - Performance metrics
        # - Trade statistics
        # - Visualizations
        # - Export to files
        
        log.warning("⚠️ Report generation not yet implemented in BacktestCommand")


def main():
    """
    Main entry point for backtest execution.
    
    This function creates and executes a BacktestCommand.
    """
    command = BacktestCommand()
    exit_code = command.execute()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
