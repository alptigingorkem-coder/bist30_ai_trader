#!/usr/bin/env python3
"""
Daily Loss Checker
Checks if daily loss exceeds threshold
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def check_daily_loss(threshold=5.0):
    """Check if daily loss exceeds threshold."""
    print("=" * 70)
    print("🚨 GÜNLÜK KAYIP KONTROLÜ")
    print("=" * 70)
    print(f"Eşik: {threshold}%")
    print("=" * 70)
    
    # Performance dosyasını oku
    perf_file = Path('data/paper_trading/daily_performance.csv')
    
    if not perf_file.exists():
        print("\n⚠️ Performance dosyası bulunamadı!")
        return
    
    try:
        df = pd.read_csv(perf_file)
        
        if len(df) < 2:
            print("\n⚠️ Günlük getiri hesaplamak için en az 2 günlük veri gerekli.")
            return
        
        # Son günün getirisini hesapla
        last_equity = df['equity'].iloc[-1]
        prev_equity = df['equity'].iloc[-2]
        
        daily_return = ((last_equity / prev_equity) - 1) * 100
        
        print(f"\n📊 Bugünkü Getiri: {daily_return:+.2f}%")
        
        if daily_return < -threshold:
            print(f"\n🚨 UYARI: Günlük kayıp eşiği aşıldı!")
            print(f"   Kayıp: {daily_return:.2f}%")
            print(f"   Eşik: -{threshold}%")
            print("\n🛑 ÖNERİLEN AKSIYONLAR:")
            print("   1. Sistemi durdur")
            print("   2. Logları incele")
            print("   3. Sorunu tespit et")
            print("   4. Parametreleri ayarla")
            print("   5. Yeniden başlat")
        elif daily_return < 0:
            print(f"\n🟡 Bugün kayıp var ama eşik altında.")
            print(f"   İzlemeye devam et.")
        else:
            print(f"\n✅ Bugün kar var. Sistem normal çalışıyor.")
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")


if __name__ == "__main__":
    check_daily_loss()
