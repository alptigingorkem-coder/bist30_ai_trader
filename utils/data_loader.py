import yfinance as yf
import pandas as pd
import numpy as np
import config
from datetime import datetime, timedelta

class DataLoader:
    def __init__(self, start_date=config.START_DATE, end_date=config.END_DATE):
        self.start_date = start_date
        self.end_date = end_date
        self.tickers = config.TICKERS
        self.macro_tickers = config.MACRO_TICKERS
        self._macro_cache = None # Macro verileri bir kez çekmek için

    def fetch_macro_data(self):
        """Makroekonomik verileri çeker ve birleştirir (Önbellekli)."""
        if self._macro_cache is not None:
            return self._macro_cache
            
        print("Makroekonomik veriler indiriliyor...")
        macro_df = pd.DataFrame()
        
        for name, ticker in self.macro_tickers.items():
            try:
                data = yf.download(ticker, start=self.start_date, end=self.end_date, progress=False)
                if not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.droplevel(1)
                    macro_df[name] = data['Close']
            except Exception as e:
                print(f"HATA: {name} ({ticker}) indirilirken sorun: {e}")
        
        macro_df = macro_df.ffill()
        
        us_tickers = ['VIX', 'SP500']
        for col in us_tickers:
            if col in macro_df.columns:
                macro_df[col] = macro_df[col].shift(1)
        
        self._macro_cache = macro_df
        return macro_df

    def get_combined_data(self, ticker):
        """Hisse verisi ile makro verileri birleştirir."""
        stock_data = self.fetch_stock_data(ticker)
        if stock_data is None:
            return None
            
        macro_data = self.fetch_macro_data()
        
        # Tarih indekslerini hizala
        combined_df = stock_data.join(macro_data, how='left')
        
        # Makro verilerdeki eksiklikleri (tatiller vs) doldur
        combined_df = combined_df.ffill()
        
        # Haftalık resample (eğer aktifse)
        combined_df = self.resample_to_weekly(combined_df)
        
        return combined_df

    def _fetch_fallback(self, ticker):
        """YFinance başarısız olursa İş Yatırım'dan dener."""
        if 'KOZAL' not in ticker: return None
        
        print(f"  [Fallback] İş Yatırım deneniyor: {ticker}...")
        try:
            from isyatirimhisse import fetch_stock_data
            # Sembol Dönüşümü (Mapping)
            # KOZAL.IS -> TRALT
            sym = ticker.replace('.IS', '')
            if sym == 'KOZAL': sym = 'TRALT'
            
            end_d = datetime.now().strftime('%d-%m-%Y')
            start_d = pd.to_datetime(self.start_date).strftime('%d-%m-%Y')

            df_is = fetch_stock_data(
                symbols=[sym], 
                start_date=start_d,
                end_date=end_d
            )
            
            if df_is is not None and not df_is.empty:
                df_is['Date'] = pd.to_datetime(df_is['HGDG_TARIH'])
                df_is.set_index('Date', inplace=True)
                
                rename_map = {
                    'HGDG_EN_YUKSEK': 'High',
                    'HGDG_EN_DUSUK': 'Low',
                    'HGDG_KAPANIS': 'Close',
                    'HGDG_HACIM_LOT': 'Volume'
                }
                
                df_is.rename(columns=rename_map, inplace=True)
                
                # Open sütunu kontrolü
                if 'HGDG_ACILIS' in df_is.columns:
                    df_is['Open'] = df_is['HGDG_ACILIS']
                else:
                    df_is['Open'] = df_is['Close'] # Fallback
                    
                # Eksik sütunları tamamla
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if col not in df_is.columns:
                        df_is[col] = df_is['Close'] if col != 'Volume' else 0
                        
                df_is = df_is[['Open', 'High', 'Low', 'Close', 'Volume']]
                print(f"  [Başarılı] İş Yatırım'dan veri alındı: {sym}")
                return df_is
                
        except Exception as e_is:
            print(f"  [Fallback Hata] İş Yatırım da başarısız: {e_is}")
            
        return None

    def fetch_stock_data(self, ticker):
        """Tek bir hisse senedi için veri çeker."""
        print(f"{ticker} verisi indiriliyor...")
        try:
            data = yf.download(ticker, start=self.start_date, end=self.end_date, progress=False)
            if data.empty:
                print(f"UYARI: {ticker} için veri bulunamadı (YFinance).")
                return self._fetch_fallback(ticker)
            
            # MultiIndex sütunları düzeltme (yfinance bazen Adj Close, Close seviyelerinde dönebilir)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
            
            # Sadece gerekli sütunları al
            data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
            return data
        except Exception as e:
            print(f"HATA: {ticker} (yfinance) indirilirken sorun oluştu: {e}")
            return self._fetch_fallback(ticker)
    
    def resample_to_weekly(self, data):
        """Günlük OHLCV verisini haftalık periyoda dönüştürür."""
        if config.TIMEFRAME != 'W':
            return data  # Günlük modda hiçbir şey yapma
        
        print("  Veri haftalık periyoda dönüştürülüyor...")
        
        # OHLCV aggregation kuralları
        agg_rules = {
            'Open': 'first',    # Haftanın ilk açılışı
            'High': 'max',      # Haftanın en yükseği
            'Low': 'min',       # Haftanın en düşüğü
            'Close': 'last',    # Haftanın son kapanışı
            'Volume': 'sum'     # Toplam hacim
        }
        
        # Makro sütunlar varsa onları da ekle (ortalama al)
        macro_cols = [c for c in data.columns if c not in agg_rules]
        for col in macro_cols:
            agg_rules[col] = 'mean'
        
        # Weekly resample (Pazartesi başlangıçlı)
        weekly_data = data.resample('W-MON').agg(agg_rules)
        
        # Boş satırları temizle
        weekly_data = weekly_data.dropna(how='all')
        
        print(f"  Günlük: {len(data)} satır -> Haftalık: {len(weekly_data)} satır")
        return weekly_data

    def fetch_macro_data(self):
        """Makroekonomik verileri çeker ve birleştirir."""
        print("Makroekonomik veriler indiriliyor...")
        macro_df = pd.DataFrame()
        
        for name, ticker in self.macro_tickers.items():
            try:
                data = yf.download(ticker, start=self.start_date, end=self.end_date, progress=False)
                if not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.droplevel(1)
                    # Sadece kapanış fiyatını al ve yeniden adlandır
                    macro_df[name] = data['Close']
            except Exception as e:
                print(f"HATA: {name} ({ticker}) indirilirken sorun: {e}")
        
        # Eksik verileri doldur (Forward Fill - Hafta sonları vs. için)
        macro_df = macro_df.ffill()
        
        # ZAMAN UYUMU SUZGEÇİ (Lagging)
        # US piyasaları (VIX, SP500) BIST kapandıktan sonra kapanır.
        # Bu yüzden bugünün BIST kapanışını tahmin ederken, "bugünün" US kapanışını bilemeyiz.
        # Dünün US kapanışını kullanmak zorundayız.
        us_tickers = ['VIX', 'SP500']
        for col in us_tickers:
            if col in macro_df.columns:
                # print(f"Bilgi: {col} verisi look-ahead bias önlemek için 1 gün kaydırılıyor.")
                macro_df[col] = macro_df[col].shift(1)
        
        return macro_df

    def get_combined_data(self, ticker):
        """Hisse verisi ile makro verileri birleştirir."""
        stock_data = self.fetch_stock_data(ticker)
        if stock_data is None:
            return None
            
        macro_data = self.fetch_macro_data()
        
        # Tarih indekslerini hizala
        combined_df = stock_data.join(macro_data, how='left')
        
        # Makro verilerdeki eksiklikleri (tatiller vs) doldur
        combined_df = combined_df.ffill()
        
        # Haftalık resample (eğer aktifse)
        combined_df = self.resample_to_weekly(combined_df)
        
        return combined_df

if __name__ == "__main__":
    # Test
    loader = DataLoader()
    sample_data = loader.get_combined_data("THYAO.IS")
    if sample_data is not None:
        print(sample_data.head())
        print(sample_data.tail())
    else:
        print("Veri çekilemedi.")