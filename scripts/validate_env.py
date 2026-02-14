import sys
import torch
import pandas as pd
import lightgbm as lgb
import pytorch_forecasting
from pytorch_forecasting import TemporalFusionTransformer

print(f"Python Version: {sys.version}")
print(f"Pandas Version: {pd.__version__}")
print(f"LightGBM Version: {lgb.__version__}")
print(f"PyTorch Forecasting Version: {pytorch_forecasting.__version__}")
print("-" * 30)
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA Device Count: {torch.cuda.device_count()}")
    print(f"CUDA Device Name: {torch.cuda.get_device_name(0)}")
else:
    print("WARNING: CUDA/ROCm not detected!")

try:
    import pykap
    print(f"PyKap Version: {pykap.__version__}")
except ImportError:
    print("PyKap not installed (Expected if disabled in config).")

print("-" * 30)
print("Environment Validation Complete.")
