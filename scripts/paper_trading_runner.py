import time
import pandas as pd
import numpy as np
# import schedule (Removed dependency)
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from core.risk_manager import RiskManager
from core.execution import ExecutionManager
import joblib

from utils.logging_config import get_logger
log = get_logger(__name__)

class PaperTrader:
    def __init__(self):
        self.model_path = "models/saved/global_ranker.pkl"
        self.model = None
        self.loader = DataLoader()
        self.risk_manager = RiskManager() 
        self.execution_manager = ExecutionManager(commission_rate=0.002)
        
        # 10.000 TL Başlangıç Sermayesi
        self.initial_capital = 10000.0
        self.portfolio = {
            'cash': self.initial_capital,
            'holdings': {}, # ticker: qty
            'equity': self.initial_capital,
            'history': []
        }
        self.load_model()
        log.info(f"🚀 Paper Trader Başlatıldı (Sanal Bakiye: {self.initial_capital:,.2f} TL)")
        
    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            log.info(f"✅ Model yüklendi: {self.model_path}")
        else:
            log.error(f"❌ Model bulunamadı: {self.model_path}. Lütfen önce 'train_models.py' çalıştırın.")
            sys.exit(1)

    def update_market_data(self):
        log.info("Piyasa Verisi Kontrol Ediliyor...")

    def check_signals(self):
        log.info("Sinyaller Taranıyor...")
        
        for ticker in config.TICKERS:
            try:
                # 1. Canlı Veri Çek
                df = self.loader.get_combined_data(ticker)
                
                if df is None or df.empty: continue
                
                # 2. Feature Engineering
                engineer = FeatureEngineer(df)
                df_processed = engineer.process_all(ticker)
                
                if df_processed.empty: continue
                
                # Son veriyi al
                last_row = df_processed.iloc[[-1]] 
                raw_price = last_row['Close'].values[0]
                
                # Execution Manager ile Fiyat Simülasyonu
                current_price = self.execution_manager.simulate_slippage(raw_price)
                
                # Model Tahmini
                if self.model:
                    # Feature Alignment
                    if hasattr(self.model, 'feature_name_'):
                        model_features = self.model.feature_name_
                        for f in model_features:
                            if f not in last_row.columns: last_row[f] = 0
                        last_row = last_row[model_features]
                    
                    prediction = self.model.predict(last_row)
                    score = prediction[0]
                    
                    log.info(f"   {ticker:<10} | Fiyat: {current_price:.2f} | Skor: {score:.4f}")
                    
                    # --- İŞLEM MANTIĞI (EXECUTION) ---
                    in_position = ticker in self.portfolio['holdings'] and self.portfolio['holdings'][ticker] > 0
                    
                    # ALIM SİNYALİ (> 0.8)
                    if score > 0.8 and not in_position:
                        target_allocation = self.portfolio['equity'] * 0.20 
                        qty = self.execution_manager.calculate_optimal_lots(current_price, target_allocation)
                        
                        if self.execution_manager.validate_order(ticker, qty, current_price, self.portfolio['cash']):
                            cost = qty * current_price * (1 + self.execution_manager.commission_rate)
                            self.portfolio['cash'] -= cost
                            self.portfolio['holdings'][ticker] = qty
                            log.info(f"   🟢 ALIM YAPILDI: {ticker} x {qty} @ {current_price:.2f} (Tutar: {cost:.2f})")
                            
                    # SATIŞ SİNYALİ (< 0.2)
                    elif score < 0.2 and in_position:
                        qty = self.portfolio['holdings'][ticker]
                        revenue = (qty * current_price) * (1 - self.execution_manager.commission_rate)
                        self.portfolio['cash'] += revenue
                        del self.portfolio['holdings'][ticker]
                        log.info(f"   🔴 SATIŞ YAPILDI: {ticker} x {qty} @ {current_price:.2f} (Gelir: {revenue:.2f})")
                        
            except Exception as e:
                log.error(f"   Hata ({ticker}): {e}")

    def run(self):
        log.info("🕒 Gün Sonu (EOD) Trader Modu Başlatıldı.")
        log.info("ℹ️  Sistem her gün saat 18:05'te (Piyasa Kapanış Seansı) işlem yapacak.")
        
        last_run_date = None
        
        while True:
            now = datetime.now()
            target_hour = 18
            target_minute = 5
            
            if last_run_date != now.date():
                if now.hour == target_hour and now.minute >= target_minute:
                    log.info(f"🔔 Piyasa Kapanış Seansı Başladı ({now.strftime('%H:%M')})!")
                    self.check_signals()
                    last_run_date = now.date()
                    log.info(f"✅ Bugünü ({last_run_date}) tamamladık.")
                else:
                    if now.minute == 0 and now.second < 5:
                        remaining = (datetime(now.year, now.month, now.day, target_hour, target_minute) - now).total_seconds() / 3600
                        if remaining > 0:
                            log.info(f"Kapanışa {remaining:.1f} saat var. Bekleniyor...")
            
            time.sleep(10)

if __name__ == "__main__":
    trader = PaperTrader()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        log.info("🛠️ TEST MODU: 18:05 beklenmiyor, hemen çalıştırılıyor...")
        trader.check_signals()
    else:
        trader.run()
