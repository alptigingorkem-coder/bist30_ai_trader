
import torch
import pytorch_lightning
import lightning.pytorch
import pytorch_forecasting
from pytorch_forecasting import TemporalFusionTransformer

print(f"PyTorch Version: {torch.__version__}")
print(f"PyTorch Lightning Version: {pytorch_lightning.__version__}")
try:
    print(f"Lightning Version: {lightning.__version__}")
except:
    print("Lightning package version not found directly")

model = TemporalFusionTransformer.from_dataset(
    None, # Dataset lazım değil sadece class check
    learning_rate=0.01,
    hidden_size=16, 
    attention_head_size=4,
    dropout=0.1, 
    hidden_continuous_size=8,
    output_size=1,
    log_interval=10,
    reduce_on_plateau_patience=4,
) if False else None # Instance yaratamayız dataset olmadan

print("\n--- Inheritance Check ---")
print(f"TFT Class: {TemporalFusionTransformer}")
print(f"In MRO of TFT:")
for cls in TemporalFusionTransformer.mro():
    print(f"  - {cls} (Module: {cls.__module__})")

print("\n--- Lightning Trainer Check ---")
print(f"PL Trainer: {pytorch_lightning.Trainer}")
print(f"L.PT Trainer: {lightning.pytorch.Trainer}")

# Check if pytorch_lightning.LightningModule is same as lightning.pytorch.LightningModule
print(f"\nAre modules same? {pytorch_lightning.LightningModule is lightning.pytorch.LightningModule}")
