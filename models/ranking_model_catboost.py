# models/ranking_model_catboost.py

import numpy as np
import pandas as pd
from catboost import CatBoostRanker, Pool
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class CatBoostRankingModel:
    """
    CatBoost tabanlı ranking modeli.
    LightGBM'e alternatif/tamamlayıcı model.
    """
    
    def __init__(self, config=None):
        """
        Args:
            config: Config nesnesi veya dict
        """
        self.config = config or {}
        self.model = None
        self.feature_names = None
        self.categorical_features = []
        
        # CatBoost parametreleri - Hem module hem dict destekler
        def get_cfg(key, default):
            if hasattr(self.config, key):
                return getattr(self.config, key)
            if isinstance(self.config, dict):
                return self.config.get(key, default)
            return default

        # İYİLEŞTİRME 1: Listwise ranking + diversity için optimize edilmiş parametreler
        self.params = {
            'iterations': get_cfg('CATBOOST_ITERATIONS', 500),
            'learning_rate': get_cfg('CATBOOST_LEARNING_RATE', 0.03),
            'depth': get_cfg('CATBOOST_DEPTH', 6),
            'loss_function': 'YetiRankPairwise',  # Pairwise -> daha iyi top-k performansı
            'custom_metric': ['NDCG:top=5', 'NDCG:top=3', 'NDCG:top=1'],
            'eval_metric': 'NDCG:top=5',  # Top-5'e odaklan
            'early_stopping_rounds': 50,
            'verbose': 100,
            'random_seed': 42,
            'thread_count': -1,
            'task_type': 'CPU',  # GPU varsa 'GPU' yapılabilir
            # Diversity için regularization
            'l2_leaf_reg': 3.0,  # L2 regularization artırıldı (default: 3.0)
            'bagging_temperature': 1.0,  # Diversity için bagging
            'random_strength': 1.0,  # Ağaç çeşitliliği
        }
        
        logger.info("CatBoostRankingModel initialized with params: %s", self.params)
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, 
            group_train: pd.Series, 
            X_val: Optional[pd.DataFrame] = None,
            y_val: Optional[pd.Series] = None,
            group_val: Optional[pd.Series] = None) -> 'CatBoostRankingModel':
        """
        Modeli eğit.
        
        Args:
            X_train: Eğitim özellikleri
            y_train: Eğitim hedefleri
            group_train: Eğitim grupları (Date bazlı)
            X_val, y_val, group_val: Validasyon verileri (opsiyonel)
        
        Returns:
            self
        """
        logger.info("CatBoost eğitimi başlatılıyor...")
        logger.info(f"Train shape: {X_train.shape}, Val shape: {X_val.shape if X_val is not None else 'None'}")
        
        # Feature isimleri kaydet
        self.feature_names = list(X_train.columns)
        
        # Kategorik feature'ları tespit et
        self.categorical_features = [
            i for i, col in enumerate(self.feature_names)
            if X_train[col].dtype == 'object' or X_train[col].dtype.name == 'category'
        ]
        
        # CatBoost Pool oluştur
        train_pool = Pool(
            data=X_train,
            label=y_train,
            group_id=group_train,
            cat_features=self.categorical_features
        )
        
        # Validation pool (varsa)
        eval_set = None
        if X_val is not None and y_val is not None and group_val is not None:
            val_pool = Pool(
                data=X_val,
                label=y_val,
                group_id=group_val,
                cat_features=self.categorical_features
            )
            eval_set = val_pool
        
        # Model oluştur ve eğit
        self.model = CatBoostRanker(**self.params)
        
        self.model.fit(
            train_pool,
            eval_set=eval_set,
            use_best_model=True if eval_set else False,
            plot=False
        )
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            feature_importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            logger.info("\nTop 10 Feature Importances:")
            logger.info("\n" + feature_importance.head(10).to_string(index=False))
        
        # Best iteration
        if eval_set:
            best_iter = self.model.get_best_iteration()
            best_score = self.model.get_best_score()
            logger.info(f"Best iteration: {best_iter}")
            logger.info(f"Best validation score: {best_score}")
        
        logger.info("CatBoost eğitimi tamamlandı!")
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Tahmin yap.
        
        Args:
            X: Özellikler
        
        Returns:
            Tahmin skorları (yüksek = daha iyi ranking)
        """
        if self.model is None:
            raise ValueError("Model henüz eğitilmemiş! Önce fit() çağırın.")
        
        # Feature sıralaması kontrol et
        if list(X.columns) != self.feature_names:
            logger.warning("Feature sıralaması farklı, düzeltiliyor...")
            X = X[self.feature_names]
        
        predictions = self.model.predict(X)
        
        return predictions
    
    def predict_top_n(self, X: pd.DataFrame, group: pd.Series, n: int = 5) -> pd.DataFrame:
        """
        Her grup için en yüksek N tahmini döndür.
        
        Args:
            X: Özellikler
            group: Grup ID'leri (genelde Date)
            n: Kaç tane döndürülecek
        
        Returns:
            DataFrame with 'Group', 'Index', 'Score'
        """
        scores = self.predict(X)
        
        results = []
        for group_id in group.unique():
            group_mask = group == group_id
            group_scores = scores[group_mask]
            group_indices = np.where(group_mask)[0]
            
            # En yüksek N skor
            top_n_idx = np.argsort(group_scores)[-n:][::-1]
            
            for rank, idx in enumerate(top_n_idx, 1):
                results.append({
                    'Group': group_id,
                    'Index': group_indices[idx],
                    'Score': group_scores[idx],
                    'Rank': rank
                })
        
        return pd.DataFrame(results)
    
    def save(self, filepath: str):
        """Model kaydet."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Model kaydet
        model_path = filepath.with_suffix('.cbm')
        self.model.save_model(str(model_path))
        
        # Metadata kaydet
        metadata = {
            'feature_names': self.feature_names,
            'categorical_features': self.categorical_features,
            'params': self.params
        }
        
        metadata_path = filepath.with_suffix('.cbm_metadata.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Model kaydedildi: {model_path}")
        logger.info(f"Metadata kaydedildi: {metadata_path}")
    
    @classmethod
    def load(cls, filepath: str, config=None) -> 'CatBoostRankingModel':
        """Model yükle."""
        filepath = Path(filepath)
        
        # Model yükle
        model_path = filepath.with_suffix('.cbm')
        if not model_path.exists():
            raise FileNotFoundError(f"Model dosyası bulunamadı: {model_path}")
        
        instance = cls(config=config)
        instance.model = CatBoostRanker()
        instance.model.load_model(str(model_path))
        
        # Metadata yükle
        metadata_path = filepath.with_suffix('.cbm_metadata.pkl')
        if metadata_path.exists():
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            instance.feature_names = metadata.get('feature_names')
            instance.categorical_features = metadata.get('categorical_features', [])
            instance.params = metadata.get('params', {})
        
        logger.info(f"Model yüklendi: {model_path}")
        
        return instance
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series, group: pd.Series) -> Dict:
        """
        Model performansını değerlendir.
        
        Returns:
            Dict: Metrikler (NDCG@3, NDCG@5, vb.)
        """
        from sklearn.metrics import ndcg_score
        
        predictions = self.predict(X)
        
        # Grup bazında NDCG hesapla
        ndcg_scores = []
        
        for group_id in group.unique():
            mask = group == group_id
            y_true = y[mask].values.reshape(1, -1)
            y_pred = predictions[mask].reshape(1, -1)
            
            if len(y_true[0]) > 0:
                ndcg = ndcg_score(y_true, y_pred, k=5)
                ndcg_scores.append(ndcg)
        
        metrics = {
            'ndcg@5_mean': np.mean(ndcg_scores),
            'ndcg@5_std': np.std(ndcg_scores),
            'num_groups': len(ndcg_scores)
        }
        
        return metrics
    
    def train(self, train_df: pd.DataFrame, valid_df: Optional[pd.DataFrame] = None):
        """
        Wrapper metodu - RankingModel ile uyumluluk için.
        DataFrame'lerden feature'ları çıkarıp fit() metodunu çağırır.
        
        Args:
            train_df: Eğitim DataFrame'i (MultiIndex: Date, Ticker)
            valid_df: Validasyon DataFrame'i (opsiyonel)
        """
        from models.ranking_model import RankingModel
        
        # RankingModel'in prepare_data metodunu kullan
        temp_ranker = RankingModel(train_df, self.config)
        X_train, y_train, groups_train = temp_ranker.prepare_data(is_training=True)
        
        # groups_train: [5, 5, 5, ...] formatında (her grubun boyutu)
        # CatBoost group_id: [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, ...] formatında (her satırın grup ID'si)
        # Dönüşüm yap
        group_id_train = np.repeat(np.arange(len(groups_train)), groups_train)
        
        group_id_val = None
        X_val, y_val = None, None
        if valid_df is not None:
            temp_ranker_val = RankingModel(valid_df, self.config)
            X_val, y_val, groups_val = temp_ranker_val.prepare_data(is_training=True)
            
            # CRITICAL: Train ve validation feature'ları aynı olmalı
            # Validation'da train'de olmayan feature'ları kaldır, eksik olanları ekle
            missing_features = set(X_train.columns) - set(X_val.columns)
            extra_features = set(X_val.columns) - set(X_train.columns)
            
            if missing_features:
                logger.warning(f"Validation'da eksik feature'lar (0 ile doldurulacak): {missing_features}")
                for feat in missing_features:
                    X_val[feat] = 0.0
            
            if extra_features:
                logger.warning(f"Validation'da fazla feature'lar (kaldırılacak): {extra_features}")
                X_val = X_val.drop(columns=list(extra_features))
            
            # Feature sıralamasını train ile aynı yap
            X_val = X_val[X_train.columns]
            
            group_id_val = np.repeat(np.arange(len(groups_val)), groups_val)
        
        # fit() metodunu çağır
        return self.fit(X_train, y_train, group_id_train, X_val, y_val, group_id_val)


# Geriye uyumluluk için alias
RankingModelCatBoost = CatBoostRankingModel
