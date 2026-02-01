import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class MonteCarloSimulator:
    def __init__(self, returns, n_simulations=1000):
        self.returns = returns # Günlük getiri serisi (pandas Series)
        self.n_simulations = n_simulations
        
    def run_simulation(self):
        """Bootstrap yöntemiyle simülasyon çalıştırır."""
        print(f"Monte Carlo Simülasyonu ({self.n_simulations} senaryo)...")
        
        sim_results = []
        n_days = len(self.returns)
        
        for i in range(self.n_simulations):
            # Mevcut getirilerden rastgele örneklem al (Replacement ile)
            sim_returns = np.random.choice(self.returns, size=n_days, replace=True)
            cumulative_ret = (1 + sim_returns).cumprod()
            final_return = cumulative_ret[-1] - 1
            
            # Max Drawdown
            running_max = np.maximum.accumulate(cumulative_ret)
            drawdown = (cumulative_ret - running_max) / running_max
            max_dd = drawdown.min()
            
            sim_results.append({
                'Final Return': final_return,
                'Max Drawdown': max_dd
            })
            
        self.results_df = pd.DataFrame(sim_results)
        return self.results_df
        
    def get_stats(self):
        """İstatistikleri raporlar."""
        if not hasattr(self, 'results_df'): return None
        
        df = self.results_df
        stats = {
            'Mean Return': df['Final Return'].mean(),
            'Median Return': df['Final Return'].median(),
            'Worst Case (5%)': df['Final Return'].quantile(0.05),
            'Best Case (95%)': df['Final Return'].quantile(0.95),
            'Worst Drawdown (5%)': df['Max Drawdown'].quantile(0.05)
        }
        
        print("\nMonte Carlo Analizi:")
        for k, v in stats.items():
            print(f"{k}: {v:.4f}")
            
        return stats
