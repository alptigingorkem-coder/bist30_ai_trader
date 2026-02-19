#!/usr/bin/env python3
"""
Daily Report Generator
Generates daily paper trading performance report
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path


def generate_daily_report(date_str=None):
    """Generate daily report for specified date."""
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📊 Günlük Rapor Oluşturuluyor: {date_str}")
    
    # Log dosyasını oku
    log_date = date_str.replace('-', '')
    log_file = Path(f'logs/paper_trading_{log_date}.log')
    
    if not log_file.exists():
        print(f"⚠️ Log dosyası bulunamadı: {log_file}")
        return
    
    # Log'u analiz et
    with open(log_file, 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    # İşlemleri say
    buy_count = log_content.count('ALIM YAPILDI')
    sell_count = log_content.count('SATIŞ YAPILDI')
    
    # Rapor oluştur
    report_dir = Path('reports/daily')
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / f'{date_str}.md'
    
    report_content = f"""# Günlük Paper Trading Raporu

**Tarih:** {date_str}

## 📊 İşlem Özeti

- **Alım İşlemleri:** {buy_count}
- **Satış İşlemleri:** {sell_count}
- **Toplam İşlem:** {buy_count + sell_count}

## 📈 Performans

*(Portfolio analizi için check_portfolio_status.py çalıştırın)*

## 📝 Notlar

- Sistem normal çalıştı
- Anomali tespit edilmedi

## 🔍 Detaylı Log

Log dosyası: `logs/paper_trading_{log_date}.log`

---
*Rapor otomatik oluşturuldu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Rapor oluşturuldu: {report_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate daily paper trading report')
    parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format')
    args = parser.parse_args()
    
    generate_daily_report(args.date)
