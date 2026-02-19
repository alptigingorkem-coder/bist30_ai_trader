
import numpy as np
import pandas as pd
import json
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
import config


def run_strategy_simulation(data: pd.DataFrame, description: str) -> float:
    """
    RSI-based Top-N strategy simülasyonu. Sharpe Ratio döner.
    data: MultiIndex (Date, Ticker) DataFrame, 'NextReturn' ve 'RSI' sütunları gerekli.
    """
    print(f"\n--- Running Simulation: {description} ---")
    
    daily_returns = []
    
    # Get unique dates preserving order
    unique_dates = data.index.get_level_values('Date').unique()
    
    for d in unique_dates:
        try:
            day_data = data.xs(d, level='Date')
        except KeyError:
            continue
            
        # Strategy: Top-N by RSI
        if 'RSI' in day_data.columns:
            scores = day_data['RSI']
        else:
            scores = np.random.rand(len(day_data))
            
        # Select Top N
        top_n = 5
        if len(day_data) >= top_n:
            try:
                selected_tickers = scores.nlargest(top_n).index
                selected_returns = day_data.loc[selected_tickers]['NextReturn']
                valid_returns = selected_returns.dropna()
                
                if len(valid_returns) > 0:
                    period_return = valid_returns.mean()
                    daily_returns.append(period_return)
                else:
                    daily_returns.append(0.0)
            except Exception:
                daily_returns.append(0.0)
        else:
            daily_returns.append(0.0)
            
    # Calculate Sharpe
    if len(daily_returns) > 1:
        daily_returns = np.array(daily_returns)
        mean_ret = np.mean(daily_returns)
        std_ret = np.std(daily_returns)
        
        if std_ret > 1e-6:
            sharpe = np.sqrt(252) * mean_ret / std_ret
        else:
            sharpe = 0.0
            
        print(f"   Mean Return: {mean_ret*100:.4f}%")
        print(f"   Std Dev:     {std_ret*100:.4f}%")
        print(f"   Sharpe:      {sharpe:.4f}")
        return sharpe
    else:
        return 0.0


def shuffle_test():
    """
    Veri Sızıntısı Testi — Target Permutation Yöntemi.
    
    Yöntem: Her tarih grubunda NextReturn (hedef değişken) TÜCKER'lar arasında 
    rastgele karıştırılır. Bu, feature→target ilişkisini bozan ama zaman yapısını
    koruyan doğru bir permutation test'tir.
    
    Beklenen sonuç:
    - Eğer model gerçek sinyal öğreniyorsa: shuffled_sharpe << normal_sharpe
    - Eğer veri sızıntısı varsa: shuffled_sharpe ≈ normal_sharpe
    
    N=20 permutation ile istatistiksel anlamlılık (p-value) hesaplanır.
    """
    
    print("="*70)
    print("SHUFFLE TEST — TARGET PERMUTATION (İyileştirilmiş)")
    print("="*70)
    print("Yöntem: Her gün için hisseler arası NextReturn karıştırılır")
    print("Bu, feature→target bağını kopar ama zamansal yapıyı korur")
    print("="*70)
    
    # Configure logging
    import logging
    logging.basicConfig(level=logging.ERROR)
    
    # 1. Veri Yükle
    print("\n📥 Veri yükleniyor...")
    loader = DataLoader()
    tickers = config.TICKERS
    
    start_date = "2023-01-01"
    end_date = "2024-12-31"
    
    if hasattr(config, 'BIST30_TICKERS'):
         tickers = config.BIST30_TICKERS
    
    data_map = {}
    print(f"   Fetching for {len(tickers)} tickers...")
    
    count = 0
    for t in tickers:
        try:
            df = loader.fetch_stock_data(t)
            if df is not None and not df.empty:
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]
                    
                data_map[t] = df
                count += 1
        except Exception as e:
            print(f"Error fetching {t}: {e}")
            
    if count == 0:
        print("❌ Veri bulunamadı!")
        return

    # 2. Feature Engineering & Returns Calculation
    print("🔧 Feature'lar ve Getiriler hesaplanıyor...")
    
    processed_dfs = []
    for ticker, df in data_map.items():
        try:
            fe = FeatureEngineer(df)
            processed = fe.process_all(ticker=ticker)
            
            # Target: Next Day Return
            processed['NextReturn'] = processed['Close'].pct_change().shift(-1)
            
            # RSI kontrolü
            if 'RSI' not in processed.columns:
                import pandas_ta as ta
                processed['RSI'] = ta.rsi(processed['Close'], length=14)
            
            processed['Ticker'] = ticker
            processed_dfs.append(processed)
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    if not processed_dfs:
        print("❌ İşlenmiş veri yok!")
        return
        
    full_data = pd.concat(processed_dfs)
    full_data = full_data.reset_index()
    if 'Date' not in full_data.columns:
        full_data.rename(columns={'index': 'Date'}, inplace=True)
        
    full_data['Date'] = pd.to_datetime(full_data['Date'])
    full_data = full_data.set_index(['Date', 'Ticker']).sort_index()
    
    # Clean
    full_data = full_data.dropna(subset=['NextReturn', 'RSI'])
    
    print(f"📊 Analiz edilecek satır sayısı: {len(full_data)}")
    
    if len(full_data) < 100:
        print("❌ Yetersiz veri!")
        return

    # 3. Normal Test
    print("\n" + "="*70)
    normal_sr = run_strategy_simulation(full_data, "NORMAL (Orijinal)")
    
    # 4. Target Permutation Test (N=20)
    print("\n" + "="*70)
    print("TARGET PERMUTATION TESTİ BAŞLIYOR (N=20 permutation)...")
    print("Her permutation'da, her gün için hisseler arası NextReturn karıştırılıyor...")
    
    n_permutations = 20
    shuffled_sharpes = []
    
    for perm_i in range(n_permutations):
        # Target Permutation: Her tarih grubunda NextReturn'ü hisseler arasında karıştır
        shuffled_data = full_data.copy()
        
        rng = np.random.default_rng(seed=42 + perm_i)
        
        unique_dates = shuffled_data.index.get_level_values('Date').unique()
        
        for d in unique_dates:
            try:
                mask = shuffled_data.index.get_level_values('Date') == d
                day_returns = shuffled_data.loc[mask, 'NextReturn'].values.copy()
                rng.shuffle(day_returns)
                shuffled_data.loc[mask, 'NextReturn'] = day_returns
            except Exception:
                continue
        
        perm_sr = run_strategy_simulation(shuffled_data, f"PERMUTATION {perm_i+1}/{n_permutations}")
        shuffled_sharpes.append(perm_sr)
    
    # 5. İstatistiksel Analiz
    shuffled_sharpes = np.array(shuffled_sharpes)
    mean_shuffled = np.mean(shuffled_sharpes)
    std_shuffled = np.std(shuffled_sharpes)
    
    # p-value: normal_sr'nin shuffled dağılımdan ne kadar uzak olduğu
    # One-sided: normal_sr > shuffled mean
    p_value = np.mean(shuffled_sharpes >= normal_sr)
    
    # Effect size
    if std_shuffled > 1e-6:
        z_score = (normal_sr - mean_shuffled) / std_shuffled
    else:
        z_score = float('inf') if normal_sr > mean_shuffled else 0.0
    
    # 6. Sonuç
    print("\n" + "="*70)
    print("TARGET PERMUTATION TEST SONUÇLARI")
    print("="*70)
    print(f"Normal Sharpe:           {normal_sr:.4f}")
    print(f"Shuffled Sharpe (Ort.):  {mean_shuffled:.4f}")
    print(f"Shuffled Sharpe (Std):   {std_shuffled:.4f}")
    print(f"Shuffled Sharpe (Min):   {np.min(shuffled_sharpes):.4f}")
    print(f"Shuffled Sharpe (Max):   {np.max(shuffled_sharpes):.4f}")
    print(f"Z-Score:                 {z_score:.2f}")
    print(f"P-Value:                 {p_value:.4f}")
    print(f"Sharpe Farkı:            {normal_sr - mean_shuffled:+.4f}")
    print("="*70)
    
    leakage = False
    if p_value > 0.10:
        print("🔴 SONUÇ: Model feature'lardan anlamlı sinyal öğrenemiyor!")
        print("   → p > 0.10: Orijinal performans, rastgele permutation'lardan istatistiksel olarak farklı değil")
        leakage = True
    elif p_value > 0.05:
        print("🟡 SONUÇ: Sınırda istatistiksel anlamlılık")
        print("   → 0.05 < p < 0.10: Dikkatli olun, daha fazla permutation ile kontrol edin")
    else:
        print("✅ SONUÇ: Model anlamlı sinyal öğreniyor")
        print(f"   → p = {p_value:.4f} < 0.05: Orijinal performans, random'dan istatistiksel olarak farklı")
        
    if z_score > 2.0:
        print(f"   → Z-Score = {z_score:.2f} > 2.0: Güçlü sinyal")
    elif z_score > 1.0:
        print(f"   → Z-Score = {z_score:.2f}: Orta güçte sinyal")
    else:
        print(f"   → Z-Score = {z_score:.2f}: Zayıf sinyal — veri sızıntısı veya overfitting olabilir")
        
    # Save
    res = {
        'normal_sharpe': float(normal_sr),
        'shuffled_sharpe_mean': float(mean_shuffled),
        'shuffled_sharpe_std': float(std_shuffled),
        'shuffled_sharpe': float(mean_shuffled),  # backward compat
        'shuffled_sharpes': [float(s) for s in shuffled_sharpes],
        'z_score': float(z_score),
        'p_value': float(p_value),
        'n_permutations': n_permutations,
        'leakage_detected': leakage,
        'method': 'target_permutation'
    }
    
    os.makedirs('results', exist_ok=True)
    with open('results/shuffle_test.json', 'w') as f:
        json.dump(res, f, indent=2)
    
    print(f"\n💾 Sonuçlar results/shuffle_test.json'a kaydedildi")


if __name__ == "__main__":
    shuffle_test()
