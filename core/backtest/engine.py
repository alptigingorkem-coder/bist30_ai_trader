"""
Backtest Engine Mixin
Event-driven backtesting motoru: run_backtest, slippage, market impact.
"""
import pandas as pd
import numpy as np
import config
from typing import Optional, Union, Dict, Any


class BacktestEngineMixin:
    """Backtest motoru metotlarını sağlayan mixin."""

    def calculate_slippage(self, volume: float, avg_volume: float, position_size_qty: float) -> float:
        """
        FIX 19: Gerçekçi slippage hesabı (Spread + Market Impact).
        Kümülatif maliyet oranını döner.
        """
        if pd.isna(volume) or pd.isna(avg_volume) or avg_volume == 0:
            return 0.001

        volume_ratio = position_size_qty / avg_volume
        
        # 1. Base Spread (Liquidity based)
        base_slippage = 0.0005
        if volume_ratio < 0.01:
            base_slippage = 0.0002
        elif volume_ratio < 0.05:
            base_slippage = 0.0005
        else:
            base_slippage = 0.001

        # 2. Market Impact (Size based)
        # Kurumsal Denetim: Double Counting'i önlemek için impact buraya dahil edildi.
        market_impact = 0.0
        if volume_ratio > 0.10:
            # Her %10 fazlalık için %5 impact (Kurumsal Düzeltme)
            # Örnek: %50 volume -> (0.5 - 0.1) * 0.05 = 0.02 (%2)
            market_impact = (volume_ratio - 0.10) * 0.05
            
        return base_slippage + market_impact



    def _get_market_indicators(self, current_slice: pd.DataFrame) -> pd.DataFrame:
        """
        Rejim tespiti için gerekli market-wide göstergeleri hazırla.
        Single-asset modunda olduğumuz için mevcut df slice'ı kullanıyoruz.
        Bu df zaten VIX, USDTRY vb. makro verileri içeriyor olmalı.
        """
        return current_slice


    def run_backtest(
        self, 
        signals_or_weights: Optional[pd.Series] = None, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None, 
        override_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Event-driven Backtest with Risk Management.
        
        This method has been refactored to use BacktestStrategy for improved
        maintainability and reduced complexity.
        
        Args:
            signals_or_weights: Series of 1/0 for Signals or floats (0.0-1.0) for Weights
            start_date: Optional start date for backtest
            end_date: Optional end date for backtest
            override_data: Optional data override for stress testing
            
        Returns:
            DataFrame with backtest results
        """
        from core.risk_manager import RiskManager
        from models.regime_detector import RegimeDetector
        from core.execution import ExecutionManager, SmartOrderRouter
        from core.backtest.backtest_strategy import BacktestStrategy, BacktestConfig
        
        # Prepare data
        data = self._prepare_backtest_data(override_data, start_date, end_date)
        
        # Initialize components
        risk_manager = RiskManager()
        regime_detector = self._initialize_regime_detector()
        exec_manager, router = self._initialize_execution_components()
        
        # Create backtest configuration
        backtest_config = BacktestConfig(
            initial_capital=self.initial_capital,
            commission=getattr(self, 'commission', 0.002),
            max_drawdown_limit=getattr(config, 'MAX_DRAWDOWN_LIMIT', 0.30),
            enable_risk_sizing=getattr(config, 'ENABLE_RISK_SIZING', False),
            enable_kelly=getattr(config, 'ENABLE_KELLY', True),
            risk_per_trade=getattr(config, 'RISK_PER_TRADE', 0.02),
            max_single_pos_weight=getattr(config, 'MAX_SINGLE_POS_WEIGHT', 0.20),
            min_holding_days=getattr(config, 'MIN_HOLDING_DAYS', 0)
        )
        
        # Create and run backtest strategy
        strategy = BacktestStrategy(backtest_config)
        
        print("  Regime Detection Running...")
        
        results = strategy.run(
            data=data,
            signals_or_weights=signals_or_weights,
            risk_manager=risk_manager,
            regime_detector=regime_detector,
            position_sizer=getattr(self, 'position_sizer', None),
            execution_manager=exec_manager,
            router=router
        )
        
        # Store results for compatibility
        self.results = results
        
        return results
    
    def _prepare_backtest_data(
        self,
        override_data: Optional[pd.DataFrame],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """Prepare and filter data for backtest."""
        # Use override data if provided
        if override_data is not None:
            data = override_data.copy()
        else:
            data = self.data.copy()
        
        # Apply date filters
        if start_date:
            start_date = pd.to_datetime(start_date)
            if isinstance(data.index, pd.MultiIndex):
                data = data[data.index.get_level_values('Date') >= start_date]
            else:
                data = data[data.index >= start_date]
        
        if end_date:
            end_date = pd.to_datetime(end_date)
            if isinstance(data.index, pd.MultiIndex):
                data = data[data.index.get_level_values('Date') <= end_date]
            else:
                data = data[data.index <= end_date]
        
        return data
    
    def _initialize_regime_detector(self):
        """Initialize regime detector with configuration."""
        from models.regime_detector import RegimeDetector
        
        regime_config = {
            'REGIME_THRESHOLDS': getattr(config, 'REGIME_THRESHOLDS', {}),
            'REGIME_ACTIONS': getattr(config, 'REGIME_ACTIONS', {})
        }
        return RegimeDetector(regime_config)
    
    def _initialize_execution_components(self):
        """Initialize execution manager and smart order router."""
        from core.execution import ExecutionManager, SmartOrderRouter
        
        exec_manager = ExecutionManager(commission_rate=getattr(self, 'commission', 0.002))
        router = SmartOrderRouter(exec_manager)
        
        return exec_manager, router

