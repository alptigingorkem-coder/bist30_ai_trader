"""
Macro Gate Modülü
-----------------

Amaç:
- Tüm macro gate kurallarını tek bir merkezde toplamak
- Hem backtest (`run_backtest.py`) hem de canlı/paper trading tarafında
  aynı mantığın kullanılmasını sağlamak

Tanım:
- Gate maskesi: True → Trade KAPALI (Risk OFF), False → Trade AÇIK (Risk ON)
"""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

import config


DEFAULT_THRESHOLDS: Dict[str, float] = {
    "VIX_HIGH": 30.0,
    "USDTRY_CHANGE_5D": 0.03,
    "SP500_MOMENTUM": 0.0,
}


def get_thresholds() -> Dict[str, float]:
    """Config üzerinden macro gate eşiklerini döndürür."""
    custom = getattr(config, "MACRO_GATE_THRESHOLDS", {})
    merged = DEFAULT_THRESHOLDS.copy()
    merged.update(custom)
    return merged


def vectorized_macro_gate(
    df: pd.DataFrame,
    thresholds: Optional[Dict[str, float]] = None,
) -> pd.Series:
    """
    Tarihsel veri üzerinde vektörel Macro Gate maskesi oluşturur.

    Dönüş:
        pd.Series[bool] (index=df.index)
        True  → Gate kapalı (işlem yapılmaz)
        False → Gate açık

    Not:
    - Tüm kontroller `shift(1)` ile bir önceki günün makro durumuna göre yapılır
      (look-ahead bias önleme).
    """
    if thresholds is None:
        thresholds = get_thresholds()

    mask = pd.Series(False, index=df.index)

    # VIX seviyesi
    if "VIX" in df.columns:
        mask |= df["VIX"].shift(1) > thresholds["VIX_HIGH"]

    # USDTRY 5 günlük değişim
    if "USDTRY" in df.columns:
        if "USDTRY_Change" in df.columns:
            usd_change = df["USDTRY_Change"].shift(1)
        else:
            # Fallback: ham seriden hesapla
            lookback = 1 if getattr(config, "TIMEFRAME", "D") == "W" else 5
            usd_change = df["USDTRY"].pct_change(lookback).shift(1)
        mask |= usd_change > thresholds["USDTRY_CHANGE_5D"]

    # SP500 momentum
    if "SP500" in df.columns:
        if "SP500_Return" in df.columns:
            sp_mom = df["SP500_Return"].shift(1)
        else:
            lookback = 1 if getattr(config, "TIMEFRAME", "D") == "W" else 5
            sp_mom = df["SP500"].pct_change(lookback).shift(1)
        mask |= sp_mom < thresholds["SP500_MOMENTUM"]

    return mask.fillna(False)


def single_step_macro_gate(
    last_row: pd.Series,
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, bool]:
    """
    Tek adımlık (canlı kullanım) macro gate değerlendirmesi.

    Dönüş:
        {
          "VIX_HIGH": bool,
          "USDTRY_SHOCK": bool,
          "GLOBAL_RISK_OFF": bool,
          "BLOCK_ALL": bool  # true ise trade yapılmamalı
        }
    """
    if thresholds is None:
        thresholds = get_thresholds()

    status = {
        "VIX_HIGH": False,
        "USDTRY_SHOCK": False,
        "GLOBAL_RISK_OFF": False,
        "BLOCK_ALL": False,
    }

    # VIX
    if "VIX" in last_row.index and pd.notna(last_row["VIX"]):
        status["VIX_HIGH"] = bool(last_row["VIX"] > thresholds["VIX_HIGH"])

    # USDTRY
    if "USDTRY_Change" in last_row.index and pd.notna(last_row["USDTRY_Change"]):
        status["USDTRY_SHOCK"] = bool(
            last_row["USDTRY_Change"] > thresholds["USDTRY_CHANGE_5D"]
        )

    # SP500
    if "SP500_Return" in last_row.index and pd.notna(last_row["SP500_Return"]):
        status["GLOBAL_RISK_OFF"] = bool(
            last_row["SP500_Return"] < thresholds["SP500_MOMENTUM"]
        )

    # Basit kural: herhangi biri tetiklenmişse blokla
    status["BLOCK_ALL"] = (
        status["VIX_HIGH"] or status["USDTRY_SHOCK"] or status["GLOBAL_RISK_OFF"]
    )
    return status

