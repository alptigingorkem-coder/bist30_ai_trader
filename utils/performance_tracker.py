import numpy as np

class PerformanceTracker:
    def __init__(self):
        self.trades = []
        self.daily_returns = []
        
    def add_trade(self, trade_info):
        """
        trade_info dict: {'return': 0.05, ...}
        """
        self.trades.append(trade_info)
        
    def add_daily_return(self, ret):
        self.daily_returns.append(ret)
        
    def calculate_sharpe(self):
        if not self.daily_returns or len(self.daily_returns) < 2:
            return 0.0
        
        returns = np.array(self.daily_returns)
        mean_ret = np.mean(returns)
        std_ret = np.std(returns)
        
        if std_ret < 1e-6:
            return 0.0
            
        # Basit Sharpe (Risk-free rate = 0 varsayımıyla)
        # Yıllıklandırmak için sqrt(252)
        return (mean_ret / std_ret) * np.sqrt(252)

    def get_current_metrics(self):
        """
        FIX 21: Real-time metrikler
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'sharpe': 0.0
            }
            
        returns = [t.get('return', 0.0) for t in self.trades]
        
        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r < 0]
        
        win_rate = len(wins) / len(returns) if returns else 0
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        if not losses and wins: profit_factor = float('inf')
        
        return {
            'total_trades': len(self.trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe': self.calculate_sharpe()
        }
        
    def should_stop_trading(self):
        """
        FIX 22: Otomatik durdurma
        """
        metrics = self.get_current_metrics()
        
        # 20+ trade sonrası değerlendir
        if metrics['total_trades'] < 20:
            return False, ""
            
        # Win rate < %35 ise dur
        if metrics['win_rate'] < 0.35:
            return True, f"Win rate çok düşük ({metrics['win_rate']:.1%})"
            
        # Profit factor < 0.8 ise dur
        if metrics['profit_factor'] < 0.8:
            return True, f"Profit factor negatif ({metrics['profit_factor']:.2f})"
            
        return False, ""
