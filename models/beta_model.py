import pandas as pd
import numpy as np
import lightgbm as lgb
import optuna
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error
import joblib
import os

class BetaModel:
    def __init__(self, data, config_module):
        self.data = data.copy()
        self.config = config_module # Sectoral config
        self.model = None
        self.best_params = None
        
    def prepare_features(self, is_training=True):
        """
        Beta Modeli için veriyi hazırlar.
        - Sadece Trend_Up (2) ve Sideways (0) rejimlerini kullanır (Training'de).
        - Featurelar: Momentum, Trend, Makro.
        - Hedef: NextDay_Return (Haftalık veri olduğu için önümüzdeki hafta).
        """
        df = self.data.copy()
        
        # 1. Feature Engineering (Artık FeatureEngineer tarafından yapılıyor)
        # Model sadece seçme işlemi yapacak.
            
        # Feature Listesi (FeatureEngineer çıktılarıyla uyumlu)
        default_features = [
            # Momentum
            'Return_Lag_1', 'Return_Lag_2', 'Return_Lag_3', 'Return_Lag_4',
            'RSI', 
            # Trend
            'Close_to_SMA200', 'BB_Width', 'Above_SMA200', 'MACD', 'MACD_Signal', 'MACD_Hist',
            # Makro (Eğer varsa)
            'VIX_Change', 'USDTRY_Change', 'XBANK_Momentum',
            # Rejim
            'Regime_Num'
        ]
        
        # Sütun kontrolü - Sadece DataFrame'de olanları seç
        selected_features = [c for c in default_features if c in df.columns]
        
        # 2. Rejim Filtreleme (Sadece Eğitimde)
        # Crash_Bear (1) modunda Beta modeline güvenilmez.
        if is_training and 'Regime_Num' in df.columns:
            valid_regimes = [0, 2] 
            df = df[df['Regime_Num'].isin(valid_regimes)]
            
        # Target
        target_col = 'NextDay_Return'
        
        X = df[selected_features]
        y = df[target_col] if target_col in df.columns else None
        
        # NaN Temizliği
        if y is not None:
            valid_mask = ~X.isna().any(axis=1) & ~y.isna()
            X = X[valid_mask]
            y = y[valid_mask]
        else:
            # Prediction modu (Target yok)
            X = X.dropna()
            
        return X, y

    def optimize_and_train(self, n_trials=50):
        """Optuna ile Risk-Adjusted Return (Sharpe + Penaltı) odaklı eğitim."""
        X, y = self.prepare_features(is_training=True)
        
        if len(X) < 50:
            print(f"[{self.config.SECTOR_NAME}] Yetersiz veri (Beta Model), eğitim atlanıyor.")
            return None
            
        def objective(trial):
            # Hyperparameters
            params = {
                'objective': 'regression_l1', # Temel eğitim yine regression
                'metric': 'mae',
                'verbosity': -1,
                'boosting_type': 'gbdt',
                'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.1),
                'num_leaves': trial.suggest_int('num_leaves', 32, 128),
                'max_depth': trial.suggest_int('max_depth', 5, 12),
                'reg_alpha': trial.suggest_float('reg_alpha', 0.1, 10.0),
                'reg_lambda': trial.suggest_float('reg_lambda', 0.1, 10.0),
                'min_child_samples': trial.suggest_int('min_child_samples', 20, 100),
                'feature_fraction': trial.suggest_float('feature_fraction', 0.4, 1.0),
                'n_estimators': 300
            }
            
            tscv = TimeSeriesSplit(n_splits=5)
            scores = []
            
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                dtrain = lgb.Dataset(X_train, label=y_train)
                dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)
                
                model = lgb.train(
                    params, dtrain, 
                    valid_sets=[dval], 
                    callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False), lgb.log_evaluation(0)]
                )
                
                # Validation Predictions
                preds = model.predict(X_val)
                
                # --- Trading Simulation on Validation Set ---
                # Basit Strateji: Tahmin > 0 ise Pozisyon Al
                signals = (preds > 0).astype(int)
                
                # Strategy Returns: Signal * Actual Return
                strategy_returns = signals * y_val
                
                # Metrics
                if len(strategy_returns) < 2:
                    scores.append(0)
                    continue
                    
                # Sharpe (Yıllık 52 hafta varsayımı ile)
                mean_ret = np.mean(strategy_returns)
                std_ret = np.std(strategy_returns)
                sharpe = (mean_ret / std_ret * np.sqrt(52)) if std_ret > 1e-6 else 0
                
                # Max Drawdown
                cum_ret = (1 + strategy_returns).cumprod()
                peak = cum_ret.cummax()
                dd = (cum_ret - peak) / peak
                max_dd = dd.min() if len(dd) > 0 else 0
                
                # Win Rate
                wins = np.sum(strategy_returns > 0)
                total_trades = np.sum(signals > 0)
                win_rate = (wins / total_trades) if total_trades > 0 else 0
                
                # --- CUSTOM SCORE / PENALTY ---
                # 1. Drawdown Cezası
                if max_dd < -0.20:
                    score = -1.0
                # 2. Win Rate Cezası
                elif win_rate < 0.40:
                    score = 0.0
                else:
                    # 3. Risk Adjusted Score
                    score = sharpe * (1 + (win_rate - 0.40))
                
                scores.append(score)
                
            return np.mean(scores)

        print(f"[{self.config.SECTOR_NAME}] Beta Model Optimizasyonu Başlıyor (Risk-Adjusted)...")
        # Hedef Skoru Maximize Etmek
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials)
        
        self.best_params = study.best_params
        self.best_params.update({
            'objective': 'regression_l1',
            'metric': 'mae',
            'verbosity': -1,
            'n_estimators': 500
        })
        
        # Final Eğitim
        dtrain = lgb.Dataset(X, label=y)
        self.model = lgb.train(self.best_params, dtrain)
        
        return self.model

    def predict(self, current_features_df):
        """Tahmin üretir."""
        if self.model is None:
            return None
        
        X, _ = self.prepare_features(is_training=False)
        
        if X.empty:
            return None

        # Feature order must match training
        # LightGBM handles this but ensuring columns match is good practice
        # X columns should be same as used in training
        
        preds = self.model.predict(X)
        return pd.Series(preds, index=X.index)

    def save(self, path):
        if self.model:
            joblib.dump(self.model, path)

    def load(self, path):
        if os.path.exists(path):
            self.model = joblib.load(path)
        else:
            print(f"Model dosyası bulunamadı: {path}")
