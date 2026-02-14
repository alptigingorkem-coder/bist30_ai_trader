"""
Feature Engineering Orchestrator
Tüm feature'ları oluşturmak için mixin sınıflarını birleştirir.

Kullanım:
    from utils.feature_engineering import FeatureEngineer
    fe = FeatureEngineer(raw_data)
    processed = fe.process_all(ticker='AKBNK.IS')

Alt modüller:
    utils/features/technical.py   — RSI, MACD, Bollinger, Ichimoku, ADX, OBV, ATR
    utils/features/volatility.py  — Garman-Klass, Rogers-Satchell, Parkinson
    utils/features/macro.py       — Makro etkileşimler, sektör dummies, gate
    utils/features/fundamental.py — Feature Store, KAP bildirimleri
    utils/features/derived.py     — Getiri, lag, hedef değişkenler, temizlik
    utils/features/transformer.py — TFT özel feature'ları
"""
import numpy as np
import config

from utils.features.technical import TechnicalMixin
from utils.features.volatility import VolatilityMixin
from utils.features.macro import MacroMixin
from utils.features.fundamental import FundamentalMixin
from utils.features.derived import DerivedMixin
from utils.features.transformer import TransformerMixin

# Re-export prepare_tft_dataset for backward compatibility
from utils.features.transformer import prepare_tft_dataset  # noqa: F401


class FeatureEngineer(
    TechnicalMixin,
    VolatilityMixin,
    MacroMixin,
    FundamentalMixin,
    DerivedMixin,
    TransformerMixin,
):
    """
    BIST30 AI Trader Feature Engineering Pipeline.
    
    Mixin sınıflarını birleştirerek tüm özellik mühendisliği fonksiyonlarını
    tek bir arayüz altında toplar. process_all() orkestratör metodudur.
    """

    def __init__(self, data):
        self.data = data.copy()

    def process_all(self, ticker=None):
        """Tüm işlemleri sırasıyla çalıştırır."""
        # 1. Targets First
        self.add_multi_window_targets()

        self.add_technical_indicators()
        self.add_volatility_estimators()

        # Gelişmiş teknik indikatörler
        if getattr(config, 'ENABLE_CUSTOM_INDICATORS', True):
            self.add_custom_indicators()

        # Macro Technicals
        if getattr(config, 'ENABLE_MACRO_IN_MODEL', False):
            self.add_bank_features()
            self.add_advanced_market_features()

        # Fundamental Data
        if ticker:
            self.add_fundamental_features_from_file(ticker)
            self.add_sector_dummies(ticker)
            if getattr(config, 'ENABLE_KAP_FEATURES', True):
                self.add_kap_features(ticker)

        self.add_time_features()
        self.add_derived_features()
        self.add_macro_derived_features()

        # Volume / Stochastic / ATR
        self.add_volume_and_extra_indicators()

        # Macro Interaction (sektör + makro feature'lar oluştuktan sonra)
        self.add_macro_interaction_features()

        # TFT feature'ları
        self.add_transformer_features()

        # Robustness: Clean Inf
        self.data.replace([np.inf, -np.inf], np.nan, inplace=True)

        self.clean_data()
        return self.data
