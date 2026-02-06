
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import joblib
import torch

import config

class HybridEnsemble:
    def __init__(self, lgbm_model=None, tft_model=None):
        self.lgbm = lgbm_model
        self.tft = tft_model
        
        # Load weights from config
        lgbm_w = getattr(config, 'HYBRID_WEIGHT', 0.6)
        tft_w = 1.0 - lgbm_w
        self.weights = {'lgbm': lgbm_w, 'tft': tft_w}
        print(f"DEBUG: Hybrid Weights set to: {self.weights}")
        
    def load_models(self, lgbm_path, tft_path, tft_config=None):
        """Eğitilmiş modelleri yükler"""
        # LightGBM (RankingModel) yükle
        from models.ranking_model import RankingModel
        self.lgbm = RankingModel.load(lgbm_path)
        print(f"✅ LightGBM modeli yüklendi: {lgbm_path}")
        
        # TFT Model yükle
        if tft_config:
            from models.transformer_model import BIST30TransformerModel
            # Yeni instance oluştur
            self.tft_wrapper = BIST30TransformerModel(tft_config)
            # Modeli yükle (Architecture dataset'ten gelmeliydi ama burada state dict yükleyeceğiz)
            # NOT: TFT load işlemi dataset parametrelerini gerektirir. 
            # Bu yüzden eğitimden sonra tüm modeli (pickle) veya parametreleri kaydetmek daha iyi.
            # Şimdilik placeholder.
            pass
            
    def predict(self, df, tft_dataset=None):
        """
        Tahminleri birleştirir.
        df: LightGBM için DataFrame
        tft_dataset: TFT için TimeSeriesDataSet veya DataLoader
        """
        if self.lgbm is None:
            raise ValueError("LightGBM modeli yüklü değil.")
            
        # 1. LightGBM Tahmini
        lgbm_pred = self.lgbm.predict(df)
        
        # 2. TFT Tahmini
        tft_pred = None
        if self.tft:
            # TFT wrapper üzerinden tahmin al
            # Eğer self.tft bir wrapper instance ise:
            tft_pred = self.tft.predict(df) # Wrapper handle data conversion hopefully
            # Tensor to numpy
            if isinstance(tft_pred, torch.Tensor):
                tft_pred = tft_pred.cpu().numpy()
            
            # Boyut eşitleme (Flatten)
            tft_pred = tft_pred.flatten()
            
        # Eğer TFT yoksa veya başarısızsa sadece LGBM dön (Soft fallback)
        if tft_pred is None:
            return lgbm_pred
            
        # Uzunluk kontrolü
        min_len = min(len(lgbm_pred), len(tft_pred))
        lgbm_pred = lgbm_pred[:min_len]
        tft_pred = tft_pred[:min_len]
        
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
    
    def optimize_weights(self, val_df, val_target):
        """
        Validation set üzerinde en iyi ağırlıkları bulur (Maximize Sharpe or Correlation).
        Şimdilik basit bir placeholder.
        """
        print("Optimizasyon henüz aktif değil, varsayılan ağırlıklar kullanılacak.")
        pass
