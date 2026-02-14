import yfinance as yf
import pandas as pd
import numpy as np
import config
from datetime import datetime, timedelta

from utils.logging_config import get_logger

log = get_logger(__name__)

class DataLoader:
    def __init__(self, start_date=config.START_DATE, end_date=config.END_DATE):
        self.start_date = start_date
        self.end_date = end_date
        self.tickers = config.TICKERS
        self.macro_tickers = config.MACRO_TICKERS
        self._macro_cache = None # Macro verileri bir kez çekmek için

    def fetch_live_data(self, ticker, interval='1m', period='1d'):
        """
        Paper Trading için canlı/anlık veri çeker.
        Varsayılan: Son 1 günlük 1 dakikalık veri.
        """
        try:
            # Yahoo Finance'ten canlı veri
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            
            if df.empty:
                log.info(f"UYARI: {ticker} için canlı veri alınamadı.")
                return None
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
                
            return df
        except Exception as e:
            log.error(f"HATA: {ticker} canlı veri hatası: {e}")
            return None

    def fetch_macro_data(self):
        """Makroekonomik verileri çeker ve birleştirir (Önbellekli)."""
        if self._macro_cache is not None:
            return self._macro_cache
            
        log.info("Makroekonomik veriler indiriliyor...")
        macro_df = pd.DataFrame()
        
        for name, ticker in self.macro_tickers.items():
            try:
                data = yf.download(ticker, start=self.start_date, end=self.end_date, progress=False)
                if not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.droplevel(1)
                    macro_df[name] = data['Close']
            except Exception as e:
                log.error(f"HATA: {name} ({ticker}) indirilirken sorun: {e}")
        
        macro_df = macro_df.ffill()
        
        us_tickers = ['VIX', 'SP500']
        for col in us_tickers:
            if col in macro_df.columns:
                macro_df[col] = macro_df[col].shift(1)
        
        self._macro_cache = macro_df
        return macro_df

    def get_combined_data(self, ticker):
        """Hisse verisi ile makro verileri birleştirir."""
        try:
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
        except Exception as e:
            log.error(f"get_combined_data error for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def _check_data_quality(self, data, ticker):
        """Verinin mantıklı olup olmadığını kontrol eder (Sanity Check)."""
        if data is None or data.empty: return False
        
        # 1. Yeterli veri var mı?
        if len(data) < 10:
            log.info(f"  [UYARI] {ticker}: Yetersiz veri ({len(data)} gün).")
            return False
            
        # 2. Son güncel tarih kontrolü (Canlı moddaysa)
        # last_date = data.index[-1]
        # if (datetime.now() - last_date).days > 7:
        #     print(f"  [UYARI] {ticker}: Veri çok eski ({last_date.date()}).")
        #     # return False # Backtest için kapalı
            
        # 3. Anormal Fiyat Hareketleri (Split harici devasa düşüşler)
        # pct_change < -0.60 (%60'tan büyük düşüş) -> Bölünme veya Hata olabilir
        daily_pct = data['Close'].pct_change()
        crashes = daily_pct[daily_pct < -0.60]
        
        if not crashes.empty:
            log.info(f"  [UYARI] {ticker}: Anormal fiyat düşüşü tespit edildi (Split Olabilir?):")
            for d, val in crashes.items():
                log.info(f"    - {d.date()}: {val:.2%}")
            # Otomatik düzeltme veya reddetme eklenebilir. Şimdilik uyarı.
            
        return True

    def _fetch_fallback(self, ticker):
        """YFinance başarısız olursa İş Yatırım'dan dener (Generic)."""
        log.info(f"  [Fallback] İş Yatırım deneniyor: {ticker}...")
        try:
            from isyatirimhisse import fetch_stock_data
            
            # Sembol Dönüşümü (Mapping)
            sym = ticker.replace('.IS', '')
            
            # Özel Mappingler (İş Yatırım tarafındaki farklı kodlar)
            mapping = {
                'KOZAL': 'TRALT' # Altın Fonu/Hissesi özel durumu
            }
            if sym in mapping:
                sym = mapping[sym]
            
            # Tarih formatı: DD-MM-YYYY
            end_d = datetime.now().strftime('%d-%m-%Y')
            start_d = pd.to_datetime(self.start_date).strftime('%d-%m-%Y')
            
            # isyatirim kütüphanesi genelde T+2 gecikmeli olabilir veya temettü/bölünme verisi farklı olabilir.
            # Ancak veri hiç yoksa, bu candır.
            df_is = fetch_stock_data(
                symbols=[sym], 
                start_date=start_d,
                end_date=end_d
            )
            
            if df_is is not None and not df_is.empty:
                # Sütunları tanı ve dönüştür
                # Kütüphane versiyonuna göre sütun adları değişebilir, kontrol edelim.
                # Genelde: HGDG_TARIH, HGDG_KAPANIS vs.
                
                # Tarih
                date_col = 'HGDG_TARIH' if 'HGDG_TARIH' in df_is.columns else 'Date'
                if date_col in df_is.columns:
                    df_is['Date'] = pd.to_datetime(df_is[date_col])
                    df_is.set_index('Date', inplace=True)
                
                # Mapping
                rename_map = {
                    'HGDG_EN_YUKSEK': 'High',
                    'HGDG_EN_DUSUK': 'Low',
                    'HGDG_KAPANIS': 'Close',
                    'HGDG_HACIM_LOT': 'Volume',
                    'HGDG_HACIM_TL': 'Volume_TL' # Alternatif
                }
                df_is.rename(columns=rename_map, inplace=True)
                
                # Open Fallback (İş Yatırım bazen vermiyor)
                if 'HGDG_ACILIS' in df_is.columns:
                    df_is['Open'] = df_is['HGDG_ACILIS']
                elif 'Close' in df_is.columns:
                    df_is['Open'] = df_is['Close'] # Mecburi
                
                # Eksik sütun kontrolü
                required = ['Open', 'High', 'Low', 'Close', 'Volume']
                for col in required:
                    if col not in df_is.columns:
                        if col == 'Volume': df_is[col] = 0
                        else: df_is[col] = df_is['Close']
                
                df_is = df_is[required]
                
                # Type conversion (bazen object gelir)
                df_is = df_is.apply(pd.to_numeric, errors='coerce')
                df_is.dropna(inplace=True)
                
                log.info(f"  [Başarılı] İş Yatırım'dan veri kurtarıldı: {sym} ({len(df_is)} bar)")
                return df_is
                
        except Exception as e_is:
            log.error(f"  [Fallback Hata] İş Yatırım da başarısız: {e_is}")
            
        return None

    def fetch_stock_data(self, ticker):
        """Tek bir hisse senedi için veri çeker (Robust)."""
        log.info(f"{ticker} verisi indiriliyor (Kaynak: Yahoo)...")
        data = None
        
        # 1. Deneme: Yahoo Finance
        try:
            data = yf.download(ticker, start=self.start_date, end=self.end_date, progress=False)
            
            # Yapısal Kontroller
            if not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.droplevel(1)
                
                # Sütun varlık kontrolü
                required = ['Open', 'High', 'Low', 'Close', 'Volume']
                if not all(col in data.columns for col in required):
                     log.warning(f"  [UYARI] Yahoo eksik sütun döndürdü.")
                     data = None # Bad data
                else:
                    data = data[required]
            
        except Exception as e:
            log.error(f"  [HATA] Yahoo Finance bağlantı sorunu: {e}")
            data = None
            
        # 2. Kalite Kontrolü ve Fallback Kararı
        is_valid = False
        if data is not None and not data.empty:
            is_valid = self._check_data_quality(data, ticker)
            
        if not is_valid:
            log.error(f"  [UYARI] Birincil kaynak başarısız veya kalitesiz. Fallback devreye giriyor...")
            data = self._fetch_fallback(ticker)
            
        return data
    
    def resample_to_weekly(self, data):
        """Günlük OHLCV verisini haftalık periyoda dönüştürür."""
        if config.TIMEFRAME != 'W':
            return data  # Günlük modda hiçbir şey yapma
        
        log.info("  Veri haftalık periyoda dönüştürülüyor...")
        
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
        
        log.info(f"  Günlük: {len(data)} satır -> Haftalık: {len(weekly_data)} satır")
        return weekly_data

if __name__ == "__main__":
    # Test
    from utils.logging_config import get_logger
    log = get_logger(__name__)
    
    loader = DataLoader()
    sample_data = loader.get_combined_data("THYAO.IS")
    if sample_data is not None:
        log.info("%s", sample_data.head())
        log.info("%s", sample_data.tail())
    else:
        log.info("Veri çekilemedi.")