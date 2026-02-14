"""
Backtest Visualizer Mixin
Grafik, ısı haritası, trade log, HTML rapor.
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class BacktestVisualizerMixin:
    """Görselleştirme ve raporlama metotlarını sağlayan mixin."""

    def plot_results(self, filename='reports/backtest_results.png'):
        """Sonuçları görselleştirir."""
        if not hasattr(self, 'results'):
            return

        os.makedirs(os.path.dirname(filename) or 'reports', exist_ok=True)

        plt.figure(figsize=(12, 6))
        plt.plot(self.results['Cumulative_Market_Return'], label='Hisse (Buy & Hold)', alpha=0.5, linestyle='--')
        plt.plot(self.results['Cumulative_Strategy_Return'], label='AI Stratejisi', linewidth=2, color='blue')

        if 'Cumulative_Benchmark_Return' in self.results.columns:
            plt.plot(self.results['Cumulative_Benchmark_Return'], label='XU100 Endeksi', alpha=0.7, color='orange')

        plt.title("Backtest Sonuçları: Strateji vs Market vs Benchmark")
        plt.legend()
        plt.grid(True)
        plt.savefig(filename)
        plt.close()

    def plot_drawdown(self, filename='reports/drawdown.png'):
        """Drawdown grafiğini çizer ve kaydeder."""
        if not hasattr(self, 'results') or self.results.empty:
            return

        os.makedirs(os.path.dirname(filename) or 'reports', exist_ok=True)

        if 'Drawdown' not in self.results.columns:
            cum_ret = self.results['Cumulative_Strategy_Return']
            running_max = cum_ret.cummax()
            self.results['Drawdown'] = (cum_ret - running_max) / running_max

        plt.figure(figsize=(12, 6))
        plt.plot(self.results.index, self.results['Drawdown'], color='red')
        plt.fill_between(self.results.index, self.results['Drawdown'], 0, color='red', alpha=0.3)
        plt.title('Portfolio Drawdown')
        plt.xlabel('Date')
        plt.ylabel('Drawdown')
        plt.grid(True)
        plt.savefig(filename)
        plt.close()

    def plot_monthly_heatmap(self, filename='reports/monthly_heatmap.png'):
        """Aylık getiri ısı haritasını çizer."""
        import seaborn as sns

        if not hasattr(self, 'results') or self.results.empty:
            return

        os.makedirs(os.path.dirname(filename) or 'reports', exist_ok=True)

        df = self.results.copy()
        df['Year'] = df.index.year
        df['Month'] = df.index.month

        monthly_returns = df.groupby(['Year', 'Month'])['Net_Strategy_Return'].apply(lambda x: (1 + x).prod() - 1).unstack()

        plt.figure(figsize=(10, len(monthly_returns) / 2 + 2))
        sns.heatmap(monthly_returns * 100, annot=True, fmt=".1f", cmap="RdYlGn", center=0, cbar_kws={'label': 'Return (%)'})
        plt.title("Monthly Returns (%)")
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()

    def save_trade_log(self, filename='trade_log.csv'):
        """İşlem geçmişini CSV olarak kaydeder."""
        if not hasattr(self, 'results'):
            return

        df = self.results
        df['Pos_Diff'] = df['Position'].diff()

        trades = []
        entry_date = None
        entry_price = 0

        for date, row in df.iterrows():
            if row['Pos_Diff'] == 1:  # Alış
                entry_date = date
                entry_price = row['Close']
            elif row['Pos_Diff'] == -1:  # Satış
                exit_date = date
                exit_price = row['Close']
                gross_pct = (exit_price - entry_price) / entry_price

                total_cost_pct = (self.commission + 0.001) * 2
                net_pct = gross_pct - total_cost_pct

                reason = row['ExitReason']

                trades.append({
                    'Entry Date': entry_date,
                    'Entry Price': entry_price,
                    'Exit Date': exit_date,
                    'Exit Price': exit_price,
                    'Gross Return': gross_pct,
                    'Net Return': net_pct,
                    'Reason': reason
                })

        if trades:
            pd.DataFrame(trades).to_csv(filename, index=False)

    def generate_html_report(self, filename='report.html', ticker="UNKNOWN"):
        """Tek sayfalık detaylı HTML rapor oluşturur."""
        if not hasattr(self, 'results'):
            return

        metrics = self.calculate_metrics()

        safe_ticker = ticker.replace('.', '_').replace(':', '')

        img_backtest = f"reports/backtest_results_{safe_ticker}.png"
        img_drawdown = f"reports/drawdown_{safe_ticker}.png"
        img_heatmap = f"reports/monthly_heatmap_{safe_ticker}.png"

        self.plot_results(filename=img_backtest)
        self.plot_drawdown(filename=img_drawdown)
        self.plot_monthly_heatmap(filename=img_heatmap)

        src_backtest = os.path.basename(img_backtest)
        src_drawdown = os.path.basename(img_drawdown)
        src_heatmap = os.path.basename(img_heatmap)

        html_content = f"""
        <html>
        <head>
            <title>{ticker} Backtest Report</title>
            <style>
                body {{ font-family: monospace; padding: 20px; background-color: #f4f4f4; }}
                .container {{ background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 1200px; margin: auto; }}
                h1, h2 {{ color: #333; }}
                .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
                .metric-box {{ background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 5px solid #007bff; }}
                .metric-title {{ font-size: 0.9em; color: #666; }}
                .metric-value {{ font-size: 1.4em; font-weight: bold; color: #333; }}
                .images {{ display: flex; flex-direction: column; gap: 20px; }}
                img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{ticker} AI Trader Backtest Report</h1>
                <p>Generated on: {pd.Timestamp.now()}</p>
                <hr>
                
                <h2>Performance Metrics</h2>
                <div class="metrics-grid">
        """

        for k, v in metrics.items():
            if isinstance(v, float):
                val_str = f"{v:.2f}" if abs(v) > 0.01 else f"{v:.4f}"
                if "Return" in k or "Drawdown" in k or "Rate" in k or "Volatility" in k:
                    val_str = f"{v * 100:.2f}%"
            else:
                val_str = str(v)

            html_content += f"""
                    <div class="metric-box">
                        <div class="metric-title">{k}</div>
                        <div class="metric-value">{val_str}</div>
                    </div>
            """

        html_content += f"""
                </div>
                
                <h2>Equity Curve</h2>
                <div class="images">
                    <img src="{src_backtest}" alt="Equity Curve">
                    <img src="{src_drawdown}" alt="Drawdown">
                    <img src="{src_heatmap}" alt="Monthly Heatmap">
                </div>
            </div>
        </body>
        </html>
        """

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
