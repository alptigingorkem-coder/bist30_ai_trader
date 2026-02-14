"""
Temel Analiz Mixin'i
Feature Store'dan fundamental veriler, KAP bildirimleri.
"""
import pandas as pd
import numpy as np
import config
from datetime import datetime

from core.feature_store import feature_store

from utils.logging_config import get_logger

log = get_logger(__name__)

class FundamentalMixin:
    """Temel analiz feature metotlarını sağlayan mixin."""

    def add_fundamental_features_from_file(self, ticker):
        """
        Feature Store'dan temel analiz verilerini okur (Parquet).
        Dosya formatı: Ticker, Date, Forward_PE, EBITDA_Margin, PB_Ratio, Debt_to_Equity
        """
        df = self.data

        try:
            start_date = config.START_DATE
            end_date = datetime.now().strftime('%Y-%m-%d')

            stock_fund = feature_store.load_fundamentals(tickers=[ticker], start_date=start_date, end_date=end_date)

            if stock_fund.empty:
                pass
            else:
                stock_fund['Date'] = pd.to_datetime(stock_fund['Date'])
                stock_fund['Date'] = stock_fund['Date'] + pd.Timedelta(days=60)

                stock_fund['Date'] = stock_fund['Date'].dt.normalize()
                if stock_fund['Date'].dt.tz is not None:
                    stock_fund['Date'] = stock_fund['Date'].dt.tz_localize(None)

                stock_fund.set_index('Date', inplace=True)
                stock_fund.sort_index(inplace=True)

                cols_to_merge = ['Forward_PE', 'EBITDA_Margin', 'PB_Ratio']

                for col in cols_to_merge:
                    if col in stock_fund.columns:
                        aligned_series = self._align_quarterly_data(df.index, stock_fund[col])
                        df[col] = aligned_series

                        if col == 'Forward_PE':
                            df['Forward_PE_Change'] = df['Forward_PE'].pct_change()
                        if col == 'EBITDA_Margin':
                            df['EBITDA_Margin_Change'] = df['EBITDA_Margin'].diff()
                    else:
                        df[col] = np.nan

                log.info(f"  [Başarılı] Temel analiz verileri Feature Store'dan eklendi: {ticker}")
                self.data['FUNDAMENTAL_DATA_AVAILABLE'] = True

        except FileNotFoundError:
            log.warning(f"⚠️ {ticker}: Fundamental data YOK - Alpha model devre dışı")
            self.data['FUNDAMENTAL_DATA_AVAILABLE'] = False
            return df

        except Exception:
            pass

        self.data = df
        return df

    def _align_quarterly_data(self, daily_index, quarterly_series):
        """Quarterly (çeyreklik) veriyi günlük/haftalık index'e hizalar"""
        quarterly_series = quarterly_series.sort_index()

        target_index = pd.to_datetime(daily_index).normalize()
        if target_index.tz is not None:
            target_index = target_index.tz_localize(None)

        source_index = pd.to_datetime(quarterly_series.index).normalize()
        if source_index.tz is not None:
            source_index = source_index.tz_localize(None)

        quarterly_series.index = source_index

        aligned = quarterly_series.reindex(target_index, method='ffill')
        aligned.index = daily_index

        if aligned.notna().any():
            first_valid_value = aligned.dropna().iloc[0]
            aligned.fillna(first_valid_value, inplace=True)

        return aligned

    def add_kap_features(self, ticker):
        """
        KAP bildirimlerinden feature üretir.
        - days_since_disclosure: Son bildirimden bu yana gün
        - disclosure_count_30d: Son 30 günde bildirim sayısı
        - has_recent_disclosure: Son 7 günde bildirim var mı?
        """
        df = self.data

        df['days_since_disclosure'] = 999
        df['disclosure_count_30d'] = 0
        df['has_recent_disclosure'] = 0

        try:
            from utils.kap_data_fetcher import kap_fetcher

            df = kap_fetcher.create_event_features(ticker, df)
            log.info(f"  [KAP] {ticker} için KAP feature'ları eklendi.")

        except Exception as e:
            log.error(f"  [KAP] {ticker} için feature ekleme hatası: {e}")

        self.data = df
        return df
