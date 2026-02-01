"""
Position-Aware Paper Trading - Portfolio State Module
Portföy belleği: Açık pozisyonları, exposure'ı ve PnL'i takip eder.
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, Tuple, List

class PortfolioState:
    """
    Stateful portföy yönetimi.
    Pozisyon takibi, exposure analizi ve risk kontrolü sağlar.
    """
    
    def __init__(self, 
                 initial_capital: float = 100000,
                 max_positions: int = 10,
                 max_single_exposure: float = 0.10,  # %10
                 max_total_exposure: float = 0.80,   # %80
                 state_file: str = "paper_trading_position_aware/logs/portfolio_state.json"):
        
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.max_single_exposure = max_single_exposure
        self.max_total_exposure = max_total_exposure
        self.state_file = state_file
        
        # Pozisyon yapısı
        self.positions: Dict[str, dict] = {}
        self.cash = initial_capital
        self.realized_pnl = 0.0
        self.trade_history: List[dict] = []
        
        # State'i yükle (varsa)
        self._load_state()
    
    # ═══════════════════════════════════════════════════════════════════════
    # POSITION QUERIES
    # ═══════════════════════════════════════════════════════════════════════
    
    def has_position(self, symbol: str) -> bool:
        """Belirtilen sembolde açık pozisyon var mı?"""
        return symbol in self.positions and self.positions[symbol]['quantity'] > 0
    
    def get_position(self, symbol: str) -> Optional[dict]:
        """Pozisyon detaylarını döndür."""
        return self.positions.get(symbol, None)
    
    def get_all_positions(self) -> Dict[str, dict]:
        """Tüm açık pozisyonları döndür."""
        return {k: v for k, v in self.positions.items() if v['quantity'] > 0}
    
    def position_count(self) -> int:
        """Aktif pozisyon sayısı."""
        return len(self.get_all_positions())
    
    # ═══════════════════════════════════════════════════════════════════════
    # EXPOSURE CALCULATIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    def current_total_exposure(self) -> float:
        """Toplam portföy exposure'ı (TL cinsinden)."""
        total = 0.0
        for symbol, pos in self.positions.items():
            price = pos.get('current_price', pos['entry_price'])
            total += pos['quantity'] * price
        return total
    
    def exposure_ratio(self) -> float:
        """Toplam exposure oranı (0-1 arası)."""
        total_value = self.cash + self.current_total_exposure()
        if total_value <= 0:
            return 0.0
        return self.current_total_exposure() / total_value
    
    def position_exposure(self, symbol: str) -> float:
        """Belirli bir pozisyonun exposure oranı."""
        if not self.has_position(symbol):
            return 0.0
        pos = self.positions[symbol]
        price = pos.get('current_price', pos['entry_price'])
        position_value = pos['quantity'] * price
        total_value = self.cash + self.current_total_exposure()
        return position_value / total_value if total_value > 0 else 0.0
    
    # ═══════════════════════════════════════════════════════════════════════
    # TRADE VALIDATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def can_open_new_position(self, symbol: str, size_pct: float) -> Tuple[bool, str]:
        """
        Yeni pozisyon açılabilir mi?
        Returns: (allowed, reason)
        """
        # Zaten pozisyon var mı?
        if self.has_position(symbol):
            return False, "ALREADY_HAS_POSITION"
        
        # Max pozisyon sayısı aşıldı mı?
        if self.position_count() >= self.max_positions:
            return False, "MAX_POSITIONS_REACHED"
        
        # Tek pozisyon limiti aşılıyor mu?
        if size_pct > self.max_single_exposure:
            return False, "EXCEEDS_SINGLE_POSITION_LIMIT"
        
        # Toplam exposure limiti aşılıyor mu?
        if self.exposure_ratio() + size_pct > self.max_total_exposure:
            return False, "EXCEEDS_TOTAL_EXPOSURE_LIMIT"
        
        # Yeterli nakit var mı?
        total_value = self.cash + self.current_total_exposure()
        required_cash = total_value * size_pct
        if required_cash > self.cash:
            return False, "INSUFFICIENT_CASH"
        
        return True, "OK"
    
    def can_scale_in(self, symbol: str, additional_pct: float) -> Tuple[bool, str]:
        """Mevcut pozisyona ekleme yapılabilir mi?"""
        if not self.has_position(symbol):
            return False, "NO_POSITION_TO_SCALE"
        
        current_exposure = self.position_exposure(symbol)
        new_exposure = current_exposure + additional_pct
        
        if new_exposure > self.max_single_exposure:
            return False, "EXCEEDS_SINGLE_POSITION_LIMIT"
        
        if self.exposure_ratio() + additional_pct > self.max_total_exposure:
            return False, "EXCEEDS_TOTAL_EXPOSURE_LIMIT"
        
        return True, "OK"
    
    # ═══════════════════════════════════════════════════════════════════════
    # TRADE EXECUTION
    # ═══════════════════════════════════════════════════════════════════════
    
    def apply_trade_decision(self, decision: dict) -> dict:
        """
        Karar uygula ve state'i güncelle.
        decision: {
            'action': 'OPEN_POSITION' | 'CLOSE_POSITION' | 'SCALE_IN' | 'SCALE_OUT',
            'symbol': str,
            'price': float,
            'quantity': float,
            'side': 'LONG' | 'SHORT'
        }
        """
        action = decision.get('action')
        symbol = decision.get('symbol')
        price = decision.get('price', 0)
        quantity = decision.get('quantity', 0)
        
        result = {
            'success': False,
            'action': action,
            'symbol': symbol,
            'message': '',
            'realized_pnl': 0.0
        }
        
        if action == 'OPEN_POSITION':
            result = self._open_position(symbol, price, quantity, decision.get('side', 'LONG'))
            
        elif action == 'CLOSE_POSITION':
            result = self._close_position(symbol, price)
            
        elif action == 'SCALE_IN':
            result = self._scale_in(symbol, price, quantity)
            
        elif action == 'SCALE_OUT':
            scale_pct = decision.get('scale_pct', 0.5)  # Varsayılan %50
            result = self._scale_out(symbol, price, scale_pct)
            
        elif action in ['HOLD_EXISTING', 'IGNORE_SIGNAL']:
            result['success'] = True
            result['message'] = f'{action}: No trade executed'
        
        # State'i kaydet
        if result['success']:
            self._save_state()
            self.trade_history.append({
                **decision,
                'timestamp': datetime.now().isoformat(),
                'result': result
            })
        
        return result
    
    def _open_position(self, symbol: str, price: float, quantity: float, side: str) -> dict:
        """Yeni pozisyon aç."""
        trade_value = price * quantity
        
        if trade_value > self.cash:
            return {'success': False, 'message': 'INSUFFICIENT_CASH'}
        
        self.positions[symbol] = {
            'side': side,
            'entry_price': price,
            'quantity': quantity,
            'current_price': price,
            'open_date': datetime.now().isoformat(),
            'unrealized_pnl': 0.0
        }
        self.cash -= trade_value
        
        return {
            'success': True,
            'action': 'OPEN_POSITION',
            'symbol': symbol,
            'message': f'Opened {side} position: {quantity} @ {price}'
        }
    
    def _close_position(self, symbol: str, price: float) -> dict:
        """Pozisyonu kapat."""
        if not self.has_position(symbol):
            return {'success': False, 'message': 'NO_POSITION'}
        
        pos = self.positions[symbol]
        trade_value = price * pos['quantity']
        
        # PnL hesapla
        if pos['side'] == 'LONG':
            pnl = (price - pos['entry_price']) * pos['quantity']
        else:
            pnl = (pos['entry_price'] - price) * pos['quantity']
        
        self.cash += trade_value
        self.realized_pnl += pnl
        
        # Pozisyonu sil
        del self.positions[symbol]
        
        return {
            'success': True,
            'action': 'CLOSE_POSITION',
            'symbol': symbol,
            'message': f'Closed position @ {price}',
            'realized_pnl': pnl
        }
    
    def _scale_in(self, symbol: str, price: float, quantity: float) -> dict:
        """Pozisyona ekle."""
        if not self.has_position(symbol):
            return {'success': False, 'message': 'NO_POSITION'}
        
        trade_value = price * quantity
        if trade_value > self.cash:
            return {'success': False, 'message': 'INSUFFICIENT_CASH'}
        
        pos = self.positions[symbol]
        
        # Ortalama maliyet güncelle
        total_cost = (pos['entry_price'] * pos['quantity']) + (price * quantity)
        total_qty = pos['quantity'] + quantity
        new_avg_price = total_cost / total_qty
        
        pos['entry_price'] = new_avg_price
        pos['quantity'] = total_qty
        pos['current_price'] = price
        
        self.cash -= trade_value
        
        return {
            'success': True,
            'action': 'SCALE_IN',
            'symbol': symbol,
            'message': f'Added {quantity} @ {price}, new avg: {new_avg_price:.2f}'
        }
    
    def _scale_out(self, symbol: str, price: float, scale_pct: float) -> dict:
        """Pozisyonun bir kısmını sat."""
        if not self.has_position(symbol):
            return {'success': False, 'message': 'NO_POSITION'}
        
        pos = self.positions[symbol]
        sell_qty = pos['quantity'] * scale_pct
        trade_value = price * sell_qty
        
        # PnL hesapla
        if pos['side'] == 'LONG':
            pnl = (price - pos['entry_price']) * sell_qty
        else:
            pnl = (pos['entry_price'] - price) * sell_qty
        
        pos['quantity'] -= sell_qty
        pos['current_price'] = price
        
        self.cash += trade_value
        self.realized_pnl += pnl
        
        # Tamamen kapandıysa sil
        if pos['quantity'] <= 0:
            del self.positions[symbol]
        
        return {
            'success': True,
            'action': 'SCALE_OUT',
            'symbol': symbol,
            'message': f'Sold {sell_qty:.2f} @ {price}',
            'realized_pnl': pnl
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # PRICE UPDATES
    # ═══════════════════════════════════════════════════════════════════════
    
    def update_prices(self, prices: Dict[str, float]):
        """Tüm pozisyonların güncel fiyatlarını güncelle."""
        for symbol, price in prices.items():
            if symbol in self.positions:
                pos = self.positions[symbol]
                pos['current_price'] = price
                
                # Unrealized PnL güncelle
                if pos['side'] == 'LONG':
                    pos['unrealized_pnl'] = (price - pos['entry_price']) * pos['quantity']
                else:
                    pos['unrealized_pnl'] = (pos['entry_price'] - price) * pos['quantity']
    
    def total_unrealized_pnl(self) -> float:
        """Toplam gerçekleşmemiş kar/zarar."""
        return sum(pos.get('unrealized_pnl', 0) for pos in self.positions.values())
    
    def total_portfolio_value(self) -> float:
        """Toplam portföy değeri."""
        return self.cash + self.current_total_exposure()
    
    # ═══════════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════
    
    def _load_state(self):
        """State'i dosyadan yükle."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.positions = state.get('positions', {})
                    self.cash = state.get('cash', self.initial_capital)
                    self.realized_pnl = state.get('realized_pnl', 0.0)
                    self.trade_history = state.get('trade_history', [])
            except Exception as e:
                print(f"State yüklenirken hata: {e}")
    
    def _save_state(self):
        """State'i dosyaya kaydet."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump({
                'positions': self.positions,
                'cash': self.cash,
                'realized_pnl': self.realized_pnl,
                'trade_history': self.trade_history,
                'last_updated': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def get_summary(self) -> dict:
        """Portföy özeti."""
        return {
            'cash': self.cash,
            'positions_count': self.position_count(),
            'total_exposure': self.current_total_exposure(),
            'exposure_ratio': self.exposure_ratio(),
            'unrealized_pnl': self.total_unrealized_pnl(),
            'realized_pnl': self.realized_pnl,
            'total_portfolio_value': self.total_portfolio_value(),
            'positions': list(self.positions.keys())
        }
    
    def reset(self):
        """Portföyü sıfırla."""
        self.positions = {}
        self.cash = self.initial_capital
        self.realized_pnl = 0.0
        self.trade_history = []
        self._save_state()
