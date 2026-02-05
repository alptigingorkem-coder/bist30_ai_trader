
import os
from dataclasses import dataclass
from typing import Dict, Optional

import joblib
import numpy as np
import pandas as pd

import config


@dataclass
class EnsembleWeights:
    """
    Basit ağırlık yapısı.

    Gelecekte:
    - Rejim bazlı ağırlık setleri (Crash_Bear / Trend_Up / Sideways)
    - Sektör bazlı ağırlık setleri
    eklenebilir.
    """

    lgbm: float = 0.6
    catboost: float = 0.4

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "EnsembleWeights":
        return cls(
            lgbm=data.get("lgbm", 0.6),
            catboost=data.get("catboost", 0.4),
        )

    def to_dict(self) -> Dict[str, float]:
        return {"lgbm": self.lgbm, "catboost": self.catboost}


class EnsembleModel:
    """
    Global ensemble modeli.

    Şu an:
    - LightGBM + CatBoost skoru basit ağırlıklı ortalama ile birleştiriliyor.

    Tasarım olarak:
    - Rejim (Crash_Bear / Trend_Up / Sideways) ve istenirse sektör
      bazlı dinamik ağırlıklandırmayı destekleyecek şekilde genişletilebilir.
    """

    def __init__(
        self,
        lgbm_model,
        catboost_model,
        weights: Optional[Dict[str, float]] = None,
        regime_aware: bool = False,
    ):
        self.lgbm_model = lgbm_model
        self.catboost_model = catboost_model
        self.weights = EnsembleWeights.from_dict(weights or {"lgbm": 0.6, "catboost": 0.4})
        # Rejim bazlı ağırlıklandırma ileride etkinleştirilebilir
        self.regime_aware = regime_aware

        # Rejim → ağırlık haritası (taslak)
        # Örn: Crash_Bear'da CatBoost daha defansif ise ağırlığı artırılabilir.
        self.regime_weights: Dict[str, EnsembleWeights] = getattr(
            config,
            "ENSEMBLE_REGIME_WEIGHTS",
            {
                "Sideways": self.weights.to_dict(),
                "Crash_Bear": {"lgbm": 0.4, "catboost": 0.6},
                "Trend_Up": {"lgbm": 0.7, "catboost": 0.3},
            },
        )

    def _resolve_weights_for_row(self, regime: Optional[str]) -> EnsembleWeights:
        """
        Verilen rejim için kullanılacak ağırlıkları döndürür.
        Şu an için sadece tasarım: Rejim yoksa global default kullanılır.
        """
        if not self.regime_aware or not regime:
            return self.weights

        raw = self.regime_weights.get(regime, self.weights.to_dict())
        return EnsembleWeights.from_dict(raw)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Ensemble prediction using (opsiyonel) regime-aware weighted scores.
        """
        lgbm_scores = self.lgbm_model.predict(df)
        cat_scores = self.catboost_model.predict(df)

        scores_df = pd.DataFrame(
            {
                "lgbm": lgbm_scores,
                "catboost": cat_scores,
            },
            index=df.index,
        )

        # Rejim bilgisi varsa satır bazlı dinamik ağırlık seti kullan
        if self.regime_aware and "Regime" in df.columns:
            weights_l = []
            weights_c = []
            for r in df["Regime"].astype(str):
                w = self._resolve_weights_for_row(r)
                weights_l.append(w.lgbm)
                weights_c.append(w.catboost)
            weights_l = np.asarray(weights_l)
            weights_c = np.asarray(weights_c)
        else:
            # Global sabit ağırlıklar
            weights_l = np.full(len(scores_df), self.weights.lgbm)
            weights_c = np.full(len(scores_df), self.weights.catboost)

        ensemble_score = (scores_df["lgbm"].values * weights_l) + (
            scores_df["catboost"].values * weights_c
        )

        # Basit kural tabanlı RSI filtresi
        if "RSI" in df.columns:
            rsi = df["RSI"].to_numpy()
            # Overbought penalty
            ensemble_score = np.where(rsi > 80, ensemble_score * 0.8, ensemble_score)
            # Oversold boost
            ensemble_score = np.where(rsi < 30, ensemble_score * 1.1, ensemble_score)

        return ensemble_score

    def save(self, path: str) -> None:
        """
        Yalnızca ağırlık ve konfig bilgilerini kaydeder.
        Modeller ayrı dosyalarda tutulur.
        """
        payload = {
            "weights": self.weights.to_dict(),
            "regime_aware": self.regime_aware,
            "regime_weights": self.regime_weights,
        }
        joblib.dump(payload, path)

    @classmethod
    def load_with_models(cls, path: str, lgbm_model, cat_model) -> "EnsembleModel":
        if os.path.exists(path):
            payload = joblib.load(path)
            weights = payload.get("weights", {"lgbm": 0.6, "catboost": 0.4})
            regime_aware = payload.get("regime_aware", False)
        else:
            weights = {"lgbm": 0.6, "catboost": 0.4}
            regime_aware = False

        return cls(lgbm_model, cat_model, weights, regime_aware=regime_aware)

