import pandas as pd
import pandas_ta as ta
import numpy as np
import config
import yfinance as yf
from datetime import datetime, timedelta

class FeatureEngineer:
    def __init__(self, data):
        self.data = data.copy()

    def add_technical_indicators(self):
        """Teknik indikatörleri ekler (RSI, MACD, Bollinger, SMA, vb.)"""
        df = self.data
        
        # RSI
        df['RSI'] = ta.rsi(df['Close'], length=config.RSI_PERIOD)
        
        # MACD
        macd = ta.macd(df['Close'], fast=config.MACD_FAST, slow=config.MACD_SLOW, signal=config.MACD_SIGNAL)
        if macd is not None:
            # Pandas TA returns MACD, Histogram, Signal
            # Rename columns to standard names
            macd.columns = ['MACD', 'MACD_Hist', 'MACD_Signal']
            df = pd.concat([df, macd], axis=1)
        
        # Bollinger Bands
        bb = ta.bbands(df['Close'], length=config.BB_LENGTH, std=config.BB_STD)
        if bb is not None:
            df = pd.concat([df, bb], axis=1) # BBL, BBM, BBU
            # BB Width (Growth Stratejisi için)
            lower_col = f"BBL_{config.BB_LENGTH}_{config.BB_STD}.0"
            upper_col = f"BBU_{config.BB_LENGTH}_{config.BB_STD}.0"
            mid_col = f"BBM_{config.BB_LENGTH}_{config.BB_STD}.0"
            
            # Pandas TA bazen sütun isimlerini farklı döndürebilir
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

        # SMA & Above_SMA200
        sma_periods = [2, 4, 10, 40] if config.TIMEFRAME == 'W' else [5, 20, 50, 200]
        for p in sma_periods:
            col_name = f'SMA_{p}'
            df[col_name] = ta.sma(df['Close'], length=p)
            
        long_term_sma = f'SMA_{sma_periods[-1]}'
        if long_term_sma in df.columns:
            df['Close_to_SMA200'] = df['Close'] / df[long_term_sma]
            df['Above_SMA200'] = (df['Close'] > df[long_term_sma]).astype(int)

        self.data = df
        return df

    def add_macro_derived_features(self):
        """
        Create derived macro features for crisis detection BEFORE raw columns are deleted.
        """
        df = self.data
        
        lookback = 1 if config.TIMEFRAME == 'W' else 5
        
        # 1. USDTRY_Change
        if 'USDTRY' in df.columns:
            df['USDTRY_Change'] = df['USDTRY'].pct_change(lookback)
        
        # 2. VIX_Risk & VIX_Change
        if 'VIX' in df.columns:
            df['VIX_Risk'] = df['VIX'].copy()
            df['VIX_Change'] = df['VIX'].pct_change(lookback)
        
        # 3. SP500_Return & RS_vs_SP500
        if 'SP500' in df.columns:
            df['SP500_Return'] = df['SP500'].pct_change(lookback)
            df['RS_vs_SP500'] = df['Close'] / df['SP500']

        # 4. Gold & Oil & XBANK Momentum
        if 'GOLD' in df.columns and 'USDTRY' in df.columns:
            df['Gold_TRY'] = df['GOLD'] * df['USDTRY']
            df['Gold_TRY_Momentum'] = df['Gold_TRY'].pct_change(lookback)
            
        if 'OIL' in df.columns and 'USDTRY' in df.columns:
            df['Oil_TRY'] = df['OIL'] * df['USDTRY']
            df['Oil_TRY_Momentum'] = df['Oil_TRY'].pct_change(lookback)
            
        if 'XBANK' in df.columns:
            df['XBANK_Momentum'] = df['XBANK'].pct_change(lookback)

        # 5. Commodity Volatility
        if 'GOLD' in df.columns and 'OIL' in df.columns:
             gold_vol = df['GOLD'].pct_change().rolling(20).std()
             oil_vol = df['OIL'].pct_change().rolling(20).std()
             df['Commodity_Volatility'] = (gold_vol + oil_vol) / 2
        
        self.data = df
        return df

        # Stochastic Oscillator
        stoch = ta.stoch(df['High'], df['Low'], df['Close'])
        if stoch is not None:
            df = pd.concat([df, stoch], axis=1)
            
        # Volume Indicators
        if 'Volume' in df.columns:
            # On Balance Volume
            df['OBV'] = ta.obv(df['Close'], df['Volume'])
            # Money Flow Index
            df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'])

        # ATR (Average True Range) - Volatilite ve Risk Yönetimi İçin
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
        Harici bir veri kaynağından (Excel/CSV) temel analiz verilerini okur.
        Dosya formatı: Ticker, Date, Forward_PE, EBITDA_Margin, PB_Ratio, Debt_to_Equity
        """
        df = self.data
        file_path = "data/fundamental_data.xlsx" # Varsayılan yol
        
        try:
            # Dosya kontrolü 
            fundamentals = pd.read_excel(file_path)
            
            # İlgili hisseyi filtrele
            stock_fund = fundamentals[fundamentals['Ticker'] == ticker].copy()
            if stock_fund.empty:
                 # raise ValueError("Ticker not found in file")
                 pass
            else:
                # Tarih formatını ayarla ve index yap
                stock_fund['Date'] = pd.to_datetime(stock_fund['Date'])
                stock_fund.set_index('Date', inplace=True)
                stock_fund.sort_index(inplace=True)
                
                # Ana veri setine merge et (reindex ile)
                cols_to_merge = ['Forward_PE', 'EBITDA_Margin', 'PB_Ratio']
                
                for col in cols_to_merge:
                    if col in stock_fund.columns:
                        # Feature Engineer içindeki _align metodunu kullanabiliriz
                         df[col] = self._align_quarterly_data(df.index, stock_fund[col])
                         
                         # Türetilmiş özellikler (Değişim)
                         if col == 'Forward_PE':
                             df['Forward_PE_Change'] = df['Forward_PE'].pct_change()
                         if col == 'EBITDA_Margin':
                             df['EBITDA_Margin_Change'] = df['EBITDA_Margin'].diff()
                    else:
                        df[col] = np.nan
                        
                print(f"  [Başarılı] Temel analiz verileri dosyadan eklendi: {ticker}")
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
        
        # Her günlük/haftalık tarihe karşılık gelen quarterly değeri bul (forward fill)
        aligned = quarterly_series.reindex(daily_index, method='ffill')
        
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

    def add_time_features(self):
        """Zaman bazlı özellikleri ekler."""
        df = self.data
        df['DayOfWeek'] = df.index.dayofweek
        df['Month'] = df.index.month
        df['Quarter'] = df.index.quarter
        df['IsMonday'] = (df.index.dayofweek == 0).astype(int)
        df['IsFriday'] = (df.index.dayofweek == 4).astype(int)
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
        
        # Relative Volatility (Hisse volatilitesi / Uzun vadeli ortalaması)
        df['Volatility_Ratio'] = df['Volatility_20'] / df['Volatility_20'].rolling(52 if config.TIMEFRAME=='W' else 252).mean()

        # Excess Return (Alpha) = Hisse Getirisi - Endeks Getirisi
        if 'XU100' in df.columns:
            df['XU100_Return'] = np.log(df['XU100'] / df['XU100'].shift(1))
            df['Excess_Return_Current'] = df['Log_Return'] - df['XU100_Return']
        else:
            df['Excess_Return_Current'] = df['Log_Return']

        # Lag Features (Haftalık: 1, 2, 4, 12 hafta)
        lags = [1, 2, 4, 12] if config.TIMEFRAME == 'W' else [1, 5, 20, 60]
        for lag in lags:
            df[f'Close_Lag_{lag}'] = df['Close'].shift(lag)
            df[f'Return_Lag_{lag}'] = df['Close'].pct_change(lag) 
            df[f'Excess_Return_Lag_{lag}'] = df['Excess_Return_Current'].shift(lag)
            
        # Momentum Trend (Growth Stratejisi için Kompozit Skor)
        # RSI + Return_Lag_4w + Return_Lag_12w kombinasyonu
        col_list = df.columns
        if 'Return_Lag_4w' in col_list and 'Return_Lag_12w' in col_list:
            df['Momentum_Trend'] = (
                (df['Return_Lag_4w'] > 0).astype(int) + 
                (df['Return_Lag_12w'] > 0).astype(int) + 
                (df['RSI'] > 50).astype(int)
            )
            
        # Hedef Değişkenler
        df['NextDay_Close'] = df['Close'].shift(-1)
        df['NextDay_Direction'] = (df['NextDay_Close'] > df['Close']).astype(int)
        df['NextDay_Return'] = df['Close'].shift(-1) / df['Close'] - 1
        
        if 'XU100' in df.columns:
            df['NextDay_XU100_Return'] = df['XU100'].shift(-1) / df['XU100'] - 1
            df['Excess_Return'] = df['NextDay_Return'] - df['NextDay_XU100_Return']
        else:
            df['Excess_Return'] = df['NextDay_Return']
        
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
    
    def get_macro_status(self):
        """
        Makroekonomik verilerin durumunu analiz eder ve boolean flag'ler döndürür.
        Bu çıktı model tarafından DEĞİL, Daily Run execution gate tarafından kullanılır.
        """
        status = {
            "VIX_HIGH": False,
            "USDTRY_SHOCK": False,
            "GLOBAL_RISK_OFF": False
        }
        df = self.data
        
        # Son satırı (en güncel veriyi) al
        # Dikkat: Data henüz drop edilmediği için raw macro sütunları duruyor olmalı.
        if df.empty: return status
        
        last_row = df.iloc[-1]
        
        # Eşik Değerler
        thresholds = getattr(config, 'MACRO_GATE_THRESHOLDS', {
            'VIX_HIGH': 30.0,
            'USDTRY_CHANGE_5D': 0.03,
            'SP500_MOMENTUM': 0.0
        })
        
        # 1. VIX Kontrolü
        if 'VIX' in df.columns and not pd.isna(last_row['VIX']):
            status["VIX_HIGH"] = bool(last_row['VIX'] > thresholds['VIX_HIGH'])
            
        # 2. USDTRY Şok Kontrolü
        if 'USDTRY' in df.columns:
            # 5 günlük değişim hesapla (anlık)
            try:
                # Son 5 günü alıp yüzdesel değişime bak
                # Shift yerine iloc ile manuel bakalım, en son eksi 5 gün öncesi
                current_price = last_row['USDTRY']
                lookback = 1 if config.TIMEFRAME == 'W' else 5
                
                if len(df) >= lookback:
                    prev_price = df['USDTRY'].iloc[-lookback]
                    pct_change = (current_price - prev_price) / prev_price
                    status["USDTRY_SHOCK"] = bool(pct_change > thresholds['USDTRY_CHANGE_5D'])
            except:
                pass

        # 3. Global Risk Off (SP500 Momentum)
        if 'SP500' in df.columns:
            try:
                # 5 günlük (veya haftalık modda 1 bar) momentum
                lookback = 1 if config.TIMEFRAME == 'W' else 5
                if len(df) > lookback:
                    current = last_row['SP500']
                    prev = df['SP500'].iloc[-lookback]
                    mom = (current - prev) / prev
                    # Eğer momentum negatifse Risk Off
                    status["GLOBAL_RISK_OFF"] = bool(mom < thresholds['SP500_MOMENTUM'])
            except:
                pass
                
        return status

    def clean_data(self):
        """NaN değerleri temizler ve MAKRO SÜTUNLARI SİLER."""
        # Önce gereksiz makro sütunları tespit et ve düşür
        # Bunlar modelde 'leakage' veya 'noise' yaratmamalı
        macro_cols_to_drop = ['VIX', 'USDTRY', 'SP500', 'GOLD', 'OIL', 'Tahvil_Faizi']
        existing_cols_to_drop = [c for c in macro_cols_to_drop if c in self.data.columns]
        
        if existing_cols_to_drop:
            # print(f"  [Safety] Modelden gizlenen makro sütunlar siliniyor: {existing_cols_to_drop}")
            self.data.drop(columns=existing_cols_to_drop, inplace=True)

        exclude_cols = [
            'NextDay_Close', 'NextDay_Direction', 'NextDay_Return', 'Excess_Return', 
            'Forward_PE', 'EBITDA_Margin', 'Revenue_Growth_YoY', 'Debt_to_Equity', 'PB_Ratio',
            'EBITDA_Margin_Change', 'Forward_PE_Change'
        ]
        
        cols_to_check = [c for c in self.data.columns if c not in exclude_cols]
        self.data.dropna(subset=cols_to_check, inplace=True)
        return self.data
        
    def process_all(self, ticker=None):
        """Tüm işlemleri sırasıyla çalıştırır."""
        self.add_technical_indicators()
        
        # Macro Technicals only (XBANK, etc.)
        if getattr(config, 'ENABLE_MACRO_IN_MODEL', False):
            self.add_bank_features()
            self.add_advanced_market_features()
        else:
            print("  [Bilgi] Macro featurelar (Bank, Advanced Market) devre dışı bırakıldı.")

        # Fundamental Data (Dosyadan)
        if ticker:
            self.add_fundamental_features_from_file(ticker)
        
        self.add_time_features()
        self.add_derived_features()
        
        # FIX 1: Create derived macro features BEFORE clean_data() deletes raw columns
        self.add_macro_derived_features()
        
        self.clean_data()
        return self.data
