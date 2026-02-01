
import pandas as pd
import numpy as np
from catboost import CatBoostRanker, Pool
import os
import joblib

class CatBoostRankingModel:
    def __init__(self, data, config_module):
        self.data = data.copy()
        self.config = config_module
        self.model = None
        self.feature_names = []

    def prepare_data(self, is_training=True):
        """
        CatBoost Ranking için veriyi hazırlar.
        """
        df = self.data.copy()
        
        # Feature Selection
        exclude_cols = [
            'NextDay_Close', 'NextDay_Direction', 'NextDay_Return', 'Excess_Return', 
            'NextDay_XU100_Return', 'Log_Return', 'Ticker', 'Date',
            'FUNDAMENTAL_DATA_AVAILABLE'
        ]
        
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        # Keep numeric only for simplicity, though CatBoost handles cats well
        # If we had categorical cols like 'Sector', we could pass them to cat_features
        numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        self.feature_names = numeric_cols
        
        # Target: NextDay_Return (Continuous)
        # CatBoost YetiRank accepts continuous targets (relevance) directly 
        # or we can rank them.
        # YetiRank optimizes NDCG based on relevance.
        target_col = 'NextDay_Return'
        
        if is_training:
            df = df.dropna(subset=numeric_cols + [target_col])
            df = df.sort_index(level='Date') 
            
            X = df[numeric_cols]
            y = df[target_col] # Continuous target is fine for YetiRank
            
            # Query IDs (Group ID)
            # CatBoost needs Group ID column or count
            # We will use Group ID column for Pool
            # Create unique ID for each Date date
            dates = df.index.get_level_values('Date')
            # Convert dates to unique integers (queries)
            # factorize returns (codes, uniques)
            q_ids = pd.factorize(dates)[0]
            
            pool = Pool(data=X, label=y, group_id=q_ids)
            return pool
        else:
            df = df.dropna(subset=numeric_cols)
            X = df[numeric_cols]
            return X

    def train(self, valid_df=None):
        print(f"[{self.config.SECTOR_NAME}] Ranking Model Eğitimi (CatBoost YetiRank)...")
        
        train_pool = self.prepare_data(is_training=True)
        
        if valid_df is not None:
             valid_model = CatBoostRankingModel(valid_df, self.config)
             val_pool = valid_model.prepare_data(is_training=True)
             eval_set = val_pool
        else:
             eval_set = None
             
        # CatBoost Parameters
        params = {
            'loss_function': 'YetiRank',
            'custom_metric': ['NDCG:top=5'],
            'eval_metric': 'NDCG:top=5',
            'iterations': 1000,
            'learning_rate': 0.03,
            'depth': 6,
            'l2_leaf_reg': 3,
            'random_seed': 42,
            'logging_level': 'Verbose',
            'early_stopping_rounds': 100,
            'train_dir': 'catboost_info',
            'allow_writing_files': False # Avoid clutter
        }
        
        model = CatBoostRanker(**params)
        
        model.fit(
            train_pool,
            eval_set=eval_set,
            # logging_level='Verbose', # already in params
            plot=False
        )
        
        self.model = model
        return model

    def predict(self, df):
        if self.model is None: return None
        X = df[self.feature_names]
        # CatBoost returns scores
        return self.model.predict(X)

    def save(self, path):
         if self.model:
            # CatBoost save
            self.model.save_model(path)
            # Save features separately as joblib implementation
            joblib.dump(self.feature_names, path + '_features.pkl')

    @classmethod
    def load(cls, path, config_module=None):
        instance = cls(pd.DataFrame(), config_module)
        if os.path.exists(path):
            from catboost import CatBoostRanker
            instance.model = CatBoostRanker()
            instance.model.load_model(path)
            
            feat_path = path + '_features.pkl'
            if os.path.exists(feat_path):
                instance.feature_names = joblib.load(feat_path)
            return instance
        else:
            return None
