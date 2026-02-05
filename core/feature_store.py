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
        Temel analiz verilerini okur ve filtreleme yapar.
        """
        if not os.path.exists(self.fundamentals_path):
            print("[FeatureStore] Fundamentals file not found.")
            return pd.DataFrame()
            
        df = pd.read_parquet(self.fundamentals_path, engine='pyarrow')
        
        if tickers:
            df = df[df['Ticker'].isin(tickers)]
            
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
            
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
            
        return df
        
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
