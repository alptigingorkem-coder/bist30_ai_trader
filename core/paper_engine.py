
from datetime import datetime
import numpy as np
from core.paper_logger import PaperLogger
from core.paper_portfolio import PaperPortfolioState

class PaperEngine:
    """
    Shadow Execution Engine v2.0
    - ATR + Volume bazlı slippage simülasyonu
    - Opsiyonel PaperPortfolioState entegrasyonu
    """
    
    def __init__(self, use_portfolio=True, initial_capital=100000):
        self.logger = PaperLogger()
        self.use_portfolio = use_portfolio
        
        if use_portfolio:
            self.portfolio = PaperPortfolioState(initial_capital=initial_capital)
        else:
            self.portfolio = None
    
    def calculate_slippage(self, snapshot):
        """
        ATR + Volume Percentile bazlı slippage hesaplama.
        Returns slippage as a percentage (0.001 = 0.1%)
        """
        base_slippage = 0.001  # %0.1 varsayılan
        
        # ATR bazlı volatilite çarpanı
        atr = snapshot.get('atr', None)
        price = snapshot.get('current_price', 1)
        
        if atr and price > 0:
            atr_pct = atr / price
            # Yüksek ATR = yüksek slippage
            if atr_pct > 0.05:  # ATR %5'ten fazla
                base_slippage *= 2.0
            elif atr_pct > 0.03:
                base_slippage *= 1.5
        
        # Volume percentile çarpanı
        volume_percentile = snapshot.get('volume_percentile', 50)
        
        if volume_percentile < 20:  # Düşük hacim günü
            base_slippage *= 2.5
        elif volume_percentile < 40:
            base_slippage *= 1.5
        elif volume_percentile > 80:  # Yüksek hacim günü
            base_slippage *= 0.7
        
        return base_slippage
    
    def apply_slippage(self, price, action, slippage_pct):
        """
        Alış/satış yönüne göre slippage uygula.
        Alışta fiyat artar, satışta düşer.
        """
        if action == 'BUY':
            return price * (1 + slippage_pct)
        elif action == 'SELL':
            return price * (1 - slippage_pct)
        return price
        
    def execute_snapshot(self, snapshot):
        """
        Takes a signal snapshot and determines the Shadow Execution result.
        """
        signal = snapshot.get('action', 'WAIT')
        price = snapshot.get('current_price', 0)
        quantity = snapshot.get('size', 0)
        ticker = snapshot.get('ticker', 'UNKNOWN')
        
        # Calculate slippage
        slippage_pct = self.calculate_slippage(snapshot)
        executed_price = self.apply_slippage(price, signal, slippage_pct)
        
        execution_result = {
            'executed': False,
            'blocked_reason': None,
            'simulated_price': executed_price,
            'original_price': price,
            'slippage_pct': slippage_pct,
            'simulated_quantity': quantity,
            'execution_time': datetime.now().isoformat()
        }
        
        # Check 1: Signal Validity
        if signal == 'WAIT':
            execution_result['blocked_reason'] = 'NO_SIGNAL'
            
        # Check 2: Macro Gate Block
        elif snapshot.get('macro_blocked', False):
            execution_result['blocked_reason'] = 'MACRO_GATE_BLOCK'
            
        # Check 3: Zero Quantity
        elif quantity <= 0:
            execution_result['blocked_reason'] = 'ZERO_QUANTITY'
        
        # Check 4: Portfolio State (if enabled)
        elif self.use_portfolio and self.portfolio:
            can_trade, reason = self.portfolio.can_open_position(ticker, signal)
            if not can_trade:
                execution_result['blocked_reason'] = reason
            else:
                # Execute in portfolio
                portfolio_result = self.portfolio.execute_shadow_trade(
                    ticker=ticker,
                    action=signal,
                    price=executed_price,
                    quantity=quantity
                )
                execution_result['executed'] = portfolio_result['executed']
                if not portfolio_result['executed']:
                    execution_result['blocked_reason'] = portfolio_result.get('blocked_reason')
                else:
                    execution_result['action_taken'] = f"SHADOW_{signal}"
                    if 'realized_pnl' in portfolio_result:
                        execution_result['realized_pnl'] = portfolio_result['realized_pnl']
        else:
            # Stateless mode - just mark as executed
            execution_result['executed'] = True
            execution_result['action_taken'] = f"SHADOW_{signal}"
        
        # Merge Execution Result into Snapshot
        full_record = {**snapshot, **execution_result}
        
        # Log
        self.logger.log_decision(full_record)
        
        return full_record
    
    def get_portfolio_summary(self):
        """Get current portfolio state (if portfolio tracking enabled)."""
        if self.portfolio:
            return self.portfolio.get_portfolio_summary()
        return {'status': 'Portfolio tracking disabled'}
