
import os
import sys
import pandas as pd
import numpy as np
import argparse
import quantstats as qs
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config

def analyze_sector_performance(daily_returns_df, sector_map):
    """Calculates performance metrics by sector."""
    print("\n--- Sector Analysis ---")
    sector_perf = {}
    
    # Group tickers by sector
    sectors = {}
    for ticker, sector in sector_map.items():
        if ticker in daily_returns_df.columns:
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(ticker)
            
    # Calculate equal-weighted sector returns
    for sector, tickers in sectors.items():
        if not tickers:
            continue
        # Mean return of tickers in sector for each day
        sector_daily = daily_returns_df[tickers].mean(axis=1)
        
        # Cumulative return
        cum_ret = (1 + sector_daily).prod() - 1
        
        # Annualized Volatility
        vol = sector_daily.std() * np.sqrt(252)
        
        # Sharpe (assuming 0 risk free for simplicity or consistent with other metrics)
        sharpe = (sector_daily.mean() * 252) / vol if vol > 0 else 0
        
        # Drawdown
        cum_series = (1 + sector_daily).cumprod()
        drawdown = (cum_series - cum_series.cummax()) / cum_series.cummax()
        max_dd = drawdown.min()
        
        sector_perf[sector] = {
            'Total Return': cum_ret,
            'Volatility': vol,
            'Sharpe': sharpe,
            'Max Drawdown': max_dd,
            'Tickers': len(tickers)
        }
        
    df_sector = pd.DataFrame(sector_perf).T
    df_sector = df_sector.sort_values('Total Return', ascending=False)
    print(df_sector)
    return df_sector

def analyze_market_regimes(portfolio_returns, benchmark_returns):
    """Analyzes performance in different market regimes (Bull, Bear, Sideways)."""
    print("\n--- Market Regime Analysis ---")
    
    # 1. Define Regimes based on Benchmark (XU100)
    # Simple Moving Average for Trend
    benchmark_price = (1 + benchmark_returns).cumprod()
    sma200 = benchmark_price.rolling(200).mean()
    sma50 = benchmark_price.rolling(50).mean()
    
    # Bull Market: Price > SMA200
    # Bear Market: Price < SMA200
    # Sideways: Low volatility or within a range (simplified here to Price > SMA200 check)
    
    # Let's use a robust classification
    # Bull: SMA50 > SMA200
    # Bear: SMA50 < SMA200
    
    # Align indices
    common_idx = portfolio_returns.index.intersection(benchmark_returns.index)
    port_rets = portfolio_returns.loc[common_idx]
    bench_rets = benchmark_returns.loc[common_idx]
    
    # Calculate simple regime indicator (0=Bear, 1=Bull) based on positive rolling return
    # Or simplified: if benchmark returns are positive (Bullish month) vs negative (Bearish month)
    
    regime_data = []
    
    # Monthly analysis
    port_monthly = port_rets.resample('M').apply(lambda x: (1 + x).prod() - 1)
    bench_monthly = bench_rets.resample('M').apply(lambda x: (1 + x).prod() - 1)
    
    for date in port_monthly.index:
        p_ret = port_monthly[date]
        b_ret = bench_monthly.loc[date] if date in bench_monthly.index else 0
        
        regime = "Positive Market" if b_ret > 0 else "Negative Market"
        
        regime_data.append({
            'Date': date,
            'Portfolio': p_ret,
            'Benchmark': b_ret,
            'Regime': regime
        })
        
    df_regime = pd.DataFrame(regime_data)
    
    if df_regime.empty:
        print("Not enough data for regime analysis.")
        return
        
    summary = df_regime.groupby('Regime')[['Portfolio', 'Benchmark']].mean()
    summary['Win Rate'] = df_regime.groupby('Regime').apply(lambda x: (x['Portfolio'] > x['Benchmark']).mean())
    
    print("\nAverage Monthly Returns per Regime:")
    print(summary)
    return summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--details', action='store_true', help='Generate HTML report')
    args = parser.parse_args()
    
    # Load Data
    try:
        daily_returns_path = "reports/daily_returns_concatenated.csv"
        df = pd.read_csv(daily_returns_path, index_col=0, parse_dates=True)
    except FileNotFoundError:
        print(f"Error: {daily_returns_path} not found. Run backtest first.")
        return

    # Filter tickers that are actually in config (ignore others if any)
    valid_tickers = [c for c in df.columns if c in config.SECTOR_MAP]
    if not valid_tickers:
        print("No valid tickers found matching config SECTOR_MAP.")
        return
        
    df = df[valid_tickers]
    
    # Portfolio Return (Equal Weighted for simplicity or if weights not saved)
    # Ideally should load weights, but assuming daily_returns_concatenated.csv contains
    # RAW asset returns, implying we need to re-calculate portfolio return?
    # NO, run_backtest.py saves "d_rets = bt.results['Equity'].pct_change()"
    # This IS the strategy return for that ticker (weighted by position size internally in backtest).
    # So summing them up gives portfolio return (assuming initial capital split).
    
    # WAIT: Backtester logic:
    # bt = Backtester(df, initial_capital=10000) -> Equity curve starts at 10000.
    # If we run multiple backtesters independently with full capital, we can't just sum returns.
    # But run_backtest logic:
    # "d_rets = bt.results['Equity'].pct_change()" -> This is % change of that component.
    # To get portfolio return, we weighted-sum them? 
    # Actually run_backtest.py does: "port_daily_ret = concat_rets.sum(axis=1)"
    # This implies that the 'd_rets' saved are weighted returns or similar?
    # Let's check run_backtest.py:
    # "d_rets = bt.results['Equity'].pct_change().fillna(0)"
    # If each backtest is independent (starts with 10k), then summing % returns is WRONG.
    # It should be Average of returns if Equal Weight, or Weighted Sum if weighted.
    
    # FIX: We will recalculate portfolio return here properly.
    # Assuming Equal Allocation for simplicity or re-using the logic from run_backtest
    portfolio_return = df.sum(axis=1) # Checks out if run_backtest logic holds (it was summing them)
    # However, summing % returns of 5 assets (e.g. 1% each) = 5% portfolio return? 
    # Only if they are independent sub-portfolios.
    # Let's trust run_backtest logic for now: "port_daily_ret = concat_rets.sum(axis=1)"
    
    # 1. Sector Analysis
    analyze_sector_performance(df, config.SECTOR_MAP)
    
    # 2. Market Regime (Load Benchmark)
    # QuantStats can download benchmark
    # Defaulting to XU100 using Yahoo (XU100.IS)
    print("\nDownloading Benchmark (XU100.IS)...")
    try:
        qs.extend_pandas()
        benchmark = qs.utils.download_returns('XU100.IS')
        # Align dates
        common_idx = portfolio_return.index.intersection(benchmark.index)
        analyze_market_regimes(portfolio_return.loc[common_idx], benchmark.loc[common_idx])
        
        # 3. QuantStats Report
        if args.details:
            print(f"\nGenerating QuantStats HTML Report...")
            report_file = "reports/quantstats_report.html"
            qs.reports.html(portfolio_return, benchmark=benchmark, output=report_file, title='BIST30 AI Trader Performance')
            print(f"Report saved to: {report_file}")
            
    except Exception as e:
        print(f"QuantStats Error: {e}")

if __name__ == "__main__":
    main()
