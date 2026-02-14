"""
Backtester Orchestrator
Tüm backtesting fonksiyonlarını birleştiren mixin-tabanlı sınıf.

Kullanım:
    from core.backtesting import Backtester
    bt = Backtester(data, initial_capital=10000)
    results = bt.run_backtest(signals)
    metrics = bt.calculate_metrics()

Alt modüller:
    core/backtest/engine.py     — run_backtest, slippage, market impact
    core/backtest/metrics.py    — Sharpe, Sortino, Calmar, Alpha, Beta vb.
    core/backtest/visualizer.py — Grafikler, ısı haritası, HTML rapor
"""
from core.position_sizing import KellyPositionSizer
from core.backtest.engine import BacktestEngineMixin
from core.backtest.metrics import BacktestMetricsMixin
from core.backtest.visualizer import BacktestVisualizerMixin
import pandas as pd


class Backtester(
    BacktestEngineMixin,
    BacktestMetricsMixin,
    BacktestVisualizerMixin,
):
    """
    BIST30 AI Trader Backtesting Pipeline.

    Mixin sınıflarını birleştirerek event-driven backtesting, performans metrikleri
    ve görselleştirme fonksiyonlarını tek bir arayüz altında toplar.
    """

    def __init__(
        self, 
        data: pd.DataFrame, 
        initial_capital: float = 10000.0, 
        commission: float = 0.002
    ) -> None:
        """
        Backtester sınıfını başlatır.

        Args:
            data (pd.DataFrame): Backtest edilecek OHLCV verisi.
            initial_capital (float, optional): Başlangıç sermayesi. Varsayılan: 10000.0
            commission (float, optional): İşlem komisyon oranı (0.002 = %0.2). Varsayılan: 0.002
        """
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.commission = commission
        self.position_sizer = KellyPositionSizer()
