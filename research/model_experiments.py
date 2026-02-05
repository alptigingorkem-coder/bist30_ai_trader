
import optuna
import pandas as pd
import numpy as np
import os
import sys
import joblib
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel
from models.ranking_model_catboost import CatBoostRankingModel
from models.ensemble_model import EnsembleModel
from configs import banking as config_banking

# Suppress logs
optuna.logging.set_verbosity(optuna.logging.WARNING)

def calculate_ndcg(scores, targets, top_n=5):
    """Simple NDCG@5 calculation per date group."""
    df = pd.DataFrame({'score': scores, 'target': targets})
    # Sort by score descending
    df = df.sort_values('score', ascending=False)
    
    # DCG
    actual_top = df.head(top_n)['target']
    # If target is rank, higher is better? 
    # Actually our target is NextDay_Return or Rank. 
    # Let's assume target is relevance (higher = better).
    dcg = np.sum(actual_top / np.log2(np.arange(2, len(actual_top) + 2)))
    
    # IDCG
    ideal_top = df['target'].sort_values(ascending=False).head(top_n)
    idcg = np.sum(ideal_top / np.log2(np.arange(2, len(ideal_top) + 2)))
    
    return dcg / idcg if idcg > 0 else 0

def evaluate_ensemble(lgbm_model, cat_model, df_valid, weights):
    ensemble = EnsembleModel(lgbm_model, cat_model, weights)
    scores = ensemble.predict(df_valid)
    
    # Group by Date and calculate average NDCG
    df_eval = df_valid.copy()
    df_eval['Ensemble_Score'] = scores
    
    # Use NextDay_Return as ground truth for NDCG
    target_col = 'NextDay_Return'
    
    ndcg_list = []
    for date, group in df_eval.groupby(level='Date'):
        if len(group) < 5: continue
        ndcg = calculate_ndcg(group['Ensemble_Score'], group[target_col], top_n=5)
        ndcg_list.append(ndcg)
        
    return np.mean(ndcg_list)

def tune_lgbm(df_train, df_valid, trials=50):
    print(f"--- Tuning LightGBM ({trials} trials) ---")
    
    def objective(trial):
        params = {
            'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.1, log=True),
            'num_leaves': trial.suggest_int('num_leaves', 31, 255),
            'max_depth': trial.suggest_int('max_depth', 3, 12),
            'min_child_samples': trial.suggest_int('min_child_samples', 20, 100),
            'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
            'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
            'n_estimators': 1000,
            'importance_type': 'gain'
        }
        
        ranker = RankingModel(df_train, config_banking)
        model = ranker.train(valid_df=df_valid, custom_params=params)
        return model.best_score_['valid_0']['ndcg@5']

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=trials)
    print(f"Best LGBM NDCG: {study.best_value:.4f}")
    return study.best_params

def tune_catboost(df_train, df_valid, trials=30):
    print(f"--- Tuning CatBoost ({trials} trials) ---")
    
    def objective(trial):
        params = {
            'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.1, log=True),
            'depth': trial.suggest_int('depth', 4, 10),
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1.0, 10.0),
            'random_strength': trial.suggest_float('random_strength', 0.0, 2.0),
            'bagging_temperature': trial.suggest_float('bagging_temperature', 0.0, 1.0),
            'iterations': 1000
        }
        
        ranker = CatBoostRankingModel(df_train, config_banking)
        model = ranker.train(valid_df=df_valid, custom_params=params)
        
        # Get best NDCG from eval set
        best_scores = model.get_best_score()
        # Possible keys: 'validation', 'validation_0', 'eval'
        for k in ['validation', 'validation_0']:
            if k in best_scores:
                return best_scores[k]['NDCG:top=5']
        
        # Fallback to learn if validation not found (at least we return something)
        return best_scores.get('learn', {}).get('NDCG:top=5', 0.0)

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=trials)
    print(f"Best CatBoost NDCG: {study.best_value:.4f}")
    return study.best_params

def main():
    # 1. Load & Process Data
    print("Loading data for experiments...")
    loader = DataLoader(start_date=config.START_DATE)
    all_dfs = []
    for t in config.TICKERS:
        data = loader.get_combined_data(t)
        if data is None or len(data) < 200: continue
        fe = FeatureEngineer(data)
        df = fe.process_all(t)
        df['Ticker'] = t
        all_dfs.append(df)
        
    full_data = pd.concat(all_dfs)
    full_data.reset_index(inplace=True)
    full_data.set_index(['Date', 'Ticker'], inplace=True)
    full_data.sort_index(inplace=True)
    
    dates = full_data.index.get_level_values('Date').unique()
    split_idx = int(len(dates) * 0.85)
    test_start_date = dates[split_idx]
    
    df_train = full_data[full_data.index.get_level_values('Date') < test_start_date]
    df_valid = full_data[full_data.index.get_level_values('Date') >= test_start_date]
    
    print(f"Data Split at {test_start_date}. Train: {len(df_train)}, Valid: {len(df_valid)}")

    # 2. Tune LGBM
    lgbm_params = tune_lgbm(df_train, df_valid, trials=20)
    
    # 3. Tune CatBoost
    cat_params = tune_catboost(df_train, df_valid, trials=10)
    
    # 4. Train final models with best params
    print("Training final models...")
    lgbm_ranker = RankingModel(df_train, config_banking)
    lgbm_model = lgbm_ranker.train(valid_df=df_valid, custom_params=lgbm_params)
    
    cat_ranker = CatBoostRankingModel(df_train, config_banking)
    cat_model = cat_ranker.train(valid_df=df_valid, custom_params=cat_params)
    
    # 5. Tune Ensemble Weights
    print("--- Tuning Ensemble Weights ---")
    def ensemble_objective(trial):
        w_lgbm = trial.suggest_float('w_lgbm', 0.0, 1.0)
        w_cat = 1.0 - w_lgbm
        return evaluate_ensemble(lgbm_ranker, cat_ranker, df_valid, {'lgbm': w_lgbm, 'catboost': w_cat})

    ensemble_study = optuna.create_study(direction='maximize')
    ensemble_study.optimize(ensemble_objective, n_trials=30)
    
    best_weights = {'lgbm': ensemble_study.best_params['w_lgbm'], 'catboost': 1.0 - ensemble_study.best_params['w_lgbm']}
    
    print("\n" + "="*50)
    print("EXPERIMENT FINAL RESULTS")
    print("="*50)
    print(f"Best LGBM Params: {lgbm_params}")
    print(f"Best CatBoost Params: {cat_params}")
    print(f"Best Ensemble Weights: {best_weights}")
    print(f"Final Ensemble NDCG: {ensemble_study.best_value:.4f}")
    
    # 6. Save BEST models and weights for production use
    print("\nSaving best models and weights to models/saved/...")
    lgbm_ranker.save("models/saved/global_ranker.pkl")
    cat_ranker.save("models/saved/global_ranker_catboost.cbm")
    joblib.dump(best_weights, "models/saved/ensemble_weights.joblib")
    
    # 7. Save Best Config to a report
    report_path = f"reports/model_tuning_{datetime.now().strftime('%Y%m%d')}.joblib"
    joblib.dump({
        'lgbm_params': lgbm_params,
        'cat_params': cat_params,
        'ensemble_weights': best_weights,
        'ndcg': ensemble_study.best_value
    }, report_path)
    print(f"Experiment report saved to: {report_path}")

if __name__ == "__main__":
    main()
