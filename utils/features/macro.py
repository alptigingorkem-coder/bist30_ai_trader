"""
Makro Ekonomik Mixin'i
Makro etkileşim özellikleri, türetilmiş makro feature'ları, makro gate,
sektör dummies, banka/market özellikleri.
"""
import pandas as pd
import numpy as np
import config


class MacroMixin:
    """Makroekonomik feature metotlarını sağlayan mixin."""

    def add_sector_dummies(self, ticker):
        """Sektörel dummy değişkenleri ekler."""
        df = self.data
        sector = config.get_sector(ticker)

        critical_sectors = ['Banking', 'Holding', 'Aviation', 'Automotive', 'Steel', 'Energy', 'Telecom', 'Retail', 'RealEstate']

        for s in critical_sectors:
            df[f'Sector_{s}'] = 1 if sector == s else 0

        self.data = df
        return df

    def add_macro_interaction_features(self):
        """Makro veriler ile hisse/sektör özellikleri arasındaki etkileşimleri ekler."""
        df = self.data

        # Banking <-> Bond Yields
        if 'BOND_Change' in df.columns and 'Sector_Banking' in df.columns:
            df['Banking_Interest_Interaction'] = df['Sector_Banking'] * df['BOND_Change']

        # Export Oriented <-> USDTRY
        if 'USDTRY_Change' in df.columns:
            sector_fx_pairs = [
                ('Sector_Aviation', 'Aviation_FX_Interaction'),
                ('Sector_Automotive', 'Auto_FX_Interaction'),
                ('Sector_Energy', 'Energy_FX_Interaction'),
                ('Sector_Telecom', 'Telecom_FX_Interaction'),
                ('Sector_Steel', 'Steel_FX_Interaction'),
                ('Sector_Retail', 'Retail_FX_Interaction'),
            ]
            for sector_col, interaction_col in sector_fx_pairs:
                if sector_col in df.columns:
                    df[interaction_col] = df[sector_col] * df['USDTRY_Change']

        self.data = df
        return df

    def add_bank_features(self):
        """Bankalar için özel featurelar: XBANK Momentum, Sektör Korelasyonu"""
        df = self.data

        if 'XBANK' in df.columns:
            momentum_lag = 1 if config.TIMEFRAME == 'W' else 5
            df['XBANK_Momentum'] = df['XBANK'] / df['XBANK'].shift(momentum_lag) - 1

            corr_window = 6 if config.TIMEFRAME == 'W' else 30
            df['XBANK_Corr'] = df['Close'].rolling(corr_window).corr(df['XBANK'])

            if 'XU100' in df.columns:
                df['XBANK_Rel_XU100'] = df['XBANK'] / df['XU100']
                df['XBANK_Rel_Mom'] = df['XBANK_Rel_XU100'] / df['XBANK_Rel_XU100'].shift(momentum_lag) - 1

        self.data = df
        return df

    def add_advanced_market_features(self):
        """Gelişmiş piyasa özellikleri: Sektör Rotasyonu (Fiyat Bazlı)"""
        df = self.data

        if 'XBANK' in df.columns and 'XU100' in df.columns:
            df['Sector_Rotation'] = df['XBANK'] / df['XU100']
            rotation_lag = 1 if config.TIMEFRAME == 'W' else 5
            df['Sector_Rotation_Trend'] = df['Sector_Rotation'].pct_change(rotation_lag)

        self.data = df
        return df

    def add_macro_derived_features(self):
        """
        Kriz tespiti için türetilmiş makro özellikler.
        Ham sütunlar clean_data()'da silinmeden önce hesaplanır.
        """
        df = self.data

        if 'USDTRY' in df.columns:
            lookback = 1 if config.TIMEFRAME == 'W' else 5
            df['USDTRY_Change'] = df['USDTRY'].pct_change(lookback)

        if 'VIX' in df.columns:
            df['VIX_Risk'] = df['VIX'].copy()

        if 'BOND_10Y' in df.columns:
            df['BOND_Change'] = df['BOND_10Y'].diff(5)

        if 'SP500' in df.columns:
            lookback = 1 if config.TIMEFRAME == 'W' else 5
            df['SP500_Return'] = df['SP500'].pct_change(lookback)
            df['RS_vs_SP500'] = df['Close'] / df['SP500']

        lookback = 1 if config.TIMEFRAME == 'W' else 5

        if 'GOLD' in df.columns and 'USDTRY' in df.columns:
            df['Gold_TRY'] = df['GOLD'] * df['USDTRY']
            df['Gold_TRY_Momentum'] = df['Gold_TRY'].pct_change(lookback)

        if 'OIL' in df.columns and 'USDTRY' in df.columns:
            df['Oil_TRY'] = df['OIL'] * df['USDTRY']
            df['Oil_TRY_Momentum'] = df['Oil_TRY'].pct_change(lookback)

        if 'GOLD' in df.columns and 'OIL' in df.columns:
            gold_vol = df['GOLD'].pct_change().rolling(20).std()
            oil_vol = df['OIL'].pct_change().rolling(20).std()
            df['Commodity_Volatility'] = (gold_vol + oil_vol) / 2

        self.data = df
        return df

    def get_macro_gate_status(self):
        """Legacy method for single step check."""
        status = {
            "VIX_HIGH": False,
            "USDTRY_SHOCK": False,
            "GLOBAL_RISK_OFF": False
        }
        df = self.data
        if df.empty:
            return status

        last_row = df.iloc[-1]
        thresholds = getattr(config, 'MACRO_GATE_THRESHOLDS', {
            'VIX_HIGH': 30.0,
            'USDTRY_CHANGE_5D': 0.03,
            'SP500_MOMENTUM': 0.0
        })

        if 'VIX' in df.columns and not pd.isna(last_row['VIX']):
            status["VIX_HIGH"] = bool(last_row['VIX'] > thresholds['VIX_HIGH'])

        if 'USDTRY' in df.columns:
            try:
                lookback = 1 if config.TIMEFRAME == 'W' else 5
                if len(df) >= lookback:
                    current_price = last_row['USDTRY']
                    prev_price = df['USDTRY'].iloc[-lookback]
                    pct_change = (current_price - prev_price) / prev_price
                    status["USDTRY_SHOCK"] = bool(pct_change > thresholds['USDTRY_CHANGE_5D'])
            except:
                pass

        if 'SP500' in df.columns:
            try:
                lookback = 1 if config.TIMEFRAME == 'W' else 5
                if len(df) > lookback:
                    current = last_row['SP500']
                    prev = df['SP500'].iloc[-lookback]
                    mom = (current - prev) / prev
                    status["GLOBAL_RISK_OFF"] = bool(mom < thresholds['SP500_MOMENTUM'])
            except:
                pass

        return status

    def get_macro_gate_status_vectorized(self, df=None, thresholds=None):
        """
        Vectorized version of macro gate check for backtesting.
        Returns a boolean Series (True = Gate Closed / Risk OFF).
        """
        if df is None:
            df = self.data
        if thresholds is None:
            thresholds = getattr(config, 'MACRO_GATE_THRESHOLDS', {
                'VIX_HIGH': 30.0,
                'USDTRY_CHANGE_5D': 0.03,
                'SP500_MOMENTUM': 0.0
            })

        mask = pd.Series(False, index=df.index)

        if 'VIX' in df.columns:
            mask |= (df['VIX'].shift(1) > thresholds['VIX_HIGH'])

        if 'USDTRY' in df.columns:
            if 'USDTRY_Change' in df.columns:
                mask |= (df['USDTRY_Change'].shift(1) > thresholds['USDTRY_CHANGE_5D'])
            else:
                usd_change = df['USDTRY'].pct_change(5).shift(1)
                mask |= (usd_change > thresholds['USDTRY_CHANGE_5D'])

        if 'SP500' in df.columns:
            if 'SP500_Return' in df.columns:
                mask |= (df['SP500_Return'].shift(1) < thresholds['SP500_MOMENTUM'])
            else:
                sp_mom = df['SP500'].pct_change(5).shift(1)
                mask |= (sp_mom < thresholds['SP500_MOMENTUM'])

        return mask
