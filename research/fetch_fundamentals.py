import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
import pandas as pd
import numpy as np
import config
import time

def ensure_data_dir():
    if not os.path.exists("data"):
        os.makedirs("data")

def fetch_and_calculate_fundamentals():
    print("Temel Analiz Verileri Toplanıyor... (Bu işlem biraz sürebilir)")
    
    all_fundamentals = []
    
    tickers = config.TICKERS
    # tickers = ["KCHOL.IS", "GARAN.IS"] # Test için
    
    for ticker in tickers:
        print(f"\nProcessing {ticker}...")
        try:
            stock = yf.Ticker(ticker)
            
            # 1. Finansal Tabloları Çek (Quarterly)
            # Balance Sheet: Equity, Shares
            # Income Stmt: Net Income, EBITDA, Revenue
            
            bs = stock.quarterly_balance_sheet
            inc = stock.quarterly_income_stmt
            hist = stock.history(period="5y") # Fiyat verisi (5 yıllık)
            
            if bs.empty or inc.empty or hist.empty:
                print(f"  [UYARI] {ticker} için finansal tablo veya fiyat verisi eksik.")
                continue
                
            # Transpose yap (Tarihler satır olsun)
            bs = bs.T
            inc = inc.T
            
            # Tarihleri timezone-naive yap (karşılaştırma için)
            bs.index = pd.to_datetime(bs.index).tz_localize(None)
            inc.index = pd.to_datetime(inc.index).tz_localize(None)
            hist.index = pd.to_datetime(hist.index).tz_localize(None)
            
            # Ortak tarihleri bul (Finansal tabloların tarihleri)
            # Genellikle bilanço tarihleri dönem sonudur (31 Mart, 30 Haziran...)
            # Ancak yfinance bazen raporlama tarihini verebilir.
            
            # Income Statement verilerini al
            financials = pd.DataFrame(index=inc.index)
            
            # Sütun isimleri bazen değişebilir, güvenli erişim
            try: 
                financials['Net_Income'] = inc['Net Income'] 
                financials['Total_Revenue'] = inc['Total Revenue']
                
                if 'EBITDA' in inc.columns:
                    financials['EBITDA'] = inc['EBITDA']
                elif 'Normalized EBITDA' in inc.columns:
                    financials['EBITDA'] = inc['Normalized EBITDA']
                else:
                    # Basit proxy: Operating Income + Depreciation (yoksa 0)
                    financials['EBITDA'] = inc.get('Operating Income', 0)
            except KeyError as e:
                print(f"  [HATA] {ticker} Gelir tablosu sütun hatası: {e}")
                continue

            # Balance Sheet verilerini al
            try:
                # Tarihleri eşleştirmek gerekebilir ama varsayılan olarak aynı çeyrekler gelir
                # BS ve INC indexleri aynı mı kontrol et, değilse merge
                if not bs.index.equals(inc.index):
                     # Indexler farklıysa merge (outer join) veya reindex
                     # Basitlik için sadece BS'deki tarihleri kullanalım
                     pass
                
                financials['Stockholders_Equity'] = bs['Stockholders Equity']
                # Share Issued veya Ordinary Shares Number
                if 'Share Issued' in bs.columns:
                     financials['Shares_Outstanding'] = bs['Share Issued']
                elif 'Ordinary Shares Number' in bs.columns:
                     financials['Shares_Outstanding'] = bs['Ordinary Shares Number']
                else:
                     # Statik info'dan al (son çare)
                     financials['Shares_Outstanding'] = stock.info.get('sharesOutstanding', np.nan)
                     
            except KeyError as e:
                 print(f"  [HATA] {ticker} Bilanço sütun hatası: {e}")
                 # continue # Equity olmadan devam edilemez
            
            # Hesaplamalar
            financials = financials.sort_index() # Eskiden yeniye
            
            # TTM (Trailing 12 Months) Hesaplamaları - 4 çeyrek toplamı
            financials['Net_Income_TTM'] = financials['Net_Income'].rolling(window=4).sum()
            financials['EBITDA_TTM'] = financials['EBITDA'].rolling(window=4).sum()
            financials['Revenue_TTM'] = financials['Total_Revenue'].rolling(window=4).sum()
            
            # Rasyoları Hesapla (Tarihsel Fiyat ile)
            for date in financials.index:
                # O tarihteki veya en yakın önceki fiyatı bul
                try:
                    # Bilanço açıklandığında fiyat neydi? (Bilanço tarihinden 1-2 ay sonra açıklanır ama
                    # biz bilanço dönem sonu fiyatına göre veya o günkü fiyata göre bakabiliriz.
                    # P/E genellikle "Anlık Fiyat / Son 4 Çeyrek Kar" dır.
                    # Bilanço tarihini kullanırsak "Look-ahead bias" olabilir çünkü bilanço o gün açıklanmadı.
                    # Ancak tarihsel veri seti oluştururken "o çeyreğin verisi" olarak kaydedip, 
                    # modelde "Lag" (gecikme) vererek kullanacağız. Yani feature engineering'de
                    # bu veriyi 2-3 ay sonrasına kaydırarak (shift) kullanmak doğru olandır.
                    # Burada "Dönem Sonu" değerlerini hesaplayıp kaydedelim.
                    
                    price_at_date = hist.loc[hist.index <= date]['Close'].iloc[-1]
                except IndexError:
                    # Fiyat verisi yoksa
                    continue
                
                shares = financials.loc[date, 'Shares_Outstanding']
                equity = financials.loc[date, 'Stockholders_Equity']
                net_income_ttm = financials.loc[date, 'Net_Income_TTM']
                ebitda = financials.loc[date, 'EBITDA'] # Çeyreklik
                revenue = financials.loc[date, 'Total_Revenue'] # Çeyreklik
                
                # EPS
                if shares > 0:
                    eps_ttm = net_income_ttm / shares
                    book_value_per_share = equity / shares
                else:
                    eps_ttm = 0
                    book_value_per_share = 0
                
                # P/E (F/K)
                pe_ratio = price_at_date / eps_ttm if eps_ttm > 0 else np.nan
                
                # P/B (PD/DD)
                pb_ratio = price_at_date / book_value_per_share if book_value_per_share > 0 else np.nan
                
                # EBITDA Margin (Çeyreklik)
                ebitda_margin = ebitda / revenue if revenue > 0 else np.nan
                
                # Kayıt
                all_fundamentals.append({
                    'Ticker': ticker,
                    'Date': date,
                    'Price': price_at_date,
                    'Net_Income_TTM': net_income_ttm,
                    'Equity': equity,
                    'Forward_PE': pe_ratio, # Aslında Trailing PE bu, ama modelde Forward_PE column ismi kullanılıyor
                    'PB_Ratio': pb_ratio,
                    'EBITDA_Margin': ebitda_margin,
                    'Shares': shares
                })
                
            print(f"  {len(financials)} dönem verisi eklendi.")
            time.sleep(1) # API limitini zorlamamak için
            
        except Exception as e:
            print(f"  [GENEL HATA] {ticker}: {e}")

    # DataFrame Oluştur
    df_fund = pd.DataFrame(all_fundamentals)
    
    if not df_fund.empty:
        # Sütun isimlerini feature_engineering.py ile uyumlu yap
        # Forward_PE sütununa Trailing PE yazdık (geçmiş veri olduğu için).
        # Gelecek tahmini (gerçek Forward PE) tarihsel olarak bulunmaz.
        
        # Dosyayı Kaydet
        ensure_data_dir()
        output_path = "data/fundamental_data.xlsx"
        df_fund.to_excel(output_path, index=False)
        print(f"\n✅ Veriler kaydedildi: {output_path}")
        print(df_fund.head())
    else:
        print("\n❌ Hiçbir veri toplanamadı.")

if __name__ == "__main__":
    fetch_and_calculate_fundamentals()
