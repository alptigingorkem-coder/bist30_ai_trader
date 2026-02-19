
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from paper_trading.position_engine import PositionEngine
from paper_trading.portfolio_state import PortfolioState
from core.risk_manager import RiskManager
import config

class TestSharpeImprovement(unittest.TestCase):
    def setUp(self):
        self.portfolio = MagicMock(spec=PortfolioState)
        self.risk_manager = RiskManager()
        self.engine = PositionEngine(self.portfolio, self.risk_manager)
        
        # Mock portfolio methods
        self.portfolio.current_weight.return_value = 0.0
        self.portfolio.total_portfolio_value.return_value = 100000.0
        self.portfolio.get_open_symbols.return_value = []
        
        # Config mock
        config.WEIGHTING_STRATEGY = 'RiskParity'

    def test_dynamic_risk_params(self):
        """Test if calculate_position_size accepts dynamic params"""
        # Case 1: Default
        size_default = self.risk_manager.calculate_position_size(100000, 10, 0.2)
        
        # Case 2: High Win Rate (Should be higher/same size but restricted by max allocation)
        size_high_wr = self.risk_manager.calculate_position_size(100000, 10, 0.2, win_rate=0.8, win_loss_ratio=2.0)
        
        # Case 3: Low Win Rate (Should be 0)
        size_low_wr = self.risk_manager.calculate_position_size(100000, 10, 0.2, win_rate=0.3, win_loss_ratio=1.0)
        
        print(f"Default Size: {size_default}, High WR Size: {size_high_wr}, Low WR Size: {size_low_wr}")
        self.assertTrue(size_high_wr >= size_default)
        self.assertEqual(size_low_wr, 0)

    def test_process_signal_signature(self):
        """Test if process_signal accepts new arguments"""
        try:
            decision = self.engine.process_signal(
                symbol="TEST.IS",
                target_weight=0.2,
                confidence=0.8,
                price=10.0,
                win_rate=0.6,
                win_loss_ratio=1.5
            )
            print("Process Signal Decision:", decision)
            self.assertEqual(decision['action'], 'OPEN')
        except TypeError as e:
            self.fail(f"process_signal raised TypeError: {e}")

if __name__ == '__main__':
    unittest.main()
