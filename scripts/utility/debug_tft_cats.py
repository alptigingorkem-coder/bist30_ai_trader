import torch
import joblib
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.transformer_model import BIST30TransformerModel

model_path = "models/saved/tft_model.pth"
config_path = "models/saved/tft_config.joblib"

tft_config = joblib.load(config_path)
model = BIST30TransformerModel(tft_config)
model.load(model_path)

if model.dataset_params and 'categorical_encoders' in model.dataset_params:
    encoders = model.dataset_params['categorical_encoders']
    if 'Ticker' in encoders:
        known = encoders['Ticker'].classes_
        print("TICKER CLASSES:")
        print(list(known))
    if 'Sector' in encoders:
        known_sectors = encoders['Sector'].classes_
        print("\nSECTOR CLASSES:")
        print(list(known_sectors))
else:
    print("No dataset_params found")
