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
# --- REJİM SINIFLANDIRMA EŞİKLERİ ---
# Bankalar volatilitesi yüksek olduğu için eşikler daha geniştir.
REGIME_THRESHOLDS = {
    "volatility_low": 0.20,      # 0.22 -> 0.20
    "volatility_high": 0.50,     # 0.55 -> 0.50 (Daha erken Crash tespiti)
    "try_change_high": 0.008,    # Kur şoku eşiği (Haftalık %0.8 üzeri kritik)
    "min_regime_days": 3         # 4 -> 3 (Rejim değişimine daha hızlı tepki)
}

# --- MODEL AĞIRLIKLARI (HİBRİT YAPI) ---
# Trend zamanlarında Beta (Piyasa Takibi) baskın.
# Yatay piyasada Alpha (Hisse Seçimi) devreye girer.
BETA_ALPHA_RATIO = {
    'beta': 0.75,  # 0.85 -> 0.75 (Hisse seçiminin etkisi artırıldı)
    'alpha': 0.25  # 0.15 -> 0.25
}

# --- RİSK YÖNETİMİ ---
MIN_RETURN_THRESHOLD = 0.008  # Haftalık %0.8 altı getiri tahminine işlem açma (Komisyon + Slippage)
KELLY_FRACTION = 0.5          # 0.6 -> 0.5 (Risk azaltıldı)
STOP_LOSS_ATR = 1.4           # 1.5 -> 1.4 (Çok sıkı Stop-Loss)
TAKE_PROFIT_ATR = 2.8         # 3.0 -> 2.8 (Karı daha güvenli al)

# Loglama için önek
LOG_PREFIX = "[BANKING_STRATEGY]"
