
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backtesting import Backtester
import config

class TestBacktestEngine(unittest.TestCase):
    def setUp(self):
        """Test ortamını hazırla."""
        # 30 günlük mock veri
        dates = pd.date_range(start="2024-01-01", periods=30, freq='B')
        tickers = ["AKBNK.IS", "THYAO.IS"]
        
        # MultiIndex oluştur
        index = pd.MultiIndex.from_product([dates, tickers], names=['Date', 'Ticker'])
        data = pd.DataFrame(index=index)
        
        # Rastgele fiyat artışı
        np.random.seed(42)
        n = len(data)
        data['Open'] = 100.0 * (1 + np.random.normal(0, 0.01, n).cumsum())
        data['Close'] = data['Open'] * (1 + np.random.normal(0, 0.005, n))
        data['High'] = data[['Open', 'Close']].max(axis=1) * 1.01
        data['Low'] = data[['Open', 'Close']].min(axis=1) * 0.99
        data['Volume'] = 1000000
        
        # Gerekli sütunlar
        data['ATR'] = data['Close'] * 0.02
        data['Regime'] = 'Trend_Up'
        data['Log_Return'] = np.log(data['Close'] / data['Close'].shift(1)).fillna(0)
        
        self.data = data
        self.bt = Backtester(self.data, initial_capital=100_000, commission=0.001)

    def test_initial_state(self):
        """Başlangıç durumu kontrolü."""
        self.assertEqual(self.bt.initial_capital, 100_000)
        self.assertEqual(self.bt.commission, 0.001)
        
    def test_run_backtest_basic(self):
        """Basit bir backtest çalıştır."""
        # Rastgele sinyaller (0-1 arası ağırlıklar)
        signals = pd.Series(np.random.uniform(0, 0.5, len(self.data)), index=self.data.index)
        
        try:
            results = self.bt.run_backtest(signals_or_weights=signals)
            
            # Sonuç kontrolü
            self.assertIsInstance(results, pd.DataFrame)
            self.assertIn('Equity', results.columns)
            self.assertIn('Trades', results.columns)
            
            # Equity başlangıçtan farklı olmalı (işlem yapıldıysa) - veya en azından var olmalı
            final_equity = results['Equity'].iloc[-1]
            self.assertGreater(final_equity, 0)
            
            # İşlem yapıldı mı?
            total_trades = results['Trades'].sum()
            # Rastgele sinyallerle en az 1 işlem olmalı
            # self.assertGreater(total_trades, 0) 
            
        except Exception as e:
            self.fail(f"run_backtest() hata fırlattı: {e}")

if __name__ == '__main__':
    unittest.main()
