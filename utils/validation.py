
import pandas as pd
from typing import List, Optional
from utils.logging_config import get_logger

log = get_logger(__name__)

class DataValidator:
    """
    Head of Quant Recommendation:
    Schema Enforcement logic to prevent 'Garbage In, Garbage Out'.
    """
    
    REQUIRED_COLUMNS = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    @staticmethod
    def validate_ohlcv(df: pd.DataFrame, ticker: str = "Unknown") -> bool:
        """
        Validates OHLCV DataFrame schema and basic constraints.
        """
        if df is None or df.empty:
            log.warning(f"❌ Validation Failed [{ticker}]: DataFrame empty or None.")
            return False
            
        # 1. Schema Check
        missing = [col for col in DataValidator.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            log.error(f"❌ Validation Failed [{ticker}]: Missing columns {missing}")
            return False
            
        # 2. Type Check
        try:
            # Ensure numeric
            for col in DataValidator.REQUIRED_COLUMNS:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    log.error(f"❌ Validation Failed [{ticker}]: Column {col} is not numeric.")
                    return False
        except Exception as e:
            log.error(f"❌ Validation Error [{ticker}]: {e}")
            return False
            
        # 3. Value Constraints
        # Negative Prices
        if (df['Close'] < 0).any() or (df['Open'] < 0).any():
             log.error(f"❌ Validation Failed [{ticker}]: Negative prices detected.")
             return False
             
        # High < Low (Impossible)
        invalid_ohlc = df[df['High'] < df['Low']]
        if not invalid_ohlc.empty:
             log.warning(f"⚠️ Validation Warning [{ticker}]: {len(invalid_ohlc)} rows with High < Low. (Autocorrection possible but flagged)")
             # Strict mode might return False here
             
        return True

    @staticmethod
    def validate_features(df: pd.DataFrame, required_features: List[str]) -> bool:
        """
        Check if generated features exist.
        """
        missing = [f for f in required_features if f not in df.columns]
        if missing:
            log.error(f"❌ Feature Validation Failed: Missing {len(missing)} features. First 5: {missing[:5]}")
            return False
        return True
