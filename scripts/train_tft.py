
import sys
import os
import torch
import pandas as pd
import joblib
from datetime import datetime, timedelta
from pytorch_forecasting import TimeSeriesDataSet

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.transformer_model import BIST30TransformerModel
from utils.logging_config import get_logger

log = get_logger(__name__)

def main():
    log.info("🚀 TFT Model Eğitimi Başlıyor...")
    
    # 1. Veri Hazırlığı
    log.info("Veri yükleniyor...")
    loader = DataLoader()
    
    # fetch_stock_data tek bir hisse için çalışır, döngü gerektirir.
    # Ancak burada tüm hisseleri çekmek istiyoruz.
    # DataLoader.fetch_stock_data(ticker) -> DataFrame
    
    raw_data_list = []
    end_date = datetime.now().strftime('%Y-%m-%d')
    for ticker in config.TICKERS:
        try:
            df = loader.fetch_stock_data(ticker)
            if df is not None and not df.empty:
                df['Ticker'] = ticker
                raw_data_list.append(df)
        except Exception as e:
            log.error(f"{ticker} veri çekme hatası: {e}")
            
    if not raw_data_list:
        log.error("Veri yüklenemedi!")
        return
        
    raw_data = pd.concat(raw_data_list)
    
    # Düzeltme: fetch_stock_data index'i zaten Date olabilir.
    if 'Date' not in raw_data.columns and 'Date' not in raw_data.index.names:
         # Index ise resetle
         raw_data = raw_data.reset_index()
         
    # raw_data artık long formatta ve Ticker sütunu var.
    # Aşağıdaki kod buna göre uyarlanmalı.
    
    log.info(f"Toplanan veri boyutu: {raw_data.shape}")

    # Feature Engineering
    log.info("Feature engineering uygulanıyor...")
    fe = FeatureEngineer(raw_data)
    # Batch process all tickers
    processed_dfs = []
    # Multi-index or Loop? fetch_historical_data returns MultiIndex dataframe usually?
    # Actually fetch_historical_data returns a single DF with MultiIndex (Date, Ticker) or Panel
    # Let's check data_loader.py structure if needed, but assuming standard format.
    
    # Adjust for FE pipeline
    # FeatureEngineer.process_all expects single ticker DF usually inside loop or handles it?
    # Let's look at FE implementation again. It seems process_all takes ticker arg but operates on self.data?
    # Actually FE works on the whole self.data provided in init. 
    # If self.data is multi-index, we need to iterate or FE handles it.
    # Looking at live_data_engine it returns dict.
    # But historical_data usually returns MultiIndex DF in this project.
    
    # FE process_all logic:
    # It calls add_technical_indicators which uses 'Close' column.
    # If MultiIndex (Ticker, Attributes) or (Date, Ticker)?
    # config.TICKERS is a list.
    
    # We will loop for safety and concat.
    if isinstance(raw_data.index, pd.MultiIndex):
        # Assuming (Date, Ticker) or (Ticker, Date)
        # Let's flatten to long format for TFT
        df_long = raw_data.reset_index()
    else:
        # Check structure
        df_long = raw_data.reset_index()
    
    # Ensure columns: Date, Ticker, Open, High, Low, Close, Volume
    # Standartize
    if 'Date' not in df_long.columns and 'index' in df_long.columns:
        df_long.rename(columns={'index': 'Date'}, inplace=True)
        
    # FE Loop
    processed_list = []
    tickers = df_long['Ticker'].unique() if 'Ticker' in df_long.columns else config.TICKERS
    
    # If data is wide format (Ticker columns), melt?
    # Let's assume DataLoader returns long format or we need to handle it.
    # Checking DataLoader.fetch_historical_data... 
    # Usually it downloads via yfinance group_by='ticker' -> MultiIndex (Ticker, Price).
    # We shoud stack it to long format.
    
    if isinstance(raw_data.columns, pd.MultiIndex):
        # (Ticker, OHLCV) -> Stack to (Date, Ticker, OHLCV)
        df_long = raw_data.stack(level=0).reset_index()
        df_long.rename(columns={'level_1': 'Ticker'}, inplace=True)
    
    log.info(f"İşlenecek ticker sayısı: {len(tickers)}")
    
    final_df = pd.DataFrame()
    
    for ticker in tickers:
        # Filter ticker data
        df_tik = df_long[df_long['Ticker'] == ticker].copy()
        if df_tik.empty: continue
        
        # Sort and Set Index for FE
        df_tik.set_index('Date', inplace=True)
        
        # Apply FE
        fe_eng = FeatureEngineer(df_tik)
        df_processed = fe_eng.process_all(ticker=ticker)
        
        # Reset index for concatenation
        df_processed = df_processed.reset_index()
        if 'Ticker' not in df_processed.columns:
            df_processed['Ticker'] = ticker
            
        processed_list.append(df_processed)
        
    if not processed_list:
        log.error("Hiçbir hisse için feature üretilemedi!")
        return

    full_data = pd.concat(processed_list, ignore_index=True)
    full_data['Date'] = pd.to_datetime(full_data['Date'])
    
    # TFT Dataset Hazırlığı
    from utils.features.transformer import prepare_tft_dataset
    
    # Config
    tft_config = {
        'target': 'Log_Return', # Veya Return_1d
        'max_encoder_length': 60,
        'max_prediction_length': 5,
        'static': ['Ticker', 'Sector'] if 'Sector' in full_data.columns else ['Ticker'],
        'known': ['day_of_week', 'month', 'Volume', 'Log_Return'], # Örnek
        'unknown': []
    }
    
    # Sektör bilgisi ekle
    full_data['Sector'] = full_data['Ticker'].apply(config.get_sector)
    
    # Zaman değişkenleri
    full_data['day_of_week'] = full_data['Date'].dt.dayofweek.astype(str).astype('category')
    full_data['month'] = full_data['Date'].dt.month.astype(str).astype('category')
    
    # Sütun isimlerindeki noktaları temizle (PyTorch Forecasting sevmez)
    full_data.columns = [c.replace('.', '_') for c in full_data.columns]
    
    # Eksik verileri temizle
    full_data = full_data.dropna()
    
    # Model Init
    tft_model_wrapper = BIST30TransformerModel(config)
    
    try:
        # Dataset oluştur
        dataset_config = prepare_tft_dataset(full_data, target_col='Log_Return')
        # Custom override
        if 'Sector' in full_data.columns:
            dataset_config['static'] = ['Ticker', 'Sector']
            
        train_dataset, full_data_processed = tft_model_wrapper.create_dataset(full_data, dataset_config, mode='train')
        val_dataset = TimeSeriesDataSet.from_dataset(train_dataset, full_data_processed, predict=True, stop_randomization=True)
        
        # Model Build
        tft_model_wrapper.build_model(train_dataset)
        
        # Train
        log.info(f"Eğitim başlıyor (GPU: {config.DEVICE})...")
        batch_size = getattr(config, 'TFT_BATCH_SIZE', 64)
        tft_model_wrapper.train(train_dataset, val_dataset, epochs=20, batch_size=batch_size)
        
        # Save
        save_path = "models/saved/tft_model.pth"
        os.makedirs("models/saved", exist_ok=True)
        tft_model_wrapper.save(save_path)
        log.info(f"Eğitim tamamlandı ve kaydedildi: {save_path}")
        
    except Exception as e:
        log.error(f"Eğitim sırasında hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
