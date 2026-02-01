"""
Position-Aware Paper Trading - Position Execution Engine
Sinyal + Portföy durumu → Pozisyon kararı
"""

from datetime import datetime
from typing import Dict, Optional, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_trading_position_aware.portfolio_state import PortfolioState

class PositionExecutionEngine:
    """
    Position-Aware Karar Motoru.
    Model sinyalini pozisyon bağlamında yorumlar.
    """
    
    # Karar tipleri
    OPEN_POSITION = 'OPEN_POSITION'
    HOLD_EXISTING = 'HOLD_EXISTING'
    SCALE_IN = 'SCALE_IN'
    SCALE_OUT = 'SCALE_OUT'
    CLOSE_POSITION = 'CLOSE_POSITION'
    IGNORE_SIGNAL = 'IGNORE_SIGNAL'
    
    def __init__(self, 
                 default_position_size: float = 0.05,  # %5
                 scale_in_threshold: float = 0.7,      # Confidence > 0.7 ise scale in
                 scale_out_threshold: float = 0.4,     # Confidence < 0.4 ise scale out
                 macro_position_action: str = 'HOLD'): # HOLD | SCALE_OUT | CLOSE
        
        self.default_position_size = default_position_size
        self.scale_in_threshold = scale_in_threshold
        self.scale_out_threshold = scale_out_threshold
        self.macro_position_action = macro_position_action  # Macro gate aktifken mevcut pozisyonlara ne yapılsın
    
    def decide(self, 
               snapshot: dict, 
               portfolio: PortfolioState) -> dict:
        """
        Sinyal snapshot'ı ve portföy durumuna göre karar üret.
        
        Returns:
        {
            'action': str,          # OPEN_POSITION, HOLD_EXISTING, etc.
            'symbol': str,
            'price': float,
            'quantity': float,
            'side': str,            # LONG / SHORT
            'reason': str,
            'signal_info': dict,    # Orijinal sinyal bilgisi
            'portfolio_before': dict
        }
        """
        symbol = snapshot.get('ticker', '')
        signal = snapshot.get('action', 'WAIT')
        confidence = snapshot.get('confidence', 0)
        price = snapshot.get('current_price', 0)
        regime = snapshot.get('regime', 'Sideways')
        macro_blocked = snapshot.get('macro_blocked', False)
        
        # Portföy snapshot'ı
        portfolio_before = portfolio.get_summary()
        has_position = portfolio.has_position(symbol)
        
        # Karar yapısı
        decision = {
            'action': self.IGNORE_SIGNAL,
            'symbol': symbol,
            'price': price,
            'quantity': 0,
            'side': 'LONG',
            'reason': '',
            'signal_info': {
                'signal': signal,
                'confidence': confidence,
                'regime': regime,
                'macro_blocked': macro_blocked
            },
            'portfolio_before': portfolio_before,
            'timestamp': datetime.now().isoformat()
        }
        
        # ═══════════════════════════════════════════════════════════════════
        # KARAR AĞACI
        # ═══════════════════════════════════════════════════════════════════
        
        # 1. WAIT sinyali → Mevcut pozisyona göre davran
        if signal == 'WAIT':
            if has_position:
                decision['action'] = self.HOLD_EXISTING
                decision['reason'] = 'Signal is WAIT, holding existing position'
            else:
                decision['action'] = self.IGNORE_SIGNAL
                decision['reason'] = 'Signal is WAIT, no position to manage'
            return decision
        
        # 2. Macro Gate aktif
        if macro_blocked:
            if has_position:
                # Mevcut pozisyona ne yapılsın?
                decision = self._handle_macro_with_position(decision, portfolio, symbol, price)
            else:
                # Yeni pozisyon açılamaz
                decision['action'] = self.IGNORE_SIGNAL
                decision['reason'] = 'Macro gate blocked, cannot open new position'
            return decision
        
        # 3. BUY sinyali
        if signal == 'BUY':
            if has_position:
                # Zaten pozisyon var - Scale in mi yapalım?
                decision = self._handle_buy_with_position(decision, portfolio, symbol, price, confidence)
            else:
                # Yeni pozisyon aç
                decision = self._handle_open_position(decision, portfolio, symbol, price, confidence, 'LONG')
            return decision
        
        # 4. SELL sinyali
        if signal == 'SELL':
            if has_position:
                # Pozisyonu kapat veya küçült
                decision = self._handle_sell_with_position(decision, portfolio, symbol, price, confidence)
            else:
                # Short pozisyon açılabilir (şimdilik desteklenmez)
                decision['action'] = self.IGNORE_SIGNAL
                decision['reason'] = 'SELL signal without position, short selling not supported'
            return decision
        
        return decision
    
    # ═══════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _handle_macro_with_position(self, decision: dict, portfolio: PortfolioState, 
                                     symbol: str, price: float) -> dict:
        """Macro gate aktifken mevcut pozisyona ne yapılacak?"""
        
        if self.macro_position_action == 'CLOSE':
            decision['action'] = self.CLOSE_POSITION
            decision['reason'] = 'Macro gate active, closing position for risk management'
            
        elif self.macro_position_action == 'SCALE_OUT':
            decision['action'] = self.SCALE_OUT
            decision['scale_pct'] = 0.5  # %50 azalt
            decision['reason'] = 'Macro gate active, reducing position by 50%'
            
        else:  # HOLD
            decision['action'] = self.HOLD_EXISTING
            decision['reason'] = 'Macro gate active, holding position'
        
        decision['price'] = price
        return decision
    
    def _handle_buy_with_position(self, decision: dict, portfolio: PortfolioState,
                                   symbol: str, price: float, confidence: float) -> dict:
        """Zaten pozisyon varken BUY sinyali geldi."""
        
        if confidence >= self.scale_in_threshold:
            # Yüksek güven - Scale in yap
            can_scale, reason = portfolio.can_scale_in(symbol, self.default_position_size * 0.5)
            
            if can_scale:
                total_value = portfolio.total_portfolio_value()
                add_value = total_value * self.default_position_size * 0.5
                quantity = add_value / price if price > 0 else 0
                
                decision['action'] = self.SCALE_IN
                decision['quantity'] = quantity
                decision['reason'] = f'High confidence ({confidence:.2f}), scaling in'
            else:
                decision['action'] = self.HOLD_EXISTING
                decision['reason'] = f'Would scale in but: {reason}'
        else:
            # Normal güven - Sadece tut
            decision['action'] = self.HOLD_EXISTING
            decision['reason'] = f'Already has position, confidence ({confidence:.2f}) not high enough to scale in'
        
        return decision
    
    def _handle_open_position(self, decision: dict, portfolio: PortfolioState,
                               symbol: str, price: float, confidence: float, side: str) -> dict:
        """Yeni pozisyon aç."""
        
        can_open, reason = portfolio.can_open_new_position(symbol, self.default_position_size)
        
        if can_open:
            total_value = portfolio.total_portfolio_value()
            position_value = total_value * self.default_position_size
            quantity = position_value / price if price > 0 else 0
            
            decision['action'] = self.OPEN_POSITION
            decision['quantity'] = quantity
            decision['side'] = side
            decision['reason'] = f'Opening {side} position with {self.default_position_size*100:.0f}% allocation'
        else:
            decision['action'] = self.IGNORE_SIGNAL
            decision['reason'] = f'Cannot open position: {reason}'
        
        return decision
    
    def _handle_sell_with_position(self, decision: dict, portfolio: PortfolioState,
                                    symbol: str, price: float, confidence: float) -> dict:
        """Pozisyon varken SELL sinyali."""
        
        if confidence >= self.scale_out_threshold:
            # Yüksek güvenli SELL - Tamamen kapat
            decision['action'] = self.CLOSE_POSITION
            decision['reason'] = f'SELL signal with high confidence ({confidence:.2f}), closing position'
        else:
            # Düşük güvenli SELL - Kısmi kapat
            decision['action'] = self.SCALE_OUT
            decision['scale_pct'] = 0.5
            decision['reason'] = f'SELL signal with moderate confidence ({confidence:.2f}), scaling out 50%'
        
        decision['price'] = price
        return decision
    
    def execute(self, decision: dict, portfolio: PortfolioState) -> dict:
        """Kararı uygula ve sonucu döndür."""
        result = portfolio.apply_trade_decision(decision)
        
        return {
            'decision': decision,
            'execution_result': result,
            'portfolio_after': portfolio.get_summary()
        }
