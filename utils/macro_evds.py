"""
TCMB EVDS tabanlı makro veri entegrasyonu için yardımcı modül.

Bu modül şu amaçlarla tasarlanmıştır:
- EVDS API üzerinden faiz, enflasyon, rezerv, CDS vb. serileri çekmek
- Çekilen serileri tek bir `DataFrame` içinde normalize etmek
- Fiyat verisi ile (hisse zaman serileri) güvenli şekilde merge etmek

Not:
- Şu an için sadece fonksiyon iskeletleri ve tip imzaları tanımlıdır.
- Gerçek API anahtarı ve seriler kullanıcı tarafından doldurulmalıdır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class EVDSConfig:
    api_key: str
    series_codes: Dict[str, str]  # Örn: {"POLICY_RATE": "TP.FG2", "CPI": "TP.FG.J0"}


class EVDSMacroClient:
    """
    TCMB EVDS API için basit bir istemci iskeleti.

    Kullanım senaryosu:
    - Backtest / araştırma aşamasında offline makro dataset hazırlama
    - Daha sonra bu dataset'i feature store veya ayrı bir parquet dosyasına yazma
    """

    def __init__(self, config: EVDSConfig):
        self.config = config
        # Gerçek implementasyonda: evdsAPI veya requests tabanlı bir istemci tutulabilir.

    def fetch_series(
        self,
        start_date: str,
        end_date: str,
        series: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Verilen tarih aralığı için belirtilen EVDS serilerini çeker.

        Parametreler:
        - start_date, end_date: 'YYYY-MM-DD'
        - series: ['POLICY_RATE', 'CPI', ...] gibi logical isimler.

        Dönüş:
        - index: Date
        - kolonlar: logical seri isimleri

        Şu an yalnızca fonksiyon imzası ve temel iskelet mevcuttur.
        """
        if series is None:
            series = list(self.config.series_codes.keys())

        # TODO: EVDS entegrasyonu eklenecek.
        # Yerine geçici olarak boş DataFrame döndürülür.
        idx = pd.date_range(start=start_date, end=end_date, freq="D")
        return pd.DataFrame(index=idx)

    @staticmethod
    def merge_with_price_data(
        price_df: pd.DataFrame,
        macro_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Makro serileri, hisse fiyat verisi ile güvenli şekilde birleştirir.

        - Tarihleri normalize eder (tz, saat bilgisi temizlenir)
        - Forward fill ile eksikleri doldurur
        """
        if price_df.empty or macro_df.empty:
            return price_df

        left = price_df.copy()
        right = macro_df.copy()

        left.index = pd.to_datetime(left.index).normalize()
        right.index = pd.to_datetime(right.index).normalize()

        # Outer join yerine left join: sadece fiyat tarihleri kalsın
        merged = left.join(right, how="left")
        merged = merged.ffill()
        return merged

