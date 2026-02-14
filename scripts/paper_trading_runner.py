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
import joblib

class PaperTrader:
    def __init__(self):
        self.model_path = "models/saved/global_ranker.pkl"
        self.model = None
        self.loader = DataLoader()
        self.risk_manager = RiskManager()
        self.portfolio = {
            'cash': 100000.0,
            'holdings': {}, # ticker: qty
            'equity': 100000.0,
            'history': []
        }
        self.load_model()
        print("🚀 Paper Trader Başlatıldı (Sanal Bakiye: 100,000 TL)")
        
    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print(f"✅ Model yüklendi: {self.model_path}")
        else:
            print(f"❌ Model bulunamadı: {self.model_path}. Lütfen önce 'train_models.py' çalıştırın.")
            sys.exit(1)

    def update_market_data(self):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Piyasa Verisi Kontrol Ediliyor...")

    def check_signals(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sinyaller Taranıyor...")
        
        for ticker in config.TICKERS:
            try:
                # 1. Canlı Veri Çek (Makro veriler dahil)
                # Model eğitimi get_combined_data ile yapıldığı için burada da onu kullanmalıyız.
                df = self.loader.get_combined_data(ticker)
                
                if df is None or df.empty: continue
                
                # Canlı simülasyon için son verinin güncel olup olmadığını kontrol edebiliriz
                # ancak Yahoo verisi bazen gecikmeli gelir.
                
                # 2. Feature Engineering
                # Son satır için feature hesapla
                engineer = FeatureEngineer(df)
                df_processed = engineer.process_all(ticker)
                
                if df_processed.empty: continue
                
                # Son veriyi al (Bugün/Dün kapanışı)
                last_row = df_processed.iloc[[-1]] 
                current_price = last_row['Close'].values[0]
                current_date = last_row.index[-1]
                
                # Model Tahmini
                if self.model:
                    # Feature Alignment
                    if hasattr(self.model, 'feature_name_'):
                        model_features = self.model.feature_name_
                        
                        # Eksik feature varsa 0 ile doldur
                        for f in model_features:
                            if f not in last_row.columns:
                                last_row[f] = 0
                                
                        # Fazla feature varsa at ve sıralamayı eşle
                        last_row = last_row[model_features]
                    
                    prediction = self.model.predict(last_row)
                    score = prediction[0]
                    
                    # Loglama
                    print(f"   {ticker:<10} | Fiyat: {current_price:.2f} | Skor: {score:.4f}")
                    
                    # Basit Alım/Satım Mantığı (Risk Manager ile)
                    # Mevcut pozisyon var mı?
                    in_position = ticker in self.portfolio['holdings'] and self.portfolio['holdings'][ticker] > 0
                    
                    # Risk Manager Kontrolü (Stop Loss / Take Profit)
                    # Not: Burada tam bir simülasyon için giriş fiyatını vb. tutmalıyız.
                    # Basitleştirilmiş:
                    
                    if score > 0.8 and not in_position:
                        # AL Sinyali
                        qty = int(self.portfolio['cash'] * 0.10 / current_price) # %10 portföy
                        if qty > 0:
                            cost = qty * current_price
                            self.portfolio['cash'] -= cost
                            self.portfolio['holdings'][ticker] = qty
                            print(f"   🟢 ALIM YAPILDI: {ticker} x {qty} @ {current_price:.2f}")
                            
                    elif score < 0.2 and in_position:
                        # SAT Sinyali
                        qty = self.portfolio['holdings'][ticker]
                        revenue = qty * current_price
                        self.portfolio['cash'] += revenue
                        del self.portfolio['holdings'][ticker]
                        print(f"   🔴 SATIŞ YAPILDI: {ticker} x {qty} @ {current_price:.2f}")
                        
            except Exception as e:
                print(f"   Hata ({ticker}): {e}")

    def run(self):
        print("Otomatik pilot başlatılıyor... (CTRL+C ile durdurun)")
        
        while True:
            self.check_signals()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Bekleniyor (60 saniye)...")
            time.sleep(60)

if __name__ == "__main__":
    trader = PaperTrader()
    # Tek seferlik test
    trader.check_signals()
    # Sürekli döngüyü başlatmak için aşağıdaki satırı açın:
    # trader.run()
