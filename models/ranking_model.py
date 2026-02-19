
import pandas as pd
import numpy as np
import lightgbm as lgb
import os
import joblib
import json

from utils.logging_config import get_logger

log = get_logger(__name__)

class RankingModel:
    def __init__(self, data, config_module, blacklist_path=None):
        self.data = data.copy()
        self.config = config_module
        self.model = None
        self.feature_names = []
        self.blacklist_path = blacklist_path  # Store the path for reloading
        self.blacklist = self._load_blacklist(blacklist_path)
    
    def _get_sector_name(self):
        """Helper to get sector name from config, with fallback."""
        return getattr(self.config, 'SECTOR_NAME', 'General')

    def _load_blacklist(self, path=None):
        """
        Load feature blacklist from JSON file.
        
        Args:
            path: Path to blacklist JSON file. If None, uses default location.
            
        Returns:
            List[str]: List of blacklisted feature names, or empty list if file doesn't exist.
        """
        if path is None:
            path = "models/saved/feature_blacklist.json"
        
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    blacklist = json.load(f)
                sector_name = getattr(self.config, 'SECTOR_NAME', 'General')
                log.info(f"[{sector_name}] Feature blacklist loaded: {len(blacklist)} features will be filtered")
                return blacklist
            except Exception as e:
                sector_name = getattr(self.config, 'SECTOR_NAME', 'General')
                log.warning(f"[{sector_name}] Failed to load blacklist from {path}: {e}")
                return []
        return []

    def prepare_data(self, is_training=True):
        """
        Ranking için veriyi hazırlar.
        Veri (Date, Ticker) indeksli olmalı.
        """
        # Reload blacklist for dynamic updates
        self.blacklist = self._load_blacklist(self.blacklist_path)
        
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
        
        # Apply blacklist filtering
        if self.blacklist:
            original_count = len(feature_cols)
            feature_cols = [f for f in feature_cols if f not in self.blacklist]
            filtered_count = original_count - len(feature_cols)
            if filtered_count > 0:
                log.info(f"[{self._get_sector_name()}] Blacklist applied: {filtered_count} features filtered, {len(feature_cols)} features remaining")
        
        self.feature_names = feature_cols
        
        if is_training:
            # Drop NaNs
            # Ensure all forward window targets are present if using multi-window
            windows = getattr(self.config, 'FORWARD_WINDOWS', [1])
            target_cols = [f'Excess_Return_T{win}' for win in windows]
            
            # DEBUG: Check for NaNs before drop
            log.info(f"[{self._get_sector_name()}] Data Shape Before Drop: {df.shape}")
            log.info(f"[{self._get_sector_name()}] Target Cols: {target_cols}")
            
            # Check for columns that are ALL NaN
            nan_counts = df[feature_cols + target_cols].isnull().sum()
            all_nan_cols = nan_counts[nan_counts == len(df)].index.tolist()
            if all_nan_cols:
                log.error(f"[{self._get_sector_name()}] CRITICAL: The following columns are ALL NaN: {all_nan_cols}")
                log.info(f"[{self._get_sector_name()}] Dropping these columns to save data rows.")
                df.drop(columns=all_nan_cols, inplace=True)
                # Update cols lists
                feature_cols = [c for c in feature_cols if c not in all_nan_cols]
                target_cols = [c for c in target_cols if c not in all_nan_cols]
                
                # FIX: Update instance variable so predict works correctly
                if is_training:
                    self.feature_names = feature_cols
            
            # Check rows with NaNs
            rows_with_nan = df[feature_cols + target_cols].isnull().any(axis=1).sum()
            log.info(f"[{self._get_sector_name()}] Rows with NaN: {rows_with_nan} / {len(df)}")

            df = df.dropna(subset=feature_cols + target_cols)
            log.info(f"[{self._get_sector_name()}] Data Shape After Drop: {df.shape}")
            
            # Sort by Date (Important for grouping)
            df = df.sort_index(level='Date') 
            
            X = df[feature_cols]
            
            # Feature Korelasyon Filtresi: >0.95 korelasyonlu çiftlerden birini çıkar
            enable_corr_filter = getattr(self.config, 'ENABLE_CORRELATION_FILTER', True)
            corr_threshold = getattr(self.config, 'CORRELATION_THRESHOLD', 0.95)
            
            if enable_corr_filter and len(feature_cols) > 10:
                try:
                    corr_matrix = X.corr().abs()
                    upper_tri = corr_matrix.where(
                        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
                    )
                    cols_to_drop = [col for col in upper_tri.columns 
                                    if any(upper_tri[col] > corr_threshold)]
                    
                    if cols_to_drop:
                        log.info(f"[{self._get_sector_name()}] Korelasyon filtresi: {len(cols_to_drop)} feature kaldırıldı "
                                 f"(eşik={corr_threshold}): {cols_to_drop[:10]}")
                        feature_cols = [c for c in feature_cols if c not in cols_to_drop]
                        X = df[feature_cols]
                        self.feature_names = feature_cols
                    else:
                        log.info(f"[{self._get_sector_name()}] Korelasyon filtresi: Kaldırılacak feature yok (eşik={corr_threshold})")
                except Exception as e:
                    log.warning(f"[{self._get_sector_name()}] Korelasyon filtresi hatası: {e}")
            
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
                # FIX: Index alignment error prevention by using numpy values
                y_values = (hybrid_weight * base_target_ranks.values) + ((1 - hybrid_weight) * quantile_ranks.values)
                y = pd.Series(y_values, index=df.index)
                
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
        log.info(f"[{self._get_sector_name()}] Ranking Model Eğitimi (LambdaRank)...")
        
        X_train, y_train, q_train = self.prepare_data(is_training=True)
        
        if X_train.empty or len(y_train) == 0:
            raise ValueError(f"[{self._get_sector_name()}] Training data is empty! Check feature engineering or data range.")
        
        if valid_df is not None and not valid_df.empty:
             valid_model = RankingModel(valid_df, self.config)
             try:
                 X_val, y_val, q_val = valid_model.prepare_data(is_training=True)
                 if X_val.empty or len(y_val) == 0:
                     log.info(f"[{self._get_sector_name()}] Validation set empty after processing. Skipping validation.")
                     eval_set = None
                     eval_group = None
                 else:
                     eval_set = [(X_val, y_val)]
                     eval_group = [q_val]
             except Exception as e:
                 log.error(f"[{self._get_sector_name()}] Validation prep error: {e}. Skipping validation.")
                 eval_set = None
                 eval_group = None
        else:
             eval_set = None
             eval_group = None
             
        # LambdaRank Parameters — Config'deki optimize edilmiş değerleri kullan
        import config as _cfg
        optimized = getattr(_cfg, 'OPTIMIZED_MODEL_PARAMS', {})
        
        default_params = {
            'objective': 'lambdarank',
            'metric': 'ndcg',
            'ndcg_eval_at': [1, 3, 5],
            'boosting_type': 'gbdt',
            'learning_rate': optimized.get('learning_rate', 0.01538),
            'num_leaves': optimized.get('num_leaves', 77),
            'max_depth': optimized.get('max_depth', 6),
            'n_estimators': optimized.get('n_estimators', 1000),
            'importance_type': 'gain',
            'reg_alpha': optimized.get('reg_alpha', 0.9187),
            'reg_lambda': optimized.get('reg_lambda', 0.4115),
            'min_child_samples': optimized.get('min_child_samples', 66),
            'random_state': 42,
            'verbosity': -1
        }
        log.info(f"[{self._get_sector_name()}] LightGBM parametreleri: lr={default_params['learning_rate']}, "
                 f"leaves={default_params['num_leaves']}, depth={default_params['max_depth']}, "
                 f"reg_alpha={default_params['reg_alpha']:.4f}, reg_lambda={default_params['reg_lambda']:.4f}")
        
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
            log.error(f"[{self._get_sector_name()}] Large labels detected (max: {max_label}). Using linear label_gain to avoid error.")
            # Use linear gain (0, 1, 2, ...) to avoid overflow with exponential gain on large labels
            model.set_params(label_gain=list(range(int(max_label) + 1)))
            
        # Callbacks logic
        callbacks = [lgb.log_evaluation(50)]
        if eval_set:
            callbacks.append(lgb.early_stopping(stopping_rounds=50, first_metric_only=True))

        model.fit(
            X_train, y_train,
            group=q_train,
            eval_set=eval_set,
            eval_group=eval_group,
            eval_metric='ndcg',
            callbacks=callbacks
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
                log.info(f"[{self._get_sector_name()}] Low Importance Features (SHAP < 0.01): {low_imp_features[:5]}... (Total: {len(low_imp_features)})")
                # Auto-drop for future iterations (stateful within session)
                # FIX: Model feature mismatch! Model eğitildikten sonra feature listesini değiştirirsek,
                # save() metodunda eksik liste kaydediliyor ama model tüm feature'ları bekliyor.
                # self.feature_names = [f for f in self.feature_names if f not in low_imp_features]
        except Exception as e:
            log.warning(f"[{self._get_sector_name()}] SHAP Feature Importance Failed: {e}")

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
