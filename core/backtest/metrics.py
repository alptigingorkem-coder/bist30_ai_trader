"""
Backtest Metrics Mixin
Performans metrikleri: Sharpe, Sortino, Calmar, Alpha, Beta, Information Ratio vb.
"""
import numpy as np
import pandas as pd


class BacktestMetricsMixin:
    """Performans metrik metotlarını sağlayan mixin."""

    def calculate_metrics(self):
        """Gelişmiş performans metriklerini hesaplar."""
        if not hasattr(self, 'results'):
            print("Önce run_backtest() çalıştırılmalı.")
            return None

        df = self.results
        returns = df['Net_Strategy_Return']

        # Temel Metrikler
        total_return = df['Cumulative_Strategy_Return'].iloc[-1] - 1

        n_trading_days = max(len(returns), 1)
        annual_return = (1 + total_return) ** (252.0 / n_trading_days) - 1 if total_return > -1 else 0.0

        annual_volatility = returns.std() * np.sqrt(252)

        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0

        # Max Drawdown
        cum_ret = df['Cumulative_Strategy_Return']
        running_max = cum_ret.cummax()
        drawdown = (cum_ret - running_max) / running_max
        max_drawdown = drawdown.min()

        # Win Rate
        winning_trades = returns[returns > 0].count()
        losing_trades = returns[returns < 0].count()
        total_trades = df['Trades'].sum()
        num_round_trip_trades = df['Trades'].sum() / 2

        win_rate = winning_trades / (winning_trades + losing_trades) if (winning_trades + losing_trades) > 0 else 0

        # Profit Factor
        gross_profit = returns[returns > 0].sum()
        gross_loss = abs(returns[returns < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Calmar Ratio
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino_ratio = annual_return / downside_std if downside_std > 0 else 0

        # Information Ratio
        information_ratio = 0.0
        omega_ratio = 0.0
        ulcer_index = 0.0
        avg_holding_days = 0.0

        if 'XU100_Return' in df.columns:
            common = returns.index.intersection(df.index)
            if len(common) > 0:
                strat = returns.loc[common]
                bench = df.loc[common, 'XU100_Return']
                active = strat - bench
                tracking_error = active.std() * np.sqrt(252)
                if tracking_error > 0:
                    information_ratio = (active.mean() * 252) / tracking_error

        # Omega Ratio
        gains = returns[returns > 0]
        losses = -returns[returns < 0]
        if not losses.empty:
            omega_ratio = gains.sum() / losses.sum() if losses.sum() > 0 else float('inf')

        # Ulcer Index
        if not drawdown.empty:
            ulcer_index = np.sqrt((drawdown.pow(2)).mean()) * 100.0

        # Ortalama Holding Süresi
        pos = df['Position']
        if not pos.empty:
            in_trade = False
            start_idx = None
            durations = []
            for i, (idx, val) in enumerate(pos.items()):
                if not in_trade and val > 0:
                    in_trade = True
                    start_idx = idx[0] if isinstance(idx, tuple) else idx
                elif in_trade and val == 0:
                    end_idx = idx[0] if isinstance(idx, tuple) else idx
                    durations.append((end_idx - start_idx).days)
                    in_trade = False
                    start_idx = None
            if durations:
                avg_holding_days = float(np.mean(durations))

        # Alpha & Beta
        alpha = 0.0
        beta = 0.0

        if 'Cumulative_Benchmark_Return' in self.results.columns:
            strategy_returns = self.results['Strategy_Return'].fillna(0)
            benchmark_returns = self.results['Benchmark_Return'].fillna(0)

            covariance = np.cov(strategy_returns, benchmark_returns)[0][1]
            benchmark_variance = np.var(benchmark_returns)

            if benchmark_variance > 0:
                beta = covariance / benchmark_variance
            else:
                beta = 0.0

            risk_free_daily = 0.0005

            rp_annual = annual_return
            rm_annual = (1 + benchmark_returns.mean()) ** 252 - 1

            alpha = rp_annual - (0.30 + beta * (rm_annual - 0.30))

        metrics = {
            'Total Return': total_return,
            'CAGR': annual_return,
            'Alpha': alpha,
            'Beta': beta,
            'Annual Return': annual_return,
            'Volatility': annual_volatility,
            'Sharpe Ratio': sharpe_ratio,
            'Max Drawdown': max_drawdown,
            'Win Rate': win_rate,
            'Profit Factor': profit_factor,
            'Calmar Ratio': calmar_ratio,
            'Sortino Ratio': sortino_ratio,
            'Information Ratio': information_ratio,
            'Omega Ratio': omega_ratio,
            'Ulcer Index': ulcer_index,
            'Avg Holding Days': avg_holding_days,
            'Num Trades': num_round_trip_trades
        }

        return metrics
