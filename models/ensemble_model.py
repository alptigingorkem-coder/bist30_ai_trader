
import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import joblib
import torch
try:
    from catboost import CatBoostRanker, Pool
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

import config

from utils.logging_config import get_logger

log = get_logger(__name__)

class HybridEnsemble:
    def __init__(self, lgbm_model=None, tft_model=None, catboost_model=None):
        self.lgbm = lgbm_model
        self.tft = tft_model
        self.catboost = catboost_model
        
        # Load weights from config
        # Default distribution: 40% LGBM, 30% TFT, 30% CatBoost if enabled
        # or stick to config if CatBoost not present
        
        # Simple logic: Equal weight if not specified
        self.weights = {
            'lgbm': 0.4, 
            'tft': 0.3, 
            'catboost': 0.3
        }
        log.debug(f"DEBUG: Hybrid Weights set to: {self.weights}")
        
    def load_models(self, lgbm_path, tft_path, tft_config=None, catboost_path=None):
        """Eğitilmiş modelleri yükler"""
        # LightGBM (RankingModel) yükle
        from models.ranking_model import RankingModel
        if os.path.exists(lgbm_path):
             self.lgbm = RankingModel.load(lgbm_path)
             log.info(f"✅ LightGBM modeli yüklendi: {lgbm_path}")
        else:
             log.warning(f"⚠️ LightGBM modeli bulunamadı: {lgbm_path}")
        
        # TFT Model yükle
        if tft_config and tft_path and os.path.exists(tft_path):
            try:
                from models.transformer_model import BIST30TransformerModel
                self.tft_wrapper = BIST30TransformerModel(tft_config)
                self.tft_wrapper.load(tft_path)
                self.tft = self.tft_wrapper
                log.info(f"✅ TFT modeli yüklendi: {tft_path}")
            except Exception as e:
                log.error(f"❌ TFT Model yüklenemedi: {e}")
                self.tft = None
                
        # CatBoost Model yükle
        if catboost_path and os.path.exists(catboost_path) and CATBOOST_AVAILABLE:
            try:
                self.catboost = CatBoostRanker()
                self.catboost.load_model(catboost_path)
                log.info(f"✅ CatBoost modeli yüklendi: {catboost_path}")
            except Exception as e:
                log.error(f"❌ CatBoost Model yüklenemedi: {e}")
                self.catboost = None
            
    def predict(self, df, tft_dataset=None, backtest=False, regime='NORMAL'):
        """
        Tahminleri birleştirir.
        Args:
            regime (str): Piyasa rejimi ('TREND_UP', 'SIDEWAYS' vb.) - Ağırlıkları belirler.
        """
        # Dynamic Weight Selection
        current_weights = config.ENSEMBLE_REGIME_WEIGHTS.get(regime, self.weights)
        log.debug(f"Using weights for regime {regime}: {current_weights}")
        
        if self.lgbm is None:
            # Fallback if LGBM is main requirement
            log.warning("LightGBM is None in predict!")
            lgbm_pred = np.zeros(len(df))
        else:
            lgbm_pred = self.lgbm.predict(df)
        
        # 2. TFT Tahmini
        tft_pred = None
        if self.tft:
            try:
                df_tft = df.copy()
                
                # Multi-index'i column'lara taşı
                if df_tft.index.names and any(n in (df_tft.index.names or []) for n in ['Date', 'Ticker']):
                    df_tft = df_tft.reset_index()
                
                df_tft.columns = df_tft.columns.str.replace(".", "_", regex=False)
                
                # TFT için time_idx oluştur
                if 'time_idx' not in df_tft.columns:
                    if 'Date' in df_tft.columns:
                        dates = df_tft['Date']
                    elif 'Date' in df_tft.index.names:
                        dates = df_tft.index.get_level_values('Date')
                    else:
                        dates = None
                    
                    if dates is not None:
                        unique_dates = pd.Series(dates.unique()).sort_values(ignore_index=True)
                        date_map = {d: i for i, d in enumerate(unique_dates)}
                        df_tft['time_idx'] = dates.map(date_map).values
                        log.debug(f"Ensemble: TFT için time_idx oluşturuldu ({len(unique_dates)} date)")
                
                # Ticker sütunu kontrol et
                if 'Ticker' not in df_tft.columns:
                    if 'Ticker' in df_tft.index.names:
                        df_tft['Ticker'] = df_tft.index.get_level_values('Ticker')
                
                # Sector sütunu oluştur (TFT static_categoricals gereksinimi)
                if 'Sector' not in df_tft.columns and 'Ticker' in df_tft.columns:
                    try:
                        import config as cfg
                        df_tft['Sector'] = df_tft['Ticker'].apply(cfg.get_sector)
                    except Exception:
                        df_tft['Sector'] = 'Other'
                
                # Index unique olmalı
                df_tft = df_tft.reset_index(drop=True)
                
                tft_pred = self.tft.predict(df_tft, backtest=backtest) 
            except Exception as e:
                log.error(f"TFT Tahmin hatası: {e}")
                tft_pred = None
            
            if isinstance(tft_pred, torch.Tensor):
                tft_pred = tft_pred.cpu().numpy()
            if tft_pred is not None:
                tft_pred = tft_pred.flatten()
                
        # 3. CatBoost Tahmini
        catboost_pred = None
        if self.catboost:
            try:
                # CatBoost needs specific features. Assuming same as LGBM or defined in model
                # We often need to pass Pool or specific columns.
                # Since .cbm stores feature names, we can try predicting on df (if columns match)
                # Ensure we select only numeric/categorical as trained
                # Ideally we know feature names.
                # FIX: CatBoost might need strictly ordered feature columns or Pool
                # Attempt direct predict
                catboost_pred = self.catboost.predict(df[self.catboost.feature_names_])
            except Exception as e:
                # If feature names mismatch or missing
                log.error(f"CatBoost Tahmin hatası: {e}")
                catboost_pred = None

        # Hizalama (Length) - Minimum Length wins (usually due to TFT lag)
        lens = [len(lgbm_pred)]
        if tft_pred is not None: lens.append(len(tft_pred))
        if catboost_pred is not None: lens.append(len(catboost_pred))
        
        min_len = min(lens)
        
        # Crop to min_len (from end)
        lgbm_pred = lgbm_pred[-min_len:]
        if tft_pred is not None: tft_pred = tft_pred[-min_len:]
        if catboost_pred is not None: catboost_pred = catboost_pred[-min_len:]
        
        # Rank Averaging
        from scipy.stats import rankdata
        
        rank_lgbm = rankdata(lgbm_pred)
        norm_rank_lgbm = rank_lgbm / len(rank_lgbm)
        
        score = current_weights.get('lgbm', 0.4) * norm_rank_lgbm
        
        if tft_pred is not None:
            rank_tft = rankdata(tft_pred)
            norm_rank_tft = rank_tft / len(rank_tft)
            score += current_weights.get('tft', 0.3) * norm_rank_tft
            
        if catboost_pred is not None:
            rank_cb = rankdata(catboost_pred)
            norm_rank_cb = rank_cb / len(rank_cb)
            score += current_weights.get('catboost', 0.3) * norm_rank_cb
            
        return score
    
    def optimize_weights(self, val_df, val_target, tft_dataset=None, regime='NORMAL'):
        """
        Validation verisi üzerinde Rank IC'yi maximize eden ağırlıkları bulur.
        
        Args:
            val_df: Validation DataFrame
            val_target: Hedef değişken (Excess_Return veya benzeri)
            tft_dataset: TFT için hazırlanmış dataset (opsiyonel)
            regime: Optimizasyon yapılacak rejim
            
        Returns:
            dict: Optimize edilmiş ağırlıklar {'lgbm': w1, 'tft': w2, 'catboost': w3}
        """
        from scipy.stats import rankdata, spearmanr
        
        # Her modelin ayrı ayrı tahminlerini al
        predictions = {}
        
        # LGBM
        if self.lgbm is not None:
            try:
                predictions['lgbm'] = self.lgbm.predict(val_df)
            except Exception as e:
                log.warning(f"LGBM validation predict hatası: {e}")
        
        # TFT
        if self.tft is not None:
            try:
                tft_pred = self.tft.predict(val_df, backtest=True)
                if tft_pred is not None:
                    predictions['tft'] = tft_pred.flatten()
            except Exception as e:
                log.warning(f"TFT validation predict hatası: {e}")
        
        # CatBoost
        if self.catboost is not None:
            try:
                predictions['catboost'] = self.catboost.predict(val_df[self.catboost.feature_names_])
            except Exception as e:
                log.warning(f"CatBoost validation predict hatası: {e}")
        
        if len(predictions) < 2:
            log.warning("Optimize için en az 2 model tahmini gerekli. Varsayılan ağırlıklar korunuyor.")
            return self.weights
        
        # Hizala — minimum uzunluğa kırp
        target = np.array(val_target).flatten()
        min_len = min(len(target), *[len(p) for p in predictions.values()])
        target = target[-min_len:]
        
        model_names = list(predictions.keys())
        pred_matrix = np.column_stack([predictions[k][-min_len:] for k in model_names])
        
        # Optimization: Rank IC (Spearman) maximize
        def neg_rank_ic(w):
            combined = np.zeros(min_len)
            for i, name in enumerate(model_names):
                combined += w[i] * rankdata(pred_matrix[:, i]) / min_len
            
            corr, _ = spearmanr(combined, target)
            return -corr if not np.isnan(corr) else 0.0
        
        n_models = len(model_names)
        x0 = np.ones(n_models) / n_models
        bounds = [(0.05, 0.90)] * n_models  # Min %5, max %90
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        
        try:
            result = minimize(
                neg_rank_ic, x0, method='SLSQP',
                bounds=bounds, constraints=constraints,
                options={'maxiter': 200}
            )
            
            if result.success:
                opt_weights = {name: round(float(w), 4) for name, w in zip(model_names, result.x)}
                opt_ic = -result.fun
                
                # Optimize öncesi IC hesapla
                old_ic = -neg_rank_ic(x0)
                
                log.info(f"✅ Ensemble ağırlıkları optimize edildi:")
                log.info(f"   Eski ağırlıklar: {self.weights} (IC={old_ic:.4f})")
                log.info(f"   Yeni ağırlıklar: {opt_weights} (IC={opt_ic:.4f})")
                log.info(f"   IC İyileşme: {opt_ic - old_ic:+.4f}")
                
                self.weights = opt_weights
                return opt_weights
            else:
                log.warning(f"Optimizasyon yakınsamadı: {result.message}. Varsayılan ağırlıklar korunuyor.")
                return self.weights
                
        except Exception as e:
            log.error(f"Ağırlık optimizasyonu hatası: {e}")
            return self.weights

