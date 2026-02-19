"""
Walk-Forward Backtest: Adil Model Performans Ölçümü
Her yıl için: Geçmiş veriyle eğit → O yıl test et → Sonuçları birleştir
Tüm metrikler 100% Out-of-Sample
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
import numpy as np
import joblib
import yfinance as yf
import lightgbm as lgb
import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer


def calculate_metrics(daily_returns, benchmark_returns=None, rf_annual=0.30):
    """Günlük getiri serisinden performans metrikleri hesaplar."""
    n_days = len(daily_returns)
    if n_days < 10:
        return None
    
    cumulative = (1 + daily_returns).cumprod()
    total_return = cumulative.iloc[-1] - 1
    years = n_days / 252.0
    
    cagr = (1 + total_return) ** (1 / years) - 1 if total_return > -1 and years > 0 else 0
    annual_vol = daily_returns.std() * np.sqrt(252)
    
    rf_daily = (1 + rf_annual) ** (1/252) - 1
    sharpe = (daily_returns.mean() - rf_daily) / daily_returns.std() * np.sqrt(252) if daily_returns.std() > 0 else 0
    
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_dd = drawdown.min()
    
    alpha, beta = 0.0, 0.0
    if benchmark_returns is not None and len(benchmark_returns) > 10:
        cov = np.cov(daily_returns.values, benchmark_returns.values)
        bm_var = cov[1][1]
        if bm_var > 0:
            beta = cov[0][1] / bm_var
        rm_annual = (1 + benchmark_returns.mean()) ** 252 - 1
        alpha = cagr - (rf_annual + beta * (rm_annual - rf_annual))
    
    return {
        'Toplam Getiri': total_return,
        'CAGR': cagr,
        'Sharpe Ratio': sharpe,
        'Max Drawdown': max_dd,
        'Alpha (Jensen)': alpha,
        'Beta': beta,
        'Volatilite': annual_vol,
        'İşlem Günü': n_days
    }


def load_all_data(start_date, end_date):
    """Tüm tickerlar için veri yükle ve feature engineer uygula."""
    loader = DataLoader(start_date=start_date, end_date=end_date)
    all_frames = []
    
    for ticker in config.TICKERS:
        try:
            raw = loader.get_combined_data(ticker)
            if raw is None or len(raw) < 200:
                continue
            
            fe = FeatureEngineer(raw)
            df = fe.process_all(ticker)
            df['Ticker'] = ticker
            all_frames.append(df)
        except Exception as e:
            print(f"  Hata ({ticker}): {e}")
    
    if not all_frames:
        return None
    
    full = pd.concat(all_frames)
    full.reset_index(inplace=True)
    full.set_index(['Date', 'Ticker'], inplace=True)
    full.sort_index(inplace=True)
    return full


def train_lgbm_ranker(train_data, feature_cols):
    """LightGBM Ranker modeli eğitir."""
    # Target: Excess_Return sıralaması
    target_col = 'Excess_Return'
    if target_col not in train_data.columns:
        target_col = 'NextDay_Return'
    if target_col not in train_data.columns:
        print("  ❌ Target sütunu bulunamadı!")
        return None, []
    
    # Feature filtreleme
    leakage = config.LEAKAGE_COLS + ['Ticker', 'Date', 'FUNDAMENTAL_DATA_AVAILABLE']
    feat_cols = [c for c in feature_cols if c not in leakage]
    feat_cols = [c for c in feat_cols if not c.startswith('Excess_Return') and not c.startswith('NextDay')]
    feat_cols = train_data[feat_cols].select_dtypes(include=[np.number]).columns.tolist()
    
    # Target: Sıralama (Rank)
    df = train_data.dropna(subset=feat_cols + [target_col]).copy()
    if len(df) < 100:
        return None, []
    
    X = df[feat_cols]
    y = df.groupby(level='Date')[target_col].rank(method='first', ascending=True)
    groups = df.groupby(level='Date').size().to_numpy()
    
    # Max label kontrolü
    max_label = int(y.max())
    
    params = {
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'ndcg_eval_at': [1, 3, 5],
        'boosting_type': 'gbdt',
        'learning_rate': 0.03,
        'num_leaves': 64,
        'n_estimators': 500,
        'reg_alpha': 0.1,
        'reg_lambda': 0.1,
        'min_child_samples': 20,
        'random_state': 42,
        'verbosity': -1
    }
    
    # Load optimized params if available
    opt_path = "models/saved/optimized_lgbm_params.joblib"
    if os.path.exists(opt_path):
        custom = joblib.load(opt_path)
        params.update(custom)
        params['verbosity'] = -1
    
    model = lgb.LGBMRanker(**params)
    
    if max_label > 30:
        model.set_params(label_gain=list(range(max_label + 1)))
    
    # Internal Train/Val split for early stopping
    unique_dates = df.index.get_level_values('Date').unique().sort_values()
    split_idx = int(len(unique_dates) * 0.85)
    val_dates = unique_dates[split_idx:]
    
    val_mask = df.index.get_level_values('Date').isin(val_dates)
    train_mask = ~val_mask
    
    X_train_split = X[train_mask]
    y_train_split = y[train_mask]
    q_train_split = df[train_mask].groupby(level='Date').size().to_numpy()
    
    X_val_split = X[val_mask]
    y_val_split = y[val_mask]
    q_val_split = df[val_mask].groupby(level='Date').size().to_numpy()
    
    model.fit(
        X_train_split, y_train_split,
        group=q_train_split,
        eval_set=[(X_val_split, y_val_split)],
        eval_group=[q_val_split],
        eval_metric='ndcg',
        callbacks=[
            lgb.early_stopping(stopping_rounds=50, first_metric_only=True),
            lgb.log_evaluation(0)  # Silent
        ],
    )
    
    return model, feat_cols


def simulate_portfolio(model, test_data, feature_cols, top_n=5):
    """OOS dönemde Top-N portföy simülasyonu yapar."""
    dates = test_data.index.get_level_values('Date').unique().sort_values()
    daily_returns = []
    
    for d in dates:
        try:
            daily_slice = test_data.loc[d].copy()
            if isinstance(daily_slice, pd.Series):
                daily_slice = daily_slice.to_frame().T
            
            if daily_slice.empty or len(daily_slice) < 3:
                daily_returns.append(0.0)
                continue
            
            # Feature alignment
            X = daily_slice.copy()
            for f in feature_cols:
                if f not in X.columns:
                    X[f] = 0
            X = X[feature_cols].fillna(0)
            
            scores = model.predict(X)
            daily_slice['Score'] = scores
            top_picks = daily_slice.nlargest(top_n, 'Score')
            
            # NextDay_Return varsa (yarınki gerçekleşen getiri)
            if 'NextDay_Return' in top_picks.columns:
                avg_ret = top_picks['NextDay_Return'].mean()
                if pd.isna(avg_ret):
                    avg_ret = 0.0
            else:
                avg_ret = 0.0
            
            daily_returns.append(avg_ret)
        except Exception:
            daily_returns.append(0.0)
    
    return pd.Series(daily_returns, index=dates)


def run_walk_forward_backtest():
    print("=" * 60)
    print("  WALK-FORWARD BACKTEST (100% Out-of-Sample)")
    print("=" * 60)
    
    # Hedef Metrikler
    targets = {
        'Toplam Getiri': 10.9169,
        'CAGR': 0.6326,
        'Sharpe Ratio': 2.06,
        'Max Drawdown': -0.3234,
        'Alpha (Jensen)': 0.1072,
        'Beta': 0.94
    }
    
    # Walk-Forward Pencereler
    # Eğitim: Genişleyen pencere (2015 → yıl sonu)
    # Test: Bir sonraki yıl
    windows = [
        {'train_end': '2020-12-31', 'test_start': '2021-01-01', 'test_end': '2021-12-31', 'label': '2021'},
        {'train_end': '2021-12-31', 'test_start': '2022-01-01', 'test_end': '2022-12-31', 'label': '2022'},
        {'train_end': '2022-12-31', 'test_start': '2023-01-01', 'test_end': '2023-12-31', 'label': '2023'},
        {'train_end': '2023-12-31', 'test_start': '2024-01-01', 'test_end': '2024-12-31', 'label': '2024'},
    ]
    
    # 1. Tüm Veri Yükle (bir kez)
    print("\n📥 Tüm veriler yükleniyor (2015-2025)...")
    full_data = load_all_data("2015-01-01", "2025-01-01")
    
    if full_data is None:
        print("❌ Veri yüklenemedi!")
        return
    
    print(f"  Toplam veri: {len(full_data)} satır")
    
    # 2. Walk-Forward Döngü
    all_oos_returns = []
    fold_results = []
    
    print("\n🔄 Walk-Forward Döngü Başlıyor...\n")
    
    for i, w in enumerate(windows):
        print(f"{'='*50}")
        print(f"  FOLD {i+1}: Test Yılı = {w['label']}")
        print(f"  Eğitim: 2015 → {w['train_end']}")
        print(f"  Test:   {w['test_start']} → {w['test_end']}")
        print(f"{'='*50}")
        
        # Train/Test Split
        train_mask = full_data.index.get_level_values('Date') <= w['train_end']
        test_mask = (full_data.index.get_level_values('Date') >= w['test_start']) & \
                    (full_data.index.get_level_values('Date') <= w['test_end'])
        
        train_data = full_data[train_mask]
        test_data = full_data[test_mask]
        
        print(f"  Eğitim: {len(train_data)} satır | Test: {len(test_data)} satır")
        
        if len(train_data) < 500 or len(test_data) < 50:
            print(f"  ⚠️ Yetersiz veri, atlanıyor.")
            continue
        
        # Eğit
        print(f"  🏋️ Model eğitiliyor...")
        model, feat_cols = train_lgbm_ranker(train_data, train_data.columns.tolist())
        
        if model is None:
            print(f"  ❌ Model eğitilemedi.")
            continue
        
        print(f"  ✅ Model eğitildi ({len(feat_cols)} özellik)")
        
        # Test (OOS Simülasyon)
        print(f"  📊 OOS Portföy Simülasyonu...")
        oos_returns = simulate_portfolio(model, test_data, feat_cols)
        
        # Fold Metrikleri
        fold_total = (1 + oos_returns).cumprod().iloc[-1] - 1
        fold_sharpe = oos_returns.mean() / oos_returns.std() * np.sqrt(252) if oos_returns.std() > 0 else 0
        
        print(f"  📈 {w['label']} OOS Getiri: {fold_total:.2%} | Sharpe: {fold_sharpe:.2f}")
        
        fold_results.append({
            'Yıl': w['label'],
            'Getiri': fold_total,
            'Sharpe': fold_sharpe,
            'Gün': len(oos_returns)
        })
        
        all_oos_returns.append(oos_returns)
    
    # 3. Tüm OOS Sonuçları Birleştir
    if not all_oos_returns:
        print("❌ Hiçbir fold çalışmadı!")
        return
    
    combined_returns = pd.concat(all_oos_returns).sort_index()
    
    # Benchmark
    print("\n📥 Benchmark (XU100) verisi indiriliyor...")
    try:
        xu100 = yf.download('XU100.IS', 
                           start=combined_returns.index.min(), 
                           end=combined_returns.index.max() + pd.Timedelta(days=1),
                           progress=False)
        if isinstance(xu100.columns, pd.MultiIndex):
            xu100.columns = xu100.columns.droplevel(1)
        bm_returns = xu100['Close'].pct_change().dropna()
        
        common = combined_returns.index.intersection(bm_returns.index)
        combined_aligned = combined_returns.reindex(common).fillna(0)
        bm_aligned = bm_returns.reindex(common).fillna(0)
    except Exception as e:
        print(f"  Benchmark hatası: {e}")
        combined_aligned = combined_returns
        bm_aligned = None
    
    # 4. Genel Metrikler
    metrics = calculate_metrics(combined_aligned, bm_aligned)
    
    if metrics is None:
        print("❌ Metrik hesaplanamadı!")
        return
    
    # 5. Sonuç Tablosu
    print("\n" + "=" * 70)
    print("  📊 YILLIK FOLD DETAYLARI (OOS)")
    print("=" * 70)
    print(f"  {'Yıl':<6} | {'Getiri':>10} | {'Sharpe':>8} | {'Gün':>5}")
    print(f"  {'-'*35}")
    for fr in fold_results:
        print(f"  {fr['Yıl']:<6} | {fr['Getiri']:>9.2%} | {fr['Sharpe']:>8.2f} | {fr['Gün']:>5}")
    
    print("\n" + "=" * 70)
    print("  📊 TOPLAM KARŞILAŞTIRMA (100% Out-of-Sample)")
    print("=" * 70)
    print(f"  {'Metrik':<20} | {'Hedef':>12} | {'Mevcut':>12} | {'Durum':>6}")
    print(f"  {'-'*58}")
    
    for key in targets:
        t = targets[key]
        c = metrics.get(key, 0)
        
        if key == 'Max Drawdown':
            status = "✅" if c >= t else "❌"
        elif key == 'Beta':
            status = "✅" if abs(c - t) < 0.3 else "⚠️"
        else:
            status = "✅" if c >= t * 0.7 else "❌"
        
        if key in ['Toplam Getiri', 'CAGR', 'Max Drawdown', 'Alpha (Jensen)']:
            print(f"  {key:<20} | {t:>11.2%} | {c:>11.2%} | {status:>6}")
        else:
            print(f"  {key:<20} | {t:>12.4f} | {c:>12.4f} | {status:>6}")
    
    print(f"  {'-'*58}")
    
    if bm_aligned is not None:
        bm_total = (1 + bm_aligned).cumprod().iloc[-1] - 1
        print(f"\n  XU100 Getirisi (aynı dönem): {bm_total:.2%}")
    
    print(f"  Toplam OOS İşlem Günü: {metrics['İşlem Günü']}")
    print(f"  Volatilite: {metrics['Volatilite']:.2%}")


if __name__ == "__main__":
    run_walk_forward_backtest()
