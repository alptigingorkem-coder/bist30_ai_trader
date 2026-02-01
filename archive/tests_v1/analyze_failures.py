
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.regime_detection import RegimeDetector
import joblib
from models.beta_model import BetaModel
from models.alpha_model import AlphaModel

def analyze_ticker_failure(ticker, sector_name):
    print(f"\n{'='*60}")
    print(f"🔍 DERİN ANALİZ: {ticker} ({sector_name})")
    print(f"{'='*60}")
    
    # 1. Veri ve Hazırlık (OOS Dönemi)
    loader = DataLoader(start_date="2022-01-01") # Biraz öncesini al ki indikatörler otursun
    raw_data = loader.get_combined_data(ticker)
    
    if raw_data is None:
        print("❌ Veri yok.")
        return

    fe = FeatureEngineer(raw_data)
    df = fe.process_all(ticker=ticker)
    
    rd = RegimeDetector(df)
    df = rd.detect_regimes(verbose=False)
    
    # OOS Filtresi
    if hasattr(config, 'TEST_START_DATE'):
        df = df[df.index >= config.TEST_START_DATE]
        print(f"📅 Analiz Dönemi: {df.index.min().date()} - {df.index.max().date()} ({len(df)} hafta)")
    
    # 2. Model Sinyalleri
    beta_path = f"models/saved/{sector_name.lower()}_beta.pkl"
    alpha_path = f"models/saved/{sector_name.lower()}_alpha.pkl"
    
    if not os.path.exists(beta_path):
        print("❌ Model dosyaları bulunamadı.")
        return

    beta_model_obj = joblib.load(beta_path)
    alpha_model_obj = joblib.load(alpha_path)
    
    # Predictions
    # Beta Wrapper
    beta_wrapper = BetaModel(df, config)
    beta_wrapper.model = beta_model_obj
    beta_preds = beta_wrapper.predict(df)
    
    # Alpha Wrapper
    alpha_wrapper = AlphaModel(df, config)
    alpha_wrapper.model = alpha_model_obj
    alpha_preds = alpha_wrapper.predict(df)
    
    # 3. İnceleme Metrikleri
    
    # A. Rejim Analizi
    print("\n--- A. Rejim Analizi ---")
    regime_counts = df['Regime'].value_counts()
    print(regime_counts)
    
    # B. Model Uyumsuzluğu
    # Fiyat yönü (Next week return) ile model tahmini tutarlı mı?
    # Gerçek getiri (gelecek hafta)
    df['Actual_Return'] = df['Close'].shift(-1) / df['Close'] - 1
    
    print("\n--- B. Sinyal Kalitesi (Correlation) ---")
    # Beta
    corr_beta = df['Actual_Return'].corr(beta_preds)
    print(f"Beta Model Korelasyonu: {corr_beta:.4f} {'(KÖTÜ)' if corr_beta < 0.05 else '(İYİ)'}")
    
    # Alpha
    corr_alpha = df['Actual_Return'].corr(alpha_preds)
    print(f"Alpha Model Korelasyonu: {corr_alpha:.4f} {'(KÖTÜ)' if corr_alpha < 0.05 else '(İYİ)'}")

    # C. Hatalı Sinyaller (Büyük Kayıplar)
    print("\n--- C. En Büyük 5 Hatalı Sinyal ---")
    # Weighted Signal
    df['Signal'] = np.where(df['Regime_Num'] == 2, beta_preds, alpha_preds) # Basit mantık
    
    # Hata = Sinyal pozitifken büyük düşüşler
    df['Error_Magnitude'] = (df['Signal'] > 0).astype(int) * df['Actual_Return'] * -1
    
    worst_errors = df.sort_values('Error_Magnitude', ascending=False).head(5)
    
    for date, row in worst_errors.iterrows():
        if row['Error_Magnitude'] > 0: # Gerçekten hata varsa
            print(f"Date: {date.date()} | Rejim: {row['Regime']} | Sinyal: {row['Signal']:.4f} | Gerçek Değişim: %{row['Actual_Return']*100:.2f}")

    # D. Feature Importance (Basit)
    # Modelin neye baktığını anlamak için (Beta Model)
    print("\n--- D. Model Neye Bakıyor? (Beta Model Önem Sırası) ---")
    try:
        importance = beta_model_obj.feature_importance()
        feature_names = beta_model_obj.feature_name()
        feat_imp = pd.DataFrame({'Feature': feature_names, 'Importance': importance})
        print(feat_imp.sort_values('Importance', ascending=False).head(5).to_string(index=False))
    except:
        print("Feature importance çekilemedi.")

def main():
    # 1. TUPRS Analizi
    analyze_ticker_failure("TUPRS.IS", "INDUSTRIAL")
    
    # 2. AKBNK Analizi
    analyze_ticker_failure("AKBNK.IS", "BANKING")

if __name__ == "__main__":
    main()
