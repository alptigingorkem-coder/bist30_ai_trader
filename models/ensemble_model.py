
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import joblib
import torch

import config

from utils.logging_config import get_logger

log = get_logger(__name__)

class HybridEnsemble:
    def __init__(self, lgbm_model=None, tft_model=None):
        self.lgbm = lgbm_model
        self.tft = tft_model
        
        # Load weights from config
        lgbm_w = getattr(config, 'HYBRID_WEIGHT', 0.6)
        tft_w = 1.0 - lgbm_w
        self.weights = {'lgbm': lgbm_w, 'tft': tft_w}
        log.debug(f"DEBUG: Hybrid Weights set to: {self.weights}")
        
    def load_models(self, lgbm_path, tft_path, tft_config=None):
        """Eğitilmiş modelleri yükler"""
        # LightGBM (RankingModel) yükle
        from models.ranking_model import RankingModel
        self.lgbm = RankingModel.load(lgbm_path)
        log.info(f"✅ LightGBM modeli yüklendi: {lgbm_path}")
        
        # TFT Model yükle
        if tft_config and tft_path:
            try:
                from models.transformer_model import BIST30TransformerModel
                # Yeni instance oluştur
                self.tft_wrapper = BIST30TransformerModel(tft_config)
                # Modeli yükle
                self.tft_wrapper.load(tft_path)
                self.tft = self.tft_wrapper
                log.info(f"✅ TFT modeli yüklendi: {tft_path}")
            except Exception as e:
                log.error(f"❌ TFT Model yüklenemedi: {e}")
                self.tft = None
            
    def predict(self, df, tft_dataset=None, backtest=False):
        """
        Tahminleri birleştirir.
        df: LightGBM için DataFrame
        tft_dataset: TFT için TimeSeriesDataSet veya DataLoader
        backtest: True ise TFT'den tüm geçmiş tahminleri ister.
        """
        if self.lgbm is None:
            raise ValueError("LightGBM modeli yüklü değil.")
            
        # 1. LightGBM Tahmini
        lgbm_pred = self.lgbm.predict(df)
        
        # 2. TFT Tahmini
        tft_pred = None
        if self.tft:
            # TFT wrapper üzerinden tahmin al
            # self.tft bir BIST30TransformerModel instance'ı
            try:
                # TFT (PyTorch Forecasting) sütun isimlerinde '.' sevmez ve '_' bekler.
                # Ancak LGBM '.' ile eğitilmiş olabilir.
                # Bu yüzden TFT'ye özel sütun isimlerini temizliyoruz.
                df_tft = df.copy()
                df_tft.columns = df_tft.columns.str.replace(".", "_", regex=False)
                
                tft_pred = self.tft.predict(df_tft, backtest=backtest) 
            except Exception as e:
                log.error(f"TFT Tahmin hatası: {e}")
                tft_pred = None
            # Tensor to numpy
            if isinstance(tft_pred, torch.Tensor):
                tft_pred = tft_pred.cpu().numpy()
            
            # Boyut eşitleme (Flatten)
            tft_pred = tft_pred.flatten()
            
        # Eğer TFT yoksa veya başarısızsa sadece LGBM dön (Soft fallback)
        if tft_pred is None:
            return lgbm_pred
            
        # 3. Hizalama (Alignment)
        # TFT geçmiş veriyi (encoder_length) kullandığı için başlangıç kısmında tahmin üretmez.
        # Bu yüzden tft_pred, lgbm_pred'den kısa olabilir.
        # Tahminlerin "sondan" hizalanması gerekir.
        
        n_lgbm = len(lgbm_pred)
        n_tft = len(tft_pred)
        
        if n_tft < n_lgbm:
            # TFT daha kısa (beklenen durum), son n_tft tanesini al
            lgbm_pred = lgbm_pred[-n_tft:]
        elif n_lgbm < n_tft:
            # LGBM daha kısa (beklenmez ama safety)
            tft_pred = tft_pred[-n_lgbm:]
            
        # Şimdi uzunluklar eşit

        
        # 3. Ağırlıklı Ortalama
        # Normalizasyon gerekebilir (Rank vs Return)
        # LGBM LambdaRank score üretir (büyük sınır yok)
        # TFT Return tahmini üretir (yüzdesel, küçük)
        
        # Bu yüzden ikisini de 0-1 arasına veya Rank'e çevirmek mantıklı.
        # Basitlik için Rank Averaging yapalım:
        
        from scipy.stats import rankdata

        rank_lgbm = rankdata(lgbm_pred)
        rank_tft = rankdata(tft_pred)
        
        # Normalized Ranks (0 to 1)
        norm_rank_lgbm = rank_lgbm / len(rank_lgbm)
        norm_rank_tft = rank_tft / len(rank_tft)
        
        ensemble_score = (
            self.weights['lgbm'] * norm_rank_lgbm + 
            self.weights['tft'] * norm_rank_tft
        )
        
        return ensemble_score
    
    # TODO: Optimizasyon (Fase 5)
    # Gelecekte validation set üzerinde ağırlıkları (LGBM vs TFT) dinamik optimize eden kod buraya gelecek.
    def optimize_weights(self, val_df, val_target):
        """
        Validation set üzerinde en iyi ağırlıkları bulur (Maximize Sharpe or Correlation).
        Şimdilik basit bir placeholder.
        """
        log.info("Optimizasyon henüz aktif değil, varsayılan ağırlıklar kullanılacak.")
        pass
