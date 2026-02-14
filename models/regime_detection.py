import pandas as pd
import numpy as np
import config

class RegimeDetector:
    def __init__(self, data, thresholds=None, use_adaptive=None):
        self.data = data.copy()
        # Eğer parametre verilmediyse config'e bak
        if use_adaptive is None:
            self.use_adaptive = getattr(config, 'USE_ADAPTIVE_REGIME', False)
        else:
            self.use_adaptive = use_adaptive
        self.thresholds = thresholds if thresholds else config.REGIME_THRESHOLDS
        
        # if self.use_adaptive:
        #    self.thresholds = self.calculate_adaptive_thresholds()
            
    def calculate_adaptive_thresholds(self):
        """
        Geçmiş veriye dayalı dinamik eşik hesaplar (Annualized Volatility üzerinden).
        """
        df = self.data
        if 'Volatility_20' not in df.columns:
            return self.thresholds # Veri yoksa config kullan
            
        # Volatilite Yıllıklandırma (Karşılaştırma aynı cinsten olmalı)
        scale_factor = 52 if getattr(config, 'TIMEFRAME', 'D') == 'W' else 252
        annual_vol = df['Volatility_20'] * np.sqrt(scale_factor)
        
        # Quantile Hesapla
        vol_low = annual_vol.quantile(0.25)
        vol_high = annual_vol.quantile(0.75)
        
        new_thresholds = self.thresholds.copy()
        new_thresholds['volatility_low'] = vol_low
        new_thresholds['volatility_high'] = vol_high
        
        log.info(f"  [Adaptive] Eşikler güncellendi: Low={vol_low:.2f}, High={vol_high:.2f}")
        return new_thresholds

    def detect_turkey_crisis(self, df, verbose=True):
        """
        Turkey-specific crisis detection (Vectorized).
        Returns a SERIES of crisis scores aligned with the dataframe index.
        """
        crisis_score = pd.Series(0, index=df.index)
        
        # Check 1: Extreme USD/TRY movement (30-day persistent)
        if 'USDTRY_Change' in df.columns:
            # 30-day change (rolling sum of logs or simple pct change over window)
            # Assuming USDTRY_Change is weekly/daily return.
            # Rolling 30 period sum roughly approximates 30-period return if log returns.
            # Convert to rolling 4-week return for weekly data
            window = 4 if getattr(config, 'TIMEFRAME', 'D') == 'W' else 30
            usd_rolling = df['USDTRY_Change'].rolling(window, min_periods=window).sum()
            
            crisis_score += (usd_rolling > 0.10).astype(int) * 2
            crisis_score += ((usd_rolling > 0.05) & (usd_rolling <= 0.10)).astype(int) * 1
        
        # Check 2: VIX spike
        if 'VIX_Risk' in df.columns:
            crisis_score += (df['VIX_Risk'] > 30.0).astype(int) * 2
        
        # Check 3: S&P500 momentum (global risk-off)
        if 'SP500_Return' in df.columns:
            window = 4 if getattr(config, 'TIMEFRAME', 'D') == 'W' else 30
            sp500_rolling = df['SP500_Return'].rolling(window, min_periods=window).sum()
            crisis_score += (sp500_rolling < -0.10).astype(int) * 1
            
        # Check 4: BIST30 collapse
        if 'Close' in df.columns:
            window = 4 if getattr(config, 'TIMEFRAME', 'D') == 'W' else 30
            # Rolling pct_change
            bist_rolling = df['Close'].pct_change(window)
            crisis_score += (bist_rolling < -0.10).astype(int) * 1

        # Check 5: High volatility
        scale_factor = 52 if getattr(config, 'TIMEFRAME', 'D') == 'W' else 252
        if 'Volatility_20' in df.columns:
            annual_vol = df['Volatility_20'] * np.sqrt(scale_factor)
            vol_high = self.thresholds.get('volatility_high', 0.30)
            crisis_score += (annual_vol > vol_high * 1.5).astype(int) * 1
            
        return crisis_score
    
    def detect_regimes(self, verbose=True):
        """
        Piyasa rejimlerini belirler:
        0: NORMAL (Düşük Volatilite, Stabil Kur)
        1: KRİZ (Yüksek Volatilite, CDS veya Kur Şoku + TURKEY CRISIS)
        2: RALLİ (Pozitif Trend, Düşük Risk, Yüksek Momentum)
        
        ENHANCED: Now includes Turkey-specific crisis detection (Fix 1).
        """
        df = self.data.copy() # Hata önlemek için kopya
        
        # Gerekli metriklerin varlığını kontrol et
        required_cols = ['Volatility_20', 'Close']
        if not all(col in df.columns for col in required_cols):
            if verbose: print("Eksik veri: Rejim tespiti için Volatility_20 gerekli.")
            return df
            
        # Volatilite Yıllıklandırma
        # Config'e göre ölçeklendirme faktörü
        scale_factor = 52 if getattr(config, 'TIMEFRAME', 'D') == 'W' else 252
        annual_volatility = df['Volatility_20'] * np.sqrt(scale_factor)
        
        # Parametreleri al (Varsayılanlar veya Config)
        default_high = config.REGIME_THRESHOLDS['volatility_high']
        default_low = config.REGIME_THRESHOLDS['volatility_low']
        
        if self.use_adaptive:
            # FIX: Global quantile yerine Expanding Window kullanarak leakage önle
            # Min 1 yıl (252 gün / 52 hafta) veri olsun, yoksa default kullan
            min_per = scale_factor 
            
            # Pandas expanding quantile (Bazen yavaştır ama doğru yöntem budur)
            # Alternatif: Rolling 3-5 yıl
            vol_low = annual_volatility.expanding(min_periods=min_per).quantile(0.25).fillna(default_low)
            vol_high = annual_volatility.expanding(min_periods=min_per).quantile(0.75).fillna(default_high)
            
            if verbose: print(f"  [Adaptive] Eşikler Expanding Window ile hesaplandı (Leakage-Free).")
            
        else:
            vol_high = self.thresholds.get('volatility_high', default_high)
            vol_low = self.thresholds.get('volatility_low', default_low)
        # try_high ve usd_change_5d artık kullanılmıyor (Macro Gate'e taşındı)
        mom_thresh = self.thresholds.get('momentum_threshold', 55) # Varsayılan RSI > 55
        min_days = int(self.thresholds.get('min_regime_days', 3)) # Rejim kalıcı olmalı
        
        # RSI Kontrolü (Yoksa hesapla - FeatureEngineer eklemiş olmalı ama garanti olsun)
        if 'RSI' not in df.columns:
            import pandas_ta as ta
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['RSI'] = df['RSI'].fillna(50)

        # Rejim Etiketleme
        # KRİZ: SADECE Yüksek Volatilite
        # USDTRY şoku artık rejimi değiştirmiyor, direkt "GATE" ile trade'i kilitliyor.
        # Volatilite Whipsaw Koruması
        # Ani günlük sıçramalar rejimi değiştirmesin diye 3 günlük ortalama (Smoothing)
        annual_volatility_smooth = annual_volatility.rolling(window=3).mean()
        # İlk 2 gün NaN olacağı için orijinal değerle doldur
        annual_volatility_smooth.fillna(annual_volatility, inplace=True)
        
        # ENHANCED CRISIS DETECTION (Fix 1)
        # Check Turkey-specific crisis score
        turkey_crisis_score = self.detect_turkey_crisis(df, verbose=verbose)
        
        # Rejim Etiketleme
        # KRİZ: Yüksek Volatilite OR Turkey Crisis Score >= 3
        cond_crash = (annual_volatility_smooth > vol_high) | (turkey_crisis_score >= 3)
        
        # RALLİ: Fiyat > SMA200 VE Volatilite < Kriz Eşiği VE Yüksek Momentum
        # SMA_200 yoksa hesapla
        if 'SMA_200' not in df.columns:
             df['SMA_200'] = df['Close'].rolling(200).mean()
             
        cond_rally = (
            (df['Close'] > df['SMA_200']) & 
            (annual_volatility_smooth < vol_high) & 
            (df['RSI'] > mom_thresh)
        )
        
        conditions = [cond_crash, cond_rally]
        choices = [1, 2] # 1: Kriz, 2: Ralli
        
        df['Regime_Raw'] = np.select(conditions, choices, default=0)
        
        # Detection Loop (Debounce)
        # Rejim sinyali en az 'min_days' boyunca kalıcı olmalı
        regimes_raw = df['Regime_Raw'].values
        final_regimes = np.zeros_like(regimes_raw)
        
        current_stable = 0
        candidate = 0
        candidate_count = 0
        
        for i in range(len(regimes_raw)):
            r = regimes_raw[i]
            
            if i < min_days:
                # Başlangıçta yeterli veri yok, raw değeri veya varsayılanı kabul et
                final_regimes[i] = r
                current_stable = r
                continue
                
            if r == current_stable:
                # Sinyal zaten mevcut rejimle aynı, aday sayacı sıfırla
                candidate = r
                candidate_count = 0
            else:
                # Sinyal farklı
                if r == candidate:
                    candidate_count += 1
                else:
                    # Yeni bir aday
                    candidate = r
                    candidate_count = 1
                
                # Aday yeterince süreklilik gösterdi mi?
                if candidate_count >= min_days:
                    current_stable = candidate
                    candidate_count = 0
            
            final_regimes[i] = current_stable

        df['Regime_Num'] = final_regimes
        
        # String Mapping
        regime_map = {
            0: 'Sideways',    # Normal/Yatay
            1: 'Crash_Bear',  # Kriz
            2: 'Trend_Up'     # Ralli
        }
        df['Regime'] = df['Regime_Num'].map(regime_map)
        
        # FIX 10: Regime confidence (Rejim ne kadar kesin?)
        df['Regime_Confidence'] = 0.0
        
        for i in range(len(df)):
            if i < 10:  # İlk 10 gün yetersiz veri
                df.loc[df.index[i], 'Regime_Confidence'] = 0.5
                continue
                
            # Son 10 günde rejim değişimi var mı?
            recent_regimes = df['Regime_Num'].iloc[i-10:i+1]
            regime_stability = (recent_regimes == recent_regimes.iloc[-1]).sum() / len(recent_regimes)
            
            df.loc[df.index[i], 'Regime_Confidence'] = regime_stability
        
        if verbose:
            log.info("Rejim Dağılımı:")
            log.info("%s", df['Regime'].value_counts())
        
        self.data = df
        return df

import lightgbm as lgb
import optuna
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, log_loss

from utils.logging_config import get_logger

log = get_logger(__name__)

class MLRegimeClassifier:
    def __init__(self, data, lookback_window=3):
        self.data = data.copy()
        self.lookback_window = lookback_window
        self.model = None
        self.best_params = None
        
    def prepare_features(self):
        """ML modeli için feature ve target (label) hazırlar."""
        df = self.data.copy()
        
        # 1. Ground Truth (Etiketler) - Kural tabanlıdan al
        # Mevcut RegimeDetector logic'ini kullanarak etiket üret
        # (Self-contained olması için burada basitçe tekrar çağırabilir veya dışarıdan alabiliriz)
        # Pratiklik için: RegimeDetector'un zaten çalıştırıldığını ve 'Regime_Num' 
        # sütununun eklendiğini varsayalım. Eğer yoksa rule-based çalıştırılmalı.
        if 'Regime_Num' not in df.columns:
            # Fallback: Kendi basit etiketleyicisini çalıştır
            detector = RegimeDetector(df)
            df = detector.detect_regimes(verbose=False)
            
        # Target
        y = df['Regime_Num']
        
        # 2. Features
        # Modelin geleceği görmemesi için featurelar lag'li olmalı mı?
        # Rejim tespiti "şu anki" durumu anlamak içinse lag gerekmez, 
        # ama "gelecek rejimi" tahmin etmek için gerekir.
        # "Current State Estimation".
        # Bu yüzden o anki verilere bakabiliriz (Feature Engineering zaten geçmiş veriden türetildi).
        
        # MAKRO FEATURE'LAR KALDIRILDI
        feature_cols = [
            'Volatility_20', 'ATR', 'RSI', 
             # 'USDTRY_Change', 'VIX_Risk', 'VIX_Change', 
            'Sector_Rotation', 'Sector_Rotation_Trend',
            'XBANK_Corr', 'Forward_PE', 'Debt_to_Equity'
        ]
        
        # Varsa ekle (eksik feature hatası vermesin)
        selected_features = [c for c in feature_cols if c in df.columns]
        
        if 'Close' in df.columns and 'SMA_200' in df.columns:
            df['Above_SMA200'] = (df['Close'] > df['SMA_200']).astype(int)
            selected_features.append('Above_SMA200')

        X = df[selected_features]
        
        # NaN temizliği
        valid_mask = ~X.isna().any(axis=1) & ~y.isna()
        X = X[valid_mask]
        y = y[valid_mask]
        
        return X, y

    def optimize_and_train(self, n_trials=20):
        """Optuna ile hiperparametre optimizasyonu ve eğitim."""
        X, y = self.prepare_features()
        
        if len(X) < 100:
            log.info("Yetersiz veri, ML eğitimi atlanıyor.")
            return None
            
        def objective(trial):
            params = {
                'objective': 'multiclass',
                'num_class': 3,
                'metric': 'multi_logloss',
                'verbosity': -1,
                'boosting_type': 'gbdt',
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1),
                'num_leaves': trial.suggest_int('num_leaves', 20, 100),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'reg_alpha': trial.suggest_float('reg_alpha', 0.1, 1.0),
                'reg_lambda': trial.suggest_float('reg_lambda', 0.1, 1.0),
                'min_child_samples': trial.suggest_int('min_child_samples', 10, 50),
                'n_estimators': 300
            }
            
            # TimeSeries CV
            tscv = TimeSeriesSplit(n_splits=5)
            scores = []
            
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                # Check if all classes exist in train (safety)
                # Multi-class lightgbm requires classes to be 0,1,2... 
                # If a class is missing, it might error or warn. 
                
                dtrain = lgb.Dataset(X_train, label=y_train)
                dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)
                
                model = lgb.train(
                    params, dtrain, 
                    valid_sets=[dval], 
                    callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False), lgb.log_evaluation(0)]
                )
                
                preds = model.predict(X_val)
                # preds is probability matrix
                val_loss = log_loss(y_val, preds, labels=[0, 1, 2])
                scores.append(val_loss)
                
            return np.mean(scores)

        log.info("Regime Classifier Hiperparametre Optimizasyonu Başlıyor...")
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=n_trials)
        
        self.best_params = study.best_params
        self.best_params.update({
            'objective': 'multiclass',
            'num_class': 3,
            'metric': 'multi_logloss',
            'verbosity': -1,
            'n_estimators': 500
        })
        
        log.info(f"En iyi parametreler: {self.best_params}")
        
        # Final Model Eğitimi (Tüm veri ile)
        dtrain = lgb.Dataset(X, label=y)
        self.model = lgb.train(self.best_params, dtrain)
        
        return self.model

    def predict_regime(self, current_features):
        """Canlı/Tekil veri için tahmin yapar."""
        if self.model is None:
            return None
            
        # Feature sırası eşleşmeli... (Production grade kodda feature name check gerekir)
        # Şimdilik feature preparation logic'i tekrar çalıştıramayız tek satır için kolayca.
        # Basitleştirme: X columns'ı saklayıp ona göre input bekleyelim.
        pass 
        
    def predict_proba(self, X):
        if self.model is None: return None
        return self.model.predict(X)

