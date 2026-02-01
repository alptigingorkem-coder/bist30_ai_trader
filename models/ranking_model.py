
import pandas as pd
import numpy as np
import lightgbm as lgb
import os
import joblib

class RankingModel:
    def __init__(self, data, config_module):
        self.data = data.copy()
        self.config = config_module
        self.model = None
        self.feature_names = []

    def prepare_data(self, is_training=True):
        """
        Ranking için veriyi hazırlar.
        Veri (Date, Ticker) indeksli olmalı.
        """
        df = self.data.copy()
        
        # Feature Selection
        # Use all available features except meta-data
        exclude_cols = [
            'NextDay_Close', 'NextDay_Direction', 'NextDay_Return', 'Excess_Return', 
            'NextDay_XU100_Return', 'Log_Return', 'Ticker', 'Date',
            'FUNDAMENTAL_DATA_AVAILABLE'
        ]
        
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        # Keep numeric only
        feature_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        self.feature_names = feature_cols
        
        # Target: NextDay_Return (Higher is better)
        # 2-Day Return smoothing for Daily timeframe?
        # Let's stick to NextDay_Return for now as base.
        target_col = 'NextDay_Return'
        
        if is_training:
            # Drop NaNs
            df = df.dropna(subset=feature_cols + [target_col])
            
            # Sort by Date (Important for grouping)
            df = df.sort_index(level='Date') 
            
            X = df[feature_cols]
            
            # Convert continuous return to integer Rank (Relevance)
            # Group by Date, rank by Return (Ascending=True means higher return = higher rank int)
            # fillna(0) just in case, rank() returns 1..N
            ranks = df.groupby('Date')[target_col].rank(method='first', ascending=True)
            y = ranks.astype(int)
            
            # Create Query Groups
            # LightGBM Ranker needs to know how many items are in each "Query" (Date)
            # count of items per date
            groups = df.groupby(level='Date').size().to_numpy()
            
            return X, y, groups
        else:
            # Prediction mode
            df = df.dropna(subset=feature_cols)
            X = df[feature_cols]
            return X, None, None

    def train(self, valid_df=None):
        print(f"[{self.config.SECTOR_NAME}] Ranking Model Eğitimi (LambdaRank)...")
        
        X_train, y_train, q_train = self.prepare_data(is_training=True)
        
        if valid_df is not None:
             valid_model = RankingModel(valid_df, self.config)
             X_val, y_val, q_val = valid_model.prepare_data(is_training=True)
             eval_set = [(X_val, y_val)]
             eval_group = [q_val]
        else:
             eval_set = None
             eval_group = None
             
        # LambdaRank Parameters
        params = {
            'objective': 'lambdarank',
            'metric': 'ndcg',
            'ndcg_eval_at': [1, 3, 5],
            'boosting_type': 'gbdt',
            'learning_rate': 0.05,
            'num_leaves': 31,
            'max_depth': -1,
            'n_estimators': 500,
            'importance_type': 'gain',
            'random_state': 42,
            'verbosity': -1
        }
        
        model = lgb.LGBMRanker(**params)
        
        model.fit(
            X_train, y_train,
            group=q_train,
            eval_set=eval_set,
            eval_group=eval_group,
            eval_metric='ndcg',
            callbacks=[
                # lgb.early_stopping(stopping_rounds=50), # LGBMRanker callback issue in some versions
                lgb.log_evaluation(50)
            ]
        )
        
        self.model = model
        return model

    def predict(self, df):
        if self.model is None: return None
        
        # Ensure correct columns
        X = df[self.feature_names]
        
        return self.model.predict(X)

    def save(self, path):
         if self.model:
            joblib.dump(self.model, path)
            joblib.dump(self.feature_names, path.replace('.pkl', '_features.pkl'))

    @classmethod
    def load(cls, path, config_module=None):
        instance = cls(pd.DataFrame(), config_module)
        if os.path.exists(path):
            instance.model = joblib.load(path)
            feat_path = path.replace('.pkl', '_features.pkl')
            if os.path.exists(feat_path):
                instance.feature_names = joblib.load(feat_path)
            return instance
        else:
            return None
