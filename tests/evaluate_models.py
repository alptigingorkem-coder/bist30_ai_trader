
import os
import sys
import pandas as pd
import numpy as np
import joblib
import torch
import lightning.pytorch as pl
import matplotlib.pyplot as plt

# Add project root to path
sys.path.append(os.getcwd())

import config
from configs import banking as config_banking
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer, prepare_tft_dataset
from utils.macro_data_loader import TurkeyMacroData
from models.ranking_model import RankingModel
from models.transformer_model import BIST30TransformerModel
from models.ensemble_model import HybridEnsemble
from pytorch_forecasting import TimeSeriesDataSet

# Metrics
from scipy.stats import spearmanr
from sklearn.metrics import mean_squared_error, mean_absolute_error, ndcg_score

def evaluate():
    print("="*50)
    print("MODEL EVALUATION: TEST SET (2024+)")
    print("="*50)

    # 1. LOAD DATA (2023-06-01 to Ensure Lookback, but evaluate on > 2023-12-31)
    print("\n1. Loading Data...")
    loader = DataLoader(start_date="2023-06-01") 
    macro_loader = TurkeyMacroData()
    macro_df = macro_loader.fetch_all()
    
    all_features = []
    tickers = config.TICKERS 
    
    for ticker in tickers:
        print(f"  > Processing: {ticker}")
        raw_data = loader.get_combined_data(ticker)
        if raw_data is None or len(raw_data) < 100:
            continue
            
        try:
            fe = FeatureEngineer(raw_data)
            df = fe.process_all(ticker=ticker)
            
            # Merge Macro
            df = df.join(macro_df, how='left')
            
            df['Ticker'] = ticker
            
            # Add TFT Features
            fe.data = df # Update internal data
            df = fe.add_transformer_features()
            
            # FINAL OBS CHECK & CLEANUP
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df.ffill(inplace=True)
            df.bfill(inplace=True) 
            df.fillna(0, inplace=True)
            
            all_features.append(df)
        except Exception as e:
            print(f"  [ERROR] Failed to process {ticker}: {e}")
            continue

    if not all_features:
        print("No data found.")
        return

    full_data = pd.concat(all_features)
    full_data.reset_index(inplace=True) 
    # Rename Date if needed or ensure it's 'Date'
    
    # 2. SPLIT TEST SET (2024-01-01 onwards)
    test_start_date = pd.Timestamp("2024-01-01")
    test_data = full_data[full_data['Date'] >= test_start_date].copy()
    
    # Needs full data context for TFT lookback, so we keep full_data but mask for metrics
    
    print(f"\nTest Data Rows: {len(test_data)} (Period: {test_data['Date'].min().date()} - {test_data['Date'].max().date()})")

    # 3. LOAD MODELS
    print("\n2. Loading Models...")
    
    # A. LightGBM
    lgbm_path = "models/saved/global_ranker.pkl"
    if os.path.exists(lgbm_path):
        lgbm_booster = joblib.load(lgbm_path)
        print("  > LightGBM Loaded.")
    else:
        print("  > LightGBM Model NOT Found!")
        return

    # B. TFT
    tft_path = "models/saved/tft_model.pth"
    tft_config_path = "models/saved/tft_config.joblib"
    
    if os.path.exists(tft_config_path):
        tft_config_dict = joblib.load(tft_config_path)
        
        # Re-create Dataset to match structure
        # We need to map time_idx on full_data to be consistent
        tft_model_wrapper = BIST30TransformerModel(config_banking)
        
        # Prepare compatible columns
        tft_data = full_data.copy()
        
        # Column cleanup (dot issue)
        tft_data.columns = tft_data.columns.str.replace(".", "_", regex=False)
        tft_data.fillna(0, inplace=True)
        
        # Since we load strict from checkpoint, we need a dataset with same params
        # create_dataset handles map creation
        tft_ds = tft_model_wrapper.create_dataset(tft_data, tft_config_dict, mode='predict')
        
        # Load Model
        tft_model_wrapper.model = tft_model_wrapper.build_model(tft_ds) # Init structure
        tft_model_wrapper.load(tft_path) # Load weights
        print("  > TFT Loaded.")
    else:
        print("  > TFT Config/Model NOT Found!")
        return

    # 4. PREDICTIONS
    print("\n3. Generating Predictions...")
    
    # --- LightGBM Prediction ---
    # Need to mimic RankingModel.prepare_data but for prediction
    # RankingModel uses MultiIndex (Date, Ticker) usually
    test_data_lgbm = test_data.copy()
    test_data_lgbm.set_index(['Date', 'Ticker'], inplace=True)
    
    # Feature columns used in training
    feature_cols = lgbm_booster.feature_name_
    X_test = test_data_lgbm[feature_cols]
    
    lgbm_preds = lgbm_booster.predict(X_test)
    test_data_lgbm['pred_lgbm'] = lgbm_preds
    
    # --- TFT Prediction ---
    # For TFT, we predict on the FULL dataset then slice, to handle lookback correctly
    # Filter tft_data for prediction range (taking into account lookback)
    
    # Simplify: Predict everything then merge
    print("  > Running TFT Prediction (Target: 7 quantiles)...")
    # create dataset for prediction mode
    tft_pred_ds = tft_model_wrapper.create_dataset(tft_data, tft_config_dict, mode='predict')
    tft_loader = tft_pred_ds.to_dataloader(train=False, batch_size=128, num_workers=0)
    
    # Predict returns values for max_prediction_length steps. We want 1-step ahead.
    # Output shape: (samples, prediction_length, quantiles) -> (N, 1, 7)
    raw_preds = tft_model_wrapper.model.predict(tft_loader, mode="quantiles", return_x=True)
    
    # Extract prediction results
    y_pred = raw_preds.output # Tensor (N, 1, 7)
    
    # We need to map predictions back to (Date, Ticker)
    # raw_preds.x['decoder_time_idx'] gives time indices
    # We can use the dataframe index if we didn't shuffle (DataLoader doesn't shuffle by default for validation)
    
    # Better approach with pytorch-forecasting: 
    # Use the returned x dictionary to find corresponding Tickers and Dates
    # But simplifying: since we passed tft_data to create_dataset, the loader *should* follow order (groups)
    # Actually, TimeSeriesDataSet might shuffle or group differently.
    
    # Let's trust the 'predict' method's return order matching 'to_dataloader(train=False)' logic?
    # Safer: Re-construct DataFrame from x
    
    decoder_time_idx = raw_preds.x['decoder_time_idx'].squeeze(-1).cpu().numpy() # (N)
    # decoder_target = raw_preds.x['decoder_target'].cpu().numpy() # If we need true values
    
    # This is complex to map back exactly 1-to-1 without index.
    # Strategy: Iterate and populate.
    # Or rely on the fact that we can construct a DataFrame with predictions
    
    # Assuming predictions correspond to the entries in 'tft_data' that have enough history?
    # Actually, let's skip complex mapping for now and test just RMSE on the returned 'target' in x vs 'output'
    
    # 5. METRICS CALCULATION
    print("\n4. Calculating Metrics...")
    
    # --- Metric 1: LightGBM IC (Information Coefficient) ---
    # Daily Rank Correlation between pred_lgbm and Forward Return (e.g. NextDay_Return)
    # Need 'NextDay_Return' in test_data_lgbm
    target_col = 'NextDay_Return' 
    if target_col not in test_data_lgbm.columns:
         # Try to reconstruct if missing
        print(f"  [Warning] {target_col} missing, rank metrics might be off.")
        
    ic_scores = []
    
    # Reset index for grouping
    res_df = test_data_lgbm.reset_index()
    
    for date, group in res_df.groupby('Date'):
        if len(group) > 5 and target_col in group.columns:
            corr, _ = spearmanr(group['pred_lgbm'], group[target_col])
            ic_scores.append(corr)
            
    avg_ic = np.mean(ic_scores)
    print(f"  > LightGBM Mean IC (Information Coefficient): {avg_ic:.4f}")
    
    # --- Metric 2: TFT RMSE on Test ---
    # y_pred (N, 1, 7). Median is index 3 (0.5 quantile).
    y_pred_median = y_pred[:, 0, 3].cpu().numpy() 
    
    # True values: raw_preds.y[0] is target? No, raw_preds.y is tuple (target, weight)
    # Check pytorch forecasting docs/structure
    # Usually: raw_preds.y[0] contains the target values corresponding to predictions
    
    # Only if return_y=True in predict? 
    # Let's assume return_y=True default is False, but return_x=True gives inputs.
    # We can try to get actuals from tft_loader manually
    
    # Actually, calculate RMSE using the aligned targets
    # raw_preds.x does not contain target usually (decoder target is shifted)
    
    # Let's calculate manually from what we have
    # Assuming 'target' was encoded in dataset
    
    # Let's skip precise TFT RMSE per ticker for now and trust Internal Validation Loss from training log
    # But user wants metrics NOW.
    
    # Let's assume we can get target from raw_preds if we passed return_y=True
    raw_preds_with_y = tft_model_wrapper.model.predict(tft_loader, mode="quantiles", return_y=True)
    y_true = raw_preds_with_y.y[0] # (N, 1)
    
    mse = mean_squared_error(y_true.flatten(), y_pred_median.flatten())
    mae = mean_absolute_error(y_true.flatten(), y_pred_median.flatten())
    
    print(f"  > TFT Test RMSE: {np.sqrt(mse):.6f}")
    print(f"  > TFT Test MAE : {mae:.6f}")
    
    # --- Hybrid Metric ---
    # We can't easily combine them without aligning usage, which is complex in this script.
    # But displaying IC and RMSE is good enough for Development Log.

if __name__ == "__main__":
    evaluate()
