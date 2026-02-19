
import sys
import os
import torch
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.transformer_model import BIST30TransformerModel
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from utils.logging_config import get_logger
import config
import joblib

log = get_logger(__name__)

def analyze_attention():
    print("="*60)
    print("TFT ATTENTION ANALYSIS")
    print("="*60)
    
    model_path = "models/saved/tft_model.pth"
    config_path = "models/saved/tft_config.joblib"
    
    if not os.path.exists(model_path) or not os.path.exists(config_path):
        print("❌ Model or config not found in models/saved/")
        return
        
    # Load Model
    print("Loading TFT Model...")
    tft_config = joblib.load(config_path)
    model = BIST30TransformerModel(tft_config)
    model.load(model_path)
    
    # Load Sample Data (Use a known ticker from model)
    ticker = "EREGL.IS" 
    print(f"Loading data for {ticker}...")
    loader = DataLoader(start_date="2023-01-01", end_date="2024-01-01")
    raw = loader.get_combined_data(ticker)
    
    if raw is None:
        print("❌ Data load failed")
        return
        
    # Check categorical encoding
    if model.dataset_params and 'categorical_encoders' in model.dataset_params:
        encoders = model.dataset_params['categorical_encoders']
        if 'Ticker' in encoders:
            known = encoders['Ticker'].classes_
            print(f"DEBUG: Ticker classes type: {type(known)}")
            try:
                print(f"Known Tickers (Total {len(known)}): {list(known)[:5]}...")
            except:
                print(f"Known Tickers: {known}")
                
            if ticker not in known:
                print(f"⚠️ Warning: {ticker} not in known tickers.")
                # Try sibling
                if ticker.replace('.IS', '') in known:
                    ticker = ticker.replace('.IS', '')
                    print(f"   Using {ticker} instead.")
        if 'Sector' in encoders:
            known_sectors = encoders['Sector'].classes_
            print(f"Known Sectors: {known_sectors}")

    fe = FeatureEngineer(raw)
    df = fe.process_all(ticker)
    df['Ticker'] = str(ticker)
    df['Sector'] = str(config.get_sector(ticker))

    # Sanitize columns (TFT does not allow dots)
    df.columns = [c.replace('.', '_') for c in df.columns]
    
    df['Ticker'] = str(ticker)
    df['Sector'] = str(config.get_sector(ticker))
    df['Ticker'] = df['Ticker'].astype(str)
    df['Sector'] = df['Sector'].astype(str)
    
    print(f"DEBUG: Ticker dtype: {df['Ticker'].dtype}, Sector dtype: {df['Sector'].dtype}")
    print(f"DEBUG: Sector sample: {df['Sector'].iloc[0]}")
    
    # Check categorical encoding
    # TFT needs known categories. If 'Ticker' uses specific encoder, we need to ensure it matches.
    # The loaded model should handle this if we use its dataset parameters.
    
    print("Predicting and Extracting Attention...")
    
    try:
        from pytorch_forecasting import TimeSeriesDataSet
        
        # Ensure df types are correct for TFT (Skip categoricals)
        categoricals = ['Ticker', 'Sector']
        for col in df.columns:
            if col not in categoricals and df[col].dtype == 'object':
                 df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # ADDED: time_idx creation (required by TFT)
        if 'time_idx' not in df.columns:
            df = df.sort_index()
            unique_dates = pd.Series(df.index.unique()).sort_values()
            date_map = {d: i for i, d in enumerate(unique_dates)}
            df['time_idx'] = df.index.map(date_map)
        
        # Raw TFT Module
        raw_tft = model.model
        
        # Check dataset params
        if model.dataset_params is None:
             print("❌ Model dataset_params not found. Load failed or model untrained.")
             return

        # Create dataset from parameters
        dataset = TimeSeriesDataSet.from_parameters(
            model.dataset_params,
            df,
            predict=False,
            stop_randomization=True
        )
        dataloader = dataset.to_dataloader(train=False, batch_size=32)
        
        # Iterate and interpret
        attentions = []
        variable_importance = []
        
        for x, _ in dataloader:
            # Move to device
            x = {k: v.to(model.device) for k, v in x.items() if isinstance(v, torch.Tensor)}
            
            # Interpret (Use mean reduction to keep dimensions better or None)
            # reduction="mean" usually reduces batch but keeps time
            interpretation = raw_tft.interpret_output(raw_tft(x), reduction="mean")
            
            # attention shape: [Time] or [Batch, Time]
            attn = interpretation['attention'].detach().cpu().numpy()
            if attn.ndim == 0: # Scalar
                attn = np.array([attn])
            attentions.append(attn)
            
            # Feature Importance
            variable_importance.append(interpretation)
            
        # Aggregate Attention
        # If we have [Time] per batch, then concatenation works if shapes match
        try:
            full_attention = np.array(attentions)
            avg_attention = np.mean(full_attention, axis=0)
            
            print(f"DEBUG: avg_attention shape: {avg_attention.shape}")
            if avg_attention.ndim > 0:
                print("\nAttention Profile (Last 10 steps):")
                print(avg_attention[-10:])
        except Exception as e:
            print(f"⚠️ Could not aggregate attention: {e}")
            avg_attention = np.array([0])
        
        # Aggregate Variable Importance
        # Summing up importance scores
        # interpretation keys: 'static_variables', 'encoder_variables', 'decoder_variables'
        
        feat_imp = {}
        counts = 0
        
        for item in variable_importance:
            for key in ['encoder_variables', 'decoder_variables', 'static_variables']:
                if key in item:
                    val = item[key].detach().cpu().numpy() # Shape [Num_Features]
                    if key not in feat_imp:
                        feat_imp[key] = np.zeros_like(val)
                    feat_imp[key] += val
            counts += 1
            
        print("\nFeature Importance (Top 10):")
        
        all_importances = []
        
        # Mapping indices to names?
        # valid_encoder_variables = dataset.reals + dataset.categoricals etc.
        # We need the feature names from the dataset
        
        # Mapping indices to names
        encoder_vars = (dataset.time_varying_known_reals or []) + (dataset.time_varying_unknown_reals or [])
        decoder_vars = (dataset.time_varying_known_reals or [])
        static_vars = (dataset.static_reals or []) + (dataset.static_categoricals or [])
        
        if 'encoder_variables' in feat_imp:
            for i, name in enumerate(encoder_vars):
                if i < len(feat_imp['encoder_variables']):
                    all_importances.append((name, feat_imp['encoder_variables'][i]))
                
        if 'static_variables' in feat_imp:
            for i, name in enumerate(static_vars):
                if i < len(feat_imp['static_variables']):
                    all_importances.append((name, feat_imp['static_variables'][i]))
                
        # Sort
        all_importances.sort(key=lambda x: x[1], reverse=True)
        
        for name, val in all_importances[:10]:
            print(f"   {name:30s}: {val:.4f}")
            
        # Save report
        with open("reports/tft_attention_analysis.txt", "w") as f:
            f.write("TFT ATTENTION & FEATURE IMPORTANCE\n")
            f.write("="*40 + "\n")
            f.write(f"Ticker: {ticker}\n\n")
            f.write("Top 20 Features:\n")
            for name, val in all_importances[:20]:
                f.write(f"{name:30s}: {val:.4f}\n")
                
        print("\n✅ Analysis saved to reports/tft_attention_analysis.txt")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_attention()
