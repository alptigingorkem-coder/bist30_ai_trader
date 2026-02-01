
import pandas as pd
import numpy as np
import os
import joblib
import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.regime_detection import RegimeDetector
from models.beta_model import BetaModel
from models.alpha_model import AlphaModel
from core.backtesting import Backtester

# Sektör Konfigürasyonları (Single Source of Truth)
from configs import banking as config_banking
from configs import holding as config_holding
from configs import industrial as config_industrial
from configs import growth as config_growth

# Sektör Haritası (Dinamik)
SECTOR_MAP = {
    'BANKING': config_banking.TICKERS,
    'HOLDING': config_holding.TICKERS,
    'INDUSTRIAL': config_industrial.TICKERS,
    'GROWTH': config_growth.TICKERS
}

def get_vectorized_macro_gate(df, thresholds):
    """
    Tarihsel veri üzerinde vektörel Macro Gate maskesi oluşturur.
    DÜZELTİLMİŞ VERSİYON: Geleceği görme engellendi (shift(1) eklendi).
    Return: Series (True: Blocked, False: Open)
    """
    mask = pd.Series(False, index=df.index)
    
    # 1. VIX Check (DÜNÜN Kapanışı > Eşik ise BUGÜN işlem yapma)
    if 'VIX' in df.columns:
        mask |= (df['VIX'].shift(1) > thresholds['VIX_HIGH'])
        
    # 2. USDTRY Shock (DÜN itibariyle son 5 günlük değişim)
    if 'USDTRY' in df.columns:
        # pct_change zaten o satırı baz alır, o yüzden sonucu shift etmeliyiz
        usd_change = df['USDTRY'].pct_change(5).shift(1)
        mask |= (usd_change > thresholds['USDTRY_CHANGE_5D'])
        
    # 3. Global Risk Off (SP500 Momentum)
    if 'SP500' in df.columns:
        # Momentum
        sp_mom = df['SP500'].pct_change(5).shift(1) # Weekly modda 1 bar olabilir ama 5 bar daha robust
        mask |= (sp_mom < thresholds['SP500_MOMENTUM'])
        
    # Shift işlemi ilk satırda NaN yaratır, bunları False (Blok yok) yapalım
    return mask.fillna(False)

def run_backtest_for_ticker(ticker, sector_name):
    # 1. Data Loading
    loader = DataLoader(start_date="2018-01-01") # Matching training period for consistency
    raw_data = loader.get_combined_data(ticker)
    
    if raw_data is None or len(raw_data) < 100:
        print(f"Skipping {ticker}: Insufficient data.")
        return None, None
    
    print(f"DEBUG: {ticker} Raw Cols: {raw_data.columns.tolist()}")
    
    # Kopyasını al (Macro veriler silinmeden önce)
    macro_data = raw_data.copy()
    
    # 2. Macro Gate Mask Extraction
    if getattr(config, 'ENABLE_MACRO_GATE', True):
        gate_mask = get_vectorized_macro_gate(macro_data, config.MACRO_GATE_THRESHOLDS)
    else:
        gate_mask = pd.Series(False, index=raw_data.index)
        
    # 3. Feature Engineering
    fe = FeatureEngineer(raw_data)
    df = fe.process_all(ticker=ticker) # This calls clean_data and drops macro cols
    
    # Align Gate Mask with cleaned DF (Date filter)
    gate_mask = gate_mask.reindex(df.index).fillna(False)
    
    # 4. Regime Detection
    rd = RegimeDetector(df)
    df = rd.detect_regimes(verbose=False)
    
    # 5. Load Models
    beta_path = f"models/saved/{sector_name.lower()}_beta.pkl"
    alpha_path = f"models/saved/{sector_name.lower()}_alpha.pkl"
    
    if not os.path.exists(beta_path) or not os.path.exists(alpha_path):
        print(f"Skipping {ticker}: Models not found for sector {sector_name}.")
        return None, None
        
    beta_model_obj = joblib.load(beta_path)
    alpha_model_obj = joblib.load(alpha_path)
    
    # 6. Predictions (Vectorized)
    # create temp wrappers to use predict method (since it handles feature prep internally if needed, 
    # but our BetaModel.predict implementation expects 'current_features_df' and calls prepare_features(is_training=False))
    
    # Instantiating wrapper class just to use predict logic
    beta_wrapper = BetaModel(df, config)
    beta_wrapper.model = beta_model_obj
    beta_preds = beta_wrapper.predict(df) # Returns Series
    
    alpha_wrapper = AlphaModel(df, config)
    alpha_wrapper.model = alpha_model_obj
    alpha_preds = alpha_wrapper.predict(df)
    
    if beta_preds is None or alpha_preds is None:
        print(f"Prediction failed for {ticker}")
        return None, None
        
    # 7. Combine Predictions based on Regime
    # if Regime == Trend_Up (2) -> Weighted Beta
    # if Regime == Sideways (0) -> Weighted Alpha
    # if Regime == Crash (1) -> 0
    
    # Weights
    w_beta = 0.5 
    w_alpha = 0.5
    # Simplified logic matching BaseStrategy
    
    final_preds = pd.Series(0.0, index=df.index)
    
    # Vectorized condition
    # Trend_Up
    mask_trend = (df['Regime_Num'] == 2)
    final_preds[mask_trend] = (beta_preds[mask_trend] * 0.7) + (alpha_preds[mask_trend] * 0.3)
    
    # Sideways
    mask_side = (df['Regime_Num'] == 0)
    final_preds[mask_side] = (beta_preds[mask_side] * 0.3) + (alpha_preds[mask_side] * 0.7)
    
    # Crash
    mask_crash = (df['Regime_Num'] == 1)
    final_preds[mask_crash] = 0.0
    
    # 8. Apply Threshold to get Target Weights (0 to 1)
    # If pred > threshold -> Buy (Size based on confidence)
    # Thresholds
    threshold = 0.005 # %0.5 weekly return expectation
    
    target_weights = final_preds.apply(lambda x: min(x * 10, 1.0) if x > threshold else 0.0)
    
    # 9. Apply Macro Gate
    # If blocked, weight = 0
    target_weights[gate_mask] = 0.0
    
    # 10. Run Backtest
    backtester = Backtester(df, initial_capital=10000, commission=config.COMMISSION_RATE)
    backtester.run_backtest(target_weights)
    
    # Save individual ticker report
    backtester.generate_html_report(filename=f"reports/report_{ticker}.html", ticker=ticker)
    backtester.save_trade_log(filename=f"reports/backtest_trades_{ticker}.csv")
    
    metrics = backtester.calculate_metrics()
    metrics['Ticker'] = ticker
    
    # Daily Returns for Portfolio Aggregation
    daily_rets = backtester.results['Equity'].pct_change().fillna(0)
    daily_rets.name = ticker
    
    return metrics, daily_rets

def main():
    if not os.path.exists("reports"):
        os.makedirs("reports")
        
    # Collect all tickers from configs
    tickers = []
    for t_list in SECTOR_MAP.values():
        tickers.extend(t_list)
    tickers = list(set(tickers)) # Unique
    
    all_metrics = []
    all_daily_returns = []
    
    print(f"Starting Backtest for {len(tickers)} tickers...")
    
    for ticker in tickers:
        print(f"Testing {ticker}...", end=" ")
        
        # Sector find
        sector = "HOLDING"
        for s, t_list in SECTOR_MAP.items():
            if ticker in t_list:
                sector = s
                break
                
        try:
            metrics, daily_rets = run_backtest_for_ticker(ticker, sector)
            if metrics:
                all_metrics.append(metrics)
                all_daily_returns.append(daily_rets)
                print(f"DONE (Return: {metrics['Total Return']:.2%})")
            else:
                print("SKIPPED/FAILED")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            
    if all_metrics:
        # 1. Summary Metrics
        df_res = pd.DataFrame(all_metrics)
        cols = ['Ticker', 'Total Return', 'Annual Return', 'Sharpe Ratio', 'Max Drawdown', 'Win Rate', 'Num Trades']
        df_res = df_res[[c for c in cols if c in df_res.columns]]
        
        print("\n" + "="*80)
        print("BACKTEST SONUÇ ÖZETİ")
        print("="*80)
        print(df_res.to_string(index=False))
        print("="*80)
        
        df_res.to_csv("reports/final_backtest_results.csv", index=False)
        print("\nRapor kaydedildi: reports/final_backtest_results.csv")
        
        # 2. Daily Returns Concatenation for Monte Carlo
        if all_daily_returns:
            print("Combining daily returns for Monte Carlo...")
            concatenated_returns = pd.concat(all_daily_returns, axis=1)
            concatenated_returns = concatenated_returns.fillna(0) # Fill missing days with 0 return
            
            # Tarih index'i string formatına çevir
            concatenated_returns.index = concatenated_returns.index.strftime('%Y-%m-%d')
            
            concatenated_returns.to_csv("reports/daily_returns_concatenated.csv")
            print("Günlük getiriler kaydedildi: reports/daily_returns_concatenated.csv")
            
    else:
        print("Sonuç yok.")

if __name__ == "__main__":
    main()
