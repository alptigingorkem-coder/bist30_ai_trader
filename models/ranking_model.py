
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
        # Target Selection from Config
        label_type = getattr(self.config, 'LABEL_TYPE', 'RawRank')
        
        if label_type == 'RiskAdjusted':
             target_col = 'Excess_Return_RiskAdjusted'
        else:
             target_col = 'Excess_Return' 
             
        exclude_cols = self.config.LEAKAGE_COLS + ['Ticker', 'Date', 'FUNDAMENTAL_DATA_AVAILABLE']
        
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        # Prevent Leakage from dynamic target columns
        feature_cols = [c for c in feature_cols if not c.startswith('Excess_Return') and not c.startswith('NextDay')]
        
        # Keep numeric only
        feature_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        self.feature_names = feature_cols
        
        if is_training:
            # Drop NaNs
            # Ensure all forward window targets are present if using multi-window
            windows = getattr(self.config, 'FORWARD_WINDOWS', [1])
            target_cols = [f'Excess_Return_T{win}' for win in windows]
            df = df.dropna(subset=feature_cols + target_cols)
            
            # Sort by Date (Important for grouping)
            df = df.sort_index(level='Date') 
            
            X = df[feature_cols]
            
            # 1. Base Target Selection: Multi-Window Weighted Average
            if len(windows) > 1:
                # Weighted average of ranks across windows
                fwd_weights = getattr(self.config, 'FORWARD_WEIGHTS', [1.0/len(windows)]*len(windows))
                raw_y_multi = pd.Series(0.0, index=df.index)
                
                for i, win in enumerate(windows):
                    win_target = f'Excess_Return_T{win}'
                    win_ranks = df.groupby('Date')[win_target].rank(method='first', ascending=True)
                    raw_y_multi += fwd_weights[i] * win_ranks
                
                base_target_ranks = raw_y_multi
            else:
                # Single window
                base_target_ranks = df.groupby('Date')[target_col].rank(method='first', ascending=True)

            # 2. Label Type Logic
            if label_type == 'Hybrid':
                # Weighted average of Raw Rank and Quantile Rank
                num_q = getattr(self.config, 'NUM_QUANTILES', 5)
                # Use Excess_Return for quantile stability
                quantile_ranks = df.groupby('Date')[target_col].transform(
                    lambda x: pd.qcut(x, num_q, labels=False, duplicates='drop')
                ).fillna(0).astype(float)
                
                hybrid_weight = getattr(self.config, 'HYBRID_WEIGHT', 0.7)
                y = (hybrid_weight * base_target_ranks) + ((1 - hybrid_weight) * quantile_ranks)
                # LightGBM lambdarank requires int labels. Scale and cast to preserve precision.
                # Use scale * 100 to keep more gradients info
                y = (y * 100).round().astype(int)
                
            elif label_type == 'Quantile':
                num_q = getattr(self.config, 'NUM_QUANTILES', 5)
                y = df.groupby('Date')[target_col].transform(
                    lambda x: pd.qcut(x, num_q, labels=False, duplicates='drop')
                ).fillna(0).astype(int)
            else:
                # Default: Raw Ranking (Multi-window result from step 1)
                y = base_target_ranks
            
            # Create Query Groups
            groups = df.groupby(level='Date').size().to_numpy()
            
            return X, y, groups
        else:
            # Prediction mode
            df = df.dropna(subset=feature_cols)
            X = df[feature_cols]
            return X, None, None

    def train(self, valid_df=None, custom_params=None):
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
        default_params = {
            'objective': 'lambdarank',
            'metric': 'ndcg',
            'ndcg_eval_at': [1, 3, 5],
            'boosting_type': 'gbdt',
            'learning_rate': 0.03,  # Reduced from 0.05
            'num_leaves': 64,       # Increased from 31
            'max_depth': -1,
            'n_estimators': 1000,   # Increased from 500
            'importance_type': 'gain',
            'reg_alpha': 0.1,    # L1 regularization
            'reg_lambda': 0.1,   # L2 regularization
            'min_child_samples': 20,
            'random_state': 42,
            'verbosity': -1
        }
        
        # Override defaults with custom params if provided
        if custom_params:
            default_params.update(custom_params)
            
        model = lgb.LGBMRanker(**default_params)
        
        # Check for large labels (caused by scaling) and set label_gain if needed
        # LightGBM default label_gain only supports up to 31 labels. 
        # If we have more (e.g. 600+), we must provide a custom label_gain.
        max_label = y_train.max()
        if eval_set:
             for _, y_eval_curr in eval_set:
                 max_label = max(max_label, y_eval_curr.max())
                 
        if max_label > 30:
            print(f"[{self.config.SECTOR_NAME}] Large labels detected (max: {max_label}). Using linear label_gain to avoid error.")
            # Use linear gain (0, 1, 2, ...) to avoid overflow with exponential gain on large labels
            model.set_params(label_gain=list(range(int(max_label) + 1)))
            
        model.fit(
            X_train, y_train,
            group=q_train,
            eval_set=eval_set,
            eval_group=eval_group,
            eval_metric='ndcg',
            callbacks=[
                lgb.early_stopping(stopping_rounds=50, first_metric_only=True),
                lgb.log_evaluation(50)
            ]
        )
        
        # FEATURE SELECTION: SHAP Importance
        try:
            import shap
            explainer = shap.TreeExplainer(model)
            # Use a sample of training data for speed
            sample_size = min(len(X_train), 500)
            X_sample = X_train.iloc[:sample_size]
            shap_values = explainer.shap_values(X_sample)
            
            # shap_values can be a list for multi-class, but for Ranker it's often a single array
            if isinstance(shap_values, list):
                shap_importance = np.abs(shap_values[0]).mean(0)
            else:
                shap_importance = np.abs(shap_values).mean(0)
                
            low_imp_features = [self.feature_names[i] for i in range(len(shap_importance)) if shap_importance[i] < 0.005]
            if low_imp_features:
                print(f"[{self.config.SECTOR_NAME}] Low Importance Features (SHAP < 0.01): {low_imp_features[:5]}... (Total: {len(low_imp_features)})")
                # Auto-drop for future iterations (stateful within session)
                self.feature_names = [f for f in self.feature_names if f not in low_imp_features]
        except Exception as e:
            # print(f"SHAP Error: {e}")
            pass

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
