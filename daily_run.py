import os
import warnings
import time
from datetime import datetime
import pandas as pd
import numpy as np
import joblib

# Proje Modülleri
import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer

# Position Aware Modülleri
from paper_trading.position_engine import PositionEngine
from paper_trading.portfolio_state import PortfolioState
from paper_trading.strategy_health import check_strategy_health, StrategyHealth
from core.risk_manager import RiskManager

warnings.filterwarnings("ignore")

# --------------------------------------------------
# UTILS & UI
# --------------------------------------------------

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_production_model():
    """En iyi modeli otomatik bulur ve yükler."""
    model_path = "models/saved/global_ranker_catboost.cbm"
    if os.path.exists(model_path):
        from catboost import CatBoostClassifier
        model = CatBoostClassifier()
        model.load_model(model_path)
        print(f"✅ CatBoost Modeli Yüklendi: {model_path}")
        return model

    fallback = "models/saved/global_ranker.pkl"
    if os.path.exists(fallback):
        model = joblib.load(fallback)
        print(f"⚠️ Yedek model yüklendi: {fallback}")
        return model

    raise FileNotFoundError("❌ Üretim modeli bulunamadı")

# --------------------------------------------------
# MAIN SNIPER RUN
# --------------------------------------------------

def run_daily_trader():
    clear_screen()
    print("\033[1;36m" + "=" * 70)
    print("🎯 BIST30 SNIPER - HYBRID LIVE TRADER (v3.0)")
    print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\033[0m")

    # 1. STATE LOAD
    print("📥 Portföy durumu yükleniyor...")
    portfolio = PortfolioState.load()
    risk_manager = RiskManager()
    engine = PositionEngine(portfolio_state=portfolio, risk_manager=risk_manager)
    
    current_positions = list(portfolio.positions.keys())
    print(f"💼 Mevcut Pozisyonlar: {current_positions if current_positions else 'Nakit'}")

    # ─────────────────────────────────────────────────────────────
    # 🏥 FAZ 5: STRATEGY HEALTH CHECK (Trade öncesi kontrol)
    # ─────────────────────────────────────────────────────────────
    print("\n🏥 Strateji sağlık kontrolü...")
    can_trade, health_msg, recommendations = check_strategy_health(portfolio)
    
    # Durum göster
    state_icon = {"ACTIVE": "🟢", "DEGRADED": "🟡", "PAUSED": "🟠", "DISABLED": "🔴", "PAPER_ONLY": "📄"}.get(
        recommendations.get("state", "ACTIVE"), "⚪"
    )
    print(f"{state_icon} Strategy State: {recommendations.get('state', 'ACTIVE')}")
    print(f"   {health_msg}")
    
    # PAUSED veya DISABLED ise durdur
    if not can_trade:
        print("\n" + "="*70)
        print("🛑 STRATEJİ DURDURULDU - Trade yapılamaz!")
        print(f"   Sebep: {health_msg}")
        print("   Manuel müdahale gerekli. strategy_health.py ile durumu inceleyin.")
        print("="*70)
        return  # Exit without trading
    
    # Position size multiplier uygula
    position_size_multiplier = recommendations.get("position_size_multiplier", 1.0)
    if position_size_multiplier < 1.0:
        print(f"   ⚠️ Position size küçültüldü: {position_size_multiplier*100:.0f}%")

    # 2. DATA DOWNLOAD (Gecikmeli)
    print("⏳ [1/5] Geçmiş veriler indiriliyor (yfinance)...")
    loader = DataLoader(config.TICKERS)
    raw_data = loader.download_data(period="1y")

    # 3. PRE-SCAN (Aday Belirleme)
    print("⏳ [2/5] Ön analiz yapılıyor (Aday tespiti)...")
    # Gecikmeli veriyle hızlı bir feature hesabı yapıp potansiyel adayları bulalım
    # Amacımız 30 hissenin hepsini sormamak, sadece Portfolio + Top Adayları sormak.
    pre_engineer = FeatureEngineer(raw_data)
    pre_features = pre_engineer.process_all()
    
    model = load_production_model()
    
    # Bugünün (gecikmeli) verisiyle tahmin
    last_date = pre_features.index[-1]
    X_pre = pre_features.loc[last_date][model.feature_names_]
    scores_pre = model.predict_proba(X_pre)[:, 1]
    
    pre_score_df = pd.DataFrame({
        "symbol": X_pre.index,
        "score": scores_pre
    }).sort_values("score", ascending=False)
    
    # LİSTE OLUŞTURMA: Mevcut Portföy + En yüksek skorlu 7 hisse
    top_candidates = pre_score_df.head(7)["symbol"].tolist()
    focus_list = list(set(current_positions + top_candidates))
    
    print(f"\n\033[1;33m⚠️ ODAK LİSTESİ BELİRLENDİ ({len(focus_list)} Hisse)")
    print("Sistemin doğru çalışması için bu hisselerin CANLI fiyatlarını girmelisiniz.\033[0m")
    
    # 4. LIVE PRICE INJECTION (Kullanıcı Girişi)
    live_prices = {}
    print("-" * 50)
    
    for ticker in focus_list:
        # Mevcut (gecikmeli) fiyatı referans göster
        delayed_price = raw_data.loc[raw_data.index[-1], ('Close', ticker)]
        
        while True:
            try:
                user_input = input(f"📊 {ticker:<10} (Ref: {delayed_price:.2f}) 👉 Canlı: ")
                
                if user_input.strip() == "":
                    # Boş geçilirse gecikmeli veriyi kabul et
                    live_prices[ticker] = delayed_price
                    print(f"   -> Gecikmeli veri kullanıldı: {delayed_price:.2f}")
                else:
                    price = float(user_input.replace(',', '.'))
                    live_prices[ticker] = price
                break
            except ValueError:
                print("❌ Hata: Sayısal değer girin (Örn: 305.5)")

    print("-" * 50)
    print("⏳ [3/5] Veriler güncelleniyor ve indikatörler yeniden hesaplanıyor...")

    # --- KRİTİK ADIM: Raw Data Update ---
    # Kullanıcının girdiği fiyatları ham verinin son satırına enjekte et
    last_idx = raw_data.index[-1]
    
    for ticker, price in live_prices.items():
        # Kapanış fiyatını güncelle
        raw_data.loc[last_idx, ('Close', ticker)] = price
        
        # High/Low tutarlılığı sağla (Mum barını bozmamak için)
        if price > raw_data.loc[last_idx, ('High', ticker)]:
            raw_data.loc[last_idx, ('High', ticker)] = price
        if price < raw_data.loc[last_idx, ('Low', ticker)]:
            raw_data.loc[last_idx, ('Low', ticker)] = price
            
    # 5. RE-PROCESS & PREDICT (Canlı Veriyle)
    # Feature Engineering'i GÜNCEL veriyle tekrar çalıştır
    final_engineer = FeatureEngineer(raw_data)
    final_features = final_engineer.process_all()
    
    today_features = final_features.loc[last_idx]
    
    # Model Tahmini (Final)
    X_final = today_features[model.feature_names_]
    final_scores = model.predict_proba(X_final)[:, 1]
    
    final_score_df = pd.DataFrame({
        "symbol": X_final.index,
        "score": final_scores
    }).sort_values("score", ascending=False)
    
    # 6. TARGET WEIGHTS
    MAX_POSITIONS = 5
    MIN_SCORE = 0.55 # Güven eşiği

    top_picks = final_score_df[final_score_df["score"] >= MIN_SCORE].head(MAX_POSITIONS)
    
    desired_positions = []
    
    print("\n" * 2)
    print(f"\033[1;32m{'='*20} 🚀 FİNAL SİNYALLER 🚀 {'='*20}\033[0m")
    
    if top_picks.empty:
        print("⚠️ Uygun sinyal bulunamadı. Nakitte kalınıyor.")
    else:
        # Ağırlıklandırma (Score bazlı)
        total_score = top_picks["score"].sum()
        top_picks["target_weight"] = (top_picks["score"] / total_score) * position_size_multiplier
        
        desired_positions = top_picks.to_dict("records")
        
        for d in desired_positions:
            score_str = f"{d['score']:.2f}"
            if d['score'] > 0.75: score_str += " 🔥"
            print(f" - {d['symbol']:<10} | Skor: {score_str:<8} | Hedef %: {d['target_weight']*100:.1f}")

    # 7. POSITION ENGINE EXECUTION
    print("\n⚙️ [4/5] Emirler işleniyor (Position Engine)...")
    
    # Engine'e sinyalleri gönder
    for signal in desired_positions:
        # Fiyat bilgisini canlı listeden veya raw_data'dan al
        current_price = raw_data.loc[last_idx, ('Close', signal['symbol'])]
        
        engine.process_signal(
            symbol=signal["symbol"],
            target_weight=signal["target_weight"],
            confidence=signal["score"],
            price=current_price
        )
        
    # 8. CLEANUP (Çıkışlar)
    print("\n🧹 [5/5] Portföy temizliği ve çıkışlar...")
    allowed_symbols = [d["symbol"] for d in desired_positions]
    
    # Engine, listede olmayanları satacak (Ancak fiyat lazım)
    # Fiyatları raw_data'dan çekebilmesi için engine'e fiyat sözlüğü veya logic lazım
    # PositionEngine içindeki close logic genellikle son fiyata ihtiyaç duyar.
    # Burada basitçe listede olmayanları kapatırken o anki (güncellenmiş) fiyatı kullanmasını sağlayalım.
    
    # Not: engine.close_unwanted_positions genellikle sembol listesi alır, 
    # satış fiyatını içeride yönetir. Eğer senin engine kodun fiyat parametresi alıyorsa burayı güncelle.
    # Senin mevcut yapında engine.close_unwanted_positions(allowed_symbols) var.
    # Biz burada manuel bir müdahale ekleyelim: Satılacakları bulup process_signal(weight=0) gönderelim.
    # Böylece fiyatı da biz veririz.
    
    for symbol in current_positions:
        if symbol not in allowed_symbols:
            exit_price = raw_data.loc[last_idx, ('Close', symbol)]
            print(f"🚫 {symbol} için çıkış sinyali (Güven: Düşük)")
            engine.process_signal(
                symbol=symbol,
                target_weight=0.0, # Tam çıkış
                confidence=0.0,
                price=exit_price
            )

    # State Save
    portfolio.save()
    
    print("\n✅ GÜNLÜK İŞLEM TAMAMLANDI.")
    print(f"📊 Son Portföy Değeri: {portfolio.total_equity:.2f} TL")
    print(f"\033[1;31m⚠️ Lütfen yukarıdaki emirleri 18:00'a kadar Borsa'ya giriniz!\033[0m")

if __name__ == "__main__":
    try:
        run_daily_trader()
    except KeyboardInterrupt:
        print("\n🛑 Kullanıcı tarafından durduruldu.")
    except Exception as e:
        print(f"\n❌ BEKLENMEYEN HATA: {e}")