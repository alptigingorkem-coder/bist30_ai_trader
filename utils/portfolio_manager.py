class PortfolioManager:
    def __init__(self, initial_capital=100000):
        self.capital = initial_capital
        self.peak_capital = initial_capital
        self.positions = {}  # {ticker: {'size': 0.2, 'entry_price': 100}}
        
    def update_capital(self, current_capital):
        """Güncel sermayeyi set eder ve zirveyi günceller."""
        self.capital = current_capital
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital
            
    def calculate_drawdown(self):
        current = self.capital
        peak = self.peak_capital
        return (current - peak) / peak if peak > 0 else 0
        
    def check_drawdown_limit(self):
        """
        FIX 12: Portföy drawdown kontrolü
        """
        dd = self.calculate_drawdown()
        
        if dd < -0.25:  # %25 kayıp
            return {
                'action': 'CLOSE_ALL',
                'multiplier': 0.0,  # Her şeyi kapat
                'reason': f'Emergency DD: {dd:.1%}'
            }
            
        if dd < -0.15:  # %15 kayıp
            return {
                'action': 'REDUCE_ALL',
                'multiplier': 0.5,  # Tüm pozisyonları yarıya indir
                'reason': f'Portfolio DD: {dd:.1%}'
            }
            
        return {'action': 'NORMAL', 'multiplier': 1.0}
