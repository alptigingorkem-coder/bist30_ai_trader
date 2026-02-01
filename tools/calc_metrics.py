import pandas as pd
try:
    df = pd.read_csv('reports/final_backtest_results.csv')
    avg_return = df['Total Return'].mean()
    avg_annual = df['Annual Return'].mean()
    avg_sharpe = df['Sharpe Ratio'].mean()
    max_dd = df['Max Drawdown'].mean()
    win_rate = df['Win Rate'].mean()
    
    print(f"METRICS_START")
    print(f"Avg Return: {avg_return:.2%}")
    print(f"Avg Annual Return: {avg_annual:.2%}")
    print(f"Avg Sharpe: {avg_sharpe:.2f}")
    print(f"Avg Max Drawdown: {max_dd:.2%}")
    print(f"Avg Win Rate: {win_rate:.2%}")
    print(f"METRICS_END")
except Exception as e:
    print(f"Error: {e}")
