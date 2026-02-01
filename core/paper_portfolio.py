
import json
import os
from datetime import datetime
import pandas as pd

class PaperPortfolioState:
    """
    Sanal portföy state yönetimi.
    Pozisyon takibi, exposure analizi ve overtrading kontrolü sağlar.
    """
    
    def __init__(self, initial_capital=100000, state_file="logs/paper_trading/portfolio_state.json"):
        self.initial_capital = initial_capital
        self.state_file = state_file
        self.positions = {}  # {ticker: {quantity, avg_price, entry_date}}
        self.cash = initial_capital
        self.trade_history = []
        
        # Load existing state if available
        self._load_state()
    
    def _load_state(self):
        """Load state from file if exists."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.positions = state.get('positions', {})
                    self.cash = state.get('cash', self.initial_capital)
                    self.trade_history = state.get('trade_history', [])
            except:
                pass
    
    def _save_state(self):
        """Persist state to file."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump({
                'positions': self.positions,
                'cash': self.cash,
                'trade_history': self.trade_history,
                'last_updated': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def has_position(self, ticker):
        """Check if we already have a position in this ticker."""
        return ticker in self.positions and self.positions[ticker]['quantity'] > 0
    
    def get_position(self, ticker):
        """Get current position details for a ticker."""
        return self.positions.get(ticker, None)
    
    def get_total_exposure(self):
        """Calculate total portfolio exposure (invested amount)."""
        total = 0
        for ticker, pos in self.positions.items():
            total += pos['quantity'] * pos['current_price'] if 'current_price' in pos else pos['quantity'] * pos['avg_price']
        return total
    
    def get_exposure_ratio(self):
        """Get exposure as percentage of total capital."""
        exposure = self.get_total_exposure()
        total_value = exposure + self.cash
        return exposure / total_value if total_value > 0 else 0
    
    def can_open_position(self, ticker, action):
        """
        Check if we can open a new position.
        Prevents overtrading and position flipping.
        """
        if action == 'WAIT':
            return True, None
            
        existing = self.get_position(ticker)
        
        if existing:
            # Already have position - check for flip
            if action == 'BUY':
                return False, 'ALREADY_LONG'
            elif action == 'SELL':
                # Closing position is allowed
                return True, None
        
        return True, None
    
    def execute_shadow_trade(self, ticker, action, price, quantity, timestamp=None):
        """
        Execute a shadow trade and update portfolio state.
        Returns execution result dict.
        """
        timestamp = timestamp or datetime.now().isoformat()
        
        result = {
            'ticker': ticker,
            'action': action,
            'price': price,
            'quantity': quantity,
            'timestamp': timestamp,
            'executed': False,
            'blocked_reason': None
        }
        
        # Check if trade is allowed
        can_trade, reason = self.can_open_position(ticker, action)
        
        if not can_trade:
            result['blocked_reason'] = reason
            return result
        
        if action == 'BUY':
            # Open new position
            trade_value = price * quantity
            if trade_value > self.cash:
                result['blocked_reason'] = 'INSUFFICIENT_CASH'
                return result
                
            self.positions[ticker] = {
                'quantity': quantity,
                'avg_price': price,
                'entry_date': timestamp,
                'current_price': price
            }
            self.cash -= trade_value
            result['executed'] = True
            
        elif action == 'SELL':
            if self.has_position(ticker):
                pos = self.positions[ticker]
                trade_value = price * pos['quantity']
                self.cash += trade_value
                
                # Calculate PnL
                result['realized_pnl'] = (price - pos['avg_price']) * pos['quantity']
                result['pnl_pct'] = (price - pos['avg_price']) / pos['avg_price']
                
                del self.positions[ticker]
                result['executed'] = True
            else:
                result['blocked_reason'] = 'NO_POSITION_TO_SELL'
        
        if result['executed']:
            self.trade_history.append(result)
            self._save_state()
        
        return result
    
    def update_prices(self, price_dict):
        """Update current prices for all positions."""
        for ticker, price in price_dict.items():
            if ticker in self.positions:
                self.positions[ticker]['current_price'] = price
        self._save_state()
    
    def get_portfolio_summary(self):
        """Get a summary of current portfolio state."""
        return {
            'cash': self.cash,
            'positions_count': len(self.positions),
            'total_exposure': self.get_total_exposure(),
            'exposure_ratio': self.get_exposure_ratio(),
            'positions': list(self.positions.keys()),
            'total_trades': len(self.trade_history)
        }
    
    def reset(self):
        """Reset portfolio to initial state."""
        self.positions = {}
        self.cash = self.initial_capital
        self.trade_history = []
        self._save_state()
