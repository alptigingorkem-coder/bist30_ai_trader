
import torch
import pandas as pd
import lightning.pytorch
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer
from pytorch_forecasting.metrics import RMSE, MAE, QuantileLoss
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor

class BIST30TransformerModel:
    def __init__(self, config_module):
        self.config = config_module
        self.model = None
        self.dataset_params = None
        
        # GPU Check
        self.device = 'gpu' if torch.cuda.is_available() else 'cpu'
        print(f"BIST30Transformer Device: {self.device}")

    def create_dataset(self, data, dataset_config, mode='train'):
        """
        TimeSeriesDataSet oluşturur.
        dataset_config: prepare_tft_dataset fonksiyonundan dönen dict
        """
        
        # DataFrame kopyası
        df = data.copy()
        
        # Time Index Creation (Eğer yoksa)
        if 'time_idx' not in df.columns:
            # Date ve Ticker'ı index veya column'dan bul
            if 'Date' in df.columns:
                dates = df['Date']
            elif 'Date' in df.index.names:
                dates = df.index.get_level_values('Date')
            else:
                raise ValueError("Date column or index level not found in data.")
                
            if 'Ticker' in df.columns:
                tickers = df['Ticker']
            elif 'Ticker' in df.index.names:
                tickers = df.index.get_level_values('Ticker')
            else:
                # If no ticker column, assume dummy or handle single series
                # But creating a new column is safer
                df['Ticker'] = 'DUMMY'
                tickers = df['Ticker']

            # Create mapping
            unique_dates = pd.Series(dates.unique()).sort_values(ignore_index=True)
            date_map = {d: i for i, d in enumerate(unique_dates)}
            
            # Map time_idx
            # We need to map the 'dates' series we extracted
            # Note: df['time_idx'] assignment relies on index alignment.
            # If dates came from index, it aligns. If from column, it aligns.
            
            # Safe assignment
            df['time_idx'] = dates.map(date_map)
            
            # Ensure Ticker is a column for GroupNormalizer/Main Group
            if 'Ticker' not in df.columns:
                 df['Ticker'] = tickers.values
        
        # Missing values in integer columns can be problematic? 
        # TimeSeriesDataSet handles some checks.
        
        # Konfigürasyon
        target = dataset_config['target']
        max_encoder_length = dataset_config['max_encoder_length']
        max_prediction_length = dataset_config['max_prediction_length']
        
        training_cutoff = df['time_idx'].max() - max_prediction_length
        
        # Dataset instantiation
        try:
            dataset = TimeSeriesDataSet(
                df[df['time_idx'] <= training_cutoff] if mode=='train' else df,
                time_idx="time_idx",
                target=target,
                group_ids=["Ticker"],
                min_encoder_length=max_encoder_length // 2, # Esneklik
                max_encoder_length=max_encoder_length,
                min_prediction_length=1,
                max_prediction_length=max_prediction_length,
                
                static_categoricals=dataset_config.get('static', []),
                time_varying_known_reals=dataset_config.get('known', []),
                time_varying_unknown_reals=dataset_config.get('unknown', []),
                
                # Normalizasyon
                target_normalizer=GroupNormalizer(
                    groups=["Ticker"], transformation=None
                ),  # Negatif değerler (Returns) için Softplus kullanılmamalı! Standard Scaling (None) uygundur.
                
                add_relative_time_idx=True,
                add_target_scales=True,
                add_encoder_length=True,
                allow_missing_timesteps=True # Tatil günleri vs.
            )
            
            self.dataset_params = dataset.get_parameters()
            return dataset
            
        except Exception as e:
            print(f"Dataset oluşturma hatası: {e}")
            raise e
    
    def build_model(self, dataset):
        """TFT modelini oluşturur (Dataset parametrelerine göre)"""
        
        self.model = TemporalFusionTransformer.from_dataset(
            dataset,
            learning_rate=getattr(self.config, 'TFT_LEARNING_RATE', 0.05), # Increased for sanity check
            hidden_size=getattr(self.config, 'TFT_HIDDEN_SIZE', 64),
            attention_head_size=getattr(self.config, 'TFT_ATTENTION_HEADS', 4),
            dropout=getattr(self.config, 'TFT_DROPOUT', 0.1),
            hidden_continuous_size=getattr(self.config, 'TFT_HIDDEN_CONTINUOUS_SIZE', 16),
            output_size=7,  # QuantileLoss default quantiles count
            loss=QuantileLoss(), # Probabilistic forecasting
            log_interval=10,
            reduce_on_plateau_patience=4,
        )
        print("✅ TFT Modeli oluşturuldu.")
        return self.model
    
    def train(self, train_dataset, val_dataset, epochs=30, batch_size=64):
        """Modeli eğitir"""
        
        train_dataloader = train_dataset.to_dataloader(
            train=True, batch_size=batch_size, num_workers=0 # Win'de worker 0 olmalı bazen
        )
        val_dataloader = val_dataset.to_dataloader(
            train=False, batch_size=batch_size * 2, num_workers=0
        )
        
        # Callbacks
        early_stop_callback = EarlyStopping(
            monitor="val_loss", min_delta=1e-4, patience=10, verbose=False, mode="min"
        )
        lr_logger = LearningRateMonitor()
        
        # Callbacks
        early_stop_callback = EarlyStopping(
            monitor="val_loss", min_delta=1e-4, patience=10, verbose=False, mode="min"
        )
        lr_logger = LearningRateMonitor()
        
        # Trainer
        print(f"DEBUG: Trainer configured for {self.device}")
        trainer = lightning.pytorch.Trainer(
            max_epochs=epochs,
            accelerator=self.device,
            devices=1,
            gradient_clip_val=0.1,
            callbacks=[early_stop_callback, lr_logger],
            limit_train_batches=1.0, 
            enable_model_summary=True,
        )
        
        print(f"🚀 Eğitim Başlıyor...")
        trainer.fit(
            self.model,
            train_dataloaders=train_dataloader,
            val_dataloaders=val_dataloader
        )
        
        # En iyi modeli yükle
        best_model_path = trainer.checkpoint_callback.best_model_path
        # Load checkpoint
        self.model = TemporalFusionTransformer.load_from_checkpoint(best_model_path)
        print(f"✅ Eğitim Tamamlandı. En iyi model: {best_model_path}")
        
        return self.model
    
    def predict(self, data, mode='prediction'):
        """
        Tahmin üretir.
        mode: 'prediction' (point forecast) veya 'quantiles'
        """
        if self.model is None:
            raise ValueError("Model henüz eğitilmedi veya yüklenmedi.")
            
        self.model.eval()
        
        # Data loader'a çevirmek gerekebilir performansı artırmak için
        # Ama predict metodu dataframe de kabul edebilir (versiyona göre)
        
        predictions = self.model.predict(data, mode=mode, return_x=False)
        return predictions.cpu().numpy()

    def save(self, path):
        if self.model:
            torch.save(self.model.state_dict(), path)

    def load(self, path):
        # Model yapısı recreate edilmeli sonra load_state_dict
        # Veya var olan instance'a yükle
        if self.model: # Build edilmişse
            self.model.load_state_dict(torch.load(path))
        else:
            print("Model önce build_model ile oluşturulmalı (Dataset parametreleri gerekir).")
