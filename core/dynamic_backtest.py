"""
Dinamik Backtest Modülü - Optimize Edilmiş Versiyon
Toplu veri indirme + Disk cache kullanarak hızlandırılmış.
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib

# Project imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from configs import banking as config_banking
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel
from core.backtesting import Backtester

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")


def ensure_cache_dir():
    """Cache klasörünü oluştur."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def get_cache_key(train_start: str, train_end: str, test_end: str) -> str:
    """Tarih parametrelerinden cache anahtarı oluştur."""
    key = f"{train_start}_{train_end}_{test_end}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def load_cached_data(cache_key: str) -> Optional[Dict[str, pd.DataFrame]]:
    """Cache'den veri yükle."""
    cache_file = os.path.join(CACHE_DIR, f"data_{cache_key}.pkl")
    if os.path.exists(cache_file):
        try:
            import pickle
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None
    return None


def save_to_cache(cache_key: str, data: Dict[str, pd.DataFrame]):
    """Veriyi cache'e kaydet."""
    ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, f"data_{cache_key}.pkl")
    try:
        import pickle
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        print(f"Cache kaydetme hatası: {e}")


def batch_download_data(tickers: list, start_date: str, end_date: str, 
                         progress_callback: Optional[callable] = None) -> Dict[str, pd.DataFrame]:
    """
    Tüm hisse ve makro verilerini tek seferde indir.
    yfinance batch download kullanarak çok daha hızlı.
    """
    import yfinance as yf
    
    all_data = {}
    
    # 1. TÜM HİSSELERİ TEK SEFERDE İNDİR
    if progress_callback:
        progress_callback("Tüm hisse verileri toplu indiriliyor...", 15)
    
    print(f"Toplu indirme başlıyor: {len(tickers)} hisse...")
    
    try:
        # Tüm hisseleri tek seferde indir
        stock_data = yf.download(
            tickers, 
            start=start_date, 
            end=end_date, 
            progress=False,
            group_by='ticker',
            threads=True
        )
        
        # Her hisse için veriyi ayır
        for ticker in tickers:
            try:
                if len(tickers) > 1:
                    df = stock_data[ticker].copy()
                else:
                    df = stock_data.copy()
                
                # MultiIndex düzelt
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                
                # NaN satırları temizle
                df = df.dropna(subset=['Close'])
                
                if len(df) > 100:
                    all_data[ticker] = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            except Exception as e:
                print(f"  {ticker} işlenirken hata: {e}")
                continue
        
        print(f"  ✅ {len(all_data)} hisse verisi başarıyla indirildi")
        
    except Exception as e:
        print(f"Toplu indirme hatası: {e}")
        return {}
    
    # 2. MAKRO VERİLERİ TEK SEFERDE İNDİR
    if progress_callback:
        progress_callback("Makro veriler toplu indiriliyor...", 25)
    
    macro_tickers = list(config.MACRO_TICKERS.values())
    macro_names = list(config.MACRO_TICKERS.keys())
    
    print(f"Makro veriler indiriliyor: {macro_names}...")
    
    try:
        macro_data = yf.download(
            macro_tickers,
            start=start_date,
            end=end_date,
            progress=False,
            group_by='ticker',
            threads=True
        )
        
        macro_df = pd.DataFrame()
        for name, ticker in config.MACRO_TICKERS.items():
            try:
                if len(macro_tickers) > 1:
                    close = macro_data[ticker]['Close']
                else:
                    close = macro_data['Close']
                
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
                    
                macro_df[name] = close
            except Exception as e:
                print(f"  {name} işlenirken hata: {e}")
                continue
        
        macro_df = macro_df.ffill()
        
        # US piyasaları 1 gün lag
        # US piyasaları 1 gün lag
        for col in ['VIX', 'SP500']:
            if col in macro_df.columns:
                macro_df[col] = macro_df[col].shift(1)
        
        # TZ-naive yap ve isimlendir
        if macro_df.index.tz is not None:
             macro_df.index = macro_df.index.tz_localize(None)
        macro_df.index.name = 'Date'

        print(f"  ✅ Makro veriler indirildi")
        
        # Makro veriyi her hisse verisine ekle
        for ticker in all_data:
            try:
                # TZ-naive yap ve isimlendir
                if all_data[ticker].index.tz is not None:
                     all_data[ticker].index = all_data[ticker].index.tz_localize(None)
                all_data[ticker].index.name = 'Date'
                
                # DEBUG LISTING
                print(f"DEBUG {ticker}: Index Name={all_data[ticker].index.name}, Type={type(all_data[ticker].index)}")
                print(f"DEBUG MACRO: Index Name={macro_df.index.name}, Type={type(macro_df.index)}")
                
                # index'ler uyumlu mu kontrol et
                # Join yerine merge deneyelim, bazen daha sağlamdır
                # FOOL PROOF MERGE: Reset index, merge on column, set index back
                
                stock_rest = all_data[ticker].reset_index()
                # Ensure date col name
                date_col = stock_rest.columns[0] # Usually 'Date' or 'index'
                stock_rest.rename(columns={date_col: 'Date'}, inplace=True)
                
                macro_rest = macro_df.reset_index()
                macro_date_col = macro_rest.columns[0]
                macro_rest.rename(columns={macro_date_col: 'Date'}, inplace=True)
                
                # FIX: Normalize dates to midnight to ensure matching despite different trading hours
                # Convert to UTC first to handle mixed inputs, then strip timezone and normalize
                stock_rest['Date'] = pd.to_datetime(stock_rest['Date'], utc=True).dt.tz_convert(None).dt.normalize()
                macro_rest['Date'] = pd.to_datetime(macro_rest['Date'], utc=True).dt.tz_convert(None).dt.normalize()
                
                # Merge
                merged = pd.merge(stock_rest, macro_rest, on='Date', how='left')
                merged.set_index('Date', inplace=True)
                
                all_data[ticker] = merged.ffill()
                
            except Exception as e:
                print(f"  ⚠️ {ticker} makro veri birleştirme hatası: {e}")
                import traceback
                traceback.print_exc()
                continue
            
    except Exception as e:
        print(f"Makro veri indirme hatası: {e}")
    
    return all_data


def validate_dates(train_start: str, train_end: str, test_end: str) -> Dict[str, Any]:
    """Tarih parametrelerini doğrular."""
    try:
        ts = datetime.strptime(train_start, "%Y-%m-%d")
        te = datetime.strptime(train_end, "%Y-%m-%d")
        test_e = datetime.strptime(test_end, "%Y-%m-%d")
    except ValueError as e:
        return {"valid": False, "error": f"Geçersiz tarih formatı: {e}"}
    
    train_days = (te - ts).days
    if train_days < 730:
        return {"valid": False, "error": f"Eğitim için en az 2 yıl veri gerekli. Şu an: {train_days} gün"}
    
    test_days = (test_e - te).days
    if test_days < 30:
        return {"valid": False, "error": f"Test için en az 30 gün veri gerekli. Şu an: {test_days} gün"}
    
    if not (ts < te < test_e):
        return {"valid": False, "error": "Tarihler kronolojik sırada olmalı"}
    
    min_date = datetime(2015, 1, 1)
    if ts < min_date:
        return {"valid": False, "error": "2015 öncesi veri mevcut değil"}
    
    return {"valid": True, "error": None}


def run_dynamic_backtest(
    train_start: str,
    train_end: str,
    test_end: str,
    initial_capital: float = 100000,
    progress_callback: Optional[callable] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Dinamik tarihlerle model eğitip backtest çalıştırır.
    Optimize edilmiş versiyon: Toplu indirme + cache.
    """
    
    def update_progress(step: str, pct: int):
        if progress_callback:
            progress_callback(step, pct)
        print(f"[{pct}%] {step}")
    
    # 1. Validasyon
    update_progress("Parametreler doğrulanıyor...", 5)
    validation = validate_dates(train_start, train_end, test_end)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    # 2. Cache kontrol
    cache_key = get_cache_key(train_start, train_end, test_end)
    cached_processed = None
    
    if use_cache:
        update_progress("Cache kontrol ediliyor...", 8)
        cached_processed = load_cached_data(cache_key)
        if cached_processed:
            print(f"  ✅ Cache bulundu! ({cache_key})")
    
    # 3. Veri İndirme veya Cache'den Yükleme
    tickers = config.TICKERS
    
    if cached_processed is None:
        # Toplu indirme
        raw_data = batch_download_data(tickers, train_start, test_end, progress_callback)
        
        if not raw_data:
            return {"success": False, "error": "Veri indirilemedi"}
        
        # Feature Engineering (paralel değil ama hızlı)
        update_progress("Feature engineering uygulanıyor...", 35)
        
        all_train_data = []
        all_test_data = []
        
        for i, (ticker, df) in enumerate(raw_data.items()):
            pct = 35 + int((i / len(raw_data)) * 10)
            if i % 5 == 0:
                update_progress(f"Feature: {ticker}", pct)
            
            try:
                fe = FeatureEngineer(df)
                features_df = fe.process_all(ticker=ticker)
                features_df['Ticker'] = ticker
                
                # Train/Test Split
                train_mask = features_df.index < train_end
                test_mask = (features_df.index >= train_end) & (features_df.index <= test_end)
                
                train_df = features_df[train_mask]
                test_df = features_df[test_mask]
                
                if len(train_df) > 50:
                    all_train_data.append(train_df)
                if len(test_df) > 10:
                    all_test_data.append(test_df)
            except Exception as e:
                print(f"  {ticker} feature engineering hatası: {e}")
                continue
        
        if not all_train_data:
            return {"success": False, "error": "Eğitim için yeterli veri bulunamadı"}
        if not all_test_data:
            return {"success": False, "error": "Test için yeterli veri bulunamadı"}
        
        # Cache'e kaydet
        cached_processed = {
            'train': all_train_data,
            'test': all_test_data
        }
        
        if use_cache:
            update_progress("Cache'e kaydediliyor...", 46)
            save_to_cache(cache_key, cached_processed)
    else:
        all_train_data = cached_processed['train']
        all_test_data = cached_processed['test']
        update_progress("Cache'den yüklendi!", 35)
    
    # 4. Model Eğitimi
    update_progress("Model eğitiliyor...", 50)
    
    full_train = pd.concat(all_train_data)
    full_train.reset_index(inplace=True)
    full_train.set_index(['Date', 'Ticker'], inplace=True)
    full_train.sort_index(inplace=True)
    
    # Validation split
    dates = full_train.index.get_level_values('Date').unique()
    split_idx = int(len(dates) * 0.9)
    val_start_date = dates[split_idx]
    
    train_mask = full_train.index.get_level_values('Date') < val_start_date
    valid_mask = full_train.index.get_level_values('Date') >= val_start_date
    
    df_train = full_train[train_mask]
    df_valid = full_train[valid_mask]
    
    update_progress("LightGBM eğitiliyor...", 55)
    ranker = RankingModel(df_train, config_banking)
    custom_params = getattr(config, 'OPTIMIZED_MODEL_PARAMS', None)
    ranker.train(valid_df=df_valid, custom_params=custom_params)
    
    # 5. Backtest
    update_progress("Backtest çalıştırılıyor...", 70)
    
    full_test = pd.concat(all_test_data)
    
    # Predict scores
    scores = ranker.predict(full_test)
    full_test['Score'] = scores
    
    # Pivot for ranking
    full_test_reset = full_test.reset_index()
    scores_pivot = full_test_reset.pivot(index='Date', columns='Ticker', values='Score')
    
    # Rank
    ranks_pivot = scores_pivot.rank(axis=1, ascending=False, method='first')
    
    # Portfolio allocation
    port_size = getattr(config, 'PORTFOLIO_SIZE', 5)
    weights_pivot = pd.DataFrame(0.0, index=ranks_pivot.index, columns=ranks_pivot.columns)
    
    top_n_mask = (ranks_pivot <= port_size)
    rank_sum = sum(range(1, port_size + 1))
    for r in range(1, port_size + 1):
        weight_val = (port_size - r + 1) / rank_sum
        weights_pivot[ranks_pivot == float(r)] = weight_val
    
    # Run individual backtests
    update_progress("Portföy performansı hesaplanıyor...", 80)
    
    all_metrics = []
    all_daily_returns = []
    test_data_dict = {df['Ticker'].iloc[0]: df for df in all_test_data}
    
    for ticker in weights_pivot.columns:
        if ticker not in test_data_dict:
            continue
        
        df = test_data_dict[ticker].copy()
        df.reset_index(inplace=True)
        df.set_index('Date', inplace=True)
        
        ticker_weights = weights_pivot[ticker].reindex(df.index).fillna(0)
        
        bt = Backtester(df, initial_capital=initial_capital)
        bt.run_backtest(ticker_weights)
        
        metrics = bt.calculate_metrics()
        metrics['Ticker'] = ticker
        all_metrics.append(metrics)
        
        d_rets = bt.results['Equity'].pct_change().fillna(0)
        d_rets.name = ticker
        all_daily_returns.append(d_rets)
    
    # 6. Aggregate Results
    update_progress("Sonuçlar hesaplanıyor...", 90)
    
    if not all_daily_returns:
        return {"success": False, "error": "Backtest sonucu üretilemedi"}
    
    concat_rets = pd.concat(all_daily_returns, axis=1).fillna(0)
    port_daily_ret = concat_rets.sum(axis=1)
    port_cum_ret = (1 + port_daily_ret).cumprod()
    total_ret = port_cum_ret.iloc[-1] - 1
    
    # Calculate metrics
    n_days = max(len(port_daily_ret), 1)
    cagr = (1 + total_ret) ** (252.0 / n_days) - 1 if total_ret > -1 else 0.0
    ann_vol = port_daily_ret.std() * np.sqrt(252)
    sharpe = cagr / ann_vol if ann_vol > 0 else 0
    
    # Sortino
    neg_rets = port_daily_ret[port_daily_ret < 0]
    downside_vol = neg_rets.std() * np.sqrt(252) if len(neg_rets) > 0 else ann_vol
    sortino = cagr / downside_vol if downside_vol > 0 else 0
    
    # Max Drawdown
    port_dd = (port_cum_ret - port_cum_ret.cummax()) / port_cum_ret.cummax()
    max_dd = port_dd.min()
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0
    
    # Trade stats
    total_trades = sum(m.get('Num Trades', 0) for m in all_metrics)
    win_rates = [m.get('Win Rate', 0) for m in all_metrics if m.get('Num Trades', 0) > 0]
    avg_win_rate = np.mean(win_rates) if win_rates else 0
    
    # Equity Curve (monthly)
    equity_curve = []
    port_cum_monthly = port_cum_ret.resample('ME').last()
    dd_monthly = port_dd.resample('ME').min()
    
    for date, eq_val in port_cum_monthly.items():
        equity_curve.append({
            "date": date.strftime("%Y-%m"),
            "equity": round(float(eq_val * initial_capital), 2),
            "drawdown": round(float(dd_monthly.get(date, 0)) * 100, 1)
        })
    
    # Monthly Returns
    monthly_returns = []
    port_monthly_ret = port_daily_ret.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    month_names_tr = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                      "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    
    for date, ret in port_monthly_ret.items():
        monthly_returns.append({
            "month": f"{month_names_tr[date.month - 1]} {date.year}",
            "value": round(float(ret * 100), 1)
        })
    
    update_progress("Tamamlandı!", 100)
    
    # Final result
    result = {
        "success": True,
        "metrics": {
            "totalReturn": round(total_ret * 100, 2),
            "cagr": round(cagr * 100, 2),
            "sharpeRatio": round(sharpe, 2),
            "sortinoRatio": round(sortino, 2),
            "maxDrawdown": round(max_dd * 100, 1),
            "calmarRatio": round(calmar, 2),
            "totalTrades": total_trades,
            "winRate": round(avg_win_rate, 1),
            "profitFactor": round(cagr / abs(max_dd) if max_dd != 0 else 0, 2),
            "avgHoldingDays": getattr(config, 'MIN_HOLDING_DAYS', 7)
        },
        "equityCurve": equity_curve,
        "monthlyReturns": monthly_returns[-12:],
        "config": {
            "trainStart": train_start,
            "trainEnd": train_end,
            "testEnd": test_end,
            "initialCapital": initial_capital,
            "portfolioSize": port_size,
            "tickerCount": len(all_test_data)
        }
    }
    
    return result


if __name__ == "__main__":
    result = run_dynamic_backtest(
        train_start="2015-01-01",
        train_end="2021-01-01",
        test_end="2024-12-31",
        initial_capital=100000,
        use_cache=True
    )
    
    if result["success"]:
        print("\n" + "="*50)
        print("BACKTEST SONUÇLARI")
        print("="*50)
        for key, value in result["metrics"].items():
            print(f"  {key}: {value}")
    else:
        print(f"HATA: {result['error']}")
