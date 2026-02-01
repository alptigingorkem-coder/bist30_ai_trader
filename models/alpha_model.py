import pandas as pd
import numpy as np
import lightgbm as lgb
import optuna
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error
import joblib
import os

class AlphaModel:
    def __init__(self, data, config_module):
        self.data = data.copy()
        self.config = config_module # Sectoral config
        self.model = None
        self.best_params = None
        
    def prepare_features(self, is_training=True):
        """
        Alpha Modeli için veriyi hazırlar.
        - Sideways (0) ve Trend_Up (2) rejimlerini kullanır.
        - Featurelar: Fundamentals, Alpha Momentum, Relative Strength.
        - Hedef: Excess_Return (Endeks Üstü Getiri).
        """
        df = self.data.copy()
        
        # FIX 15: Fundamental data yoksa Alpha modeli çalışmasın
        if 'FUNDAMENTAL_DATA_AVAILABLE' not in df.columns or not df['FUNDAMENTAL_DATA_AVAILABLE'].iloc[-1]:
            sector_name = getattr(self.config, 'SECTOR_NAME', 'UNKNOWN')
            print(f"[{sector_name}] Alpha model atlandı (Fundamental data yok)")
            return pd.DataFrame(), None  # Boş döndür
        
        # Feature Listesi (Genişletilmiş)
        feature_cols = [
            # Fundamentals (Varsa)
            'Forward_PE_Change', 'EBITDA_Margin_Change', 'Debt_to_Equity', 'PB_Ratio', 'Forward_PE',
            # Alpha Momentum (Lagged Excess Returns)
            'Excess_Return_Lag_1', 'Excess_Return_Lag_2', 'Excess_Return_Lag_4', 'Excess_Return_Lag_12',
            # Sector / Relative Strength
            'Sector_Rotation', 'Sector_Rotation_Trend', 'RS_vs_SP500',
            # Macro Filters (Alpha için önemli olabilir)
            'Gold_TRY_Momentum', 'Oil_TRY_Momentum', 'Commodity_Volatility',
            'Volatility_Ratio',
             # Rejim
            'Regime_Num'
        ]
        
        # Sütun kontrolü
        selected_features = [c for c in feature_cols if c in df.columns]
        
        # Rejim Filtreleme
        if is_training and 'Regime_Num' in df.columns:
            valid_regimes = [0, 2] 
            df = df[df['Regime_Num'].isin(valid_regimes)]
            
        # Target
        target_col = 'Excess_Return' 
        
        X = df[selected_features]
        y = df[target_col] if target_col in df.columns else None
        
        # NaN Temizliği
        if y is not None:
            valid_mask = ~X.isna().any(axis=1) & ~y.isna()
            X = X[valid_mask]
            y = y[valid_mask]
        else:
            # Prediction modu
            X = X.dropna()
            
        return X, y

    def optimize_and_train(self, n_trials=50):
        """Optuna ile Risk-Adjusted Return (Sharpe + Penaltı) odaklı eğitim."""
        X, y = self.prepare_features(is_training=True)
        
        sector_name = getattr(self.config, 'SECTOR_NAME', 'UNKNOWN')
        if len(X) < 50:
            print(f"[{sector_name}] Yetersiz veri (Alpha Model), eğitim atlanıyor.")
            return None
            
        def objective(trial):
            # Hyperparameters
            params = {
                'objective': 'regression_l1', # MAE
                'metric': 'mae',
                'verbosity': -1,
                'boosting_type': 'gbdt',
                'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.05),
                'num_leaves': trial.suggest_int('num_leaves', 20, 80),
                'max_depth': trial.suggest_int('max_depth', 3, 8),
                'reg_alpha': trial.suggest_float('reg_alpha', 0.5, 5.0), # YÜKSEK REGULARIZATION
                'reg_lambda': trial.suggest_float('reg_lambda', 0.5, 5.0),
                'min_child_samples': trial.suggest_int('min_child_samples', 20, 80),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.4, 0.9),
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
                # Strategy: Long if Excess Return Prediction > 0
                signals = (preds > 0).astype(int)
                
                # Strategy Returns: Signal * Actual Excess Return
                # (Note: This optimizes for capture of excess return, not absolute return)
                strategy_returns = signals * y_val
                
                if len(strategy_returns) < 2:
                    scores.append(0)
                    continue
                    
                # Metrics (based on Excess Returns)
                mean_ret = np.mean(strategy_returns)
                std_ret = np.std(strategy_returns)
                sharpe = (mean_ret / std_ret * np.sqrt(52)) if std_ret > 1e-6 else 0
                
                # Max Drawdown (on Excess Return curve)
                cum_ret = (1 + strategy_returns).cumprod()
                peak = cum_ret.cummax()
                dd = (cum_ret - peak) / peak
                max_dd = dd.min() if len(dd) > 0 else 0
                
                # Win Rate
                wins = np.sum(strategy_returns > 0)
                total_trades = np.sum(signals > 0)
                win_rate = (wins / total_trades) if total_trades > 0 else 0
                
                # --- CUSTOM SCORE / PENALTY ---
                if max_dd < -0.20:
                    score = -1.0
                elif win_rate < 0.40:
                    score = 0.0
                else:
                    score = sharpe * (1 + (win_rate - 0.40))
                
                scores.append(score)
                
            return np.mean(scores)

        sector_name = getattr(self.config, 'SECTOR_NAME', 'UNKNOWN')
        print(f"[{sector_name}] Alpha Model Optimizasyonu Başlıyor (Risk-Adjusted)...")
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
