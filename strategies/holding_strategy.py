from templates.base_strategy import BaseStrategy
from configs import holding as config
import pandas as pd
from models.beta_model import BetaModel
from models.alpha_model import AlphaModel
from typing import Dict, Any

class HoldingStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(config)
        self.setup()
        
    def setup(self):
        super().setup()

    def generate_signal(self, df: pd.DataFrame, regime: str) -> Dict[str, Any]:
        beta_pred = 0.0
        alpha_pred = 0.0
        
        # Beta Tahmini
        if 'beta' in self.models:
            temp_beta = BetaModel(df, self.config)
            temp_beta.model = self.models['beta']
            preds = temp_beta.predict(df)
            if preds is not None: beta_pred = preds.iloc[-1]
            
        # Alpha Tahmini
        if 'alpha' in self.models:
            temp_alpha = AlphaModel(df, self.config)
            temp_alpha.model = self.models['alpha']
            preds = temp_alpha.predict(df)
            if preds is not None: alpha_pred = preds.iloc[-1]
            
        # Holding Dengeli Yaklaşım
        w_beta = self.config.BETA_ALPHA_RATIO['beta']
        w_alpha = self.config.BETA_ALPHA_RATIO['alpha']
        
        # Holdinglerde TEMEL ANALİZ Filtresi
        # Eğer PD/DD çok yüksekse Alpha beklentisini düşür
        try:
            pb_ratio = df['PB_Ratio'].iloc[-1]
            if pb_ratio > 3.0: # Holding için pahalı
                alpha_pred *= 0.5
        except KeyError:
            pass

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
            pred *= 0.5 
        
        if regime == "Crash_Bear":
            return {"action": "HOLD_CASH", "reason": "Bear Market", "confidence": 0.0}
            
        if pred < self.config.MIN_RETURN_THRESHOLD:
            return {"action": "WAIT", "reason": "Low Return Pred", "confidence": pred}
            
        confidence = min(pred * 12, 1.0) # Holding biraz daha agresif olabilir
        size = self.calculate_position_size(confidence, regime)
        
        # Volatilite Cezası
        # (Volatility_Ratio > 1.5 ise size düşür)
        # Bu veri FeatureEngineer tarafından üretilmeli
        
        action = "BUY" if size > 0.1 else "WAIT"
        
        return {
            "action": action,
            "size": round(size, 2),
            "stop_loss": f"ATR x {self.config.STOP_LOSS_ATR}",
            "confidence": confidence
        }
