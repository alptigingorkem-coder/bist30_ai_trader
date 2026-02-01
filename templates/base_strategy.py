from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import joblib
import os
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.regime_detection import RegimeDetector

class BaseStrategy(ABC):
    """
    Tüm sektörel stratejiler için temel (abstract) sınıf.
    Ortak veri yükleme, model hazırlığı ve işlem yürütme mantığını içerir.
    """
    
    def __init__(self, config_module):
        self.config = config_module
        self.models = {}
        self.results = {}
        self.sector_name = getattr(config_module, 'SECTOR_NAME', 'UNKNOWN')
        
    def load_models(self):
        """Diskten eğitilmiş modelleri yükler."""
        beta_path = f"models/saved/{self.sector_name.lower()}_beta.pkl"
        alpha_path = f"models/saved/{self.sector_name.lower()}_alpha.pkl"
        
        try:
            if os.path.exists(beta_path):
                self.models['beta'] = joblib.load(beta_path)
                # print(f"[{self.sector_name}] Beta model yüklendi.")
            else:
                print(f"[{self.sector_name}] HATA: Beta model bulunamadı ({beta_path}). Önce eğitim yapın.")
                
            if os.path.exists(alpha_path):
                self.models['alpha'] = joblib.load(alpha_path)
                # print(f"[{self.sector_name}] Alpha model yüklendi.")
            else:
                print(f"[{self.sector_name}] HATA: Alpha model bulunamadı ({alpha_path}).")
                
        except Exception as e:
            print(f"[{self.sector_name}] Model yükleme hatası: {e}")

    @abstractmethod
    def setup(self):
        """Modelleri ve veri araçlarını başlatır."""
        self.load_models()
    
    def fetch_data(self, ticker: str) -> pd.DataFrame:
        """
        Gerçek veriyi çeker, feature engineering ve rejim tespiti yapar.
        """
        # 1. Veri İndirme
        loader = DataLoader() # Config'den tarihleri alır
        raw_data = loader.get_combined_data(ticker)
        
        if raw_data is None or len(raw_data) < 100:
            print(f"[{self.sector_name}] {ticker} için yetersiz veri.")
            return None
            
        # 2. Feature Engineering
        # 2. Feature Engineering
        fe = FeatureEngineer(raw_data)
        
        # MAKRO DURUMU AL (Gate için)
        macro_status = fe.get_macro_status()
        
        # Feature Process (Makro sütunları siler)
        df = fe.process_all(ticker=ticker)
        
        # 3. Rejim Tespiti (Veri setine eklenir)
        rd = RegimeDetector(df, thresholds=self.config.REGIME_THRESHOLDS)
        df = rd.detect_regimes()
        
        return df, macro_status
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, regime: str) -> Dict[str, Any]:
        """Al/Sat/Tut sinyali ve oranlarını üretir."""
        pass
        
    def calculate_position_size(self, confidence: float, regime: str) -> float:
        """
        Kelly Criterion bazlı dinamik boyutlandırma.
        """
        # ÖNCE (Çok agresif)
        # kelly_fraction = 0.25  # Full Kelly'nin 1/4'ü
        
        # SONRA (Daha konservatif)
        kelly_fraction = 0.15  # Full Kelly'nin 1/6'sı (FIX 1)
        
        # Win rate penalty (Geçmiş performansa göre ayarla)
        # self.historical_win_rate attributesini strateji içinde güncellemeliyiz (şimdilik varsayılan 0.50)
        historical_win_rate = getattr(self, 'historical_win_rate', 0.50)
        if historical_win_rate < 0.45:
            kelly_fraction *= 0.7  # %30 azalt (FIX 2)
        
        # Base position
        # Confidence [0, 1] -> Edge [0, 1] (Assuming confidence > 0.5 implies edge)
        if confidence <= 0.5:
             return 0.0
             
        edge = (confidence - 0.5) * 2  # [0, 1] aralığına scale et
        base_size = edge * kelly_fraction
        
        # Regime adjustment (ÖNCE çok agresif)
        regime_multipliers = {
            'Trend_Up': 1.0,      # 1.2 -> 1.0 (FIX 3)
            'Sideways': 0.6,      # 0.7 -> 0.6
            'Crash_Bear': 0.0     # Değişmedi
        }
        
        adjusted_size = base_size * regime_multipliers.get(regime, 0.5)
        
        # Hard limits
        return float(np.clip(adjusted_size, 0, 0.25))  # Max %25 pozisyon (FIX 4)

    @abstractmethod
    def apply_risk_management(self, signal: Dict[str, Any], regime: str) -> Dict[str, Any]:
        """Risk kurallarını ve Kelly kriterini uygular."""
        pass
        
    def run(self, ticker: str) -> Dict[str, Any]:
        """
        Tek bir hisse senedi için tam analiz döngüsünü çalıştırır.
        """
        # 1. Veri Hazırlığı
        data_result = self.fetch_data(ticker)
        
        if data_result is None:
            return {'ticker': ticker, 'error': 'No data'}
            
        df, macro_status = data_result
        
        if df is None or df.empty:
             return {'ticker': ticker, 'error': 'Empty dataframe'}
            
        # Son bara ait rejim
        last_regime = df['Regime'].iloc[-1]
        
        # 2. Sinyal Üretimi
        signal = self.generate_signal(df, last_regime)
        
        # 3. Risk Yönetimi & Pozisyon Büyüklüğü
        final_decision = self.apply_risk_management(signal, last_regime)
        final_decision['ticker'] = ticker
        final_decision['current_price'] = df['Close'].iloc[-1]
        final_decision['regime'] = last_regime
        
        # --- MACRO GATE (SİNYAL KİLİDİ) ---
        # Makro riskler varsa sinyali ezer ve işlemi engeller.
        blocked_by_macro = False
        block_reasons = []
        
        # Config'den Gate aktif mi kontrol et (Varsayılan: True)
        gate_enabled = getattr(self.config, 'ENABLE_MACRO_GATE', True)
        
        if gate_enabled:
            if macro_status.get('VIX_HIGH', False):
                blocked_by_macro = True
                block_reasons.append("VIX_HIGH")
                
            if macro_status.get('USDTRY_SHOCK', False):
                blocked_by_macro = True
                block_reasons.append("USDTRY_SHOCK")
                
            if macro_status.get('GLOBAL_RISK_OFF', False):
                blocked_by_macro = True
                block_reasons.append("GLOBAL_RISK_OFF")
        else:
             # Ablation Study Modu: Gate Devre Dışı
             # İsteğe bağlı: print(f"  [GATE] Devre Dışı (Ablation Mode)")
             pass
            
        if blocked_by_macro:
            print(f"  [GATE] İşlem Engellendi: {ticker} -> {block_reasons}")
            # Kararı ez
            final_decision['original_action'] = final_decision['action']
            final_decision['action'] = 'WAIT' # veya HOLD_CASH
            final_decision['size'] = 0.0
            final_decision['blocked_by_macro'] = True
            final_decision['block_reason'] = " | ".join(block_reasons)
        else:
            final_decision['blocked_by_macro'] = False
            final_decision['block_reason'] = ""
        # ----------------------------------
        
        return final_decision
