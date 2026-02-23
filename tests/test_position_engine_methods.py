"""
Tests for PositionEngine extracted methods.

This module tests the private methods extracted during Task 11.1 refactoring.
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from paper_trading.position_engine import PositionEngine


class TestPositionEngineHelperMethods(unittest.TestCase):
    """Test helper methods extracted from process_signal."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.portfolio = Mock()
        self.portfolio.current_weight = Mock(return_value=0.10)
        self.portfolio.total_portfolio_value = Mock(return_value=100000.0)
        
        self.risk_manager = Mock()
        
        self.engine = PositionEngine(
            self.portfolio,
            self.risk_manager,
            min_weight_change=0.03
        )
    
    def test_create_base_decision(self):
        """Test _create_base_decision creates correct structure."""
        decision = self.engine._create_base_decision(
            symbol='THYAO',
            price=50.0,
            current_weight=0.10,
            target_weight=0.15,
            confidence=0.75
        )
        
        self.assertEqual(decision['symbol'], 'THYAO')
        self.assertEqual(decision['price'], 50.0)
        self.assertEqual(decision['current_weight'], 0.10)
        self.assertEqual(decision['target_weight'], 0.15)
        self.assertEqual(decision['confidence'], 0.75)
        self.assertEqual(decision['action'], 'HOLD')
        self.assertEqual(decision['quantity'], 0)
        self.assertIn('timestamp', decision)
    
    def test_should_close_position_true(self):
        """Test _should_close_position returns True."""
        result = self.engine._should_close_position(
            target_weight=0.0,
            current_weight=0.10
        )
        
        self.assertTrue(result)
    
    def test_should_close_position_false(self):
        """Test _should_close_position returns False."""
        result = self.engine._should_close_position(
            target_weight=0.05,
            current_weight=0.10
        )
        
        self.assertFalse(result)
    
    def test_should_hold_true(self):
        """Test _should_hold returns True for small change."""
        result = self.engine._should_hold(weight_diff=0.02)
        
        self.assertTrue(result)
    
    def test_should_hold_false(self):
        """Test _should_hold returns False for large change."""
        result = self.engine._should_hold(weight_diff=0.05)
        
        self.assertFalse(result)
    
    def test_should_scale_in_true(self):
        """Test _should_scale_in returns True."""
        result = self.engine._should_scale_in(weight_diff=0.05)
        
        self.assertTrue(result)
    
    def test_should_scale_in_false(self):
        """Test _should_scale_in returns False."""
        result = self.engine._should_scale_in(weight_diff=-0.05)
        
        self.assertFalse(result)
    
    def test_should_scale_out_true(self):
        """Test _should_scale_out returns True."""
        result = self.engine._should_scale_out(weight_diff=-0.05)
        
        self.assertTrue(result)
    
    def test_should_scale_out_false(self):
        """Test _should_scale_out returns False."""
        result = self.engine._should_scale_out(weight_diff=0.05)
        
        self.assertFalse(result)
    
    def test_execute_close(self):
        """Test _execute_close closes position."""
        decision = {
            'action': 'HOLD',
            'reason': ''
        }
        
        result = self.engine._execute_close(decision, 'THYAO', 50.0)
        
        self.assertEqual(result['action'], 'CLOSE')
        self.assertEqual(result['reason'], 'Target weight is zero')
        self.portfolio.close_position.assert_called_once_with('THYAO', 50.0)
    
    def test_execute_scale_in_new_position(self):
        """Test _execute_scale_in for new position."""
        decision = {
            'action': 'HOLD',
            'quantity': 0,
            'reason': ''
        }
        
        result = self.engine._execute_scale_in(
            decision, 'THYAO', 50.0, 
            weight_diff=0.05, 
            current_weight=0.0
        )
        
        self.assertEqual(result['action'], 'OPEN')
        self.assertEqual(result['reason'], 'Increasing position towards target weight')
        self.assertGreater(result['quantity'], 0)
        
        # Check portfolio method called
        self.portfolio.open_or_add.assert_called_once()
    
    def test_execute_scale_in_existing_position(self):
        """Test _execute_scale_in for existing position."""
        decision = {
            'action': 'HOLD',
            'quantity': 0,
            'reason': ''
        }
        
        result = self.engine._execute_scale_in(
            decision, 'THYAO', 50.0,
            weight_diff=0.05,
            current_weight=0.10
        )
        
        self.assertEqual(result['action'], 'SCALE_IN')
        self.assertEqual(result['reason'], 'Increasing position towards target weight')
        self.assertGreater(result['quantity'], 0)
    
    def test_execute_scale_out(self):
        """Test _execute_scale_out reduces position."""
        decision = {
            'action': 'HOLD',
            'quantity': 0,
            'reason': ''
        }
        
        result = self.engine._execute_scale_out(
            decision, 'THYAO', 50.0,
            weight_diff=-0.05,
            current_weight=0.15
        )
        
        self.assertEqual(result['action'], 'SCALE_OUT')
        self.assertEqual(result['reason'], 'Reducing position towards target weight')
        self.assertGreater(result['quantity'], 0)
        
        # Check portfolio method called
        self.portfolio.reduce_position.assert_called_once()


class TestPositionEngineProcessSignalFlow(unittest.TestCase):
    """Test complete process_signal flow with extracted methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.portfolio = Mock()
        self.portfolio.total_portfolio_value = Mock(return_value=100000.0)
        
        self.risk_manager = Mock()
        
        self.engine = PositionEngine(
            self.portfolio,
            self.risk_manager,
            min_weight_change=0.03
        )
    
    def test_process_signal_close(self):
        """Test process_signal closes position."""
        self.portfolio.current_weight = Mock(return_value=0.10)
        
        decision = self.engine.process_signal(
            symbol='THYAO',
            target_weight=0.0,
            confidence=0.75,
            price=50.0
        )
        
        self.assertEqual(decision['action'], 'CLOSE')
        self.portfolio.close_position.assert_called_once()
    
    def test_process_signal_hold(self):
        """Test process_signal holds position."""
        self.portfolio.current_weight = Mock(return_value=0.10)
        
        decision = self.engine.process_signal(
            symbol='THYAO',
            target_weight=0.11,  # Small change
            confidence=0.75,
            price=50.0
        )
        
        self.assertEqual(decision['action'], 'HOLD')
        self.assertIn('below threshold', decision['reason'])
    
    def test_process_signal_scale_in(self):
        """Test process_signal scales in."""
        self.portfolio.current_weight = Mock(return_value=0.10)
        
        decision = self.engine.process_signal(
            symbol='THYAO',
            target_weight=0.20,  # Large increase
            confidence=0.75,
            price=50.0
        )
        
        self.assertIn(decision['action'], ['OPEN', 'SCALE_IN'])
        self.assertGreater(decision['quantity'], 0)
        self.portfolio.open_or_add.assert_called_once()
    
    def test_process_signal_scale_out(self):
        """Test process_signal scales out."""
        self.portfolio.current_weight = Mock(return_value=0.20)
        
        decision = self.engine.process_signal(
            symbol='THYAO',
            target_weight=0.10,  # Large decrease
            confidence=0.75,
            price=50.0
        )
        
        self.assertEqual(decision['action'], 'SCALE_OUT')
        self.assertGreater(decision['quantity'], 0)
        self.portfolio.reduce_position.assert_called_once()
    
    def test_process_signal_open_new_position(self):
        """Test process_signal opens new position."""
        self.portfolio.current_weight = Mock(return_value=0.0)
        
        decision = self.engine.process_signal(
            symbol='THYAO',
            target_weight=0.15,
            confidence=0.75,
            price=50.0
        )
        
        self.assertEqual(decision['action'], 'OPEN')
        self.assertGreater(decision['quantity'], 0)
        self.portfolio.open_or_add.assert_called_once()


if __name__ == '__main__':
    unittest.main()
