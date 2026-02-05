"""
Piyasa haberleri / sosyal medya verileri üzerinden sentiment feature'ları üretmek için
yardımcı fonksiyonlar.

Bu modül şimdilik sadece tasarım seviyesindedir:
- Dış veri kaynaklarına (Twitter/X, haber API'leri vb.) doğrudan erişim YOK.
- Amaç, sentiment skorlarının zaten hazırlanmış olduğu bir `DataFrame` veya CSV'den
  alınarak fiyat datası ile merge edilmesine olanak tanımaktır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class SentimentConfig:
    """
    Sentiment verisinin nasıl yorumlanacağına dair basit konfig:
    - column: Dış kaynaktan gelen sentiment skor kolon adı
    - smoothing_window: Günlük oynaklığı azaltmak için hareketli ortalama penceresi
    """

    column: str = "sentiment_score"
    smoothing_window: int = 3


def merge_sentiment_features(
    price_df: pd.DataFrame,
    sentiment_df: pd.DataFrame,
    config: Optional[SentimentConfig] = None,
) -> pd.DataFrame:
    """
    Sentiment skorlarını fiyat verisi ile birleştirir ve türetilmiş basit feature'lar üretir.

    Beklenen giriş:
    - price_df: Hisse fiyat datası (index: Date)
    - sentiment_df: Aynı veya daha seyrek frekansta sentiment skorları
      (index: Date, column: sentiment_score veya config.column)
    """
    if config is None:
        config = SentimentConfig()

    if price_df.empty or sentiment_df.empty:
        return price_df

    df = price_df.copy()
    s = sentiment_df.copy()

    df.index = pd.to_datetime(df.index).normalize()
    s.index = pd.to_datetime(s.index).normalize()

    col = config.column
    if col not in s.columns:
        # Beklenen kolon yoksa, feature üretmeden geri dön.
        return df

    # Left join + ffill: fiyat tarihleri üzerinde sentiment
    merged = df.join(s[[col]], how="left")
    merged[col] = merged[col].ffill()

    # Basit türev feature'lar
    merged[f"{col}_smoothed"] = (
        merged[col].rolling(config.smoothing_window).mean()
    )
    merged[f"{col}_delta"] = merged[col].diff()

    return merged

