#!/bin/bash
# AMD ROCm fix for RDNA 2 (RX 6700 etc.)
export HSA_OVERRIDE_GFX_VERSION=10.3.0

# Run Training
./venv/bin/python scripts/train_models.py
