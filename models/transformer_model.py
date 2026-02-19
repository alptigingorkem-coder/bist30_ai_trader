
import torch
import pandas as pd
import os
import lightning.pytorch
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer
from pytorch_forecasting.metrics import RMSE, MAE, QuantileLoss
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor

from utils.logging_config import get_logger

log = get_logger(__name__)

class BIST30TransformerModel:
    def __init__(self, config_module):
        self.config = config_module
        self.model = None
        self.dataset_params = None
        
        # GPU Check
        # GPU Check (Config'den al)
        self.device = getattr(self.config, 'DEVICE', torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
        log.info(f"BIST30Transformer Device: {self.device}")

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
            return dataset, df # Return processed df to reuse time_idx logic
            
        except Exception as e:
            log.error(f"Dataset oluşturma hatası: {e}")
            raise e
    
    def build_model(self, dataset, use_lr_schedule=False):
        """TFT modelini oluşturur (Dataset parametrelerine göre)"""
        
        lr = getattr(self.config, 'TFT_LEARNING_RATE', 0.03)
        hidden = getattr(self.config, 'TFT_HIDDEN_SIZE', 128)
        heads = getattr(self.config, 'TFT_ATTENTION_HEADS', 4)
        drop = getattr(self.config, 'TFT_DROPOUT', 0.15)
        hidden_cont = getattr(self.config, 'TFT_HIDDEN_CONTINUOUS_SIZE', 16)
        lstm_layers = getattr(self.config, 'TFT_LSTM_LAYERS', 2)
        
        # LR Schedule parametrelerini kaydet
        self.use_lr_schedule = use_lr_schedule
        self.base_lr = lr
        
        self.model = TemporalFusionTransformer.from_dataset(
            dataset,
            learning_rate=lr,
            hidden_size=hidden,
            attention_head_size=heads,
            dropout=drop,
            hidden_continuous_size=hidden_cont,
            lstm_layers=lstm_layers,
            output_size=7,  # QuantileLoss default quantiles count
            loss=QuantileLoss(), # Probabilistic forecasting
            log_interval=10,
            reduce_on_plateau_patience=4,
        )
        
        # LR Schedule kullanılacaksa, configure_optimizers metodunu override et
        if use_lr_schedule:
            self._override_configure_optimizers()
        
        log.info(f"✅ TFT Modeli oluşturuldu (lr={lr}, hidden={hidden}, heads={heads}, "
                 f"dropout={drop}, lstm_layers={lstm_layers}, lr_schedule={use_lr_schedule})")
        return self.model
    
    def _override_configure_optimizers(self):
        """LR Schedule için configure_optimizers metodunu override eder"""
        import torch.optim as optim
        from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts, LinearLR, SequentialLR
        
        original_configure_optimizers = self.model.configure_optimizers
        
        def new_configure_optimizers():
            # Optimizer'ı al
            optimizer = optim.Adam(self.model.parameters(), lr=self.base_lr)
            
            # Warmup Scheduler (ilk 5 epoch: 0.001 -> base_lr)
            warmup_epochs = 5
            warmup_scheduler = LinearLR(
                optimizer,
                start_factor=0.1,  # 0.1 * base_lr = 0.001 (base_lr=0.01 ise)
                end_factor=1.0,    # base_lr
                total_iters=warmup_epochs
            )
            
            # Cosine Annealing Scheduler (kalan epoch'lar)
            cosine_scheduler = CosineAnnealingWarmRestarts(
                optimizer,
                T_0=10,  # İlk restart 10 epoch sonra
                T_mult=2,  # Her restart'ta period 2 katına çıkar
                eta_min=self.base_lr * 0.01  # Minimum LR (base_lr'nin %1'i)
            )
            
            # Sequential Scheduler (önce warmup, sonra cosine)
            scheduler = SequentialLR(
                optimizer,
                schedulers=[warmup_scheduler, cosine_scheduler],
                milestones=[warmup_epochs]
            )
            
            return {
                "optimizer": optimizer,
                "lr_scheduler": {
                    "scheduler": scheduler,
                    "interval": "epoch",
                    "frequency": 1,
                    "monitor": "val_loss"
                }
            }
        
        # Override et
        self.model.configure_optimizers = new_configure_optimizers
        log.info("✅ LR Schedule aktif: Warmup (5 epoch) + Cosine Annealing")
    
    def train(self, train_dataset, val_dataset, epochs=30, batch_size=64, logger=None):
        """Modeli eğitir"""
        
        train_dataloader = train_dataset.to_dataloader(
            train=True, batch_size=batch_size, num_workers=4 # Linux optimizasyonu: 4 worker
        )
        val_dataloader = val_dataset.to_dataloader(
            train=False, batch_size=batch_size * 2, num_workers=4
        )
        
        # Callbacks
        early_stop_callback = EarlyStopping(
            monitor="val_loss", min_delta=1e-4, patience=10, verbose=False, mode="min"
        )
        lr_logger = LearningRateMonitor()
        
        # Trainer
        log.debug(f"DEBUG: Trainer configured for {self.device}")
        trainer = lightning.pytorch.Trainer(
            max_epochs=epochs,
            accelerator='auto', # 'cpu', 'gpu', 'tpu', 'ipu', 'hpu', 'mps', 'auto'
            devices=1,
            gradient_clip_val=0.1,
            callbacks=[early_stop_callback, lr_logger],
            limit_train_batches=1.0, 
            enable_model_summary=True,
            logger=logger # MLflow support
        )
        
        log.info(f"🚀 Eğitim Başlıyor...")
        trainer.fit(
            self.model,
            train_dataloaders=train_dataloader,
            val_dataloaders=val_dataloader
        )
        
        # En iyi modeli yükle
        best_model_path = trainer.checkpoint_callback.best_model_path
        # Load checkpoint
        self.model = TemporalFusionTransformer.load_from_checkpoint(best_model_path)
        log.info(f"✅ Eğitim Tamamlandı. En iyi model: {best_model_path}")
        
        return self.model
    
    def predict(self, data, mode='prediction', backtest=False):
        """
        Tahmin üretir.
        mode: 'prediction' (point forecast) veya 'quantiles'
        backtest: True ise tüm geçmiş pencereler için tahmin üretir. False ise sadece son pencere.
        """
        if self.model is None:
            raise ValueError("Model henüz eğitilmedi veya yüklenmedi.")
            
        self.model.eval()
        
        # Eğer backtest modundaysak ve data bir DataFrame ise,
        # Tüm pencereleri tahmin etmek için dataset'i manuel oluşturmalı ve predict=False yapmalıyız.
        if backtest and isinstance(data, pd.DataFrame):
             try:
                df_predict = data.copy()
                
                # Multi-index'i column'lara taşı (Date, Ticker)
                if df_predict.index.names and any(n in (df_predict.index.names or []) for n in ['Date', 'Ticker']):
                    df_predict = df_predict.reset_index()
                
                # time_idx oluştur (create_dataset mantığıyla aynı)
                if 'time_idx' not in df_predict.columns:
                    if 'Date' in df_predict.columns:
                        dates = df_predict['Date']
                    else:
                        raise ValueError("Date column not found for time_idx creation")
                    
                    unique_dates = pd.Series(dates.unique()).sort_values(ignore_index=True)
                    date_map = {d: i for i, d in enumerate(unique_dates)}
                    df_predict['time_idx'] = dates.map(date_map).values
                    log.info(f"TFT predict: time_idx oluşturuldu ({len(unique_dates)} unique date)")
                
                # Ticker sütunu kontrol et
                if 'Ticker' not in df_predict.columns:
                    df_predict['Ticker'] = 'DUMMY'
                
                # Index unique olmalı (TimeSeriesDataSet gereksinimi)
                df_predict = df_predict.reset_index(drop=True)
                
                # Eğitim sırasında kaydedilen kategorileri al
                # ve tahmin verisini filtrele (bilinmeyen ticker koruması)
                if self.dataset_params and 'categorical_encoders' in self.dataset_params:
                    encoders = self.dataset_params['categorical_encoders']
                    if 'Ticker' in encoders:
                        known_tickers = set(encoders['Ticker'].classes_)
                        original_len = len(df_predict)
                        df_predict = df_predict[df_predict['Ticker'].isin(known_tickers)]
                        filtered = original_len - len(df_predict)
                        if filtered > 0:
                            log.warning(f"TFT: {filtered} satır bilinmeyen ticker nedeniyle filtrelendi")
                        if df_predict.empty:
                            log.warning("TFT: Filtreleme sonrası veri kalmadı")
                            return None
                
                # dataset_params'taki gerekli sütunları kontrol et ve eksikleri ekle
                if self.dataset_params:
                    # Sector sütunu (static_categoricals) - config.get_sector ile oluştur
                    static_cats = self.dataset_params.get('static_categoricals', [])
                    if 'Sector' in static_cats and 'Sector' not in df_predict.columns:
                        try:
                            import config as cfg
                            if 'Ticker' in df_predict.columns:
                                df_predict['Sector'] = df_predict['Ticker'].apply(cfg.get_sector)
                            else:
                                df_predict['Sector'] = 'Other'
                            log.info(f"TFT predict: Sector sütunu oluşturuldu ({df_predict['Sector'].nunique()} unique)")
                        except Exception as sector_err:
                            log.warning(f"TFT: Sector oluşturulamadı: {sector_err}, 'Other' kullanılıyor")
                            df_predict['Sector'] = 'Other'
                    
                    # target sütunu yoksa 0 ile doldur (predict modunda hedef gerçek değeri bilinmiyor)
                    target_col = self.dataset_params.get('target', None)
                    if target_col and target_col not in df_predict.columns:
                        df_predict[target_col] = 0.0
                        log.debug(f"TFT predict: Target sütunu '{target_col}' 0 ile dolduruldu")
                    
                    # time_varying sütunları kontrol et — 0 yerine forward fill kullan
                    missing_cols = []
                    for col_list_key in ['time_varying_known_reals', 'time_varying_unknown_reals']:
                        for col in self.dataset_params.get(col_list_key, []):
                            if col not in df_predict.columns:
                                df_predict[col] = 0.0
                                missing_cols.append(col)
                    
                    # Mevcut sütunlardaki NaN'ları forward fill ile doldur
                    numeric_cols = df_predict.select_dtypes(include=['number']).columns
                    df_predict[numeric_cols] = df_predict[numeric_cols].ffill().fillna(0)
                    
                    if missing_cols:
                        log.warning(f"TFT predict: {len(missing_cols)} eksik sütun 0 ile dolduruldu: {missing_cols[:5]}")

                dataset = TimeSeriesDataSet.from_parameters(
                    self.dataset_params,
                    df_predict,
                    predict=False, 
                    stop_randomization=True
                )
                dataloader = dataset.to_dataloader(train=False, batch_size=64, num_workers=0)
                predictions = self.model.predict(dataloader, mode=mode, return_x=False)
                return predictions.cpu().numpy()
             except Exception as e:
                 log.error(f"Backtest prediction hatası: {e}")
                 # Fallback to default
                 pass

        predictions = self.model.predict(data, mode=mode, return_x=False)
        return predictions.cpu().numpy()

    def save(self, path):
        """Modeli ve parametrelerini kaydeder."""
        if self.model is None:
            log.warning("Model eğitilmediği için kaydedilemedi.")
            return

        # State dict + dataset params + config
        payload = {
            'state_dict': self.model.state_dict(),
            'dataset_params': self.dataset_params,
            'hyperparameters': self.model.hparams
        }
        torch.save(payload, path)
        log.info(f"✅ TFT Modeli kaydedildi: {path}")

    def load(self, path):
        """Kaydedilmiş modeli yükler."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model dosyası bulunamadı: {path}")
            
        try:
            payload = torch.load(path, map_location=self.device, weights_only=False)
            
            # Parametreleri geri yükle
            self.dataset_params = payload['dataset_params']
            
            # Modeli yeniden oluştur (from_dataset parametreleri dataset_params içinde olmayabilir,
            # ama from_dataset bir TimeSeriesDataSet objesi bekler.
            # Alternatif: from_dataset yerine doğrudan init edip load_state_dict yapmak.
            # TemporalFusionTransformer.load_from_checkpoint genelde Lightning ile kullanılır.
            # Burada manuel state_dict yüklemesi yapıyoruz.
            
            # Modeli tekrar build etmek için Dataset objesine ihtiyacımız yok, 
            # sadece hiperparametrelere ve statik parametrelere ihtiyacımız var.
            # Ancak TFT karmaşık bir yapı, en kolayı dummy dataset ile init etmek veya 
            # saved hyperparameters kullanmak.
            
            # Lightning modülleri genelde hparams'dan tekrar oluşturulabilir.
            self.model = TemporalFusionTransformer(**payload['hyperparameters'])
            self.model.load_state_dict(payload['state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            log.info(f"✅ TFT Modeli başarıyla yüklendi: {path}")
            
        except Exception as e:
            log.error(f"TFT Model yükleme hatası: {e}")
            raise e
