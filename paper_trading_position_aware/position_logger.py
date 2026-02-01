"""
Position-Aware Paper Trading - Logging Module
JSON (detay) ve CSV (özet) formatında logging.
"""

import json
import os
import csv
from datetime import datetime
from typing import Dict, List

class PositionLogger:
    """
    Position-Aware Paper Trading için loglama.
    - Günlük JSON: Her karar detaylı
    - Özet CSV: Aggregate metrikler
    """
    
    def __init__(self, 
                 daily_log_dir: str = "paper_trading_position_aware/logs/daily",
                 summary_log_dir: str = "paper_trading_position_aware/logs/summary"):
        
        self.daily_log_dir = daily_log_dir
        self.summary_log_dir = summary_log_dir
        
        # Dizinleri oluştur
        os.makedirs(daily_log_dir, exist_ok=True)
        os.makedirs(summary_log_dir, exist_ok=True)
        
        self._daily_buffer: List[dict] = []
    
    def log_decision(self, 
                     snapshot: dict,
                     decision: dict,
                     portfolio_before: dict,
                     portfolio_after: dict,
                     execution_result: dict):
        """
        Tek bir kararı logla.
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'ticker': snapshot.get('ticker', ''),
            'signal': snapshot.get('action', 'WAIT'),
            'confidence': snapshot.get('confidence', 0),
            'regime': snapshot.get('regime', ''),
            'macro_blocked': snapshot.get('macro_blocked', False),
            'current_price': snapshot.get('current_price', 0),
            
            # Pozisyon kararı
            'decision_action': decision.get('action', ''),
            'decision_reason': decision.get('reason', ''),
            'decision_quantity': decision.get('quantity', 0),
            
            # Portföy durumu
            'portfolio_before': {
                'positions_count': portfolio_before.get('positions_count', 0),
                'exposure_ratio': portfolio_before.get('exposure_ratio', 0),
                'cash': portfolio_before.get('cash', 0),
                'total_value': portfolio_before.get('total_portfolio_value', 0)
            },
            'portfolio_after': {
                'positions_count': portfolio_after.get('positions_count', 0),
                'exposure_ratio': portfolio_after.get('exposure_ratio', 0),
                'cash': portfolio_after.get('cash', 0),
                'total_value': portfolio_after.get('total_portfolio_value', 0)
            },
            
            # Execution sonucu
            'execution_success': execution_result.get('success', False),
            'realized_pnl': execution_result.get('realized_pnl', 0)
        }
        
        self._daily_buffer.append(log_entry)
        self._append_to_daily_file(log_entry)
    
    def _append_to_daily_file(self, entry: dict):
        """Günlük JSON dosyasına append."""
        today = datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(self.daily_log_dir, f"position_log_{today}.json")
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def flush_session_summary(self, session_metrics: dict):
        """Oturum sonunda özet kaydet."""
        today = datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(self.summary_log_dir, f"session_summary_{today}.json")
        
        summary = {
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'total_decisions': len(self._daily_buffer),
            **session_metrics
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # CSV'ye de ekle
        self._append_to_csv_summary(summary)
        
        # Buffer'ı temizle
        self._daily_buffer = []
    
    def _append_to_csv_summary(self, summary: dict):
        """Özet CSV'ye append."""
        filepath = os.path.join(self.summary_log_dir, "all_sessions.csv")
        
        file_exists = os.path.exists(filepath)
        
        # Flat dict oluştur
        flat = {
            'date': summary.get('date'),
            'timestamp': summary.get('timestamp'),
            'total_decisions': summary.get('total_decisions', 0),
            'open_positions': summary.get('open_positions', 0),
            'close_positions': summary.get('close_positions', 0),
            'hold_existing': summary.get('hold_existing', 0),
            'ignore_signals': summary.get('ignore_signals', 0),
            'realized_pnl': summary.get('realized_pnl', 0),
            'unrealized_pnl': summary.get('unrealized_pnl', 0),
            'total_exposure': summary.get('total_exposure', 0),
            'portfolio_value': summary.get('portfolio_value', 0)
        }
        
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=flat.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(flat)
    
    def load_daily_logs(self, date: str = None) -> List[dict]:
        """Belirli bir günün loglarını yükle."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        filepath = os.path.join(self.daily_log_dir, f"position_log_{date}.json")
        
        if not os.path.exists(filepath):
            return []
        
        logs = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        return logs
    
    def load_all_summaries(self) -> List[dict]:
        """Tüm özet CSV'yi yükle."""
        filepath = os.path.join(self.summary_log_dir, "all_sessions.csv")
        
        if not os.path.exists(filepath):
            return []
        
        summaries = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                summaries.append(row)
        
        return summaries
    
    def get_session_stats(self) -> dict:
        """Mevcut oturum istatistikleri."""
        if not self._daily_buffer:
            return {}
        
        stats = {
            'total_decisions': len(self._daily_buffer),
            'open_positions': 0,
            'close_positions': 0,
            'hold_existing': 0,
            'scale_in': 0,
            'scale_out': 0,
            'ignore_signals': 0,
            'realized_pnl': 0.0
        }
        
        for entry in self._daily_buffer:
            action = entry.get('decision_action', '')
            
            if action == 'OPEN_POSITION':
                stats['open_positions'] += 1
            elif action == 'CLOSE_POSITION':
                stats['close_positions'] += 1
            elif action == 'HOLD_EXISTING':
                stats['hold_existing'] += 1
            elif action == 'SCALE_IN':
                stats['scale_in'] += 1
            elif action == 'SCALE_OUT':
                stats['scale_out'] += 1
            elif action == 'IGNORE_SIGNAL':
                stats['ignore_signals'] += 1
            
            stats['realized_pnl'] += entry.get('realized_pnl', 0)
        
        return stats
