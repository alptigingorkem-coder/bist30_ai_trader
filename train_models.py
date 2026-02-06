import os

import joblib
import numpy as np
import pandas as pd

# Konfigürasyonlar
import config
from configs import banking as config_banking

# Araçlar
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel

def ensure_model_dir():
    if not os.path.exists("models/saved"):
        os.makedirs("models/saved")

def train_global_ranker():
    print(f"\n{'='*50}")
    print(f"EĞİTİM BAŞLIYOR: GLOBAL DAILY RANKER")
    print(f"Timeframe: {config.TIMEFRAME}")
    print(f"Strict Mode: Veri kesim tarihi {config.TRAIN_END_DATE}")
    print(f"{'='*50}")

    all_data_frames = []
    loader = DataLoader(start_date=config.START_DATE)
    
    # Tüm Tickerlar (config.TICKERS - A1 Core)
    tickers = config.TICKERS
    
    for ticker in tickers:
        print(f"  Veri İşleniyor: {ticker}...")
        raw_data = loader.get_combined_data(ticker)
        
        if raw_data is None or len(raw_data) < 100:
            print(f"  [UYARI] Yetersiz veri: {ticker}")
            continue
            
        # Feature Engineering (Daily Logic will apply due to config change)
        fe = FeatureEngineer(raw_data)
        features_df = fe.process_all(ticker=ticker)
        
        # Add Ticker Column (Multi-Index için gerekli olabilir ama RankingModel level='Date' kullanıyor)
        features_df['Ticker'] = ticker
        
        # Validation Split (Tarihsel)
        if hasattr(config, 'TRAIN_END_DATE') and config.TRAIN_END_DATE:
            mask = features_df.index < config.TRAIN_END_DATE
            features_df = features_df[mask]
        
        all_data_frames.append(features_df)
        
    if not all_data_frames:
        print(f"❌ Hiç veri bulunamadı.")
        return
        
    # Combine All
    print("  Veriler birleştiriliyor...")
    full_data = pd.concat(all_data_frames)
    
    # Multi-Index (Date, Ticker) set et
    full_data.reset_index(inplace=True)
    full_data.set_index(['Date', 'Ticker'], inplace=True)
    full_data.sort_index(inplace=True) 
    
    print(f"  Toplam Eğitim Verisi: {len(full_data)} satır.")
    
    ensure_model_dir()
    
    # ---------------------------------------------------------
    # 0. MAKRO VERİ (Tüm tickerlar için ortak)
    # ---------------------------------------------------------
    # YENİ: Makro verileri çekip feature dataframe'lerine merge edeceğiz
    from utils.macro_data_loader import TurkeyMacroData
    print("  > Makro Veriler Çekiliyor...")
    macro_loader = TurkeyMacroData()
    macro_df = macro_loader.fetch_all() # Index: Date
    
    # ---------------------------------------------------------
    # 1. LIGHTGBM (RANKING) EĞİTİMİ
    # ---------------------------------------------------------
    print(f"  > Ranking Model (LightGBM) Eğitiliyor...")
    
    # Config modülü olarak banking veriyoruz (Generic bir config yeterli)
    model = RankingModel(full_data, config_banking) 
    
    # Train-Validation Split (Son %10 validation)
    dates = full_data.index.get_level_values('Date').unique()
    split_idx = int(len(dates) * 0.9)
    test_start_date = dates[split_idx]
    
    print(f"  > Validasyon Başlangıç: {test_start_date}")
    
    # Dataframe split
    train_mask = full_data.index.get_level_values('Date') < test_start_date
    valid_mask = full_data.index.get_level_values('Date') >= test_start_date
    
    df_train = full_data[train_mask]
    df_valid = full_data[valid_mask]
    
    # Instantiate with Train
    ranker = RankingModel(df_train, config_banking)
    
    # Check for optimized params from Optuna (file) first, then config fallback
    custom_params = None
    opt_path = "models/saved/optimized_lgbm_params.joblib"
    if os.path.exists(opt_path):
        custom_params = joblib.load(opt_path)
        print(f"  > Optuna ile bulunan hiperparametreler kullanılıyor: {opt_path}")
    else:
        cfg_params = getattr(config, 'OPTIMIZED_MODEL_PARAMS', None)
        if cfg_params:
            custom_params = cfg_params
            print(f"  > Config içindeki OPTIMIZED_MODEL_PARAMS kullanılıyor: {cfg_params}")
    
    ranker.train(valid_df=df_valid, custom_params=custom_params)
    ranker.save(f"models/saved/global_ranker.pkl")
    print(f"✅ Global Ranker (LightGBM) Eğitimi Tamamlandı.")

    # ---------------------------------------------------------
    # 2. TFT (TRANSFORMER) EĞİTİMİ
    # ---------------------------------------------------------
    try:
        print(f"\n  > TFT (Temporal Fusion Transformer) Eğitimi Başlıyor...")
        from models.transformer_model import BIST30TransformerModel
        from utils.feature_engineering import prepare_tft_dataset
        
        # TFT feature'ları zaten FeatureEngineer içinde eklendi (process_all -> add_transformer_features)
        # Sadece Macro verilerin merge edildiğinden emin olmalıyız.
        # process_all içinde makro kullanılmadıysa burada merge edebiliriz ama FE içinde halledildi varsayalım.
        # FE içinde macro_loader kullanılmadı, o zaman burada merge edilmesi lazım.
        
        # Merge Macro Data Logic (Eğer FE içinde yapılmadıysa)
        # Note: full_data has MultiIndex (Date, Ticker) and macro_df has Index (Date)
        
        # Reset Index for Merge
        tft_data = full_data.reset_index()
        
        if not macro_df.empty:
            # Date format check
            # macro_df index is datetime
            # tft_data['Date'] is datetime
            tft_data = pd.merge(tft_data, macro_df, left_on='Date', right_index=True, how='left')
            tft_data.fillna(method='ffill', inplace=True) # Fill macro gaps
            tft_data.fillna(0, inplace=True)
            print("  > Makro veriler TFT datasetine eklendi.")
            
        # FIX: PyTorch Forecasting sütun isimlerinde '.' sevmez
        print("  > Sütun isimleri temizleniyor (PyTorch uyumluluğu için)...")
        tft_data.columns = tft_data.columns.str.replace(".", "_", regex=False)

        # Dataset Config
        tft_config_dict = prepare_tft_dataset(tft_data, lookback=60)
        
        # Model Init
        tft_model_wrapper = BIST30TransformerModel(config_banking)
        
        # Split Data (Validasyon ayrımı)
        cutoff_idx = int(len(tft_data['Date'].unique()) * 0.9)
        cutoff_date = sorted(tft_data['Date'].unique())[cutoff_idx]
        
        train_tft = tft_data[tft_data['Date'] < cutoff_date]
        val_tft = tft_data[tft_data['Date'] >= cutoff_date]
        
        # Create PyTorch Forecasting Datasets
        # Mode='train' means we cutoff last prediction length points
        train_ds = tft_model_wrapper.create_dataset(train_tft, tft_config_dict, mode='train')
        val_ds = tft_model_wrapper.create_dataset(val_tft, tft_config_dict, mode='val') # Val dataset uses exact time range
        
        # Build Model Structure
        tft_model_wrapper.build_model(train_ds)

        # Train
        print(f"  > TFT Eğitiliyor (Epochs=30, CPU - Full Mode)...")
        tft_model_wrapper.train(train_ds, val_ds, epochs=30, batch_size=64) # Batch size 64 for speed on CPU
        

        
        # --- SANITY CHECK (DENEY A) ---
        print("\n🔎 SANITY CHECK: TFT Tahmin Varyansı Kontrol Ediliyor...")
        try:
            # Validation seti üzerinde tahmin al
            raw_predictions = tft_model_wrapper.model.predict(val_ds.to_dataloader(train=False, batch_size=16), mode="prediction")
            
            # Tensor to numpy
            if hasattr(raw_predictions, 'cpu'):
                preds_np = raw_predictions.cpu().numpy()
            else:
                preds_np = np.array(raw_predictions)
                
            # Flatten if needed (predictions might be [Batch, Prediction Horizon])
            preds_flat = preds_np.flatten()
            
            p_mean = np.mean(preds_flat)
            p_std = np.std(preds_flat)
            p_min = np.min(preds_flat)
            p_max = np.max(preds_flat)
            
            print(f"  📊 İstatistikler:")
            print(f"  Mean: {p_mean:.6f}")
            print(f"  Std Dev: {p_std:.8f} (Varyans: {p_std**2:.8f})")
            print(f"  Min/Max: {p_min:.6f} / {p_max:.6f}")
            
            if p_std < 1e-5:
                print("  ❌ UYARI: MODEL COLLAPSE! Varyans çok düşük. Model öğrenmiyor (hepsi aynı değeri tahmin ediyor).")
            else:
                print("  ✅ Varyans makul görünüyor. Model farklılaşma üretiyor.")
                
        except Exception as e:
            print(f"  ⚠️ Sanity Check sırasında hata: {e}")
        # ------------------------------
        
        # Save dataset parameters for inference (IMPORTANT)
        # We need to save tft_config_dict and dataset params
        import joblib
        joblib.dump(tft_config_dict, "models/saved/tft_config.joblib")
        # joblib.dump(train_ds.get_parameters(), "models/saved/tft_dataset_params.joblib") # Complex object
        
        print(f"✅ TFT Modeli Eğitimi Tamamlandı.")
        
    except Exception as e:
        print(f"❌ TFT Eğitimi sırasında hata: {e}")
        import traceback
        traceback.print_exc()

def main():
    train_global_ranker()

if __name__ == "__main__":
    main()
