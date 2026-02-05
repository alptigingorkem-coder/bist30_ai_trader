import config
import pandas as pd

class PortfolioManager:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        # Tier Ağırlıkları
        self.tier_weights = {
            'TIER_1': 0.60,
            'TIER_2': 0.30,
            'TIER_3': 0.10
        }
        
    def get_tier(self, ticker):
        if ticker in config.TIERS['TIER_1']: return 'TIER_1'
        if ticker in config.TIERS['TIER_2']: return 'TIER_2'
        if ticker in config.TIERS['TIER_3']: return 'TIER_3'
        return None

    def calculate_position_size(self, ticker, sharpe_ratio=None):
        """
        Bir hisse için ayrılacak maksimum sermayeyi hesaplar.
        Sharpe Ratio varsa dinamik ayarlama yapar.
        """
        tier = self.get_tier(ticker)
        if not tier:
            return 0 # Tier dışı hisseye yatırım yok
            
        tier_capital = self.initial_capital * self.tier_weights[tier]
        num_stocks = len(config.TIERS[tier])
        
        if num_stocks == 0: return 0
        
        base_position = tier_capital / num_stocks
        
        # Risk Management Layer: Sharpe Bazlı Position Sizing
        if sharpe_ratio is not None:
            if sharpe_ratio > 1.5:
                position = base_position * 1.5  # Overweight
            elif sharpe_ratio > 1.0:
                position = base_position * 1.0  # Normal
            elif sharpe_ratio > 0.3:
                position = base_position * 0.5  # Underweight
            else:
                position = 0
        else:
            position = base_position # Varsayılan
            
        return position

    def get_confidence_threshold(self, ticker):
        tier = self.get_tier(ticker)
        if tier:
            return config.CONFIDENCE_THRESHOLDS[tier]
        return 0.70 # Default yüksek eşik
