
import pandas as pd
import numpy as np
import os
import joblib

class EnsembleModel:
    def __init__(self, lgbm_model, catboost_model, weights={'lgbm': 0.6, 'catboost': 0.4}):
        self.lgbm_model = lgbm_model
        self.catboost_model = catboost_model
        self.weights = weights
        
    def predict(self, df):
        """
        Ensemble prediction using weighted average of scores.
        """
        lgbm_scores = self.lgbm_model.predict(df)
        cat_scores = self.catboost_model.predict(df)
        
        # Scaling scores to 0-1 range to align distributions if necessary
        # But ranking scores are usually relative. Let's use simple weighted sum.
        
        # Normalize scores within each group (Date) for better fusion?
        # Ranking models give non-comparable raw scores across models.
        # Better to rank them first or z-score.
        
        scores_df = pd.DataFrame({
            'lgbm': lgbm_scores,
            'catboost': cat_scores
        }, index=df.index)
        
        # Cross-model normalization: Z-score per model
        # scores_df['lgbm_z'] = (scores_df['lgbm'] - scores_df['lgbm'].mean()) / scores_df['lgbm'].std()
        # scores_df['cat_z'] = (scores_df['catboost'] - scores_df['catboost'].mean()) / scores_df['catboost'].std()
        
        # Simplified: Just weighted average of raw scores for now
        ensemble_score = (scores_df['lgbm'] * self.weights['lgbm']) + (scores_df['catboost'] * self.weights['catboost'])
        
        # Rule-based filter: Confidence check
        # e.g. If RSI > 80, penalize score (Anti-bubble)
        if 'RSI' in df.columns:
            # Overbought penalty
            ensemble_score = np.where(df['RSI'] > 80, ensemble_score * 0.8, ensemble_score)
            # Oversold boost
            ensemble_score = np.where(df['RSI'] < 30, ensemble_score * 1.1, ensemble_score)
            
        return ensemble_score

    def save(self, path):
        # We don't save the full object easily due to internal class dependencies.
        # Instead, we save the weights and metadata.
        # Models should be loaded externally.
        joblib.dump(self.weights, path)
        
    @classmethod
    def load_with_models(cls, path, lgbm_model, cat_model):
        weights = joblib.load(path)
        return cls(lgbm_model, cat_model, weights)
