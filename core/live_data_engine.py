import yfinance as yf
import pandas as pd
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import config

try:
    import pandas_datareader.data as web
except Exception:
    web = None
    print("[LiveDataEngine] Warning: pandas_datareader not available. Stooq fallback disabled.")

class DataUnavailabilityError(Exception):
    """Canlı veri bulunamadığında tetiklenen kritik hata."""
    pass

class LiveDataEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LiveDataEngine, cls).__new__(cls)
            cls._instance.cache_dir = "data/live_cache"
            os.makedirs(cls._instance.cache_dir, exist_ok=True)
        return cls._instance

    def fetch_live_data(self, tickers):
        """
        Fallback zinciri ile canlı veri çeker.
        Priority:
        1. YFinance (Hızlı, Geniş)
        2. Stooq (Pandas Datareader - Yedek)
        3. Local Cache (Eğer çok eskimemişse - max 15 dk)
        
        RAISES: DataUnavailabilityError -> Eğer hiçbir kaynak çalışmazsa.
        """
        data = None
        source = "None"
        
        # 1. Try YFinance
        try:
            print(f"[LiveData] Attempting YFinance for {len(tickers)} tickers...")
            # Interval map
            interval_map = {'D': '1d', 'W': '1wk', 'M': '1mo'}
            yf_interval = interval_map.get(config.TIMEFRAME, '1d')
            
            # yfinance bazen boş döner ama hata atmaz, kontrol et
            data = yf.download(tickers, period="5d", interval=yf_interval, progress=False, group_by='ticker')
            
            if self._validate_data(data):
                source = "YFinance"
                self._save_to_cache(data, "latest_live")
                print(f"[LiveData] Success with YFinance.")
                return (self._process_yfinance_format(data, tickers), source)
            else:
                print(f"[LiveData] YFinance returned empty or invalid data.")
        except Exception as e:
            print(f"[LiveData] YFinance failed: {e}")

        # 2. Try Stooq (Yedek - Sadece kapanış verileri olabilir ama hiç yoktan iyidir)
        try:
            print(f"[LiveData] Attempting Stooq (pandas_datareader)...")
            # Stooq sembol formatı: AKBNK.IS -> AKBNK.TR (genelde) veya sadece kod
            # Stooq biraz yavaştır ve her hisse olmayabilir, bu yüzden sadece kritiklerde denenebilir.
            # Şimdilik örnek basit fallback:
            # data = web.DataReader(tickers, 'stooq') 
            # Stooq toplu çekim zor olabilir, loop gerekebilir. 
            pass 
        except Exception as e:
            print(f"[LiveData] Stooq failed: {e}")
            
        # 3. Try Local Cache (Snapshot)
        try:
            print(f"[LiveData] Checking Local Cache...")
            cached_path = os.path.join(self.cache_dir, "latest_live.parquet")
            if os.path.exists(cached_path):
                # Cache tazelik kontrolü (Örn: 15 dk)
                mod_time = datetime.fromtimestamp(os.path.getmtime(cached_path))
                age_minutes = (datetime.now() - mod_time).total_seconds() / 60
                
                if age_minutes < 15:
                    print(f"[LiveData] Cache is fresh ({age_minutes:.1f} min old). Using cache.")
                    data = pd.read_parquet(cached_path)
                    source = f"Cache ({age_minutes:.0f}m ago)"
                    # Cache'den okunan veri işlenmiş veri mi ham mı?
                    # _save_to_cache ham veriyi kaydediyor.
                    # O yüzden _process_yfinance_format'dan geçirmemiz lazım Cache'den okuyunca da.
                    # Ancak `latest_live.parquet` ham YF formatıysa işe yarar.
                    
                    # Cache okuma sonrası process
                    return (self._process_yfinance_format(data, tickers), source)
                else:
                    print(f"[LiveData] Cache is STALE ({age_minutes:.1f} min old). Ignoring.")
        except Exception as e:
            print(f"[LiveData] Cache read failed: {e}")

        # Final Decision
        # Eğer buraya geldiysek veri yok demektir.
        raise DataUnavailabilityError("CRITICAL: All data sources failed! Trading halted due to 'No Data No Trade' rule.")

    def _validate_data(self, data):
        """Verinin boş olup olmadığını kontrol eder."""
        if data is None or data.empty:
            return False
        # Multi-index kontrolü
        if isinstance(data.columns, pd.MultiIndex):
            # En az bir hissenin verisi var mı?
            # 'Close' sütununun dolu olma oranı
            # return data.iloc[-1].count() > 0 
            return True
        return len(data) > 0

    def _save_to_cache(self, data, name):
        """Ham veriyi cache'e atar (Parquet)."""
        path = os.path.join(self.cache_dir, f"{name}.parquet")
        # Parquet multi-index sevmez bazen, ama pyarrow halleder.
        try:
            data.to_parquet(path)
        except:
            pass

    def _process_yfinance_format(self, data, tickers):
        """YFinance multi-index yapısını düzleştirir veya olduğu gibi döner."""
        # Mevcut sistem yapısı nasıldı? 
        # utils/data_loader.py içindeki yapıya uygun dönmeli.
        # Muhtemelen dict of dataframes veya tek bir multi-index df istenir.
        # dynamic_backtest.py batch_download_data fonksiyonuna bakalım -> dict dönüyor.
        
        processed = {}
        if isinstance(data.columns, pd.MultiIndex):
            # yf.download(..., group_by='ticker') sonucu: (Ticker, OHLC)
            for ticker in tickers:
                try:
                    df_t = data[ticker].copy()
                    if df_t.empty: continue
                    df_t.dropna(how='all', inplace=True)
                    processed[ticker] = df_t
                except KeyError:
                    continue
        else:
            # Tek hisse durumu
             if len(tickers) == 1:
                 processed[tickers[0]] = data
                 
        return processed

# Global Instance
live_engine = LiveDataEngine()
