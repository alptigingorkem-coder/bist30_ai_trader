
import pandas as pd
import numpy as np
import os
import joblib
import config
from datetime import datetime
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel
from configs import banking as config_banking

def get_latest_macro_status(verbose=True):
    """
    Checks Macro Gate status for 'Todays' decision.
    Returns: blocked (bool), reasons (list)
    """
    blocked = False
    reasons = []
    
    thresholds = getattr(config, 'MACRO_GATE_THRESHOLDS', {})
    
    loader = DataLoader()
    # Fetch macro data (Small lookback is enough)
    macro_data = loader.fetch_macro_data() 
    
    if macro_data is None or macro_data.empty:
        if verbose: print("⚠️ Macro veri çekilemedi. Gate kontrolü atlanıyor.")
        return False, []
        
    fe = FeatureEngineer(macro_data)
    status = fe.get_macro_status()
    
    if status.get('VIX_HIGH', False):
        blocked = True
        reasons.append(f"VIX Yüksek")
        
    if status.get('USDTRY_SHOCK', False):
        blocked = True
        reasons.append(f"USDTRY Şoku")
        
    if status.get('GLOBAL_RISK_OFF', False):
        blocked = True
        reasons.append("Global Risk-Off (SP500 Momentum Negatif)")
        
    return blocked, reasons

def generate_signals(verbose=True):
    print(f"\n{'='*50}")
    print(f"BIST30 AI TRADER - GÜNLÜK SİNYAL ÜRETİMİ ({datetime.now().strftime('%Y-%m-%d')})")
    print(f"Strateji: Daily Ranking (Daily Alpha)")
    print(f"{'='*50}")

    # 1. Macro Gate Check
    macro_blocked, macro_reasons = get_latest_macro_status(verbose)
    
    if macro_blocked:
        print("\n" + "!"*60)
        print("🛑 MACRO GATE KAPALI - ALIM SİNYALLERİ BLOKLANDI")
        print(f"Olduğu Gibi Kal / Sat (Yeni Alım Yok)")
        print(f"Nedenler: {', '.join(macro_reasons)}")
        print("!"*60 + "\n")
        # In blocked state, we can still show ranks but with warning
    else:
        print("✅ Macro Gate AÇIK (Piyasa Uygun)")

    # 2. Load Model
    try:
        ranker = RankingModel.load("models/saved/global_ranker.pkl", config_banking)
        if ranker is None: raise FileNotFoundError
    except:
        print("❌ Model yüklenemedi! Önce train_models.py çalıştırın.")
        return

    # 3. Load Data for All Tickers
    tickers = config.TICKERS
    latest_rows = []
    
    loader = DataLoader() # No start date, get recent
    
    print(f"Analiz ediliyor ({len(tickers)} hisse)...")
    
    for t in tickers:
        # Get enough data for feature engineering (e.g. 200 bars)
        # Using get_combined_data might be slow if it downloads from 2015.
        # But we need history for indicators.
        # Let's try fetching normally.
        
        # Optimization: Fetch smaller chunk if possible, but TA-Lib needs history.
        # Backtest uses 2015 start, consistency is key.
        data = loader.get_combined_data(t)
        
        if data is None or len(data) < 100:
            continue
            
        fe = FeatureEngineer(data)
        df = fe.process_all(t)
        
        if df.empty: continue
        
        # Get LAST row (Today/Yesterday close)
        last_row = df.iloc[[-1]].copy()
        last_row['Ticker'] = t
        latest_rows.append(last_row)

    if not latest_rows:
        print("Veri yok.")
        return

    # 4. Predict Ranks
    full_df = pd.concat(latest_rows)
    
    # Predict
    scores = ranker.predict(full_df)
    full_df['Score'] = scores
    
    # 5. Rank and Select
    # Sort desc by Score
    full_df = full_df.sort_values('Score', ascending=False)
    
    # Add Rank
    full_df['Rank'] = range(1, len(full_df) + 1)
    
    # Select Top 5
    top_n = 5
    recommendations = full_df.head(top_n)
    
    print("\n" + "="*60)
    print("🏆 GÜNLÜK PORTFÖY ÖNERİSİ (TOP 5)")
    print("="*60)
    
    cols_to_show = ['Ticker', 'Close', 'Rank', 'Score', 'RSI', 'Momentum_Trend']
    # Filter valid cols
    cols_to_show = [c for c in cols_to_show if c in recommendations.columns]
    
    print(recommendations[cols_to_show].to_string(index=False))
    print("-" * 60)
    
    # Save Report
    if not os.path.exists("reports"): os.makedirs("reports")
    filename = f"reports/daily_signals_{datetime.now().strftime('%Y%m%d')}.csv"
    full_df[['Ticker', 'Rank', 'Score', 'Close']].to_csv(filename, index=False)
    print(f"Detaylı rapor kaydedildi: {filename}")
    
    # 6. Actionable Advice
    print("\n📢 AKSİYON PLANI:")
    if macro_blocked:
        print("🔴 PİYASA RİSKLİ. Yeni alım yapma. Mevcut pozisyonlarda SL/TP takip et.")
    else:
        print("🟢 PİYASA OLUMLU. Bu 5 hisseyi portföye ekle/tut.")
        print(f"   Hedef Dağılım: Her hisseye %{100/top_n:.0f} ağırlık.")

if __name__ == "__main__":
    generate_signals()
