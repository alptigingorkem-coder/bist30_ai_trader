"""
Teknik Analiz Mixin'i
RSI, MACD, Bollinger Bands, SMA, ROC, Ichimoku, ADX, Williams %R, VWAP,
Stochastic, OBV, MFI, CMF, Choppiness, ATR
"""
import pandas as pd
import pandas_ta as ta
import numpy as np
import config


class TechnicalMixin:
    """Teknik indikatör metotlarını sağlayan mixin."""

    def add_technical_indicators(self):
        """Teknik indikatörleri ekler (RSI, MACD, Bollinger, SMA, vb.)"""
        df = self.data

        # RSI & RSI Slope (Momentum Acceleration)
        df['RSI'] = ta.rsi(df['Close'], length=config.RSI_PERIOD)
        if 'RSI' in df.columns:
            df['RSI_Slope'] = df['RSI'].diff(3)

        # MACD
        macd = ta.macd(df['Close'], fast=config.MACD_FAST, slow=config.MACD_SLOW, signal=config.MACD_SIGNAL)
        if macd is not None:
            macd.columns = ['MACD', 'MACD_Hist', 'MACD_Signal']
            df = pd.concat([df, macd], axis=1)

        # Bollinger Bands
        bb = ta.bbands(df['Close'], length=config.BB_LENGTH, std=config.BB_STD)
        if bb is not None:
            df = pd.concat([df, bb], axis=1)
            lower_col = f"BBL_{config.BB_LENGTH}_{config.BB_STD}.0"
            upper_col = f"BBU_{config.BB_LENGTH}_{config.BB_STD}.0"
            mid_col = f"BBM_{config.BB_LENGTH}_{config.BB_STD}.0"

            cols = df.columns
            if lower_col not in cols:
                try:
                    lower_col = cols[cols.str.contains('BBL')][0]
                    upper_col = cols[cols.str.contains('BBU')][0]
                    mid_col = cols[cols.str.contains('BBM')][0]
                except IndexError:
                    pass

            if upper_col in df.columns and lower_col in df.columns and mid_col in df.columns:
                df['BB_Width'] = (df[upper_col] - df[lower_col]) / df[mid_col]
                df['Vol_Breakout'] = ((df['Close'] > df[upper_col]) & (df['BB_Width'] > df['BB_Width'].shift(1))).astype(int)

        # SMA & Above_SMA200
        sma_periods = [5, 20, 50, 200]
        for p in sma_periods:
            df[f'SMA_{p}'] = ta.sma(df['Close'], length=p)

        if f'SMA_200' in df.columns:
            # Ensure safe comparison (handle None -> NaN)
            close_series = df['Close'].astype(float)
            sma_series = df['SMA_200'].astype(float)
            
            df['Close_to_SMA200'] = close_series / sma_series
            df['Above_SMA200'] = (close_series > sma_series).fillna(False).astype(int)

        # Advanced Momentum (ROC)
        df['ROC_5'] = ta.roc(df['Close'], length=5)
        df['ROC_20'] = ta.roc(df['Close'], length=20)

        # Relative Strength vs Benchmarks
        if 'XU100' in df.columns:
            df['RS_XU100'] = df['Close'] / df['XU100']
            df['RS_XU100_Trend'] = df['RS_XU100'].pct_change(5)

        self.data = df
        return df

    def add_custom_indicators(self):
        """
        Gelişmiş teknik indikatörleri ekler.
        Ichimoku, ADX, Williams %R, VWAP.
        Herhangi bir indikatör başarısız olursa sessizce devam eder.
        """
        df = self.data

        # Ichimoku Cloud
        try:
            ichi = ta.ichimoku(high=df['High'], low=df['Low'], close=df['Close'])
            if isinstance(ichi, tuple):
                ichi_df = ichi[0]
            else:
                ichi_df = ichi

            if ichi_df is not None:
                ichi_df = ichi_df.add_prefix("ICHIMOKU_")
                df = pd.concat([df, ichi_df], axis=1)

                span_a_cols = [c for c in ichi_df.columns if "A" in c]
                span_b_cols = [c for c in ichi_df.columns if "B" in c]
                if span_a_cols and span_b_cols:
                    span_a = ichi_df[span_a_cols[0]]
                    span_b = ichi_df[span_b_cols[0]]
                    df["ICHIMOKU_Kumo_Width"] = (span_a - span_b).abs()
        except Exception:
            pass

        # ADX - Trend gücü
        try:
            adx = ta.adx(df['High'], df['Low'], df['Close'])
            if adx is not None:
                adx = adx.add_prefix("ADX_")
                df = pd.concat([df, adx], axis=1)
        except Exception:
            pass

        # Williams %R
        try:
            willr = ta.willr(df['High'], df['Low'], df['Close'])
            if willr is not None:
                df['WilliamsR_14'] = willr
        except Exception:
            pass

        # VWAP
        try:
            if 'Volume' in df.columns:
                vwap = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
                if vwap is not None:
                    df['VWAP'] = vwap
        except Exception:
            pass

        self.data = df
        return df

    def add_volume_and_extra_indicators(self):
        """
        Stochastic, Volume (OBV/MFI/CMF), Choppiness, ATR.
        """
        df = self.data

        # Stochastic Oscillator
        stoch = ta.stoch(df['High'], df['Low'], df['Close'])
        if stoch is not None:
            df = pd.concat([df, stoch], axis=1)

        # Volume-based indicators
        if 'Volume' in df.columns:
            df['OBV'] = ta.obv(df['Close'], df['Volume'])

            vol_ma = df['Volume'].rolling(20).mean()
            df['Volume_Breakout'] = ((df['Volume'] / vol_ma > 1.5) & (df['Close'] > df['Open'])).astype(int)

            if 'OBV' in df.columns:
                df['OBV_Slope'] = df['OBV'].pct_change(5)

            df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
            df['CMF_20'] = ta.cmf(df['High'], df['Low'], df['Close'], df['Volume'], length=20)

        # Choppiness Index
        try:
            chop = ta.chop(df['High'], df['Low'], df['Close'], length=14)
            if chop is not None:
                df['Choppiness_14'] = chop
        except Exception:
            pass

        # ATR
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=getattr(config, 'ATR_PERIOD', 14))

        self.data = df
        return df
