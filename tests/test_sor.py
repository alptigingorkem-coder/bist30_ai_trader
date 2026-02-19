import unittest
from core.execution import ExecutionManager, SmartOrderRouter, Urgency, OrderType

class TestSmartOrderRouter(unittest.TestCase):
    def setUp(self):
        self.em = ExecutionManager()
        self.sor = SmartOrderRouter(self.em)
        self.price = 100.0
        self.qty = 10
        self.symbol = "TEST.IS"

    def test_high_urgency_market_order(self):
        """Test HIGH urgency generates MARKET order with slippage"""
        order = self.sor.generate_order(self.symbol, "BUY", self.price, self.qty, Urgency.HIGH)
        
        self.assertEqual(order["type"], OrderType.MARKET)
        # Market order should have slippage (price > original)
        self.assertGreater(order["price"], self.price)
        print(f"HIGH Urgency Price: {order['price']}")

    def test_normal_urgency_limit_order(self):
        """Test NORMAL urgency generates LIMIT order at market price"""
        order = self.sor.generate_order(self.symbol, "BUY", self.price, self.qty, Urgency.NORMAL)
        
        self.assertEqual(order["type"], OrderType.LIMIT)
        # Normal limit should be at price (simulating crossing the spread)
        self.assertEqual(order["price"], self.price)
        print(f"NORMAL Urgency Price: {order['price']}")

    def test_low_urgency_passive_order(self):
        """Test LOW urgency generates passive LIMIT order (better price)"""
        # BUY case
        order_buy = self.sor.generate_order(self.symbol, "BUY", self.price, self.qty, Urgency.LOW)
        self.assertEqual(order_buy["type"], OrderType.LIMIT)
        # Buying cheaper
        self.assertLess(order_buy["price"], self.price)
        
        # SELL case
        order_sell = self.sor.generate_order(self.symbol, "SELL", self.price, self.qty, Urgency.LOW)
        self.assertEqual(order_sell["type"], OrderType.LIMIT)
        # Selling higher
        self.assertGreater(order_sell["price"], self.price)
        print(f"LOW Urgency Buy Price: {order_buy['price']}, Sell Price: {order_sell['price']}")

if __name__ == '__main__':
    unittest.main()
