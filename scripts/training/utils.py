"""Shared utility functions for training scripts.

This module contains common helper functions used across
multiple training scripts.
"""

import os


def ensure_model_dir():
    """Ensure the models/saved directory exists.
    
    Creates the directory if it doesn't exist.
    """
    if not os.path.exists("models/saved"):
        os.makedirs("models/saved")
