
import optuna
import pandas as pd
import numpy as np
import config
import sys
import os
import joblib

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.regime_detection import RegimeDetector
from models.beta_model import BetaModel
from models.alpha_model import AlphaModel
from core.backtesting import Backtester
from configs import banking, holding, industrial, growth

# Suppress logs
optuna.logging.set_verbosity(optuna.logging.WARNING)
import warnings
warnings.filterwarnings('ignore')

# Tickers to optimize on (Representative subset for speed)
# Including Volume heavy and Trend heavy stocks
OPTIMIZATION_TICKERS = ['GARAN.IS', 'ASELS.IS', 'THYAO.IS', 'EREGL.IS', 'BIMAS.IS', 'KCHOL.IS']

# Cache Model Load
MODELS = {}

def load_models_once():
    sectors = ['banking', 'holding', 'industrial', 'growth']
    for s in sectors:
        try:
            MODELS[f"{s}_beta"] = joblib.load(f"models/saved/{s}_beta.pkl")
            MODELS[f"{s}_alpha"] = joblib.load(f"models/saved/{s}_alpha.pkl")
        except:
            pass

def get_sector_config(ticker):
    if ticker in banking.TICKERS: return 'banking'
    if ticker in holding.TICKERS: return 'holding'
    if ticker in industrial.TICKERS: return 'industrial'
    if ticker in growth.TICKERS: return 'growth'
    return 'holding' # default

def run_simulation(data_dict, current_params):
    """
    Runs backtest for all tickers with current params.
    Returns avg sharpe.
    """
    results = []
    
    # Update Config Globals (Monkey Patching)
    config.ATR_STOP_LOSS_MULTIPLIER = current_params['stop_loss_mult']
    config.ATR_TRAILING_STOP_MULTIPLIER = current_params['trailing_stop_mult']
    # config.RSI_PERIOD = current_params['rsi_period'] # Disabled optimization
    
    threshold = current_params['confidence_threshold']

    for ticker, raw_df in data_dict.items():
        if raw_df is None or raw_df.empty: continue
        
        # 1. Feature Engineering (Recalculate if RSI changed)
        # Note: FE modifies df in place, so work on copy
        df = raw_df.copy()
        
        # Manually apply RSI since we changed config
        # FE class reads config.RSI_PERIOD
        fe = FeatureEngineer(df)
        df = fe.process_all(ticker=ticker)
        
        # 2. Regime
        rd = RegimeDetector(df)
        df = rd.detect_regimes(verbose=False)
        
        # 3. Filter OOS (or Validation set)
        mask = df.index >= "2023-01-01"
        df = df[mask]
        
        if df.empty: continue

        # 4. Predict
        sec_name = get_sector_config(ticker)
        beta_model = MODELS.get(f"{sec_name}_beta")
        alpha_model = MODELS.get(f"{sec_name}_alpha")
        
        if not beta_model or not alpha_model: continue
        
        # Wrappers
        # Note: Prediction logic depends on features. 
        # Ideally models are robust to small feature changes or specialized FE needs to happen before.
        # But BetaModel checks feature lists.
        # Check if RSI period change affects model input columns? 
        # Models were trained with RSI_3. If we change to RSI_14, model expects 'RSI' column.
        # But the meaning of 'RSI' column changes.
        # IMPORTANT: Tree models are scale invariant but distribution changes.
        # Using a model trained on RSI_3 with RSI_14 inputs is BAD ML practice.
        # However, for 'Strategy Optimization', usually we optimize thresholds, not FE params that require retraining.
        # SO: We will SKIP RSI_PERIOD optimization to avoid retraining necessity.
        # We will only optimize Risk Params and Thresholds.
        
        # Wrapper predict
        # Hack to use model object directly
        try:
            # Prepare features for model (Model expects specific columns)
            # We assume columns exist.
            # We need to recreate BetaModel/AlphaModel instances to use their predict method correctly
            # or just assume 'RSI' is present.
            
            # Simplified prediction gathering
            # We can't easily use BetaModel.predict() because it recalculates features internally based on its config
            # We will rely on the fact that we passed 'df' which has features.
            
            # Let's extract features expected by model (if we can)
            # Or just proceed if we assume FE adds standard columns.
            
            from models.beta_model import BetaModel as BM
            bm = BM(df, None)
            bm.model = beta_model
            beta_preds = bm.predict(df)
            
            from models.alpha_model import AlphaModel as AM
            am = AM(df, None)
            am.model = alpha_model
            alpha_preds = am.predict(df)
            
            if beta_preds is None or alpha_preds is None: continue
            
            # Combine
            w_beta, w_alpha = 0.5, 0.5 # Could also be optimized!
            
            final_preds = pd.Series(0.0, index=df.index)
            mask_trend = (df['Regime_Num'] == 2)
            mask_side = (df['Regime_Num'] == 0)
            
            final_preds[mask_trend] = (beta_preds[mask_trend] * 0.7) + (alpha_preds[mask_trend] * 0.3)
            final_preds[mask_side] = (beta_preds[mask_side] * 0.3) + (alpha_preds[mask_side] * 0.7)
            
            # Filter by Threshold
            # Optimization Target: 'threshold'
            signals = final_preds.apply(lambda x: 1.0 if x > threshold else 0.0)
            
            # Run Backtest
            bt = Backtester(df, initial_capital=10000)
            # Backtester reads config.ATR_* internally in check_exit_conditions logic?
            # Yes, RiskManager is instantiated inside run_backtest.
            # RiskManager reads config.
            # So updating config globally works.
            
            bt.run_backtest(signals)
            metrics = bt.calculate_metrics()
            
            if metrics:
                results.append(metrics['Sharpe Ratio'])
                
        except Exception as e:
            # print(f"Error {ticker}: {e}")
            pass

    if not results: return -999
    return np.mean(results)

def objective(trial):
    params = {
        'stop_loss_mult': trial.suggest_float('stop_loss_mult', 1.5, 4.0, step=0.1),
        'trailing_stop_mult': trial.suggest_float('trailing_stop_mult', 1.0, 3.5, step=0.1),
        # 'rsi_period': trial.suggest_int('rsi_period', 3, 14), # Disabled to avoid retraining mismatch
        'confidence_threshold': trial.suggest_float('confidence_threshold', 0.003, 0.015, step=0.001)
    }
    
    # Constrain: Trailing stop should be tighter or equal to Stop loss usually?
    # Not necessarily, but Trailing < Stop is common.
    
    return run_simulation(DATA_CACHE, params)

if __name__ == "__main__":
    print("Preloading Data...")
    loader = DataLoader()
    DATA_CACHE = {}
    for t in OPTIMIZATION_TICKERS:
        d = loader.get_combined_data(t)
        if d is not None:
            DATA_CACHE[t] = d
            
    load_models_once()
    
    print("Starting Optimization...")
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=30) # 30 trials
    
    print("\nBest Params:")
    print(study.best_params)
    print(f"Best Sharpe: {study.best_value}")
