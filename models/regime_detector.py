# models/regime_detector.py - KOMPLE YENİ VERSİYON

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class RegimeDetector:
    """
    Piyasa rejimini tespit et ve trading aksiyonlarını belirle.
    
    Rejimler:
    - TREND_UP: Güçlü yükseliş trendi (Trade tam güç)
    - NORMAL: Normal piyasa koşulları (Trade %80 güç)
    - SIDEWAYS: Yatay piyasa (Trade %50 güç)
    - VOLATILE: Yüksek volatilite (Trade YAPMA!)
    - CRISIS: Kriz durumu (Tüm pozisyonları kapat!)
    - TREND_DOWN: Düşüş trendi (Long yapma)
    """
    
    def __init__(self, config):
        self.config = config
        self.thresholds = config.get('REGIME_THRESHOLDS', {})
        self.actions = config.get('REGIME_ACTIONS', {})
        
        # Rejim geçmişi (stabilite için)
        self.regime_history = []
        self.max_history = 5
        
        logger.info("RegimeDetector initialized with thresholds: %s", self.thresholds)
    
    def detect_regime(self, market_data: pd.DataFrame) -> str:
        """
        Ana rejim tespit fonksiyonu.
        
        Args:
            market_data: En son piyasa verileri (VIX, USDTRY, ATR, SMA vb. içermeli)
        
        Returns:
            str: Tespit edilen rejim ('CRISIS', 'VOLATILE', 'TREND_UP', vb.)
        """
        
        # 1. KRİZ kontrolü (En yüksek öncelik!)
        if self._is_crisis(market_data):
            regime = "CRISIS"
            logger.warning("🚨 CRISIS REGIME DETECTED!")
        
        # 2. VOLATİL kontrolü
        elif self._is_volatile(market_data):
            regime = "VOLATILE"
            logger.warning("⚠️ VOLATILE REGIME DETECTED")
        
        # 3. TREND kontrolü
        elif self._is_trend_up(market_data):
            regime = "TREND_UP"
            logger.info("✅ TREND_UP REGIME")
        
        elif self._is_trend_down(market_data):
            regime = "TREND_DOWN"
            logger.info("📉 TREND_DOWN REGIME")
        
        # 4. YATAY piyasa kontrolü
        elif self._is_sideways(market_data):
            regime = "SIDEWAYS"
            logger.info("➡️ SIDEWAYS REGIME")
        
        # 5. NORMAL (varsayılan)
        else:
            regime = "NORMAL"
            logger.info("✅ NORMAL REGIME")
        
        # Stabilite için geçmişe ekle
        self.regime_history.append(regime)
        if len(self.regime_history) > self.max_history:
            self.regime_history.pop(0)
        
        # Minimum regime days kontrolü
        min_days = self.thresholds.get('min_regime_days', 3)
        if len(self.regime_history) >= min_days:
            # Son N gün aynı rejim mi?
            recent = self.regime_history[-min_days:]
            if len(set(recent)) == 1:
                # Evet, stabil
                return regime
            else:
                # Hayır, dalgalı -> Bir önceki rejimi döndür (whipsaw önleme)
                return self.regime_history[-2] if len(self.regime_history) > 1 else regime
        
        return regime
    
    def _is_crisis(self, data: pd.DataFrame) -> bool:
        """
        Kriz tespiti: VIX >35, Kur şoku, CDS patlaması.
        Window 1 (COVID), Window 13, 16'daki felaketleri yakalar.
        """
        vix = data['VIX'].iloc[-1] if 'VIX' in data.columns else 20.0
        usdtry_change_5d = data['USDTRY'].pct_change(5).iloc[-1] if 'USDTRY' in data.columns else 0.0
        
        # VIX kriteri
        vix_crisis = vix > self.thresholds.get('vix_crisis', 35.0)
        
        # Kur şoku kriteri (5 günde %3+ artış)
        fx_shock = usdtry_change_5d > 0.03
        
        # CDS kontrolü (varsa)
        cds_high = False
        if 'CDS' in data.columns:
            cds = data['CDS'].iloc[-1]
            cds_high = cds > self.thresholds.get('cds_high', 550)
        
        return vix_crisis or fx_shock or cds_high
    
    def _is_volatile(self, data: pd.DataFrame) -> bool:
        """
        Volatilite tespiti: VIX 25-35 arası, ATR spike.
        Window 10, 11'deki yüksek DD'leri yakalar.
        """
        vix = data['VIX'].iloc[-1] if 'VIX' in data.columns else 20.0
        
        # VIX kriteri
        vix_volatile = (vix > self.thresholds.get('vix_volatile', 25.0) and 
                       vix < self.thresholds.get('vix_crisis', 35.0))
        
        # ATR spike kontrolü
        atr_spike = False
        if 'ATR' in data.columns:
            atr_current = data['ATR'].iloc[-1]
            
            # FIX: Check for pre-calculated ATR MA first (critical for single-row backtest loop)
            if 'ATR_MA_60' in data.columns:
                atr_avg = data['ATR_MA_60'].iloc[-1]
            else:
                atr_avg = data['ATR'].rolling(60).mean().iloc[-1]
                
            atr_multiplier = self.thresholds.get('atr_spike_multiplier', 1.8)
            
            if not np.isnan(atr_avg) and atr_avg > 0:
                atr_spike = atr_current > atr_avg * atr_multiplier
        
        # Volatilite direct kontrolü
        vol_high = False
        if 'Volatility_20' in data.columns:
            vol = data['Volatility_20'].iloc[-1]
            vol_high = vol > self.thresholds.get('volatility_high', 0.50)
        
        return vix_volatile or atr_spike or vol_high
    
    def _is_trend_up(self, data: pd.DataFrame) -> bool:
        """
        Yükseliş trendi tespiti: SMA20 > SMA50, momentum pozitif.
        Window 2, 4, 8, 12'deki başarılı dönemleri yakalar.
        """
        if 'SMA_20' not in data.columns or 'SMA_50' not in data.columns:
            return False
        
        sma_20 = data['SMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]
        
        # Trend gücü
        trend_strength = (sma_20 - sma_50) / sma_50
        threshold = self.thresholds.get('sma_trend_threshold', 0.015)
        
        # Momentum kontrolü
        momentum_ok = True
        if 'RSI' in data.columns:
            rsi = data['RSI'].iloc[-1]
            momentum_ok = rsi > self.thresholds.get('momentum_threshold', 45)
        
        return trend_strength > threshold and momentum_ok
    
    def _is_trend_down(self, data: pd.DataFrame) -> bool:
        """
        Düşüş trendi: SMA20 < SMA50.
        """
        if 'SMA_20' not in data.columns or 'SMA_50' not in data.columns:
            return False
        
        sma_20 = data['SMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]
        
        trend_strength = (sma_20 - sma_50) / sma_50
        threshold = -self.thresholds.get('sma_trend_threshold', 0.015)
        
        return trend_strength < threshold
    
    def _is_sideways(self, data: pd.DataFrame) -> bool:
        """
        Yatay piyasa: SMA20 approx SMA50 (fark <%0.8).
        Window 6, 7'deki zayıf dönemleri yakalar.
        """
        if 'SMA_20' not in data.columns or 'SMA_50' not in data.columns:
            return False
        
        sma_20 = data['SMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]
        
        trend_strength = abs((sma_20 - sma_50) / sma_50)
        threshold = self.thresholds.get('sideways_range', 0.008)
        
        return trend_strength < threshold
    
    def get_trading_action(self, regime: str) -> Dict:
        """
        Rejime göre trading aksiyonu döndür.
        
        Returns:
            {
                'trade': bool,  # Trade yapılmalı mı?
                'position_multiplier': float,  # Pozisyon çarpanı (0.0-1.0)
                'stop_loss_mult': float,  # Stop-loss sıkılığı
                'max_positions': int,  # Max hisse sayısı
                'force_exit': bool  # Zorunlu çıkış mı?
            }
        """
        return self.actions.get(regime, {
            'trade': True,
            'position_multiplier': 0.8,
            'stop_loss_mult': 1.5,
            'max_positions': 4,
            'force_exit': False
        })
    
    def should_trade(self, regime: str) -> bool:
        """Basit kontrol: Bu rejimde trade yapılmalı mı?"""
        action = self.get_trading_action(regime)
        return action.get('trade', False)
    
    def get_position_multiplier(self, regime: str) -> float:
        """Rejime göre pozisyon küçültme çarpanı"""
        action = self.get_trading_action(regime)
        return action.get('position_multiplier', 0.8)
    
    def get_stop_loss_multiplier(self, regime: str) -> float:
        """Rejime göre stop-loss sıkılığı"""
        action = self.get_trading_action(regime)
        return action.get('stop_loss_mult', 1.5)
