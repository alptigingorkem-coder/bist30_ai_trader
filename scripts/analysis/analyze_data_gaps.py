
import sys
import os
import pandas as pd
import yfinance as yf
from datetime import datetime

# Proje kök dizinini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

def analyze_gaps():
    print("=== Veri Eksikliği ve Sentetik Veri İhtiyacı Analizi ===")
    print(f"Hedeflenen Başlangıç Tarihi: {config.START_DATE}")
    
    target_start = pd.to_datetime(config.START_DATE)
    report_data = []
    
    tickers = config.TICKERS
    
    for ticker in tickers:
        print(f"Analiz ediliyor: {ticker}...")
        try:
            # Sadece tarih bilgisi için hızlı indirme (sonraki adımda detaylı bakabiliriz ama şimdilik yf yeterli)
            # metadata'dan ilk tarihi almaya çalışalım veya max periyot indirelim
            # yfinance history(period="max") en garantisi
            stock = yf.Ticker(ticker)
            hist = stock.history(period="max")
            
            if hist.empty:
                print(f"  UYARI: {ticker} için veri bulunamadı!")
                report_data.append({
                    'Ticker': ticker,
                    'First_Data_Date': 'N/A',
                    'Gap_Days': 'N/A',
                    'Needs_Synthetic': 'Unknown',
                    'Status': 'No Data'
                })
                continue
                
            first_date = hist.index.min().tz_localize(None)
            last_date = hist.index.max().tz_localize(None)
            
            # Gap Hesabı
            gap_days = (first_date - target_start).days
            
            needs_synthetic = False
            if first_date > target_start:
                needs_synthetic = True
                status = f"MISSING {gap_days} DAYS"
            else:
                status = "OK"
                
            report_data.append({
                'Ticker': ticker,
                'Ref_Start_Date': config.START_DATE,
                'Actual_Start_Date': first_date.strftime('%Y-%m-%d'),
                'Gap_Days': gap_days if gap_days > 0 else 0,
                'Needs_Synthetic': 'YES' if needs_synthetic else 'NO',
                'Status': status
            })
            
        except Exception as e:
            print(f"  HATA: {ticker} - {e}")

    # Raporlama
    df_report = pd.DataFrame(report_data)
    
    print("\n\n=== SONUÇ RAPORU ===")
    # Sadece sorunu olanları göster
    problematic = df_report[df_report['Needs_Synthetic'] == 'YES']
    
    if not problematic.empty:
        print(problematic.to_string(index=False))
        print(f"\nToplam {len(problematic)} hissede veri eksikliği var (Hedef: {config.START_DATE}).")
    else:
        print("Tüm hisselerin verisi hedef tarihten önce başlıyor. Eksik yok.")

    # Tam listeyi CSV kaydet
    df_report.to_csv("reports/data_gap_analysis.csv", index=False)
    print("\nDetaylı rapor 'reports/data_gap_analysis.csv' dosyasına kaydedildi.")

if __name__ == "__main__":
    analyze_gaps()
