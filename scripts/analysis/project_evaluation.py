
import sys
import os
import pandas as pd
import numpy as np
import joblib
import torch
from datetime import datetime, timedelta


print("DEBUG: Script starting...", flush=True)

# Add project root to path
sys.path.append(os.getcwd())

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ensemble_model import HybridEnsemble
from utils.logging_config import get_logger

log = get_logger(__name__)

def evaluate_project_quality():
    print("="*60, flush=True)
    print("📊 PROJE KALİTE VE PERFORMANS TESTİ", flush=True)
    print("="*60, flush=True)
    
    # 1. Veri Hazırlığı (Son 6 Ay)
    end_date_str = datetime.now().strftime('%Y-%m-%d')
    start_date = datetime.now() - timedelta(days=180) # 6 Ay
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    print(f"📥 Veri Çekiliyor ({start_date_str} - {end_date_str})...")
    loader = DataLoader(start_date=start_date_str, end_date=end_date_str)
    
    # Tüm BIST30 Tickerları için
    # tickers = config.TICKERS
    # Hız için ilk 10 tanesiyle de test edilebilir ama kalite testi için hepsi daha iyi
    tickers = config.TICKERS[:5] 
    
    all_data_frames = []
    
    for ticker in tickers:
        print(f"DEBUG: Processing {ticker}...", flush=True)
        try:
            df = loader.get_combined_data(ticker)
            if df is None or len(df) < 60:
                print(f"DEBUG: {ticker} skipped (not enough data)", flush=True)
                continue
                
            fe = FeatureEngineer(df)
            df = fe.process_all(ticker)
            df = df.copy() # De-fragment
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
    # Use config paths
    lgbm_path = getattr(config, 'LGBM_MODEL_PATH', "models/saved/lgbm_model.pkl") 
    tft_path = getattr(config, 'TFT_MODEL_PATH', "models/saved/tft_model.pth")
    
    # Fallback to local if config not set
    if not os.path.exists(lgbm_path): lgbm_path = "models/saved/lgbm_model.pkl"
    if not os.path.exists(tft_path): tft_path = "models/saved/tft_model.pth"

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
            
            # Predict Components Separately
            
            # A. LightGBM Prediction
            # ------------------------------------------------------------------
            # LightGBM direkt feature dataframe (ticker_df) üzerinden çalışır
            # Ancak process_all ile üretilen sütunlara ihtiyaç duyar (zaten var)
            try:
                lgbm_score = ensemble.lgbm.predict(ticker_df)
                # Validasyon maskesi (son N gün)
                lgbm_valid = lgbm_score[-len(lgbm_score):] # Tümünü alıyoruz zaten loop tüm seriyi veriyor ama backtest=True
                # ensemble.predict içinde backtest mantığı nasıldı?
                # ensemble.predict -> self.lgbm.predict(df) -> tüm seriyi döner
            except Exception as e:
                print(f"LGBM Predict Error {ticker}: {e}")
                lgbm_score = np.zeros(len(ticker_df))
                
            # B. TFT Prediction
            # ------------------------------------------------------------------
            # TFT için ensemble içindeki _predict_tft benzeri mantık lazım
            # Ama ensemble objesine erişimimiz var, helper method kullanabiliriz veya direkt çağırabiliriz
            try:
                tft_score = ensemble._predict_tft(ticker_df)
                # TFT score uzunluğu ticker_df ile aynı olmayabilir (lookback nedeniyle)
                # Ensemble class'ı bunu handle ediyor ve aynı uzunluğa pad'liyor/kesiyor.
                # Emin olmak için uzunluk kontrolü:
                if len(tft_score) != len(ticker_df):
                     # Pad with NaN at start
                     diff = len(ticker_df) - len(tft_score)
                     if diff > 0:
                         tft_score = np.pad(tft_score, (diff, 0), constant_values=np.nan)
                     else:
                         tft_score = tft_score[-len(ticker_df):]
            except Exception as e:
                # print(f"TFT Predict Error {ticker}: {e}")
                tft_score = np.zeros(len(ticker_df))

            # C. Ensemble Prediction
            # ------------------------------------------------------------------
            ensure_valid = len(lgbm_score) == len(tft_score)
            if ensure_valid:
                ensemble_score = (ensemble.weights['lgbm'] * lgbm_score) + (ensemble.weights['tft'] * tft_score)
            else:
                ensemble_score = lgbm_score # Fallback
            
            
            # Results
            # Son N güne odaklanalım (örneğin tüm verinin hepsi)
            # Ama loop tüm veriyi işliyor.
            
            ticker_res = ticker_df.copy()
            ticker_res['Score_LGBM'] = lgbm_score
            ticker_res['Score_TFT'] = tft_score
            ticker_res['Score'] = ensemble_score
            
            # İlk 60 bar (Lookback) NaN olabilir TFT için, evaluation'a katmayalım
            ticker_res = ticker_res.iloc[60:]
            
            results.append(ticker_res)
            
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
    
    # -------------------------------------------------------------------------
    # ANALİZ FONKSİYONU
    # -------------------------------------------------------------------------
    from scipy.stats import spearmanr
    
    def analyze_metric(name, score_col):
        print(f"\n  🔍 ANALİZ: {name}")
        eval_df_sub = result_df.dropna(subset=[target_col, score_col])
        
        # A. Rank IC
        daily_ics = []
        for date, group in eval_df_sub.groupby('Date'):
            if len(group) >= 3:
                corr, _ = spearmanr(group[score_col], group[target_col])
                if not np.isnan(corr):
                    daily_ics.append(corr)
        
        avg_ic = np.mean(daily_ics) if daily_ics else 0.0
        print(f"  ✅ Rank IC: {avg_ic:.4f}")
        
        # B. Top-K Return (Daily)
        top_k_rets = []
        for date, group in eval_df_sub.groupby('Date'):
            if len(group) < 3: continue
            top = group.nlargest(3, score_col)
            top_k_rets.append(top[target_col].mean())
            
        avg_ret = np.mean(top_k_rets) if top_k_rets else 0.0
        print(f"  💰 Top-3 Günlük Getiri: {avg_ret:.4%}")
        
        # C. Error Metrics (RMSE, MAE)
        # Target (Return) scale is small (e.g. 0.02), so errors will be small.
        # Scale errors to basis points (bps) for readability? 1 bp = 0.0001
        mse = np.mean((eval_df_sub[score_col] - eval_df_sub[target_col])**2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(eval_df_sub[score_col] - eval_df_sub[target_col]))
        
        print(f"  📉 RMSE: {rmse:.4f} | MAE: {mae:.4f}")
        
        return avg_ic, avg_ret


    # -------------------------------------------------------------------------
    # SONUÇLAR
    # -------------------------------------------------------------------------
    print(f"\n📊 BİLEŞEN ANALİZİ (Değerlendirilen Gün Sayısı: {result_df['Date'].nunique()})")
    
    ic_lgbm, ret_lgbm = analyze_metric("Sadece LightGBM", 'Score_LGBM')
    ic_tft, ret_tft = analyze_metric("Sadece TFT", 'Score_TFT')
    ic_ens, ret_ens = analyze_metric("Ensemble (Mevcut)", 'Score')
    
    print("-" * 30)

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
