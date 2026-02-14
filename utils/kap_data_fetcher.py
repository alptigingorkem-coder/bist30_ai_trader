"""
KAP (Kamuyu Aydınlatma Platformu) Veri Çekme Modülü
PyKap kütüphanesini kullanarak KAP bildirimlerini çeker.

Özellikler:
- Rate limiting için cache mekanizması
- Disclosure type bazlı filtreleme
- Event-based feature üretimi
"""

import os
import json
import hashlib
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
import pandas as pd

from utils.logging_config import get_logger

log = get_logger(__name__)

try:
    from pykap.bist import BISTCompany
    PYKAP_AVAILABLE = True
except ImportError:
    PYKAP_AVAILABLE = False
    log.warning("[WARN] pykap kütüphanesi yüklü değil. KAP verileri çekilemeyecek.")

class KAPDataFetcher:
    """
    KAP verilerini çeken ve cache'leyen sınıf.
    """
    
    # Bildirim tipleri
    DISCLOSURE_TYPES = {
        'FR': 'Finansal Rapor',
        'ODA': 'Özel Durum Açıklaması',
        'GN': 'Genel Kurul',
        'DIV': 'Temettü',  # Custom mapping
        'CAP': 'Sermaye Artırımı'  # Custom mapping
    }
    
    def __init__(self, cache_dir: str = 'cache/kap'):
        """
        Args:
            cache_dir: Cache dosyalarının saklanacağı dizin
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache süresi (saat)
        self.cache_ttl_hours = 24
        
    def _get_cache_path(self, ticker: str, data_type: str, params: dict) -> str:
        """Cache dosya yolunu oluşturur."""
        param_hash = hashlib.md5(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()[:8]
        return os.path.join(self.cache_dir, f"{ticker}_{data_type}_{param_hash}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Cache'in geçerli olup olmadığını kontrol eder."""
        if not os.path.exists(cache_path):
            return False
            
        # Dosya yaşını kontrol et
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        age_hours = (datetime.now() - file_time).total_seconds() / 3600
        
        return age_hours < self.cache_ttl_hours
    
    def _load_cache(self, cache_path: str) -> Optional[List[Dict]]:
        """Cache'den veri yükler."""
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def _save_cache(self, cache_path: str, data: List[Dict]):
        """Veriyi cache'e kaydeder."""
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, default=str)
        except Exception as e:
            log.error(f"[WARN] Cache kaydetme hatası: {e}")
    
    def _to_date(self, d) -> date:
        """Farklı tarih formatlarını date objesine çevirir."""
        if isinstance(d, date):
            return d
        if isinstance(d, datetime):
            return d.date()
        if isinstance(d, str):
            return datetime.strptime(d, '%Y-%m-%d').date()
        raise ValueError(f"Geçersiz tarih formatı: {d}")
    
    def fetch_disclosures(
        self, 
        ticker: str, 
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        disclosure_type: str = 'ODA',
        use_cache: bool = True,
        force_live: bool = False
    ) -> pd.DataFrame:
        """
        Belirli bir hisse için KAP bildirimlerini çeker.
        
        Args:
            ticker: Hisse kodu (AKBNK, THYAO vb.)
            from_date: Başlangıç tarihi (YYYY-MM-DD)
            to_date: Bitiş tarihi (YYYY-MM-DD)
            disclosure_type: Bildirim tipi (FR, ODA, GN vb.)
            use_cache: Cache kullanılsın mı?
            
        Returns:
            pd.DataFrame: Bildirimler
        """
        if not PYKAP_AVAILABLE:
            return pd.DataFrame()
        
        # Tarih default değerleri
        if to_date is None:
            to_date = date.today()
        else:
            to_date = self._to_date(to_date)
            
        if from_date is None:
            from_date = to_date - timedelta(days=365)
        else:
            from_date = self._to_date(from_date)
        
        # Cache kontrolü
        params = {'from': str(from_date), 'to': str(to_date), 'type': disclosure_type}
        cache_path = self._get_cache_path(ticker, 'disclosures', params)
        
        # 2. Cache Kontrolü (Offline Mode Support)
        if use_cache and os.path.exists(cache_path):
            file_age = time.time() - os.path.getmtime(cache_path)
            
            # Eğer offline modda isek veya dosya yeterince yeniyse cache kullan
            # DİKKAT: Backtest için file_age kontrolünü devre dışı bırakıyoruz (Sürekli geçerli say)
            if file_age < self.cache_ttl_hours * 3600 or True: # Force Cache Usage for Backtest Stability
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if cached_data:
                        # print(f"[KAP] {ticker} bildirimleri cache'den yüklendi.")
                        return pd.DataFrame(cached_data)
                except Exception as e:
                    log.error(f"  [CACHE ERROR] {ticker} okuma hatası: {e}")
        
        # 3. Canlı Veri Çekme (PyKap) - Sadece explicit istek varsa
        # Backtest sırasında canlı veri çekip timeout riskine girmeyelim
        # force_live = False # Varsayılan olarak kapalı (Kaldırıldı)
        
        # 3. Canlı Veri Çekme (PyKap) - STRICT OFFLINE MODE
        # Backtest sırasında canlı veri çekip timeout riskine girmeyelim.
        # Sadece açıkça force_live=True denirse internete çık.
        
        if not force_live:
             # print(f"  [KAP INFO] {ticker} için cache bulunamadı, canlı veri çekilmiyor (Strict Offline).")
             return pd.DataFrame()

        # Buraya sadece force_live=True ise düşer
        import concurrent.futures

        def _fetch():
            company = BISTCompany(ticker=ticker.replace('.IS', ''))
            return company.get_historical_disclosure_list(
                fromdate=from_date,
                todate=to_date,
                disclosure_type=disclosure_type
            )
            
        try:
            log.info(f"[KAP] {ticker} bildirimleri CANLI çekiliyor ({from_date} -> {to_date})...")
            
            # DIRECT CALL (Thread Pool Removed for Debugging)
            company = BISTCompany(ticker=ticker.replace('.IS', ''))
            disclosures = company.get_historical_disclosure_list(
                fromdate=from_date,
                todate=to_date,
                disclosure_type=disclosure_type
            )
            
            if disclosures:
                self._save_cache(cache_path, disclosures)
                return pd.DataFrame(disclosures)
            
            return pd.DataFrame()
            
        except concurrent.futures.TimeoutError:
            log.warning(f"[KAP] {ticker} TIMEOUT - Veri çekme 30 saniyede tamamlanamadı.")
            return pd.DataFrame()
        except Exception as e:
            log.error(f"[KAP] {ticker} bildirim çekme hatası: {e}")
            return pd.DataFrame()
    
    def fetch_financial_reports(
        self,
        ticker: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Mali raporları çeker.
        """
        if not PYKAP_AVAILABLE:
            return pd.DataFrame()
        
        if to_date is None:
            to_date = date.today()
        else:
            to_date = self._to_date(to_date)
            
        if from_date is None:
            from_date = to_date - timedelta(days=365*3)  # Son 3 yıl
        else:
            from_date = self._to_date(from_date)
        
        params = {'from': str(from_date), 'to': str(to_date)}
        cache_path = self._get_cache_path(ticker, 'financials', params)
        
        if use_cache and self._is_cache_valid(cache_path):
            cached_data = self._load_cache(cache_path)
            if cached_data:
                log.info(f"[KAP] {ticker} mali raporları cache'den yüklendi.")
                return pd.DataFrame(cached_data)
        
        try:
            log.info(f"[KAP] {ticker} mali raporları çekiliyor...")
            company = BISTCompany(ticker=ticker.replace('.IS', ''))
            
            reports = company.get_financial_reports(
                fromdate=from_date,
                todate=to_date
            )
            
            if reports:
                self._save_cache(cache_path, reports)
                return pd.DataFrame(reports)
            
            return pd.DataFrame()
            
        except Exception as e:
            log.error(f"[KAP] {ticker} mali rapor çekme hatası: {e}")
            return pd.DataFrame()
    
    def create_event_features(
        self,
        ticker: str,
        price_df: pd.DataFrame,
        lookback_days: int = 30
    ) -> pd.DataFrame:
        """
        Fiyat verisine KAP event feature'ları ekler.
        
        Args:
            ticker: Hisse kodu
            price_df: Fiyat DataFrame'i (Date index'li)
            lookback_days: Geriye bakış penceresi
            
        Returns:
            pd.DataFrame: KAP feature'ları eklenmiş DataFrame
        """
        df = price_df.copy()
        
        # Default feature değerleri
        df['days_since_disclosure'] = 999  # Çok uzun süre önce
        df['disclosure_count_30d'] = 0
        df['has_recent_disclosure'] = 0
        
        if not PYKAP_AVAILABLE:
            return df
        
        # Tarih aralığını belirle
        if isinstance(df.index, pd.DatetimeIndex):
            min_date = df.index.min().date() - timedelta(days=lookback_days)
            max_date = df.index.max().date()
        else:
            return df
        
        # Bildirimleri çek
        disclosures_df = self.fetch_disclosures(
            ticker,
            from_date=str(min_date),
            to_date=str(max_date),
            disclosure_type='ODA',
            use_cache=True # force_live argümanı fetch_disclosures metoduna eklenmemiş, manuel eklemeliyiz veya fetch_disclosures imzasını güncellemeliyiz.
        )
        
        if disclosures_df.empty:
            return df
        
        # Bildirim tarihlerini parse et
        try:
            if 'publishDate' in disclosures_df.columns:
                disclosure_dates = pd.to_datetime(disclosures_df['publishDate']).dt.date.tolist()
            elif 'disclosureDate' in disclosures_df.columns:
                disclosure_dates = pd.to_datetime(disclosures_df['disclosureDate']).dt.date.tolist()
            else:
                return df
        except Exception:
            return df
        
        disclosure_dates = sorted(set(disclosure_dates))
        
        # Her gün için feature hesapla
        for idx in df.index:
            current_date = idx.date() if hasattr(idx, 'date') else idx
            
            # Son bildirimden bu yana gün
            past_disclosures = [d for d in disclosure_dates if d <= current_date]
            if past_disclosures:
                days_since = (current_date - max(past_disclosures)).days
                df.loc[idx, 'days_since_disclosure'] = min(days_since, 999)
            
            # Son 30 günde bildirim sayısı
            window_start = current_date - timedelta(days=lookback_days)
            count = sum(1 for d in disclosure_dates if window_start <= d <= current_date)
            df.loc[idx, 'disclosure_count_30d'] = count
            
            # Son 7 günde bildirim var mı?
            week_start = current_date - timedelta(days=7)
            has_recent = any(week_start <= d <= current_date for d in disclosure_dates)
            df.loc[idx, 'has_recent_disclosure'] = int(has_recent)
        
        return df

# Singleton instance
kap_fetcher = KAPDataFetcher()
