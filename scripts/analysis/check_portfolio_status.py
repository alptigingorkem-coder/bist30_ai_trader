#!/usr/bin/env python3
"""
Portfolio Status Checker
Displays current paper trading portfolio status
"""

import json
from pathlib import Path
from datetime import datetime


def check_portfolio_status():
    """Check and display current portfolio status."""
    print("=" * 70)
    print("💼 PAPER TRADING PORTFOLIO DURUMU")
    print("=" * 70)
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Portfolio state dosyasını oku
    portfolio_file = Path('data/paper_trading/portfolio_state.json')
    
    if not portfolio_file.exists():
        print("\n⚠️ Portfolio dosyası bulunamadı!")
        print("💡 Paper trading henüz başlatılmamış olabilir.")
        return
    
    try:
        with open(portfolio_file, 'r') as f:
            portfolio = json.load(f)
        
        # Nakit
        cash = portfolio.get('cash', 0)
        print(f"\n💰 Nakit: {cash:,.2f} TL")
        
        # Pozisyonlar
        holdings = portfolio.get('holdings', {})
        if holdings:
            print(f"\n📈 Pozisyonlar: {len(holdings)} adet")
            total_position_value = 0
            
            for ticker, qty in holdings.items():
                # Güncel fiyatı al (basitleştirilmiş)
                estimated_value = qty * 50  # Placeholder
                total_position_value += estimated_value
                print(f"   - {ticker}: {qty} hisse (~{estimated_value:,.0f} TL)")
            
            print(f"\n💼 Toplam Pozisyon Değeri: {total_position_value:,.2f} TL")
        else:
            print(f"\n📈 Pozisyonlar: Yok")
            total_position_value = 0
        
        # Toplam değer
        total_equity = cash + total_position_value
        initial_capital = portfolio.get('initial_capital', 10000)
        
        print(f"\n💎 Toplam Değer: {total_equity:,.2f} TL")
        print(f"📊 Başlangıç Sermayesi: {initial_capital:,.2f} TL")
        
        # Getiri
        total_return = ((total_equity - initial_capital) / initial_capital) * 100
        print(f"📈 Toplam Getiri: {total_return:+.2f}%")
        
        # Performans göstergesi
        if total_return > 5:
            print("\n✅ Performans: Mükemmel!")
        elif total_return > 0:
            print("\n🟢 Performans: İyi")
        elif total_return > -5:
            print("\n🟡 Performans: Orta")
        else:
            print("\n🔴 Performans: Zayıf")
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")


if __name__ == "__main__":
    check_portfolio_status()
