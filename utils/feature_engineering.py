import pandas as pd
import pandas_ta as ta
import numpy as np
import config
import yfinance as yf
from datetime import datetime, timedelta

from core.feature_store import feature_store

class FeatureEngineer:
    def __init__(self, data):
        self.data = data.copy()


    def add_multi_window_targets(self):
        """
        Multi-window target creation (Excess Return for T+1, T+5 etc.)
        This method explicitly creates targets and handles forward shifting.
        """
        df = self.data
        forward_windows = getattr(config, 'FORWARD_WINDOWS', [1])
        
        # Ensure it's a list
        if not isinstance(forward_windows, list):
            forward_windows = [forward_windows]

        for win in forward_windows:
            # Suffix for multi-window
            suffix = f"_T{win}"
            
            # Future Close & XU100
            # We create temporary columns for calculation
            col_close_fwd = f'Close_T{win}'
            col_xu100_fwd = f'XU100_T{win}'
            
            df[col_close_fwd] = df['Close'].shift(-win)
            
            # Stock Return
            df[f'NextDay_Return{suffix}'] = df[col_close_fwd] / df['Close'] - 1
            
            # Excess Return Calculation
            if 'XU100' in df.columns:
                df[col_xu100_fwd] = df['XU100'].shift(-win)
                df[f'NextDay_XU100_Return{suffix}'] = df[col_xu100_fwd] / df['XU100'] - 1
                df[f'Excess_Return{suffix}'] = df[f'NextDay_Return{suffix}'] - df[f'NextDay_XU100_Return{suffix}']
                
                # Cleanup temporary columns immediately to prevent leakage
                df.drop(columns=[col_close_fwd, col_xu100_fwd], inplace=True)
            else:
                df[f'Excess_Return{suffix}'] = df[f'NextDay_Return{suffix}']
                df.drop(columns=[col_close_fwd], inplace=True)

        # Primary Target Setup (Default to first window)
        default_win = forward_windows[0]
        if f'Excess_Return_T{default_win}' in df.columns:
             df['Excess_Return'] = df[f'Excess_Return_T{default_win}']
             df['NextDay_Return'] = df[f'NextDay_Return_T{default_win}']
             if f'NextDay_XU100_Return_T{default_win}' in df.columns:
                 df['NextDay_XU100_Return'] = df[f'NextDay_XU100_Return_T{default_win}']

        self.data = df
        return df

    def add_technical_indicators(self):
        """Teknik indikatörleri ekler (RSI, MACD, Bollinger, SMA, vb.)"""
        df = self.data
        
        # RSI & RSI Slope (Momentum Acceleration)
        df['RSI'] = ta.rsi(df['Close'], length=config.RSI_PERIOD)
        if 'RSI' in df.columns:
            df['RSI_Slope'] = df['RSI'].diff(3) # 3 günlük RSI değişimi (İvme)
        
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
                # YENİ: Volatility Breakout Signal
                df['Vol_Breakout'] = ((df['Close'] > df[upper_col]) & (df['BB_Width'] > df['BB_Width'].shift(1))).astype(int)

        # SMA & Above_SMA200
        sma_periods = [5, 20, 50, 200]
        for p in sma_periods:
            df[f'SMA_{p}'] = ta.sma(df['Close'], length=p)
            
        if f'SMA_200' in df.columns:
            df['Close_to_SMA200'] = df['Close'] / df['SMA_200']
            df['Above_SMA200'] = (df['Close'] > df['SMA_200']).astype(int)

        # YENİ: Advanced Momentum (ROC)
        df['ROC_5'] = ta.roc(df['Close'], length=5)
        df['ROC_20'] = ta.roc(df['Close'], length=20)
        
        # YENİ: Relative Strength vs Benchmarks
        if 'XU100' in df.columns:
            df['RS_XU100'] = df['Close'] / df['XU100']
            # Reverted to simple momentum (no smoothing) to avoid lag
            df['RS_XU100_Trend'] = df['RS_XU100'].pct_change(5)

        self.data = df
        return df

    def add_custom_indicators(self):
        """
        Gelişmiş teknik indikatörleri ekler.
        - Ichimoku bileşenleri (Tenkan, Kijun, Senkou, Kumo genişliği)
        - ADX (trend gücü)
        - Williams %R (aşırı alım/satım)
        - VWAP (hacim ağırlıklı ortalama fiyat)

        Not:
        Bu fonksiyon, mevcut `pandas_ta` fonksiyonlarını kullanır ve
        herhangi bir indikatör başarısız olursa sessizce devam eder.
        Böylece backtest / eğitim pipeline'ı kırılmaz.
        """
        df = self.data

        # Ichimoku Cloud
        try:
            ichi = ta.ichimoku(
                high=df['High'],
                low=df['Low'],
                close=df['Close']
            )
            # pandas_ta bazı versiyonlarda (df, df_signal) tuple döndürebilir
            if isinstance(ichi, tuple):
                ichi_df = ichi[0]
            else:
                ichi_df = ichi

            if ichi_df is not None:
                ichi_df = ichi_df.add_prefix("ICHIMOKU_")
                df = pd.concat([df, ichi_df], axis=1)

                # Kumo genişliği (bulut kalınlığı)
                span_a_cols = [c for c in ichi_df.columns if "A" in c]
                span_b_cols = [c for c in ichi_df.columns if "B" in c]
                if span_a_cols and span_b_cols:
                    span_a = ichi_df[span_a_cols[0]]
                    span_b = ichi_df[span_b_cols[0]]
                    df["ICHIMOKU_Kumo_Width"] = (span_a - span_b).abs()
        except Exception:
            # Ichimoku yoksa veya hata verdiyse devam et
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

        # VWAP (gün içi olmayan veride de referans olarak kullanılabilir)
        try:
            if 'Volume' in df.columns:
                vwap = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
                if vwap is not None:
                    df['VWAP'] = vwap
        except Exception:
            pass

        self.data = df
        return df

    def add_sector_dummies(self, ticker):
        """Sektörel dummy değişkenleri ekler."""
        df = self.data
        sector = config.get_sector(ticker)
        
        # Ana model için sadece en kritik sektörleri dummy yapalım (Sparse önlemek için)
        critical_sectors = ['Banking', 'Holding', 'Aviation', 'Automotive', 'Steel', 'Energy', 'Telecom', 'Retail', 'RealEstate']
        
        for s in critical_sectors:
            df[f'Sector_{s}'] = 1 if sector == s else 0
            
        self.data = df
        return df

    def add_macro_interaction_features(self):
        """Makro veriler ile hisse/sektör özellikleri arasındaki etkileşimleri ekler."""
        df = self.data
        
        # Selective Interactions to prevent overfitting/noise
        
        # 1. Banking <-> Bond Yields (Interest Rate Sensitivity)
        if 'BOND_Change' in df.columns and 'Sector_Banking' in df.columns:
             df['Banking_Interest_Interaction'] = df['Sector_Banking'] * df['BOND_Change']
             
        # 2. Export Oriented (Auto/Aviation) <-> USDTRY (FX Sensitivity)
        if 'USDTRY_Change' in df.columns:
            if 'Sector_Aviation' in df.columns:
                 df['Aviation_FX_Interaction'] = df['Sector_Aviation'] * df['USDTRY_Change']
            if 'Sector_Automotive' in df.columns:
                 df['Auto_FX_Interaction'] = df['Sector_Automotive'] * df['USDTRY_Change']
            if 'Sector_Energy' in df.columns:
                 df['Energy_FX_Interaction'] = df['Sector_Energy'] * df['USDTRY_Change']
            if 'Sector_Telecom' in df.columns:
                 df['Telecom_FX_Interaction'] = df['Sector_Telecom'] * df['USDTRY_Change']
            if 'Sector_Steel' in df.columns:
                 df['Steel_FX_Interaction'] = df['Sector_Steel'] * df['USDTRY_Change']
            if 'Sector_Retail' in df.columns:
                # Perakende için enflasyon verisi yok, o yüzden kur geçişgenliği varsayımı
                df['Retail_FX_Interaction'] = df['Sector_Retail'] * df['USDTRY_Change']

        self.data = df
        return df

    def add_volume_and_extra_indicators(self):
        """
        BUG-7 Fix: Stochastic, Volume (OBV/MFI/CMF), Choppiness, ATR.
        Önceki versiyonda add_macro_interaction_features() altında
        yorum satırının ardında indentation hatası ile dead code olarak
        kalmıştı → ayrı, düzgün bir metoda taşındı.
        """
        df = self.data

        # Stochastic Oscillator
        stoch = ta.stoch(df['High'], df['Low'], df['Close'])
        if stoch is not None:
            df = pd.concat([df, stoch], axis=1)

        # Volume-based indicators
        if 'Volume' in df.columns:
            df['OBV'] = ta.obv(df['Close'], df['Volume'])

            # Volume Breakout: hacim 20g ortalamasının 1.5x üstü + fiyat artış
            vol_ma = df['Volume'].rolling(20).mean()
            df['Volume_Breakout'] = ((df['Volume'] / vol_ma > 1.5) & (df['Close'] > df['Open'])).astype(int)

            # OBV Slope (5-bar trend teyidi)
            if 'OBV' in df.columns:
                df['OBV_Slope'] = df['OBV'].pct_change(5)

            # Money Flow Index (14-period)
            df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)

            # Chaikin Money Flow (20-period)
            df['CMF_20'] = ta.cmf(df['High'], df['Low'], df['Close'], df['Volume'], length=20)

        # Choppiness Index  (>61.8 sideways / <38.2 trending)
        try:
            chop = ta.chop(df['High'], df['Low'], df['Close'], length=14)
            if chop is not None:
                df['Choppiness_14'] = chop
        except Exception:
            pass

        # ATR (Average True Range)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=getattr(config, 'ATR_PERIOD', 14))

        self.data = df
        return df

    def add_bank_features(self):
        """Bankalar için özel featurelar: XBANK Momentum, Sektör Korelasyonu"""
        df = self.data
        
        # Eğer makro veriler içinde XBANK varsa
        if 'XBANK' in df.columns:
            # XBANK Momentum (Haftalık: 5 gün → 1 hafta)
            momentum_lag = 1 if config.TIMEFRAME == 'W' else 5
            df['XBANK_Momentum'] = df['XBANK'] / df['XBANK'].shift(momentum_lag) - 1
            
            # XBANK ile Korelasyon (Haftalık: 30 gün → 6 hafta)
            corr_window = 6 if config.TIMEFRAME == 'W' else 30
            df['XBANK_Corr'] = df['Close'].rolling(corr_window).corr(df['XBANK'])

        # XBANK / XU100 Rasyosu (Sektör vs Endeks)
            if 'XU100' in df.columns:
                df['XBANK_Rel_XU100'] = df['XBANK'] / df['XU100']
                # Rasyonun Momentum (Haftalık: 5 gün → 1 hafta)
                df['XBANK_Rel_Mom'] = df['XBANK_Rel_XU100'] / df['XBANK_Rel_XU100'].shift(momentum_lag) - 1
        
        self.data = df
        return df


    def add_fundamental_features_from_file(self, ticker):
        """
        Feature Store'dan temel analiz verilerini okur (Parquet).
        Dosya formatı: Ticker, Date, Forward_PE, EBITDA_Margin, PB_Ratio, Debt_to_Equity
        """
        df = self.data
        
        try:
            # Feature Store'dan veri çek (Parquet - Hızlı)
            # Eğer eksik veri varsa (örneğin 2015-2020) otomatik sentetik doldur
            start_date = config.START_DATE
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # FIX: Sentetik veri kodu kaldırıldı, direkt load_fundamentals kullan
            stock_fund = feature_store.load_fundamentals(tickers=[ticker], start_date=start_date, end_date=end_date)
            
            if stock_fund.empty:
                 # raise ValueError("Ticker not found in file")
                 pass
            else:
                # Tarih formatını ayarla
                stock_fund['Date'] = pd.to_datetime(stock_fund['Date'])
                
                # FIX: Look-ahead bias önleme
                # Sentetik veride buna gerek yok ama yine de tutarlılık için kalsın
                # Ancak sentetik veri zaten günlük üretildiği için shift 60 gün çok olabilir.
                # Gerçek veride bilanço gecikmesi var, sentetikte yok (çünkü günlük simülasyon).
                # Bu yüzden sadece gerçek veri kısmına veya genel yapıya uyalım.
                
                # Sentetik veri için 'IsSynthetic' kolonu eklenebilir ama şimdilik basit tutalım.
                stock_fund['Date'] = stock_fund['Date'] + pd.Timedelta(days=60)
                
                # FIX: Timezone Alignment Issues
                # Normalize to midnight and remove timezone
                stock_fund['Date'] = stock_fund['Date'].dt.normalize()
                if stock_fund['Date'].dt.tz is not None:
                    stock_fund['Date'] = stock_fund['Date'].dt.tz_localize(None)
                
                stock_fund.set_index('Date', inplace=True)
                stock_fund.sort_index(inplace=True)
                
                # Ana veri setine merge et (reindex ile)
                cols_to_merge = ['Forward_PE', 'EBITDA_Margin', 'PB_Ratio']
                
                for col in cols_to_merge:
                    if col in stock_fund.columns:
                        # Indexleri normalize ederek hizala
                        aligned_series = self._align_quarterly_data(df.index, stock_fund[col])
                        df[col] = aligned_series
                        
                        # Türetilmiş özellikler (Değişim)
                        if col == 'Forward_PE':
                            df['Forward_PE_Change'] = df['Forward_PE'].pct_change()
                        if col == 'EBITDA_Margin':
                            df['EBITDA_Margin_Change'] = df['EBITDA_Margin'].diff()
                    else:
                        df[col] = np.nan
                        
                print(f"  [Başarılı] Temel analiz verileri Feature Store'dan eklendi: {ticker}")
                self.data['FUNDAMENTAL_DATA_AVAILABLE'] = True
            
        except FileNotFoundError:
            # FIX 14: Fundamental data yoksa Alpha modelini devre dışı bırak
            print(f"⚠️ {ticker}: Fundamental data YOK - Alpha model devre dışı")
            self.data['FUNDAMENTAL_DATA_AVAILABLE'] = False
            return df

        except Exception as e:
            # print(f"  [HATA] Temel veri okuma hatası: {e}")
            pass
            
        self.data = df
        return df

    def _align_quarterly_data(self, daily_index, quarterly_series):
        """Quarterly (çeyreklik) veriyi günlük/haftalık index'e hizalar"""
        quarterly_series = quarterly_series.sort_index()
        
        # Normalize Indices for Alignment (Temp)
        # Daily index (Target)
        target_index = pd.to_datetime(daily_index).normalize()
        if target_index.tz is not None:
             target_index = target_index.tz_localize(None)
             
        # Quarterly index (Source)
        source_index = pd.to_datetime(quarterly_series.index).normalize()
        if source_index.tz is not None:
             source_index = source_index.tz_localize(None)
        
        quarterly_series.index = source_index
        
        # Reindex using normalized target index
        aligned = quarterly_series.reindex(target_index, method='ffill')
        
        # Restore original index to match df
        aligned.index = daily_index
        
        # BACKWARD FILL: İlk quarterly veriden önceki NaN'ları doldur
        if aligned.notna().any():
            first_valid_value = aligned.dropna().iloc[0]
            aligned.fillna(first_valid_value, inplace=True)
        
        return aligned
        
    def add_advanced_market_features(self):
        """Gelişmiş piyasa özellikleri: Sadece Sektör Rotasyonu (Fiyat Bazlı)"""
        df = self.data
        
        # 1. Sektör Rotasyonu (XBANK/XU100 trend)
        if 'XBANK' in df.columns and 'XU100' in df.columns:
            df['Sector_Rotation'] = df['XBANK'] / df['XU100']
            # Rotasyon trendi (Haftalık: 5 gün → 1 hafta)
            rotation_lag = 1 if config.TIMEFRAME == 'W' else 5
            df['Sector_Rotation_Trend'] = df['Sector_Rotation'].pct_change(rotation_lag)
            
        # DİĞER TÜM MAKRO FEATURELAR KALDIRILDI (Macro Gate Mimarisi)
        # VIX, SP500, GOLD, OIL artık model girdisi değil.
            
        self.data = df
        return df

    def add_kap_features(self, ticker):
        """
        KAP (Kamuyu Aydınlatma Platformu) bildirimlerinden feature üretir.
        - days_since_disclosure: Son bildirimden bu yana gün
        - disclosure_count_30d: Son 30 günde bildirim sayısı
        - has_recent_disclosure: Son 7 günde bildirim var mı?
        """
        df = self.data
        
        # Default değerler (PyKap yoksa veya veri çekilemezse)
        df['days_since_disclosure'] = 999
        df['disclosure_count_30d'] = 0
        df['has_recent_disclosure'] = 0
        
        try:
            from utils.kap_data_fetcher import kap_fetcher
            
            # KAP feature'ları ekle
            df = kap_fetcher.create_event_features(ticker, df)
            print(f"  [KAP] {ticker} için KAP feature'ları eklendi.")
            
        except Exception as e:
            print(f"  [KAP] {ticker} için feature ekleme hatası: {e}")
        
        self.data = df
        return df

    def add_time_features(self):
        """Zaman bazlı özellikleri ekler."""
        df = self.data
        df['DayOfWeek'] = df.index.dayofweek
        df['Month'] = df.index.month
        df['Quarter'] = df.index.quarter
        # df['IsMonday'] = (df.index.dayofweek == 0).astype(int) # Noise removal
        # df['IsFriday'] = (df.index.dayofweek == 4).astype(int) # Noise removal
        self.data = df
        return df

    def add_derived_features(self):
        """Getiri, volatilite ve lag özelliklerini ekler."""
        df = self.data
        
        # Günlük Getiri (Log Return)
        df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Volatilite (Haftalık: 20 gün / 5 = 4 hafta)
        vol_window = 4 if config.TIMEFRAME == 'W' else 20
        df['Volatility_20'] = df['Log_Return'].rolling(window=vol_window).std()
        
        # Volatility Ratio KALDIRILDI (Defansif özellik)
        # df['Volatility_Ratio'] = ... 
        
        # Upside Volatility (İyi Volatilite - Ralli Göstergesi)
        # Sadece pozitif getirilerin standart sapması
        df['Upside_Volatility'] = df['Log_Return'].where(df['Log_Return'] > 0).rolling(window=vol_window).std().fillna(0)

        # BUG-8 Fix: Removed duplicate return/lag calculation block that was repeated below
            
        # Relative Volatility (Stock volatility / Long-term average)
        df['Volatility_Ratio'] = df['Volatility_20'] / df['Volatility_20'].rolling(52 if config.TIMEFRAME=='W' else 252).mean()

        # Excess Return (Alpha) = Stock Return - Index Return
        if 'XU100' in df.columns:
            df['XU100_Return'] = np.log(df['XU100'] / df['XU100'].shift(1))
            df['Excess_Return_Current'] = df['Log_Return'] - df['XU100_Return']
        else:
            df['Excess_Return_Current'] = df['Log_Return']
            
        # Feature Cleansing: Remove raw price lags
        lags = [1, 2, 4, 12] if config.TIMEFRAME == 'W' else [1, 5, 20, 60]
        for lag in lags:
            df[f'Return_Lag_{lag}'] = df['Close'].pct_change(lag) 
            df[f'Excess_Return_Lag_{lag}'] = df['Excess_Return_Current'].shift(lag)
            
        # Momentum Trend (Composite Score for Growth Strategy)
        col_list = df.columns
        if 'Return_Lag_4w' in col_list and 'Return_Lag_12w' in col_list:
            df['Momentum_Trend'] = (
                (df['Return_Lag_4w'] > 0).astype(int) + 
                (df['Return_Lag_12w'] > 0).astype(int) + 
                (df['RSI'] > 50).astype(int)
            )
            
        # Target Variables logic moved to add_multi_window_targets()
        # This section is removed to prevent duplication.


        # Risk-Adjusted Excess Return (Sharpe-like single day/window)
        # BUG-9 Fix: Use Excess_Return_Current (today) instead of Excess_Return (future/target)
        vol_col = 'Volatility_20'
        if vol_col in df.columns:
            df['Excess_Return_RiskAdjusted'] = df['Excess_Return_Current'] / (df[vol_col] + 1e-9)
        else:
            df['Excess_Return_RiskAdjusted'] = df['Excess_Return_Current']
            
        self.data = df
        return df

    def add_macro_derived_features(self):
        """
        Create derived macro features for crisis detection BEFORE raw columns are deleted.
        These features will survive clean_data() and be available to regime detection.
        """
        df = self.data
        
        # 1. USDTRY_Change (5-day or 1-week change)
        if 'USDTRY' in df.columns:
            lookback = 1 if config.TIMEFRAME == 'W' else 5
            df['USDTRY_Change'] = df['USDTRY'].pct_change(lookback)
        
        # 2. VIX_Risk (direct copy for now, could add smoothing)
        if 'VIX' in df.columns:
            df['VIX_Risk'] = df['VIX'].copy()

        # 2a. Bond Change (Derived here to be available for interaction)
        if 'BOND_10Y' in df.columns:
             # 5-day change in bond yields
             df['BOND_Change'] = df['BOND_10Y'].diff(5)
        
        # 3. SP500_Return & RS_vs_SP500
        if 'SP500' in df.columns:
            lookback = 1 if config.TIMEFRAME == 'W' else 5
            df['SP500_Return'] = df['SP500'].pct_change(lookback)
            # Relative Strength (Fiyat / SP500)
            df['RS_vs_SP500'] = df['Close'] / df['SP500']

        # 4. Gold & Oil (TRY Bazlı Momentum)
        # Endüstriyel hisseler için kritik
        lookback = 1 if config.TIMEFRAME == 'W' else 5
        
        if 'GOLD' in df.columns and 'USDTRY' in df.columns:
            df['Gold_TRY'] = df['GOLD'] * df['USDTRY']
            df['Gold_TRY_Momentum'] = df['Gold_TRY'].pct_change(lookback)
            
        if 'OIL' in df.columns and 'USDTRY' in df.columns:
            df['Oil_TRY'] = df['OIL'] * df['USDTRY']
            df['Oil_TRY_Momentum'] = df['Oil_TRY'].pct_change(lookback)
            
        # 5. Commodity Volatility
        if 'GOLD' in df.columns and 'OIL' in df.columns:
             gold_vol = df['GOLD'].pct_change().rolling(20).std()
             oil_vol = df['OIL'].pct_change().rolling(20).std()
             df['Commodity_Volatility'] = (gold_vol + oil_vol) / 2
        
        self.data = df
        return df
    
    def get_macro_gate_status(self):
        """
        Legacy method for single step check.
        Values are calculated on the fly for the last row.
        """
        status = {
            "VIX_HIGH": False,
            "USDTRY_SHOCK": False,
            "GLOBAL_RISK_OFF": False
        }
        df = self.data
        if df.empty: return status
        
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
            except: pass

        if 'SP500' in df.columns:
            try:
                lookback = 1 if config.TIMEFRAME == 'W' else 5
                if len(df) > lookback:
                    current = last_row['SP500']
                    prev = df['SP500'].iloc[-lookback]
                    mom = (current - prev) / prev
                    status["GLOBAL_RISK_OFF"] = bool(mom < thresholds['SP500_MOMENTUM'])
            except: pass
                
        return status

    def get_macro_gate_status_vectorized(self, df=None, thresholds=None):
        """
        Vectorized version of macro gate check for backtesting.
        Returns a boolean Series (True = Gate Closed / Risk OFF).
        """
        if df is None: df = self.data
        if thresholds is None:
            thresholds = getattr(config, 'MACRO_GATE_THRESHOLDS', {
                'VIX_HIGH': 30.0,
                'USDTRY_CHANGE_5D': 0.03,
                'SP500_MOMENTUM': 0.0
            })
            
        # Initialize mask with False (Gate Open / Risk ON)
        # If any condition is met, we set True (Gate Closed / Risk OFF)
        mask = pd.Series(False, index=df.index)
        
        # BUG-10 Fix: Added shift(1) to prevent look-ahead bias in backtesting
        # and ensure decisions are based on known data (prior close macro state)
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

    def clean_data(self):
        """NaN değerleri temizler ve MAKRO SÜTUNLARI SİLER."""
        # Tahvil faizi eklendi
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
        
        # Add dynamic multi-window targets to exclude list
        for c in self.data.columns:
            if 'Excess_Return_T' in c or 'NextDay_Return_T' in c:
                exclude_cols.append(c)
        
        # Selective Drop Strategy
        # Drop columns with too many NaNs first? No, we trust our features.
        # Just drop rows where CRITICAL features are missing.
        # For derived features, we can fill with 0 (e.g. Interactions, Changes)
        
        # Critical columns: Close, RSI, etc. derived from price are usually populated together.
        # Fundamental data might be sparse.
        
        cols_to_check = [c for c in self.data.columns if c not in exclude_cols]
        
        # Reverted to Imputation Strategy (FFill + 0) to preserve data
        # especially for Macro/Interaction features which might have lag.
        self.data[cols_to_check] = self.data[cols_to_check].ffill().fillna(0)
        
        # Still drop rows where EVERYTHING is missing (e.g. at the very start)
        # But allow some NaNs to be filled 
        # self.data.dropna(subset=cols_to_check, inplace=True) # DISABLED
        
        return self.data
        
    def process_all(self, ticker=None):
        """Tüm işlemleri sırasıyla çalıştırır."""
        # 1. Targets First (Before any drop/shift operations might mess up)
        # However, targets need Close and XU100 which are present.
        self.add_multi_window_targets()
        
        self.add_technical_indicators()
        # Gelişmiş teknik indikatörler (Ichimoku, ADX, Williams %R, VWAP, vb.)
        if getattr(config, 'ENABLE_CUSTOM_INDICATORS', True):
            self.add_custom_indicators()
        
        # Macro Technicals
        if getattr(config, 'ENABLE_MACRO_IN_MODEL', False):
            self.add_bank_features()
            self.add_advanced_market_features()

        # Fundamental Data
        if ticker:
            self.add_fundamental_features_from_file(ticker)
            # YENİ: Sektör Dummies
            self.add_sector_dummies(ticker)
            # YENİ: KAP Bildirimleri Feature'ları
            if getattr(config, 'ENABLE_KAP_FEATURES', True):
                self.add_kap_features(ticker)
        
        self.add_time_features()
        self.add_derived_features()
        self.add_macro_derived_features()

        # BUG-7 Fix: Volume / Stochastic / ATR indikatörler (önceki dead code, şimdi düzgün metot)
        self.add_volume_and_extra_indicators()

        # Macro Interaction (Sektör + makro featurelar oluştuktan sonra)
        self.add_macro_interaction_features()

        # YENİ: TFT için özel feature'lar (Temizlikten önce ekle)
        self.add_transformer_features()
        
        # Robustness: Clean Inf
        self.data.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        self.clean_data()
        return self.data

    def add_transformer_features(self):
        """TFT için özel feature'lar"""
        df = self.data
        
        # 1. Zamansal feature'lar (TFT bunları sever - var olanların üzerine ek/kontrol)
        if 'DayOfWeek' not in df.columns: df['DayOfWeek'] = df.index.dayofweek
        if 'Month' not in df.columns: df['Month'] = df.index.month
        if 'Quarter' not in df.columns: df['Quarter'] = df.index.quarter
        
        # 2. Makro şok göstergeleri (Eğer makro veriler varsa)
        if 'usdtry' in df.columns: # Küçük harf standart
            df['usdtry_shock'] = (df['usdtry'].pct_change() > 0.02).astype(int)
        elif 'USDTRY' in df.columns: # Büyük harf standart
            df['usdtry_shock'] = (df['USDTRY'].pct_change() > 0.02).astype(int)
            
        if 'vix' in df.columns:
            df['vix_high'] = (df['vix'] > 25).astype(int)
        elif 'VIX' in df.columns:
            df['vix_high'] = (df['VIX'] > 25).astype(int)
            
        # 3. Trend strength
        if 'SMA_20' in df.columns:
            df['price_vs_sma20'] = df['Close'] / df['SMA_20'] - 1
            
        if 'Volume' in df.columns:
            vol_ma = df['Volume'].rolling(20).mean()
            # Avoid division by zero
            df['volume_surge'] = df['Volume'] / (vol_ma + 1e-9)
            
        self.data = df
        return df

def prepare_tft_dataset(df, lookback=60):
    """
    TFT modeli için dataset konfigürasyonunu hazırlar.
    df: (timestamp, features) DataFrame - MultiIndex veya Single Index olabilir.
    lookback: Kaç günlük geçmiş kullanılacak
    """
    
    # Statik feature'lar (hisse bazında sabit - eğer varsa)
    static_features = []
    if 'Sector' in df.columns: static_features.append('Sector')
    
    # Zamansal feature'lar (her gün değişen - bilinen)
    time_varying_known = ['DayOfWeek', 'Month']
    # Check flexible names
    for col in ['usdtry', 'USDTRY', 'vix', 'VIX', 'usdtry_shock', 'vix_high']:
        if col in df.columns:
            time_varying_known.append(col)
    
    # Zamansal feature'lar (her gün değişen - bilinmeyen/tahmin edilecek)
    # Fiyat ve teknik indikatörler
    potential_unknowns = ['Close', 'Volume', 'RSI', 'MACD', 'price_vs_sma20', 'volume_surge', 'Log_Return', 'Volatility_20']
    time_varying_unknown = [c for c in potential_unknowns if c in df.columns]
    
    # Target
    target = 'Excess_Return' 
    if target not in df.columns and 'NextDay_Return' in df.columns:
        target = 'NextDay_Return'
    
    return {
        'static': static_features,
        'known': time_varying_known,
        'unknown': time_varying_unknown,
        'target': target,
        'max_encoder_length': lookback,  # Geçmiş
        'max_prediction_length': 1       # 1 gün sonrasını tahmin
    }
