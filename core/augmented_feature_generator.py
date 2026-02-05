import pandas as pd
import numpy as np
from core.feature_store import feature_store
import config

class AugmentedFeatureGenerator:
    def __init__(self):
        """
        Learns from real data distributions to generate smart synthetic data.
        """
        self.stats_cache = {}
        self.learn_distributions()

    def learn_distributions(self):
        """
        Feature Store'daki veriyi okur ve sektör bazlı istatistikleri çıkarır.
        """
        df = feature_store.load_fundamentals()
        if df.empty: return

        # Sektör ekle
        df['Sector'] = df['Ticker'].apply(lambda x: config.get_sector(x))
        
        ratios = ['Forward_PE', 'PB_Ratio', 'EBITDA_Margin', 'Debt_to_Equity']
        sectors = df['Sector'].unique()
        
        for sector in sectors:
            sector_df = df[df['Sector'] == sector]
            self.stats_cache[sector] = {}
            
            for ratio in ratios:
                if ratio not in sector_df.columns: continue
                
                # Temizle (Outlier removal)
                data = pd.to_numeric(sector_df[ratio], errors='coerce').dropna()
                if data.empty: continue

                Q1 = data.quantile(0.25); Q3 = data.quantile(0.75); IQR = Q3 - Q1
                data = data[~((data < (Q1 - 1.5 * IQR)) | (data > (Q3 + 1.5 * IQR)))]
                if data.empty: continue
                
                self.stats_cache[sector][ratio] = {
                    "mean": data.mean(),
                    "std": data.std(),
                    "min": data.min(),
                    "max": data.max(),
                    "skew": data.skew(),
                    "last_value": data.iloc[-1] # Random walk başlangıcı için
                }

    def generate_synthetic_data(self, ticker, start_date, end_date):
        """
        Belirtilen ticker ve tarih aralığı için sentetik veri üretir.
        Geometric Brownian Motion (GBM) veya Mean Reverting Ornstein-Uhlenbeck (OU) süreci kullanır.
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        date_range = pd.date_range(start=start, end=end, freq='D')
        
        sector = config.get_sector(ticker)
        stats = self.stats_cache.get(sector, self.stats_cache.get('Other', {}))
        
        synthetic_df = pd.DataFrame(index=date_range)
        synthetic_df['Ticker'] = ticker
        synthetic_df['Date'] = date_range
        synthetic_df['Sector'] = sector
        
        for ratio, params in stats.items():
            # Ornstein-Uhlenbeck Process (Mean Reverting)
            # dx = theta * (mu - x) * dt + sigma * dW
            # Rasyolar genelde ortalamaya döner
            
            mu = params['mean']
            sigma = params['std']
            
            # Parametreler (Hardcoded calibration for now)
            theta = 0.1 # Mean reversion speed
            dt = 1/252 # Daily step
            
            values = [mu] # Start at mean initially
            current_val = mu
            
            # Generate path
            # Vectorized implementation of OU is harder, loop is fine for generating history
            noise = np.random.normal(0, np.sqrt(dt), len(date_range))
            
            x = np.zeros(len(date_range))
            x[0] = mu # Start at mean
            
            for t in range(1, len(date_range)):
                dx = theta * (mu - x[t-1]) * dt + sigma * noise[t]
                x[t] = x[t-1] + dx
                
                # Clip to realistic bounds
                if ratio == 'PB_Ratio': x[t] = max(0.1, x[t])
                elif ratio == 'Forward_PE': x[t] = max(1.0, x[t]) # Negatif PE olabilir ama genelde 0-100 arası
            
            synthetic_df[ratio] = x
            
        return synthetic_df

# Global Instance
augmented_generator = AugmentedFeatureGenerator()
