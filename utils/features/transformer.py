"""
Transformer (TFT) Mixin'i
Temporal Fusion Transformer için özel feature'lar ve dataset konfigürasyonu.
"""


class TransformerMixin:
    """TFT transformer feature metotlarını sağlayan mixin."""

    def add_transformer_features(self):
        """TFT için özel feature'lar"""
        df = self.data

        # Zamansal feature'lar
        if 'DayOfWeek' not in df.columns:
            df['DayOfWeek'] = df.index.dayofweek
        if 'Month' not in df.columns:
            df['Month'] = df.index.month
        if 'Quarter' not in df.columns:
            df['Quarter'] = df.index.quarter

        # Makro şok göstergeleri
        if 'usdtry' in df.columns:
            df['usdtry_shock'] = (df['usdtry'].pct_change() > 0.02).astype(int)
        elif 'USDTRY' in df.columns:
            df['usdtry_shock'] = (df['USDTRY'].pct_change() > 0.02).astype(int)

        if 'vix' in df.columns:
            df['vix_high'] = (df['vix'] > 25).astype(int)
        elif 'VIX' in df.columns:
            df['vix_high'] = (df['VIX'] > 25).astype(int)

        # Trend strength
        if 'SMA_20' in df.columns:
            df['price_vs_sma20'] = df['Close'] / df['SMA_20'] - 1

        if 'Volume' in df.columns:
            vol_ma = df['Volume'].rolling(20).mean()
            df['volume_surge'] = df['Volume'] / (vol_ma + 1e-9)

        self.data = df
        return df


def prepare_tft_dataset(df, lookback=60, target_col='Excess_Return'):
    """
    TFT modeli için dataset konfigürasyonunu hazırlar.
    df: (timestamp, features) DataFrame
    lookback: Kaç günlük geçmiş kullanılacak
    target_col: Hedef sütun adı
    """
    static_features = []
    if 'Sector' in df.columns:
        static_features.append('Sector')

    time_varying_known = ['DayOfWeek', 'Month']
    for col in ['usdtry', 'USDTRY', 'vix', 'VIX', 'usdtry_shock', 'vix_high']:
        if col in df.columns:
            time_varying_known.append(col)

    potential_unknowns = ['Close', 'Volume', 'RSI', 'MACD', 'price_vs_sma20', 'volume_surge', 'Log_Return', 'Volatility_20']
    time_varying_unknown = [c for c in potential_unknowns if c in df.columns]

    target = target_col
    if target not in df.columns:
        if 'NextDay_Return' in df.columns:
             target = 'NextDay_Return'
        elif 'Log_Return' in df.columns:
             target = 'Log_Return'

    return {
        'static': static_features,
        'known': time_varying_known,
        'unknown': time_varying_unknown,
        'target': target,
        'max_encoder_length': lookback,
        'max_prediction_length': 1
    }
