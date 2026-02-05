import pandas as pd
import numpy as np
import os
from datetime import datetime

class FeatureStore:
    def __init__(self, base_dir='data/feature_store'):
        """
        Feature Store yöneticisi.
        Verileri 'Parquet' formatında saklar.
        """
        self.base_dir = base_dir
        self.fundamentals_path = os.path.join(base_dir, 'fundamentals.parquet')
        self.market_data_path = os.path.join(base_dir, 'market_data.parquet') # Gelecek kullanımı için
        
        # Dizini oluştur
        os.makedirs(self.base_dir, exist_ok=True)
        
    def save_fundamentals(self, df: pd.DataFrame):
        """
        Temel analiz verilerini Parquet olarak kaydeder.
        Veri tiplerini optimize eder.
        """
        # Tarih formatını garantiye al
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            
        # Kategorik veriler (Ticker, Sector vs) - Parquet için optimize edilebilir
        # Şimdilik string kalsın.
        
        # Kaydet (Compression: Snappy default, fast)
        print(f"[FeatureStore] Saving fundamentals to {self.fundamentals_path}...")
        df.to_parquet(self.fundamentals_path, engine='pyarrow', index=False)
        print("[FeatureStore] Save complete.")
        
    def load_fundamentals(self, tickers=None, start_date=None, end_date=None) -> pd.DataFrame:
        """
        Temel analiz verilerini okur. Filtreleme yapar.
        Eksik veri durumunda AKILLI SENTETİK VERİ ile tamamlayabilir.
        """
        if not os.path.exists(self.fundamentals_path):
            print("[FeatureStore] Fundamentals file not found.")
            return pd.DataFrame()
            
        # Pyarrow ile predicate pushdown (filtreli okuma) yapılabilir ama 
        # şimdilik tümünü yükleyip pandas ile filtrelemek 80k satır için daha hızlı/kolay.
        df = pd.read_parquet(self.fundamentals_path, engine='pyarrow')
        
        # Eğer start_date belirtilmişse ve veri o tarihten önce başlıyorsa sorun yok.
        # Ama veri eksikse (örneğin 2015-2020 boşsa) sentetik doldur.
        
        # Şimdilik sadece basit filtreleme yapalım, otomatik doldurmayı
        # ayrı bir metod olarak ekleyelim veya backtest öncesi çalıştıralım.
        
        if tickers:
            df = df[df['Ticker'].isin(tickers)]
            
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
            
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
            
        return df

    def get_augmented_fundamentals(self, tickers, start_date, end_date):
        """
        Gerçek veriyi getirir, eksik kısımları (özellikle eski tarihleri)
        AugmentedFeatureGenerator ile tamamlar.
        """
        from core.augmented_feature_generator import augmented_generator
        
        # 1. Mevcut Gerçek Veriyi Yükle
        real_df = self.load_fundamentals(tickers=tickers)
        
        # Sonuç DataFrame
        final_dfs = []
        
        req_start = pd.to_datetime(start_date)
        req_end = pd.to_datetime(end_date)
        
        for ticker in tickers:
            ticker_real = real_df[real_df['Ticker'] == ticker].sort_values('Date')
            
            # Gerçek verinin kapsadığı aralık
            if not ticker_real.empty:
                real_min = ticker_real['Date'].min()
                real_max = ticker_real['Date'].max()
                
                # Eksik kısımlar?
                frames = [ticker_real]
                
                # Başlangıçta eksik varsa (Backfill with Synthetic)
                if req_start < real_min:
                    print(f"[{ticker}] Generating synthetic history: {req_start.date()} -> {real_min.date()}")
                    syn_df = augmented_generator.generate_synthetic_data(
                        ticker, req_start, real_min - pd.Timedelta(days=1)
                    )
                    frames.append(syn_df)
                    
                # Bitişte eksik varsa (Genelde olmaz ama)
                if req_end > real_max:
                     pass # Geleceği tahmin etmiyoruz, sadece boşluk dolduruyoruz
                     
                combined = pd.concat(frames).sort_values('Date')
                
                # Tarih filtresi (istenen aralık)
                combined = combined[(combined['Date'] >= req_start) & (combined['Date'] <= req_end)]
                final_dfs.append(combined)
            else:
                # Hiç veri yoksa tamamen sentetik
                print(f"[{ticker}] No real data. Generating FULL synthetic: {req_start.date()} -> {req_end.date()}")
                syn_df = augmented_generator.generate_synthetic_data(ticker, req_start, req_end)
                final_dfs.append(syn_df)
                
        if final_dfs:
            return pd.concat(final_dfs).reset_index(drop=True)
        return pd.DataFrame()

    def import_from_excel(self, excel_path: str):
        """
        Mevcut Excel dosyasını Feature Store'a aktarır.
        """
        print(f"[FeatureStore] Importing legacy data from {excel_path}...")
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel file not found: {excel_path}")
            
        df = pd.read_excel(excel_path)
        
        # Temizlik ve Tip Dönüşümü
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            
        # Sayısal kolonları zorla
        numeric_cols = df.columns.drop(['Ticker', 'Date'], errors='ignore')
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        self.save_fundamentals(df)
        return df

    def get_latest_ratios(self, ticker: str) -> dict:
        """Belirli bir hisse için en son rasyoları döner (Canlı işlem için)"""
        df = self.load_fundamentals(tickers=[ticker])
        if df.empty:
            return {}
            
        last_row = df.iloc[-1]
        return last_row.to_dict()

# Tekil kullanım için global instance
feature_store = FeatureStore()
