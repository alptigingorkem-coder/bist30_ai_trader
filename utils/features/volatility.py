"""
Volatilite Mixin'i
Garman-Klass, Rogers-Satchell, Parkinson volatilite tahminleyicileri.
"""
import numpy as np


class VolatilityMixin:
    """Gelişmiş volatilite tahminleyicilerini sağlayan mixin."""

    def add_volatility_estimators(self):
        """
        Gelişmiş volatilite tahminleyicileri ekler (Garman-Klass, Rogers-Satchell, Parkinson).
        Bu indikatörler standart sapmadan (Close-to-Close) daha verimli tahminler sunar.
        """
        df = self.data
        window = 20

        # Logaritmik fiyat farkları
        log_hl = (df['High'] / df['Low']).apply(np.log)
        log_co = (df['Close'] / df['Open']).apply(np.log)

        # 1. Parkinson Volatility
        rs = (1.0 / (4.0 * np.log(2.0))) * (log_hl ** 2)
        df['Vol_Parkinson'] = np.sqrt(rs.rolling(window=window).mean()) * np.sqrt(252)

        # 2. Garman-Klass Volatility
        gk = 0.5 * (log_hl ** 2) - (2 * np.log(2) - 1) * (log_co ** 2)
        df['Vol_GarmanKlass'] = np.sqrt(gk.rolling(window=window).mean()) * np.sqrt(252)

        # 3. Rogers-Satchell Volatility
        log_hc = (df['High'] / df['Close']).apply(np.log)
        log_ho = (df['High'] / df['Open']).apply(np.log)
        log_lc = (df['Low'] / df['Close']).apply(np.log)
        log_lo = (df['Low'] / df['Open']).apply(np.log)

        rs_vol = log_hc * log_ho + log_lc * log_lo
        df['Vol_RogersSatchell'] = np.sqrt(rs_vol.rolling(window=window).mean()) * np.sqrt(252)

        # Volatilite Rejimi (Düşük/Yüksek)
        df['Vol_Regime'] = np.where(df['Vol_GarmanKlass'] > df['Vol_GarmanKlass'].rolling(252).mean(), 1, 0)

        self.data = df
        return df
