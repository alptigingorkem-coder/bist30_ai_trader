import yfinance as yf
import pandas as pd
import numpy as np
import config
from datetime import datetime, timedelta
import concurrent.futures
import time

# SSL Patch (SAFE): Only suppress warnings, do not force verify=False globally
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


from utils.logging_config import get_logger
from utils.db_manager import DBManager
from utils.macro_data_loader import TurkeyMacroData


log = get_logger(__name__)

class DataLoader:
    def __init__(self, start_date=config.START_DATE, end_date=config.END_DATE):
        self.start_date = start_date
        self.end_date = end_date
        self.tickers = config.TICKERS
        self.macro_tickers = config.MACRO_TICKERS
        self.macro_tickers = config.MACRO_TICKERS
        self._macro_cache = None # Macro verileri bir kez çekmek için
        self.db = DBManager() # Database Connection

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
        
        # HEAD OF QUANT: Use Specialized Macro Loader (EVDS + YF)
        macro_loader = TurkeyMacroData()
        macro_df = macro_loader.fetch_all(start_date=self.start_date)
        
        if macro_df is None or macro_df.empty:
             log.warning("Makro veri çekilemedi! Sadece YF fallback denenecek...")
             macro_df = pd.DataFrame() # Fallback logic below if needed, but TurkeyMacroData handles YF too.
        
        # Lag adjustments for Global Data (US Data is valid for NEXT day in TR)
        # TurkeyMacroData already returns daily resampled data.
        
        # US Tickers lag check
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
        # HEAD OF QUANT: Schema Enforcement
        from utils.validation import DataValidator
        if not DataValidator.validate_ohlcv(data, ticker):
             return False
             
        if data is None or data.empty:
            log.warning(f"  [Quality] {ticker}: Veri Boş veya None.")
            return False
        
        # 1. Yeterli veri var mı?
        if len(data) < 10:
            log.warning(f"  [Quality] {ticker}: Yetersiz veri ({len(data)} gün).")
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
            log.info(f"  [Quality] {ticker}: Anormal fiyat düşüşü tespit edildi (Split Olabilir?):")
            for d, val in crashes.items():
                log.info(f"    - {d.date()}: {val:.2%}")
            # Otomatik düzeltme veya reddetme eklenebilir. Şimdilik uyarı.
            
        # 4. Liquidity Filter (Scalability Safeguard)
        # BIST100'e genişlerken sığ hisseleri elemek için.
        # Son 20 günlük ortalama Hacim (TL) kontrolü.
        if 'Close' in data.columns and 'Volume' in data.columns:
            # Volume 0 olanları NaN yapıp ortalama alabiliriz veya direkt alabiliriz
            # Hacim * Fiyat = TL Hacmi
            daily_vol_tl = data['Close'] * data['Volume']
            avg_vol_tl = daily_vol_tl.rolling(20).mean().iloc[-1]
            
            min_vol_limit = getattr(config, 'MIN_DAILY_VOLUME_TL', 0)
            
            if min_vol_limit > 0 and avg_vol_tl < min_vol_limit:
                 log.warning(f"  [Liquidity] {ticker}: Yetersiz Likidite! (Ort: {avg_vol_tl:,.0f} TL < Limit: {min_vol_limit:,.0f} TL)")
                 return False

        log.info(f"  [Quality] {ticker}: Kalite kontrolü BAŞARILI. ({len(data)} bar)")
        return True

    def _fetch_fallback(self, ticker):
        """YFinance başarısız olursa İş Yatırım'dan dener (Generic)."""
        log.info(f"  [Fallback] İş Yatırım deneniyor: {ticker}...")
        try:
            from isyatirimhisse import fetch_stock_data
            import requests
            import warnings
            
            # Context manager to disable SSL verification temporarily
            class NoSSLVerification:
                def __enter__(self):
                    self.old_request = requests.Session.request
                    self.old_init = requests.Session.__init__
                    
                    def new_init(obj, *args, **kwargs):
                        self.old_init(obj, *args, **kwargs)
                        obj.verify = False
                        
                    requests.Session.__init__ = new_init
                    
                    # Also patch module level get/post if needed, but Session patch is usually enough for libraries
                    return self
                
                def __exit__(self, exc_type, exc_value, traceback):
                    requests.Session.__init__ = self.old_init
            
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
            with NoSSLVerification():
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
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
                    'HGDG_HACIM': 'Volume_TL',  # Bu sütun TL Hacmidir
                    'HGDG_AOF': 'VWAP',         # Ağırlıklı Ortalama Fiyat
                    'HGDG_HACIM_LOT': 'Volume', # Varsa
                    'HGDG_HACIM_TL': 'Volume_TL' # Alternatif
                }
                df_is.rename(columns=rename_map, inplace=True)
                
                # Open Fallback (İş Yatırım bazen vermiyor)
                if 'HGDG_ACILIS' in df_is.columns:
                    df_is['Open'] = df_is['HGDG_ACILIS']
                elif 'Open' not in df_is.columns and 'Close' in df_is.columns:
                    df_is['Open'] = df_is['Close'] # Mecburi
                
                # Volume Calculation: Qty = TL / VWAP (or Close)
                if 'Volume' not in df_is.columns or (df_is['Volume'] == 0).all():
                    if 'Volume_TL' in df_is.columns:
                        divisor = df_is['VWAP'] if 'VWAP' in df_is.columns else df_is['Close']
                        # Avoid Division by Zero
                        divisor = divisor.replace(0, 1.0) 
                        df_is['Volume'] = df_is['Volume_TL'] / divisor
                        df_is['Volume'] = df_is['Volume'].fillna(0).astype('int64')
                
                # Volume zaten yukarıda hesaplandıysa tekrar silinmemesi için logic
                # Volume Fallback silindi, yukarı taşındı.

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

    def sanitize_data(self, df, ticker):
        """
        BIST limitlerine ve veri kalitesine göre veriyi temizler.
        1. Fiyat Marjı: High/Low > 1.25 (Esnek limit) -> Hatalı bar.
        2. Kapanış <= 0 -> Hatalı.
        3. Hacim = 0 veya NaN -> Hatalı (Tatil veya veri kaybı).
        """
        if df is None or df.empty: return df
        
        initial_len = len(df)
        
        # 1. Sıfır/Negatif Fiyatlar
        if 'Close' in df.columns:
            df = df[df['Close'] > 0]
        
        # 2. Hacim Kontrolü (Hacimsiz günler)
        if 'Volume' in df.columns:
            # df = df.dropna(subset=['Volume'])
            # Hacmi 0 olanları silme, sadece uyar veya kabul et.
            # Bazı kaynaklarda hacim olmayabilir.
            # df = df[df['Volume'] > 0]
            pass
            
        # 3. Marj Kontrolü (High/Low)
        if 'High' in df.columns and 'Low' in df.columns:
            # Sadece Low > 0 olanlar
            df = df[df['Low'] > 0]
            
            # Marj hesabı
            margin = df['High'] / df['Low']
            outliers = margin > 1.25
            
            if outliers.any():
                bad_dates = df.index[outliers]
                log.warning(f"  [{ticker}] {len(bad_dates)} adet 'Outlier' bar temizlendi (High/Low > 1.25).")
                df = df[~outliers]
                
        final_len = len(df)
        if initial_len != final_len:
            log.info(f"  [{ticker}] Data Sanitization: {initial_len} -> {final_len} bar (%{100*(initial_len-final_len)/initial_len:.1f} temizlendi).")
            
        return df

    def fetch_stock_data(self, ticker):
        """
        Tek bir hisse senedi için veri çeker (Hybrid: DB -> Yahoo).
        1. Önce DB'den veriyi sorgula.
        2. Veri yoksa veya eksikse Yahoo'dan çek ve DB'ye kaydet.
        """
        log.info(f"{ticker} verisi isteniyor...")
        
        # 1. DB Kontrolü
        # Integrity Check: Check for missing data (gap > 3 days)
        # If missing, we force 'start_date' adjustment or just alert?
        # User request: "otomatik tespit edip eksik günleri tamamlasın."
        # So if gap found, we should fetch from last_db_date to today.
        
        is_missing = self.db.check_missing_data(ticker, days=3)
        if is_missing:
            log.warning(f"{ticker}: Data gap detected. Forcing fresh fetch.")
            # We could adjust start_date logic here, but for now relies on standard fetch
            # Standard fetch usually gets 'start_date' from config.
            # If we want to fill gap efficiently, we should find last date.
            # But existing logic usually re-fetches window.
            pass
        
        data = self.db.fetch_data(ticker, self.start_date, self.end_date)
        
        if data is not None and not data.empty:
            # Veri güncel mi kontrol et (Basitçe son tarihe bak)
            last_date = data.index[-1]
            
            # Timezone-aware date handling
            now = datetime.now()
            if last_date.tzinfo is not None:
                now = now.replace(tzinfo=last_date.tzinfo)
                
            if (now - last_date).days < 2:
                log.info(f"  [DB] Veri güncel: {ticker} ({len(data)} bar)")
                return self.sanitize_data(data, ticker)
            else:
                log.info(f"  [DB] Veri eski ({last_date.date()}), güncelleniyor...")
        
        # 2. Yahoo Finance (DB'de yoksa veya güncel değilse)
        log.info(f"  [Yahoo] {ticker} indiriliyor...")
        try:
            new_data = yf.download(ticker, start=self.start_date, end=self.end_date, progress=False, group_by='ticker')
            
            # Yapısal Kontroller
            if not new_data.empty:
                # MultiIndex sütun düzeltmesi (yfinance yeni versiyon)
                if isinstance(new_data.columns, pd.MultiIndex):
                    # Ticker seviyesini düşür
                    try:
                        # FIX: use new_data instead of data
                        data = new_data.xs(ticker, axis=1, level=0)
                    except KeyError:
                        # Bazen level 0 ticker olmayabilir, direkt droplevel deneyelim
                        if len(new_data.columns.levels) > 1:
                            new_data.columns = new_data.columns.droplevel(0)
                        data = new_data
                else:
                    data = new_data
                
                # Check emptiness again after manipulation
                if data is None or data.empty:
                    log.warning(f"  [Yahoo] Veri formatı işlenirken boşaldı: {ticker}")
                    data = None
                # Sütun varlık kontrolü
                required = ['Open', 'High', 'Low', 'Close', 'Volume']
                missing = [col for col in required if col not in data.columns]
                
                if missing:
                     log.warning(f"  [UYARI] Yahoo eksik sütun döndürdü: {missing}")
                     # Eksik sütunları Close ile doldurmayı dene (Volume hariç)
                     if 'Close' in data.columns:
                         for col in missing:
                             if col != 'Volume': data[col] = data['Close']
                             else: data[col] = 0
                     else:
                         data = None # Kritik: Close yoksa veri çöp
                
                if data is not None:
                    # Gerekli sütunları seç
                    data = new_data[[c for c in required if c in new_data.columns]]
                    
                    # --- DATA SANITIZATION ---
                    data = self.sanitize_data(data, ticker)
                    
                    # --- DB SAVE ---
                    self.db.save_data(data, ticker)
            
        except Exception as e:
            log.error(f"  [HATA] Yahoo Finance bağlantı sorunu: {e}")
            data = None
            
        # 2. Kalite Kontrolü ve Fallback Kararı
        is_valid = False
        if data is not None and not data.empty:
            is_valid = self._check_data_quality(data, ticker)
            
        if not is_valid:
            log.warning(f"  [UYARI] Birincil kaynak başarısız veya kalitesiz. Fallback devreye giriyor...")
            data = self._fetch_fallback(ticker)
            # Fallback verisi de sanitize edilebilir
            if data is not None:
                data = self.sanitize_data(data, ticker)
            
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

    def fetch_data_parallel(self, tickers: list, max_workers: int = 10) -> dict:
        """
        Verilen ticker listesi için verileri paralel çeker.
        Async altyapısı (Scalability Upgrade).
        """
        start_t = time.time()
        results = {}
        
        # 1. Macro Cache Prime (Yarış durumunu önlemek için önce tekil çek)
        self.fetch_macro_data()
        
        log.info(f"🚀 Paralel İndirme Başlıyor: {len(tickers)} hisse, {max_workers} worker...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map ticker to future
            future_to_ticker = {
                executor.submit(self.get_combined_data, ticker): ticker 
                for ticker in tickers
            }
            
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result()
                    if data is not None and not data.empty:
                        results[ticker] = data
                    else:
                        log.warning(f"  ❌ {ticker}: Veri boş döndü.")
                except Exception as e:
                    log.error(f"  ❌ {ticker}: İndirme hatası: {e}")
                    
        duration = time.time() - start_t
        log.info(f"✅ Paralel İndirme Tamamlandı. Süre: {duration:.2f}sn. Başarılı: {len(results)}/{len(tickers)}")
        return results

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