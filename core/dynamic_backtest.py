"""
Dinamik Backtest Modülü - Optimize Edilmiş Versiyon
Toplu veri indirme + Disk cache kullanarak hızlandırılmış.
"""

import sys
import os
from typing import Dict, Any, Optional

# Project imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging_config import get_logger

log = get_logger(__name__)


class DynamicBacktest:
    def __init__(self, config):
        self.config = config
        self.trading_dates = []
        
        # Initialize Regime Detector
        if getattr(config, 'USE_ADAPTIVE_REGIME', True):
            try:
                from models.regime_detector import RegimeDetector
                self.regime_detector = RegimeDetector(config)
                log.info("✅ RegimeDetector entegre edildi (DynamicBacktest)")
            except Exception as e:
                log.warning(f"⚠️ RegimeDetector başlatılamadı: {e}")
                self.regime_detector = None
        else:
            self.regime_detector = None
            log.warning("⚠️ RegimeDetector devre dışı")

def run_dynamic_backtest(
    train_start: str,
    train_end: str,
    test_end: str,
    initial_capital: float = 100000,
    progress_callback: Optional[callable] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Dinamik tarihlerle model eğitip backtest çalıştırır.
    
    Delegates to DynamicBacktestRunner class for execution.
    
    Args:
        train_start: Training start date (YYYY-MM-DD)
        train_end: Training end date (YYYY-MM-DD)
        test_end: Test end date (YYYY-MM-DD)
        initial_capital: Initial capital for backtest
        progress_callback: Optional callback for progress updates
        use_cache: Whether to use cached data
        
    Returns:
        Dictionary with backtest results
    """
    from core.dynamic_backtest_runner import DynamicBacktestRunner
    
    # Create and run backtest
    runner = DynamicBacktestRunner(
        train_start=train_start,
        train_end=train_end,
        test_end=test_end,
        initial_capital=initial_capital,
        use_cache=use_cache
    )
    
    result = runner.run(progress_callback=progress_callback)
    
    return result

if __name__ == "__main__":
    result = run_dynamic_backtest(
        train_start="2015-01-01",
        train_end="2021-01-01",
        test_end="2024-12-31",
        initial_capital=100000,
        use_cache=True
    )
    
    if result["success"]:
        log.info("\n" + "="*50)
        log.info("BACKTEST SONUÇLARI")
        log.info("="*50)
        for key, value in result["metrics"].items():
            log.info(f"  {key}: {value}")
    else:
        log.error(f"HATA: {result['error']}")
