from config import *

# --- BANKING SINIFI ÖZEL AYARLARI ---
# Bu ayarlar ana config.py dosyasındaki değerleri ezer.

# Hisseler (Sadece Bankacılık ve Finans)
TICKERS = ["AKBNK.IS", "GARAN.IS", "YKBNK.IS", "ISCTR.IS", "TSKB.IS", "HALKB.IS", "VAKBN.IS", "ALBRK.IS"]
SECTOR_NAME = "BANKING"

# --- ÖZELLİK MÜHENDİSLİĞİ ODAK NOKTALARI ---
# Bankalar makro verilere ve faiz kararlarına çok duyarlıdır.
FEATURE_FOCUS = [
    'XBANK',            # Bankacılık Endeksi (Momentum)
    'USDTRY',           # Dolar Kuru (Kur Farkı Gelirleri/Riskleri)
    'VIX',              # Global Risk İştahı
    'RSI',              # Aşırı Alım/Satım
    'MACD',             # Trend Takibi
    'Return_Lag_4w',    # Aylık Momentum
    'Sector_Rotation',  # Sektörel Para Girişi (XU100/XBANK Oranı)
    'Tahvil_Faizi'      # (Opsiyonel) Eğer varsa 10 yıllık tahvil faizi
]

# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Bankalar volatilitesi yüksek olduğu için eşikler daha geniştir.
REGIME_THRESHOLDS = {
    "volatility_low": 0.22,      # Düşük volatilite (Yatay/Ralli başlangıcı)
    "volatility_high": 0.55,     # Yüksek volatilite (Kriz/Panik)
    "try_change_high": 0.008,    # Kur şoku eşiği (Haftalık %0.8 üzeri kritik)
    "min_regime_days": 4         # Rejim değişimi için gereken minimum gün sayısı
}

# --- MODEL AĞIRLIKLARI (HİBRİT YAPI) ---
# Trend zamanlarında Beta (Piyasa Takibi) baskın.
# Yatay piyasada Alpha (Hisse Seçimi) devreye girer.
BETA_ALPHA_RATIO = {
    'beta': 0.85,  # %85 Ana Model (Trend Takibi)
    'alpha': 0.15  # %15 Yan Model (Ayrışma)
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.008  # Haftalık %0.8 altı getiri tahminine işlem açma (Komisyon + Slippage)
KELLY_FRACTION = 0.6          # Tam Kelly çok riskli, %60'ı kullanılır.
STOP_LOSS_ATR = 1.5           # Sıkı Stop-Loss
TAKE_PROFIT_ATR = 3.0         # Geniş Kar Al

# Loglama için önek
LOG_PREFIX = "[BANKING_STRATEGY]"
