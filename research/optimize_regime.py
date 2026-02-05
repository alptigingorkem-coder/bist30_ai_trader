import optuna
import pandas as pd
import numpy as np
import sys
import os

# Proje kök dizinini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.regime_detection import RegimeDetector
import config

class RegimeOptimizer:
    def __init__(self, ticker="XU100.IS", timeframe='W'):
        self.ticker = ticker
        self.timeframe = timeframe
        self.data = None
        
    def load_data(self):
        print(f"Veri indiriliyor: {self.ticker}...")
        loader = DataLoader()
        # Tarih aralığı geniş olsun
        loader.start_date = "2015-01-01"
        
        # XU100 verisi çek (Makro ticker map'ten bulmaya gerek yok direkt indirelim veya loader kullanalım)
        # DataLoader varsayılan olarak hisse indirir, XU100 için de çalışır.
        raw_data = loader.fetch_stock_data(self.ticker)
        
        # Feature Engineering (Volatility vb. hesaplamak için)
        fe = FeatureEngineer(raw_data)
        # Sadece gerekli indikatörleri ekle
        fe.add_technical_indicators()
        fe.add_time_features()
        fe.add_derived_features()
        
        # Volatility yıllıklandırma için scale factor
        # FeatureEngineer zaten Volatility_20 hesaplıyor (std dev of returns)
        
        self.data = fe.data.dropna()
        print(f"Veri hazır: {len(self.data)} bar.")

    def objective(self, trial):
        # 1. Parametre Önerileri
        vol_high = trial.suggest_float('volatility_high', 0.20, 0.80)
        # vol_low kullanılmıyor ama mantıksal completeness için ekleyelim mi? Hayır code kullanmıyor.
        mom_thresh = trial.suggest_int('momentum_threshold', 40, 70)
        min_days = trial.suggest_int('min_regime_days', 2, 10)
        
        thresholds = {
            'volatility_high': vol_high,
            'momentum_threshold': mom_thresh,
            'min_regime_days': min_days
        }
        
        # 2. Rejim Tespiti
        detector = RegimeDetector(self.data, thresholds)
        df_regime = detector.detect_regimes(verbose=False)
        
        # 3. Basit Backtest (Market Timing)
        # Strateji:
        # Trend_Up (2) -> %100 XU100
        # Sideways (0) -> %0 (Nakit) - Risk off
        # Crash_Bear (1) -> %0 (Nakit)
        
        # Sinyal (0 veya 1) - Shift 1 (Geleceği görmemek için)
        signal = df_regime['Regime_Num'].apply(lambda x: 1.0 if x == 2 else 0.0).shift(1).fillna(0)
        
        # Getiri Hesabı
        market_returns = df_regime['Log_Return']
        strategy_returns = market_returns * signal
        
        # Kümülatif Getiri
        cumulative_return = (1 + strategy_returns).cumprod()
        
        # Metrikler
        total_return = cumulative_return.iloc[-1] - 1
        
        # Max Drawdown
        running_max = cumulative_return.cummax()
        drawdown = (cumulative_return - running_max) / running_max
        max_dd = drawdown.min()
        
        # Calmar Ratio
        if max_dd == 0:
            calmar = 0
        else:
            calmar = total_return / abs(max_dd)
            
        # Sharpe Ratio (Yıllık)
        mean_ret = strategy_returns.mean() * 52 # Weekly varsayımı
        std_ret = strategy_returns.std() * np.sqrt(52)
        sharpe = (mean_ret - 0.05) / std_ret if std_ret > 0 else 0
        
        # Hedef: Calmar ve Sharpe kombinasyonu
        # Aşırı defansif olup hiç işlem açmazsa Calmar 0 olur.
        # En azından belli sayıda trade yapmalı.
        
        trade_count = signal.diff().abs().sum()
        if trade_count < 5: # Çok az işlem
            return -1.0
            
        return calmar
        
    def optimize(self, n_trials=50):
        if self.data is None:
            self.load_data()
            
        study = optuna.create_study(direction='maximize')
        print(f"Optimizasyon başlıyor ({n_trials} deneme)...")
        study.optimize(self.objective, n_trials=n_trials)
        
        print("\n" + "="*40)
        print("OPTIMIZASYON SONUCLARI")
        print("="*40)
        print(f"En iyi Calmar Ratio: {study.best_value:.4f}")
        print("En iyi Parametreler:")
        for k, v in study.best_params.items():
            print(f"  {k}: {v}")
            
        return study.best_params

if __name__ == "__main__":
    optimizer = RegimeOptimizer()
    optimizer.optimize(n_trials=50)
