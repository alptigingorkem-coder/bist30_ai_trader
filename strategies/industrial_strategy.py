from templates.base_strategy import BaseStrategy
from configs import industrial as config
import pandas as pd
from models.beta_model import BetaModel
from models.alpha_model import AlphaModel
from typing import Dict, Any

class IndustrialStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(config)
        self.setup()
        
    def setup(self):
        super().setup()

    def generate_signal(self, df: pd.DataFrame, regime: str) -> Dict[str, Any]:
        beta_pred = 0.0
        alpha_pred = 0.0
        
        if 'beta' in self.models:
            temp = BetaModel(df, self.config)
            temp.model = self.models['beta']
            p = temp.predict(df)
            if p is not None: beta_pred = p.iloc[-1]
            
        if 'alpha' in self.models:
            temp = AlphaModel(df, self.config)
            temp.model = self.models['alpha']
            p = temp.predict(df)
            if p is not None: alpha_pred = p.iloc[-1]
            
        w_beta = self.config.BETA_ALPHA_RATIO['beta']
        w_alpha = self.config.BETA_ALPHA_RATIO['alpha']
        
        # Sanayi: Emtia Momentumu Pozitifse Alpha'yı Artır
        try:
            # Gold veya Oil momentum pozitif mi?
            # Basit kontrol
            comm_boost = 1.0
            if 'Gold_TRY_Momentum' in df.columns and df['Gold_TRY_Momentum'].iloc[-1] > 0:
                comm_boost = 1.2
            
            alpha_pred *= comm_boost
        except:
            pass

        final_pred = (beta_pred * w_beta) + (alpha_pred * w_alpha)
        
        # FIX 10: Regime Confidence'i sinyale ekle
        regime_conf = df['Regime_Confidence'].iloc[-1] if 'Regime_Confidence' in df.columns else 1.0

        return {"prediction": final_pred, "components": {"beta": beta_pred, "alpha": alpha_pred}, "regime": regime, "regime_confidence": regime_conf}

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

        if regime == "Crash_Bear": return {"action": "HOLD_CASH", "reason": "Bear Market", "confidence": 0}
        if pred < self.config.MIN_RETURN_THRESHOLD: return {"action": "WAIT", "reason": "Low Return", "confidence": pred}
        
        confidence = min(pred * 10, 1.0)
        size = self.calculate_position_size(confidence, regime)
        
        return {"action": "BUY" if size > 0.1 else "WAIT", "size": round(size, 2), "stop_loss": f"ATR x {self.config.STOP_LOSS_ATR}", "confidence": confidence}
