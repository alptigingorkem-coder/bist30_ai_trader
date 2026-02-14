
import unittest
import numpy as np
from core.risk_manager import RiskManager
import config

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager()

    def test_adjust_for_regime(self):
        # Default
        default_sl = self.rm.stop_loss_mult
        
        # Crash
        self.rm.adjust_for_regime('Crash_Bear')
        self.assertEqual(self.rm.stop_loss_mult, 1.5)
        self.assertEqual(self.rm.trailing_stop_mult, 1.0)
        
        # Sideways
        self.rm.adjust_for_regime('Sideways')
        self.assertEqual(self.rm.stop_loss_mult, 2.0)
        
        # Back to Trend/Default (Assuming config default is around 3.0)
        self.rm.adjust_for_regime('Trend_Up')
        self.assertEqual(self.rm.stop_loss_mult, config.ATR_STOP_LOSS_MULTIPLIER)

    def test_check_exit_conditions_stop_loss(self):
        # Entry: 100, Stop Mult: 3, ATR: 2 => Stop Distance = 6 => Stop Price = 94
        self.rm.stop_loss_mult = 3.0
        entry_price = 100
        atr = 2.0
        
        # Price drops to 93 (below 94)
        action, reason = self.rm.check_exit_conditions(
            current_price=93, 
            entry_price=entry_price, 
            peak_price=100, 
            atr=atr, 
            days_held=1
        )
        self.assertEqual(action, 'SELL')
        self.assertEqual(reason, 'STOP_LOSS')
        
        # Price at 95 (above 94)
        action, reason = self.rm.check_exit_conditions(95, entry_price, 100, atr, 1)
        self.assertEqual(action, 'HOLD')

    def test_check_exit_conditions_trailing_stop(self):
        # Trailing Active
        self.rm.trailing_active = True
        self.rm.trailing_stop_mult = 2.0
        atr = 2.0
        
        # Price goes up to 120 (Peak)
        # Trailing Stop = 120 - (2 * 2) = 116
        
        # Price drops to 115
        action, reason = self.rm.check_exit_conditions(
            current_price=115, 
            entry_price=100, 
            peak_price=120, 
            atr=atr, 
            days_held=5
        )
        self.assertEqual(action, 'SELL')
        self.assertEqual(reason, 'TRAILING_STOP')

    def test_calculate_position_size(self):
        capital = 100000
        price = 10
        atr = 0.5
        win_rate = 0.6
        
        # Normal inputs
        size = self.rm.calculate_position_size(capital, price, atr, win_rate)
        self.assertGreater(size, 0)
        self.assertIsInstance(size, int)
        
        # Zero ATR or Price
        self.assertEqual(self.rm.calculate_position_size(capital, 10, 0), 0)
        
        # Negative Kelly (Win rate 0.1)
        self.assertEqual(self.rm.calculate_position_size(capital, 10, 0.5, win_rate=0.1), 0)

if __name__ == "__main__":
    unittest.main()
