
import sys
import os
import torch
from pytorch_forecasting import TemporalFusionTransformer

# Add project root
sys.path.append(os.getcwd())

from models.transformer_model import BIST30TransformerModel
import config

def convert_checkpoint(ckpt_path, output_path):
    print(f"Loading checkpoint from {ckpt_path}...")
    
    # Load raw lightning model
    # We need to map location to current device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    try:
        # Load from checkpoint
        tft_model = TemporalFusionTransformer.load_from_checkpoint(ckpt_path, map_location=device)
        print("Model loaded successfully.")
        
        # Extract params
        dataset_params = tft_model.dataset_parameters
        hparams = tft_model.hparams
        
        # Create wrapper
        wrapper = BIST30TransformerModel(config)
        
        # Manually set attributes
        wrapper.model = tft_model
        wrapper.dataset_params = dataset_params
        
        # Save using wrapper's save method which creates the dictionary structure we need
        print(f"Saving to {output_path}...")
        wrapper.save(output_path)
        print("Done.")
        
    except Exception as e:
        print(f"Error converting: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    ckpt = "mlruns/841538924320409537/24ab5ca830934e3daf8cdcf2ba127c52/checkpoints/epoch=7-step=4968.ckpt"
    out = "models/saved/tft_model.pth"
    
    if not os.path.exists(ckpt):
        print(f"Checkpoint not found: {ckpt}")
        # Try finding it dynamically if path changed (unlikely in few mins)
        pass
        
    convert_checkpoint(ckpt, out)
