import os
import sys
import optuna
import joblib
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from configs import banking as config_banking
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel

# Global data to be used by objective function
full_data = None

def objective(trial):
    # Hyperparameters to tune
    params = {
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'ndcg_eval_at': [1, 3, 5],
        'boosting_type': 'gbdt',
        'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.1, log=True),
        'num_leaves': trial.suggest_int('num_leaves', 20, 150),
        'max_depth': trial.suggest_int('max_depth', 3, 12),
        'min_child_samples': trial.suggest_int('min_child_samples', 10, 100),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
        'n_estimators': 1000,
        'random_state': 42,
        'verbosity': -1
    }

    # TimeSeriesSplit for Robust Validation
    # Use 3 splits to save time during optimization
    tscv = TimeSeriesSplit(n_splits=3)
    scores = []
    
    # Group by Date to ensure we split strictly by time
    dates = full_data.index.get_level_values('Date').unique().sort_values()
    
    for train_idx, val_idx in tscv.split(dates):
        train_dates = dates[train_idx]
        val_dates = dates[val_idx]
        
        # Slicing MultiIndex
        train_df = full_data.loc[train_dates]
        valid_df = full_data.loc[val_dates]
        
        # Instantiate model helper (just for data prep)
        rm_train = RankingModel(train_df, config_banking)
        X_train, y_train, q_train = rm_train.prepare_data(is_training=True)
        
        rm_valid = RankingModel(valid_df, config_banking)
        X_valid, y_valid, q_valid = rm_valid.prepare_data(is_training=True)
        
        if X_train.empty or X_valid.empty or len(y_train) == 0 or len(y_valid) == 0:
            continue
            
        # Fit LightGBM
        model = lgb.LGBMRanker(**params)
        
        # Handle large labels if any
        max_label = max(y_train.max(), y_valid.max())
        if max_label > 30:
             model.set_params(label_gain=list(range(int(max_label) + 1)))
        
        callbacks = [
            lgb.early_stopping(stopping_rounds=20, verbose=False)
        ]
        
        model.fit(
            X_train, y_train, group=q_train,
            eval_set=[(X_valid, y_valid)], eval_group=[q_valid],
            eval_metric='ndcg',
            callbacks=callbacks
        )
        
        # Capture best score (NDCG@1 is usually first in eval_result key if multiple)
        # We target the last metric in 'ndcg_eval_at' usually, or specifically @1
        # lgb stores best_score_ as dict: {'valid_0': {'ndcg@1': 0.X, 'ndcg@3': 0.Y}}
        # We standardize on NDCG@3 as a balanced metric for Top 3 picks
        
        best_score = 0
        if model.best_score_ and 'valid_0' in model.best_score_:
            # Try to get NDCG@3, fallback to NDCG@1
            metrics = model.best_score_['valid_0']
            if 'ndcg@3' in metrics:
                best_score = metrics['ndcg@3']
            elif 'ndcg@1' in metrics:
                best_score = metrics['ndcg@1']
            else:
                # Fallback to first available value
                best_score = list(metrics.values())[0]
                
        scores.append(best_score)
        
    return np.mean(scores) if scores else 0.0

if __name__ == "__main__":
    print(f"Starting Hyperparameter Optimization...")
    print(f"Data Source: {config.START_DATE} to Present")
    
    # 1. Load Data
    loader = DataLoader(start_date=config.START_DATE)
    all_dfs = []
    
    # Use config tickers
    tickers = config.TICKERS
    print(f"Processing {len(tickers)} tickers...")
    
    for ticker in tickers:
        try:
            raw = loader.get_combined_data(ticker)
            if raw is None or len(raw) < 100: 
                continue
                
            fe = FeatureEngineer(raw)
            df = fe.process_all(ticker)
            # Add Ticker column for MultiIndex
            df['Ticker'] = ticker
            all_dfs.append(df)
            # print(f"  Loaded {ticker}: {len(df)} rows")
        except Exception as e:
            print(f"  Error loading {ticker}: {e}")
            
    if not all_dfs:
        print("❌ No data loaded. Aborting.")
        sys.exit(1)
        
    # 2. Combine & Index
    full_data = pd.concat(all_dfs)
    full_data.reset_index(inplace=True)
    full_data.set_index(['Date', 'Ticker'], inplace=True)
    full_data.sort_index(inplace=True) 
    
    print(f"Total Data: {len(full_data)} rows. Features: {full_data.shape[1]}")
    
    # 3. Optimize
    # Use 20 trials for now (can be increased)
    n_trials = 20
    print(f"Running Optuna for {n_trials} trials...")
    
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials)
    
    print("\n✅ Optimization Complete.")
    print("Best Trial:")
    print(f"  Value: {study.best_value}")
    print(f"  Params: {study.best_params}")
    
    # 4. Save Results
    ensure_dir = "models/saved"
    if not os.path.exists(ensure_dir): os.makedirs(ensure_dir)
    
    save_path = f"{ensure_dir}/optimized_lgbm_params.joblib"
    joblib.dump(study.best_params, save_path)
    print(f"Saved optimized parameters to: {save_path}")
