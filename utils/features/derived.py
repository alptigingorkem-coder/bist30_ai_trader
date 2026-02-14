"""
Türetilmiş Feature Mixin'i
Getiri, volatilite, lag özellikleri, zaman özellikleri, hedef değişkenler, temizlik.
"""
import pandas as pd
import numpy as np
import config


class DerivedMixin:
    """Türetilmiş feature metotlarını sağlayan mixin."""

    def add_multi_window_targets(self):
        """
        Multi-window target creation (Excess Return for T+1, T+5 etc.)
        """
        df = self.data
        forward_windows = getattr(config, 'FORWARD_WINDOWS', [1])

        if not isinstance(forward_windows, list):
            forward_windows = [forward_windows]

        for win in forward_windows:
            suffix = f"_T{win}"

            col_close_fwd = f'Close_T{win}'
            col_xu100_fwd = f'XU100_T{win}'

            df[col_close_fwd] = df['Close'].shift(-win)
            df[f'NextDay_Return{suffix}'] = df[col_close_fwd] / df['Close'] - 1

            if 'XU100' in df.columns:
                df[col_xu100_fwd] = df['XU100'].shift(-win)
                df[f'NextDay_XU100_Return{suffix}'] = df[col_xu100_fwd] / df['XU100'] - 1
                df[f'Excess_Return{suffix}'] = df[f'NextDay_Return{suffix}'] - df[f'NextDay_XU100_Return{suffix}']
                df.drop(columns=[col_close_fwd, col_xu100_fwd], inplace=True)
            else:
                df[f'Excess_Return{suffix}'] = df[f'NextDay_Return{suffix}']
                df.drop(columns=[col_close_fwd], inplace=True)

        default_win = forward_windows[0]
        if f'Excess_Return_T{default_win}' in df.columns:
            df['Excess_Return'] = df[f'Excess_Return_T{default_win}']
            df['NextDay_Return'] = df[f'NextDay_Return_T{default_win}']
            if f'NextDay_XU100_Return_T{default_win}' in df.columns:
                df['NextDay_XU100_Return'] = df[f'NextDay_XU100_Return_T{default_win}']

        self.data = df
        return df

    def add_time_features(self):
        """Zaman bazlı özellikleri ekler."""
        df = self.data
        df['DayOfWeek'] = df.index.dayofweek
        df['Month'] = df.index.month
        df['Quarter'] = df.index.quarter
        self.data = df
        return df

    def add_derived_features(self):
        """Getiri, volatilite ve lag özelliklerini ekler."""
        df = self.data

        # Log Return
        df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))

        # Volatilite
        vol_window = 4 if config.TIMEFRAME == 'W' else 20
        df['Volatility_20'] = df['Log_Return'].rolling(window=vol_window).std()

        # Upside Volatility
        df['Upside_Volatility'] = df['Log_Return'].where(df['Log_Return'] > 0).rolling(window=vol_window).std().fillna(0)

        # Relative Volatility
        df['Volatility_Ratio'] = df['Volatility_20'] / df['Volatility_20'].rolling(52 if config.TIMEFRAME == 'W' else 252).mean()

        # Excess Return (Alpha)
        if 'XU100' in df.columns:
            df['XU100_Return'] = np.log(df['XU100'] / df['XU100'].shift(1))
            df['Excess_Return_Current'] = df['Log_Return'] - df['XU100_Return']
        else:
            df['Excess_Return_Current'] = df['Log_Return']

        # Lags
        lags = [1, 2, 4, 12] if config.TIMEFRAME == 'W' else [1, 5, 20, 60]
        for lag in lags:
            df[f'Return_Lag_{lag}'] = df['Close'].pct_change(lag)
            df[f'Excess_Return_Lag_{lag}'] = df['Excess_Return_Current'].shift(lag)

        # Momentum Trend
        col_list = df.columns
        if 'Return_Lag_4w' in col_list and 'Return_Lag_12w' in col_list:
            df['Momentum_Trend'] = (
                (df['Return_Lag_4w'] > 0).astype(int) +
                (df['Return_Lag_12w'] > 0).astype(int) +
                (df['RSI'] > 50).astype(int)
            )

        # Risk-Adjusted Excess Return
        vol_col = 'Volatility_20'
        if vol_col in df.columns:
            df['Excess_Return_RiskAdjusted'] = df['Excess_Return_Current'] / (df[vol_col] + 1e-9)
        else:
            df['Excess_Return_RiskAdjusted'] = df['Excess_Return_Current']

        self.data = df
        return df

    def clean_data(self):
        """NaN değerleri temizler ve MAKRO SÜTUNLARI SİLER."""
        macro_cols_to_drop = ['VIX', 'USDTRY', 'SP500', 'GOLD', 'OIL', 'Tahvil_Faizi', 'BOND_10Y']
        existing_cols_to_drop = [c for c in macro_cols_to_drop if c in self.data.columns]

        if existing_cols_to_drop:
            self.data.drop(columns=existing_cols_to_drop, inplace=True)

        exclude_cols = [
            'NextDay_Close', 'NextDay_Direction', 'NextDay_Return', 'Excess_Return',
            'Forward_PE', 'EBITDA_Margin', 'Revenue_Growth_YoY', 'Debt_to_Equity', 'PB_Ratio',
            'EBITDA_Margin_Change', 'Forward_PE_Change', 'Excess_Return_RiskAdjusted',
            'XU100_Return', 'USDTRY_Change', 'VIX_Risk', 'VIX_Change', 'SP500_Return',
            'Gold_TRY', 'Oil_TRY', 'NextDay_XU100_Return', 'BOND_Change'
        ]

        for c in self.data.columns:
            if 'Excess_Return_T' in c or 'NextDay_Return_T' in c:
                exclude_cols.append(c)

        cols_to_check = [c for c in self.data.columns if c not in exclude_cols]

        self.data[cols_to_check] = self.data[cols_to_check].ffill().fillna(0)

        return self.data
