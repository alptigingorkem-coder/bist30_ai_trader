import pandas as pd
import numpy as np
import os
import sys
import glob
import joblib
from datetime import datetime

# Proje Kök Dizini
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from configs import banking as config_banking
from configs import holding as config_holding
from configs import industrial as config_industrial
from configs import growth as config_growth

from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.regime_detection import RegimeDetector
from models.beta_model import BetaModel
from models.alpha_model import AlphaModel
from core.backtesting import Backtester

class WalkForwardBacktester:
    def __init__(self):
        self.sectors = {
            'BANKING': {'config': config_banking, 'tickers': config_banking.TICKERS},
            'HOLDING': {'config': config_holding, 'tickers': config_holding.TICKERS},
            'INDUSTRIAL': {'config': config_industrial, 'tickers': config_industrial.TICKERS},
            'GROWTH': {'config': config_growth, 'tickers': config_growth.TICKERS}
        }
        self.loader = DataLoader(start_date="2015-01-01")
        self.cache_data = {} # Ticker -> Processed DF (Full History)
        
    def prepare_data(self):
        """Tüm hisselerin verisini indirir ve feature eng. yapar (Zaman kazanmak için bir kere)."""
        print("Veriler hazırlanıyor...")
        all_tickers = []
        for s in self.sectors.values():
            all_tickers.extend(s['tickers'])
        all_tickers = sorted(list(set(all_tickers)))
        
        for ticker in all_tickers:
            # print(f"  Processing {ticker}...")
            raw_data = self.loader.get_combined_data(ticker)
            if raw_data is None or len(raw_data) < 100:
                continue
                
            fe = FeatureEngineer(raw_data)
            df = fe.process_all(ticker=ticker)
            
            # Regime Detection (Geçmişe bakarak yapılıyor, leakage yok sayılır ama 
            # idealde train set üzerinden threshold belirlenmeli. 
            # Yine de şimdilik statik threshold veya adaptive ile devam)
            # Not: Adaptive Regime kullanılırsa leakage olmaz çünkü quantile geçmiş veriden.
            rd = RegimeDetector(df)
            df = rd.detect_regimes(verbose=False)
            
            # Macro Gate Mask (Vektörel)
            # Backtest sırasında yıl yıl bakacağız ama maskeyi şimdiden çıkarabiliriz.
            if getattr(config, 'ENABLE_MACRO_GATE', True):
                # FeatureEngineer clean_data ile makro sütunları siliyor.
                # O yüzden raw_data'dan hesaplamamız lazımdı.
                # FeatureEngineer process_all içinde temizlediği için burada makroya erişim zor.
                # Tekrar raw alalım veya clean öncesi maske saklayalım.
                # Çözüm: Utils içinde `process_all` makro gate maskesini döndürmüyor.
                # Tekrar raw üzerinden maske çıkarıp index ile eşleştireceğiz.
                # Hızlı yöntem: FE zaten clean_data yapıyor.
                
                # Raw data tekrar
                raw_macro = self.loader.get_combined_data(ticker)
                from run_backtest import get_vectorized_macro_gate
                gate_mask = get_vectorized_macro_gate(raw_macro, config.MACRO_GATE_THRESHOLDS)
                gate_mask = gate_mask.reindex(df.index).fillna(False) # Hizala
                df['Macro_Gate_Blocked'] = gate_mask
            else:
                df['Macro_Gate_Blocked'] = False
            
            self.cache_data[ticker] = df
            
        print(f"Toplam {len(self.cache_data)} hisse verisi hazır.")

    def run(self, start_year=2018, end_year=2025):
        """
        Yıllık döngü:
        Train: Başlangıç - (Yıl-1) sonu
        Test: Yıl başı - Yıl sonu
        """
        if not self.cache_data:
            self.prepare_data()
            
        final_results = []
        
        # Yıl döngüsü
        current_year = start_year
        while current_year <= end_year:
            print(f"\n{'='*60}")
            print(f"WALK-FORWARD YIL: {current_year}")
            print(f"{'='*60}")
            
            # 1. SEKTÖR MODELLERİNİ EĞİT (Train Data: < current_year)
            sector_models = {}
            
            for sector_name, info in self.sectors.items():
                print(f"  Eğitiliyor: {sector_name} Sektörü (Data < {current_year})...")
                
                # Sektördeki tüm hisselerin eğitim verisini topla
                train_frames = []
                for t in info['tickers']:
                    if t in self.cache_data:
                        df = self.cache_data[t]
                        # Filtre: Yıl öncesi
                        train_df = df[df.index.year < current_year]
                        if not train_df.empty:
                            train_frames.append(train_df)
                            
                if not train_frames:
                    print(f"    Uyarı: {sector_name} için eğitim verisi yok.")
                    continue
                    
                full_train_data = pd.concat(train_frames)
                
                # Beta Model (Regression)
                beta = BetaModel(full_train_data, info['config'])
                try:
                    beta.optimize_and_train(n_trials=50) # 50 Trial Optimization (Risk-Adjusted)
                except Exception as e:
                    print(f"    Beta Model Hatası: {e}")
                    beta = None
                
                # Alpha Model (Prediction/Classification or Regression)
                alpha = AlphaModel(full_train_data, info['config'])
                try:
                    alpha.optimize_and_train(n_trials=50)
                except Exception as e:
                    print(f"    Alpha Model Hatası: {e}")
                    alpha = None
                    
                sector_models[sector_name] = {'beta': beta, 'alpha': alpha}
            
            # 2. TEST PERİYODU TAHMİNİ VE BACKTEST (Test Data: == current_year)
            print(f"  Test Ediliyor: {current_year}...")
            
            for ticker in self.cache_data:
                df = self.cache_data[ticker]
                test_df = df[df.index.year == current_year]
                
                # Duplicate Index Fix
                if test_df.empty:
                    continue
                
                # Ensure unique index
                test_df = test_df[~test_df.index.duplicated(keep='first')]
                    
                # Hangi sektör?
                ticker_sector = "HOLDING" # Default
                for s_name, s_info in self.sectors.items():
                    if ticker in s_info['tickers']:
                        ticker_sector = s_name
                        break
                
                if ticker_sector not in sector_models:
                    continue
                    
                models = sector_models[ticker_sector]
                if models['beta'] is None or models['alpha'] is None:
                    continue
                
                # Tahmin Üret
                # Modeller predict metodu içinde prepare_features(is_training=False) çağırır.
                # Bu metod test verisindeki featureları kullanır.
                
                # Wrapper instance oluştur (Train verisi gerekmez, sadece config ve metod)
                # Ancak BetaModel load edilmedi, memorydeki instance'ı kullanıyoruz.
                # Models directly usable.
                
                # Wrapper instance for prediction (BetaModel uses self.data, so we need a fresh instance with test_df)
                # Beta
                beta_wrapper = BetaModel(test_df, info['config'])
                beta_wrapper.model = models['beta'].model
                
                # Alpha
                alpha_wrapper = AlphaModel(test_df, info['config'])
                alpha_wrapper.model = models['alpha'].model

                try:
                    beta_preds = beta_wrapper.predict(test_df) 
                    alpha_preds = alpha_wrapper.predict(test_df)
                except Exception as e:
                    # print(f"    Pred Error {ticker}: {e}")
                    continue
                
                if beta_preds is None or alpha_preds is None:
                    continue
                    
                # ALIGNMENT FIX: Reindex to match test_df (fill missing predictions with 0)
                beta_preds = beta_preds.reindex(test_df.index).fillna(0.0)
                alpha_preds = alpha_preds.reindex(test_df.index).fillna(0.0)
                
                # Sinyal Birleştirme
                # (Trend_Up -> Beta, Sideways -> Alpha, Crash -> 0)
                final_preds = pd.Series(0.0, index=test_df.index)
                
                mask_trend = (test_df['Regime_Num'] == 2)
                mask_side = (test_df['Regime_Num'] == 0)
                mask_crash = (test_df['Regime_Num'] == 1)
                
                # Weights (Basit 0.7 / 0.3)
                final_preds[mask_trend] = (beta_preds[mask_trend] * 0.7) + (alpha_preds[mask_trend] * 0.3)
                final_preds[mask_side] = (beta_preds[mask_side] * 0.3) + (alpha_preds[mask_side] * 0.7)
                final_preds[mask_crash] = 0.0
                
                # Confidence to Size
                threshold = 0.005
                weights = final_preds.apply(lambda x: min(x * 10, 1.0) if x > threshold else 0.0)
                
                # Kelly Config (Varsa kullan)
                # Strateji sınıfı olmadığı için manual hesap:
                # Ancak burada basitlik için linear scaling devam.
                
                # Macro Gate Uygula
                if 'Macro_Gate_Blocked' in test_df.columns:
                    weights[test_df['Macro_Gate_Blocked']] = 0.0
                    
                # Backtest (Tek yıl için)
                bt = Backtester(test_df, initial_capital=10000, commission=config.COMMISSION_RATE)
                res_df = bt.run_backtest(weights)
                
                metrics = bt.calculate_metrics()
                if metrics:
                    metrics['Ticker'] = ticker
                    metrics['Year'] = current_year
                    metrics['Sector'] = ticker_sector
                    final_results.append(metrics)
                    
            current_year += 1
            
        # Raporlama
        if final_results:
            self.generate_report(pd.DataFrame(final_results))
            
    def generate_report(self, df):
        print("\n" + "="*80)
        print("WALK-FORWARD BACKTEST RAPORU (YILLIK)")
        print("="*80)
        
        # Yıllık Ortalamalar
        yearly_summary = df.groupby('Year')[['Total Return', 'Max Drawdown', 'Sharpe Ratio', 'Num Trades', 'Win Rate']].mean()
        print("\nYıllara Göre Ortalama Performans:")
        print(yearly_summary)
        
        # Kümülatif (Basit toplama değil, bileşik getiri simülasyonu mantıklı olur ama ortalama fikir verir)
        print("\nGenel Ortalamalar:")
        print(df[['Total Return', 'Max Drawdown', 'Sharpe Ratio']].mean())
        
        # Dosyaya kaydet
        if not os.path.exists("reports"): os.makedirs("reports")
        df.to_csv("reports/walk_forward_results.csv", index=False)
        print("\nDetaylı sonuçlar kaydedildi: reports/walk_forward_results.csv")
        yearly_summary.to_csv("reports/walk_forward_yearly_summary.csv")

if __name__ == "__main__":
    wfb = WalkForwardBacktester()
    # Test için 2023-2024 (Hızlı)
    # Gerçek: 2018-2025
    wfb.run(start_year=2023, end_year=2024)
