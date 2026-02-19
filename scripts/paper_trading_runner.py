import sys
import os
import time
import schedule
from datetime import datetime
import logging

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_trading.position_runner import run_position_aware_session
from utils.logging_config import get_logger
import config
from models.regime_detector import RegimeDetector

log = get_logger(__name__)

def run_trading_cycle():
    """Execute one trading cycle"""
    log.info(f"🚀 Starting trading cycle at {datetime.now()}")
    try:
        # Initialize Regime Detector for logging
        rd = RegimeDetector(config)
        log.info(f"🛡️ Regime Detector Initialized. Thresholds: {rd.thresholds}")

        # Run the position-aware session
        result = run_position_aware_session(verbose=True)
        log.info(f"✅ Trading cycle completed. Portfolio Value: {result.get('portfolio_value', 0):,.2f} TL")
    except Exception as e:
        log.error(f"❌ Trading cycle failed: {e}", exc_info=True)

def main():
    """Main loop for paper trading"""
    log.info("🤖 Paper Trading Runner Started")
    
    # Run immediately on startup
    run_trading_cycle()
    
    # Schedule daily runs
    schedule.every().day.at("18:15").do(run_trading_cycle) # After close
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
