
import sys
import os
import pandas as pd
import numpy as np
import joblib
import torch
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ensemble_model import HybridEnsemble
from utils.logging_config import get_logger

log = get_logger(__name__)

def evaluate_project_quality():
    print("="*60)
    print("📊 PROJE KALİTE VE PERFORMANS TESTİ")
    print("="*60)
    
    # 1. Veri Hazırlığı (Son 6 Ay)
    end_date_str = datetime.now().strftime('%Y-%m-%d')
    start_date = datetime.now() - timedelta(days=180) # 6 Ay
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    print(f"📥 Veri Çekiliyor ({start_date_str} - {end_date_str})...")
    loader = DataLoader(start_date=start_date_str, end_date=end_date_str)
    
    # Tüm BIST30 Tickerları için
    tickers = config.TICKERS
    # Hız için ilk 10 tanesiyle de test edilebilir ama kalite testi için hepsi daha iyi
    # tickers = tickers[:5] 
    
    all_data_frames = []
    
    for ticker in tickers:
        try:
            df = loader.get_combined_data(ticker)
            if df is None or len(df) < 60:
                continue
                
            fe = FeatureEngineer(df)
            df = fe.process_all(ticker)
            df['Ticker'] = ticker
            
            # -----------------------------------------------------------------
            # TFT EKSİK FEATURE'LARI EKLEME (train_tft.py ile uyum)
            # -----------------------------------------------------------------
            # 1. Sector
            df['Sector'] = df['Ticker'].apply(config.get_sector)
            
            # 2. Zaman (train_tft.py: day_of_week, month - lowercase ve string category)
            if 'Date' in df.columns:    
                df['day_of_week'] = df['Date'].dt.dayofweek.astype(str).astype('category')
                df['month'] = df['Date'].dt.month.astype(str).astype('category')
            else:
                 # Date index ise
                 df['day_of_week'] = df.index.dayofweek.astype(str).astype('category')
                 df['month'] = df.index.month.astype(str).astype('category')
            # -----------------------------------------------------------------
            
            # Feature Engineering sonrası Date index olabilir, resetleyelim
            if 'Date' not in df.columns:
                df = df.reset_index()
            
            all_data_frames.append(df)
        except Exception as e:
            print(f"⚠️ {ticker} hatası: {e}")
            
    if not all_data_frames:
        print("❌ Veri bulunamadı!")
        return
        
    full_df = pd.concat(all_data_frames, ignore_index=True)
    full_df['Date'] = pd.to_datetime(full_df['Date'])
    
    # 2. TFT Gereksinimleri (time_idx)
    # Global time_idx (tüm tickerlar için ortak tarih bazlı)
    dates = full_df['Date'].sort_values().unique()
    date_map = {d: i for i, d in enumerate(dates)}
    full_df['time_idx'] = full_df['Date'].map(date_map)
    
    # Sütun isimleri temizliği (Train sırasında yapılan replace işlemini tekrar etmeliyiz)
    # DİKKAT: LGBM modeli '.' ile eğitilmiş olabilir. TFT '_' bekler.
    # HybridEnsemble.predict içinde TFT için özel dönüşüm yapıldı.
    # Burada global değişiklik yapmaktan vazgeçiyoruz.
    # full_df.columns = [c.replace('.', '_') for c in full_df.columns]
    
    # 3. Model Yükleme
    print("\n🧠 Modeller Yükleniyor...")
    lgbm_path = "models/saved/global_ranker.pkl"
    tft_path = "models/saved/tft_model.pth"
    
    ensemble = HybridEnsemble()
    # TFT Config için config modülünü geçiyoruz
    try:
        ensemble.load_models(lgbm_path, tft_path, tft_config=config)
    except Exception as e:
        print(f"❌ Model yükleme hatası: {e}")
        return

    # 4. Tahmin (Batch Prediction)
    print("\n🔮 Tahminler Üretiliyor (Batch)...")
    
    # Tahmin için son N gün (örneğin son 30 gün) üzerinde metrik hesaplayalım
    # Ancak TFT geçmişe ihtiyaç duyar.
    # O yüzden Full DF'i verip, sonuçların son kısmını analiz edeceğiz.
    
    try:
        # HybridEnsemble.predict tek bir DF alıp sonuç döner
        # Ancak bizim yapımızda predict metodunu çağırdığımızda
        # LGBM her satıra, TFT ise time_idx uygunluğuna göre tahmin üretir
        # Ve biz ensemble_model.py içinde "alignment" yaptık.
        # Bu durumda dönen sonuçlar pandas Series veya Array olacak.
        # Bunların hangi satırlara ait olduğunu bilmemiz lazım!
        
        # Alignment logic: Sondan N tanesini alıyor.
        # Yani dönen skorlar, full_df'in SON satırlarına ait.
        # Ancak full_df karışık tickerlar içeriyorsa alignment bozulur!
        # DİKKAT: HybridEnsemble.predict (mevcut haliyle) TEK BİR TIME SERIES (tek ticker) veya
        # time-aligned multi-series bekler mi?
        # LGBM için fark etmez.
        # TFT için: PyTorch Forecasting predict, grup ID'lerini kullanarak tahmin üretir.
        # Ancak dönen sonucun sırası dataset oluşturma sırasına bağlıdır.
        # Eğer "predict" metoduna raw dataframe verirsek, pytorch-forecasting dökümantasyonuna göre
        # sonuçlar DataFrame sırasıyla uyumlu olmayabilir (eğer grup varsa).
        
        # GÜVENLİ YOL: Her Ticker için ayrı predict çağırıp birleştirmek.
        
        results = []
        
        for ticker in full_df['Ticker'].unique():
            ticker_df = full_df[full_df['Ticker'] == ticker].copy()
            ticker_df = ticker_df.sort_values('Date') # Tarihe göre sıralı olmalı TFT için
            
            if len(ticker_df) < 60: continue
            
            # Predict
            # ensemble.predict -> (N_samples,) scores (aligned to END of input)
            # Backtest modu ile tüm geçmiş için tahmin istiyoruz
            scores = ensemble.predict(ticker_df, backtest=True)
            
            # Scores son N güne ait.
            # Kaç tane? len(scores)
            
            valid_rows = ticker_df.iloc[-len(scores):].copy()
            valid_rows['Score'] = scores
            
            results.append(valid_rows)
            
        result_df = pd.concat(results)
        
    except Exception as e:
        print(f"❌ Tahmin hatası: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. Metrik Hesaplama
    print("\n📈 Performans Analizi...")
    
    # Hedef: NextDay_Return veya Log_Return
    target_col = 'NextDay_Return'
    if target_col not in result_df.columns:
        # Calculate if missing
        result_df[target_col] = result_df.groupby('Ticker')['Close'].pct_change().shift(-1)
        
    # Drop NaN targets (last day prediction cannot be evaluated)
    eval_df = result_df.dropna(subset=[target_col, 'Score'])
    
    print(f"  Değerlendirilen Örnek Sayısı: {len(eval_df)}")
    
    # A. Directional Accuracy (Yön Doğruluğu)
    # Score > 0.5 (veya mean) -> Up?
    # Ensemble skoru 0-1 arasında (Rank Averaging yaptıysak)
    # Rank 0.5 üstü -> Yukarı beklemiyoruz, sadece göreceli sıralama.
    # Ancak Yön doğruluğu için: Yüksek skor alanların getirisi pozitif mi?
    
    # Correlation (Rank IC)
    from scipy.stats import spearmanr
    
    daily_ics = []
    for date, group in eval_df.groupby('Date'):
        if len(group) > 5:
            corr, _ = spearmanr(group['Score'], group[target_col])
            if not np.isnan(corr):
                daily_ics.append(corr)
                
    avg_ic = np.mean(daily_ics)
    print(f"  ✅ Ortalama Rank IC (Information Coefficient): {avg_ic:.4f}")
    if avg_ic > 0.05:
        print("     -> İYİ: Model sıralaması getiri ile pozitif korelasyonlu.")
    elif avg_ic > 0:
        print("     -> ORTA: Hafif pozitif korelasyon.")
    else:
        print("     -> KÖTÜ: Model rastgele veya ters çalışıyor.")

    # B. Top-K Getiri Analizi
    # Her gün en yüksek skorlu 3 hisseyi alıp ertesi gün getirisini ölçelim
    top_k_returns = []
    benchmark_returns = []
    
    for date, group in eval_df.groupby('Date'):
        if len(group) < 3: continue
        
        # Model seçimi
        top_picks = group.nlargest(3, 'Score')
        daily_ret = top_picks[target_col].mean()
        top_k_returns.append(daily_ret)
        
        # Benchmark (Average of all available that day)
        bm_ret = group[target_col].mean()
        benchmark_returns.append(bm_ret)
        
    # --- DETAYLI METRİKLER ---
    strategy_returns_series = pd.Series(top_k_returns)
    benchmark_returns_series = pd.Series(benchmark_returns)
    
    # 1. Cumulative Return
    cum_strategy = (1 + strategy_returns_series).cumprod().iloc[-1] - 1
    cum_benchmark = (1 + benchmark_returns_series).cumprod().iloc[-1] - 1
    
    # 2. Annualized Metrics (Assuming 252 trading days)
    avg_daily_ret = strategy_returns_series.mean()
    std_daily_ret = strategy_returns_series.std()
    
    annualized_return = avg_daily_ret * 252
    annualized_vol = std_daily_ret * np.sqrt(252)
    
    # 3. Sharpe Ratio (Risk Free Rate ~ 40% currently in TR => daily ~ 0.13%)
    rf_daily = 0.40 / 252 
    sharpe_ratio = (avg_daily_ret - rf_daily) / std_daily_ret if std_daily_ret > 0 else 0
    
    # 4. Win Rate
    win_rate = (strategy_returns_series > 0).mean()
    
    # 5. Max Drawdown
    cum_returns = (1 + strategy_returns_series).cumprod()
    running_max = cum_returns.cummax()
    drawdown = (cum_returns - running_max) / running_max
    max_drawdown = drawdown.min()

    avg_strategy_ret = np.mean(top_k_returns)
    avg_benchmark_ret = np.mean(benchmark_returns)
    
    print(f"\n  💰 Strateji Simülasyonu (Günlük Top 3 Hisse):")
    print(f"  Toplam Getiri (Kümülatif): {cum_strategy:.4%}")
    print(f"  Yıllıklandırılmış Getiri: {annualized_return:.4%}")
    print(f"  Ortalama Günlük Getiri (Model): {avg_strategy_ret:.4%}")
    print(f"  Ortalama Günlük Getiri (Piyasa Ort.): {avg_benchmark_ret:.4%}")
    
    diff = avg_strategy_ret - avg_benchmark_ret
    print(f"  Fark (Günlük Alpha): {diff:.4%}")
    
    print(f"\n  📊 Risk Metrikleri:")
    print(f"  Sharpe Ratio: {sharpe_ratio:.4f}")
    print(f"  Maksimum Düşüş (MaxDD): {max_drawdown:.4%}")
    print(f"  Kazanma Oranı (Win Rate): {win_rate:.4%}")
    
    if diff > 0.001: # Günlük %0.1 fark
        print("     -> BAŞARILI: Model piyasa ortalamasını yeniyor.")
    else:
        print("     -> NÖTR/BAŞARISIZ: Model belirgin bir avantaj sağlamadı.")
        
    print("\n" + "="*60)

if __name__ == "__main__":
    evaluate_project_quality()
