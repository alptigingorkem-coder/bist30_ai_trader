#!/usr/bin/env python3
"""
Daily Sharpe Calculator
Calculates daily Sharpe ratio from paper trading performance
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


def calculate_daily_sharpe():
    """Calculate daily Sharpe ratio."""
    print("=" * 70)
    print("📊 GÜNLÜK SHARPE RATIO HESAPLAMA")
    print("=" * 70)
    
    # Performance dosyasını oku
    perf_file = Path('data/paper_trading/daily_performance.csv')
    
    if not perf_file.exists():
        print("\n⚠️ Performance dosyası bulunamadı!")
        print("💡 Henüz yeterli veri yok.")
        return
    
    try:
        df = pd.read_csv(perf_file)
        
        if len(df) < 2:
            print("\n⚠️ Sharpe hesaplamak için en az 2 günlük veri gerekli.")
            return
        
        # Günlük getiriyi hesapla
        df['daily_return'] = df['equity'].pct_change()
        
        # Sharpe ratio hesapla (risk-free rate = 0 varsayımı)
        mean_return = df['daily_return'].mean()
        std_return = df['daily_return'].std()
        
        if std_return > 0:
            sharpe = (mean_return / std_return) * np.sqrt(252)  # Annualized
        else:
            sharpe = 0
        
        # Kümülatif getiri
        cumulative_return = ((df['equity'].iloc[-1] / df['equity'].iloc[0]) - 1) * 100
        
        # Max drawdown
        cummax = df['equity'].cummax()
        drawdown = (df['equity'] - cummax) / cummax
        max_dd = drawdown.min() * 100
        
        print(f"\n📊 Günlük Sharpe Ratio: {sharpe:.2f}")
        print(f"📈 Kümülatif Getiri: {cumulative_return:+.2f}%")
        print(f"📉 Max Drawdown: {max_dd:.2f}%")
        print(f"📅 Veri Günü: {len(df)}")
        
        # Değerlendirme
        print("\n🎯 Değerlendirme:")
        if sharpe > 1.5:
            print("   ✅ Mükemmel! Hedefin üzerinde.")
        elif sharpe > 1.0:
            print("   🟢 İyi! Hedefe yakın.")
        elif sharpe > 0.5:
            print("   🟡 Orta. İyileştirme gerekebilir.")
        else:
            print("   🔴 Zayıf. Ciddi iyileştirme gerekli.")
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")


if __name__ == "__main__":
    calculate_daily_sharpe()
