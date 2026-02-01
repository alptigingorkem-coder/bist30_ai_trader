from templates.base_strategy import BaseStrategy
from configs import banking as config
import pandas as pd
import numpy as np
from typing import Dict, Any

class BankingStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(config)
        self.setup()
        
    def setup(self):
        super().setup() # Modelleri yükle
        
    def generate_signal(self, df: pd.DataFrame, regime: str) -> Dict[str, Any]:
        """
        Rejime göre Beta ve Alpha modellerini ağırlıklandırarak sinyal üretir.
        """
        # Model tahminleri (Son bar için)
        # Model input formatı için tüm df'i gönderiyoruz, model sonuncuyu seçer veya biz burada seçeriz.
        # BetaModel.predict tüm seriyi döndürür.
        
        beta_pred = 0.0
        alpha_pred = 0.0
        
        if 'beta' in self.models and self.models['beta']:
            try:
                # Feature uyumluluğu için prepare_features gerekebilir ama
                # LightGBM genelde sütun isimlerine bakar. 
                # Modelimiz "BetaModel" class wrapper değil, direkt LGBM Booster objesi ise predict metodu farklıdır.
                # Ancak biz joblib ile "BetaModel" instance mı yoksa "lgb.Booster" mı kaydettik?
                # train_models.py'de: beta_model.save(...) -> joblib.dump(self.model, path)
                # self.model bir lgb.Booster veya sklearn wrapper.
                
                # LGBM sklearn wrapper (LGBMRegressor) ise predict(X) ister.
                # Veri hazırlığı (Feature seçimi) kritik.
                # Bu yüzden wrapper class'ı kaydetmek daha iyi olurdu ama sadece modeli kaydettik.
                # Sütunları tekrar seçmeliyiz.
                
                # HIZLI ÇÖZÜM: Tahmin için BetaModel sınıfını geçici olarak instantiate et.
                from models.beta_model import BetaModel
                temp_beta = BetaModel(df, self.config)
                temp_beta.model = self.models['beta'] # Yüklenen modeli tak
                preds = temp_beta.predict(df)
                if preds is not None:
                    beta_pred = preds.iloc[-1]
            except Exception as e:
                print(f"Beta Prediction Error: {e}")

        if 'alpha' in self.models and self.models['alpha']:
            try:
                from models.alpha_model import AlphaModel
                temp_alpha = AlphaModel(df, self.config)
                temp_alpha.model = self.models['alpha']
                preds = temp_alpha.predict(df)
                if preds is not None:
                    alpha_pred = preds.iloc[-1]
            except Exception as e:
                print(f"Alpha Prediction Error: {e}")

        # Ağırlıklandırma
        if regime == "Trend_Up":
            w_beta = self.config.BETA_ALPHA_RATIO['beta']
            w_alpha = self.config.BETA_ALPHA_RATIO['alpha']
        elif regime == "Sideways":
             # Bankacılık Trend odaklıdır ama yatayda alpha'ya bir miktar kayılabilir
            w_beta = 0.50
            w_alpha = 0.50
        else: # Crash
            w_beta = 0.0
            w_alpha = 0.0
            
        final_pred = (beta_pred * w_beta) + (alpha_pred * w_alpha)
        
        # FIX 10: Regime Confidence'i sinyale ekle
        regime_conf = df['Regime_Confidence'].iloc[-1] if 'Regime_Confidence' in df.columns else 1.0
        
        return {
            "prediction": final_pred,
            "components": {"beta": beta_pred, "alpha": alpha_pred},
            "regime": regime,
            "regime_confidence": regime_conf
        }

    def apply_risk_management(self, signal: Dict[str, Any], regime: str) -> Dict[str, Any]:
        pred = signal['prediction']
        
        # FIX 9: Prediction threshold - Çok düşük tahminlerde işlem yapma
        MIN_PREDICTION_THRESHOLD = {
            'Trend_Up': 0.008,    # Haftalık min %0.8 beklenti
            'Sideways': 0.012,    # Yatayda daha yüksek eşik
            'Crash_Bear': 999     # Krizde hiç işlem yok
        }
        
        threshold = MIN_PREDICTION_THRESHOLD.get(regime, 0.010)
        
        if pred < threshold:
            return {
                "action": "WAIT",
                "reason": f"Prediction too low ({pred:.3f} < {threshold:.3f})",
                "confidence": 0.0,
                "size": 0.0
            }
            
        # FIX 11: Regime confidence penalty
        regime_conf = signal.get('regime_confidence', 1.0)
        if regime_conf < 0.6:  # Rejim belirsizse
            pred *= 0.5 # Tahmini (ve dolayısıyla boyutu) düşür
            # Not: size hesaplanmadan önce confidence/pred düşürülürse size da düşer.
            
        beta_val = signal['components']['beta']
        
        if regime == "Crash_Bear":
            return {"action": "HOLD_CASH", "reason": "Bear Market Regime", "confidence": 0.0}
            
        if pred < self.config.MIN_RETURN_THRESHOLD:
            return {"action": "WAIT", "reason": f"Low Return Prediction ({pred:.2%})", "confidence": pred}
            
        # Kelly Boyutlandırma (BaseStrategy metodu)
        # Güven = Tahmin / Beklenen Volatilite (Ölçeklenmiş)
        confidence = min(pred * 10, 1.0) 
        
        size = self.calculate_position_size(confidence, regime)
        
        # Bankacılık Ek Risk Kuralı: Tahvil Faizi Artıyorsa daha defansif
        # (Bu veri varsa FeatureEngineer'den gelir ama şimdilik pas geçiyoruz)
        
        # Tavsiye
        action = "BUY" if size > 0.1 else "WAIT"
        
        return {
            "action": action,
            "size": round(size, 2),
            "target_price": "Dynamic",
            "stop_loss": f"ATR x {self.config.STOP_LOSS_ATR}",
            "confidence": confidence
        }
