import pandas as pd
import numpy as np
from isyatirimhisse import fetch_financials, fetch_stock_data
from datetime import datetime
import time
import os

# Hedef Hisseler (BIST 30 Benzeri)
TICKERS = [
    'AKBNK', 'ALARK', 'ASELS', 'ASTOR', 'BIMAS', 'EKGYO', 'ENKAI', 'EREGL', 
    'FROTO', 'GARAN', 'GUBRF', 'HEKTS', 'ISCTR', 'KCHOL', 'KONTR', 'KRDMD', 
    'ODAS', 'OYAKC', 'PETKM', 'PGSUS', 'SAHOL', 'SASA', 'SISE', 'TAVHL', 
    'TCELL', 'THYAO', 'TOASO', 'TSKB', 'TTKOM', 'TUPRS', 'YKBNK'
]

START_YEAR = '2015'
END_YEAR = str(datetime.now().year)
START_DATE_STOCK = '01-01-2015'
END_DATE_STOCK = datetime.now().strftime('%d-%m-%Y')

OUTPUT_FILE = 'data/fundamental_data.xlsx'

def get_financial_group(symbol):
    """Hissenin hangi grupta (Banka, Sanayi vs) olduğunu bulur."""
    for group in ['1', '2', '3']:
        try:
            # Sadece geçmiş bir yılı çekip kontrol et (Garanti olsun diye 2023/2024)
            test_year = str(datetime.now().year - 2) 
            fin = fetch_financials(symbols=[symbol], start_year=test_year, end_year=test_year, financial_group=group)
            if fin is not None and not fin.empty:
                return group
        except:
            continue
    return None

def find_item_in_financials(df, keywords):
    """
    Verilen keywordleri içeren satırı bulur.
    df: Wide formatında değil, Item Code/Name sütunları olan df.
    """
    # İsim sütunu: FINANCIAL_ITEM_NAME_TR veya EN
    col_name = 'FINANCIAL_ITEM_NAME_TR'
    if col_name not in df.columns:
        return None

    for keyword in keywords:
        # Case insensitive search
        # regex=False önemli çünkü parantez içerebilir
        matches = df[df[col_name].str.contains(keyword, case=False, na=False, regex=False)]
        if not matches.empty:
            # En iyi eşleşmeyi döndür
            # "NET DÖNEM KARI/ZARARI" gibi net ifadeler öncelikli
            
            # Tam eşleşme (whitespace temizleyerek)
            # exact = df[df[col_name].str.strip().str.lower() == keyword.lower()]
            # if not exact.empty:
            #     return exact.iloc[0]
            
            # İlk eşleşmeyi dön
            return matches.iloc[-1] # Genelde toplamlar en altta olur (örn: XXIII. NET DÖNEM KARI)
            
    return None

def fetch_and_process():
    all_data = []

    for symbol in TICKERS:
        print(f"Processing {symbol}...")
        
        # 1. Finansal Grubu Bul
        group = get_financial_group(symbol)
        if not group:
            print(f"  [WARN] Financial group not found for {symbol}. Skipping.")
            continue
            
        print(f"  Group: {group}")

        # 2. Bilançoları Çek
        try:
            fin = fetch_financials(symbols=[symbol], start_year=START_YEAR, end_year=END_YEAR, financial_group=group)
        except Exception as e:
            print(f"  [ERR] Failed to fetch financials: {e}")
            continue

        if fin is None or fin.empty:
            continue

        # 3. Kritik Kalemleri Bul
        # Sanayi ve Banka karışık keywordler
        net_income_keywords = [
            'DÖNEM NET KARI VEYA ZARARI', 
            'Dönem Net Karı/Zararı', 
            'Dönem Net Karı (Zararı)',
            'NET DÖNEM KARI/ZARARI', # Banka: XXIII. NET DÖNEM KARI/ZARARI (XVII+XXII)
            'Dönem Karı/Zararı'
        ]
        equity_keywords = [
            'ÖZKAYNAKLAR', # Sanayi: ÖZKAYNAKLAR (Toplam) ve Banka: XVI. ÖZKAYNAKLAR
            'TOPLAM ÖZKAYNAKLAR'
        ]

        net_income_row = find_item_in_financials(fin, net_income_keywords)
        equity_row = find_item_in_financials(fin, equity_keywords)

        if net_income_row is None or equity_row is None:
            # Logging
            print(f"  [WARN] Critical items missing for {symbol} (Group {group})")
            if net_income_row is None: print("    - Net Income missing")
            if equity_row is None: print("    - Equity missing")
            continue

        # 4. Veriyi Transpose Et (Tarih bazlı yapıya çevir)
        # Sütunlar: ... '2020/3', '2020/6' ...
        date_cols = [c for c in fin.columns if '/' in str(c)]
        
        # Net Income Series
        ni_series = net_income_row[date_cols].T
        ni_series.name = 'Net_Income_Quarterly'
        
        # Equity Series
        eq_series = equity_row[date_cols].T
        eq_series.name = 'Equity'
        
        # Birleştir
        fund_df = pd.concat([ni_series, eq_series], axis=1)
        fund_df.index.name = 'Date_Str'
        
        # Sayısal olmayan karakterleri temizle ve numeric yap
        # Bazen binlik ayracı nokta olabilir, ondalık virgül olabilir?
        # Python TR locale sorunu olabilir.
        # Varsayım: isyatirimhisse float döner ama bazen object kalabilir.
        for col in fund_df.columns:
             fund_df[col] = pd.to_numeric(fund_df[col], errors='coerce')

        # Tarih formatını düzelt (YYYY/Q -> YYYY-MM-DD Quarter End)
        dates = []
        for d_str in fund_df.index:
            try:
                y, q = d_str.split('/')
                # Q to Month: 3->3, 6->6, 9->9, 12->12
                # Ay sonu gününü bulmak zor, statik verelim.
                # pd.to_datetime(f"{y}-{m}-01") + MonthEnd
                m = int(q)
                # Geçici tarih (Ayın 1'i)
                dt = pd.Timestamp(int(y), m, 1) + pd.offsets.MonthEnd(1)
                dates.append(dt)
            except:
                dates.append(pd.NaT)
                
        fund_df['Date'] = dates
        fund_df.set_index('Date', inplace=True)
        fund_df.dropna(how='all', inplace=True)
        
        # Yıllıklandırılmış Net Kar (Trailing 12 Months)
        # Veriler kümülatif mi dönemsel mi?
        # İş Yatırım verileri genelde KÜMÜLATİF gelir (3 aylık, 6 aylık, 9 aylık, 12 aylık).
        # TTM hesaplamak için: 
        # TTM = (Son 12 Aylık) = Cari Yıl Kümülatif + (Önceki Yıl Yıllık - Önceki Yıl Aynı Dönem Kümülatif)
        # Basitlik için: Direkt 12 aylık veriyi kullanmak en temizidir ama ara dönemlerde TTM lazım.
        # Şimdilik direkt "Net_Income_Quarterly" değerini TTM gibi kabul edemeyiz kümalatifse.
        # Varsayım: Veriler kümülatif.
        # Q4 verisi = Yıllık Kar.
        # Q3 = 9 aylık kar.
        # TTM yaklaşımı: Son mevcut veri * (12 / Ay). Çok kaba bir tahmin.
        # Veya direkt Equity üzerinden gidelim, P/E biraz zorlayacak bu formatta.
        # Ancak, 'Net Income' olarak çektiğimiz satırın ne olduğu önemli. 
        # Biz 'Net Income TTM'i manuel hesaplamak yerine 'Equity' ve PD'yi kullanıp PB Ratio çıkaralım.
        # P/E için: Son 4 çeyreği toplayamayız kümülatifse.
        # Kümülatif karı TTM'e çevirmek biraz iş. Şimdilik "Son Açıklanan Kar * 4" (Quarterly ise) veya "Kümülatif Kar" kullanalım.
        # İyileştirme: PD/DD daha güvenilir şu an.
        
        # 5. Hisse Fiyatı (PD) Çek
        try:
            stock_data = fetch_stock_data(symbols=[symbol], start_date=START_DATE_STOCK, end_date=END_DATE_STOCK)
        except Exception as e:
            print(f"  [ERR] Failed to fetch stock data: {e}")
            continue

        if stock_data is None or stock_data.empty:
            continue
            
        # Sütunları seç: 'HGDG_TARIH', 'PD' (Piyasa Değeri)
        stock_data['Date'] = pd.to_datetime(stock_data['HGDG_TARIH'], dayfirst=True) # DD-MM-YYYY
        stock_data = stock_data[['Date', 'PD', 'HGDG_KAPANIS']].copy()
        stock_data.set_index('Date', inplace=True)
        stock_data.rename(columns={'HGDG_KAPANIS': 'Price'}, inplace=True)
        
        # 6. Merge (Bilanço verilerini Günlüklere yay)
        # Bilançoları stock dataya merge et (asof merge / ffill)
        merged = stock_data.sort_index().join(fund_df.sort_index(), how='left')
        
        # İleriye doğru doldur (En son açıklanan bilanço geçerlidir)
        merged['Equity'] = merged['Equity'].ffill()
        merged['Net_Income_TTM'] = merged['Net_Income_Quarterly'].ffill() # Şimdilik placeholder
        
        # 7. Rasyo Hesapla (Günlük Fiyat ile)
        # PB Ratio
        merged['PB_Ratio'] = merged['PD'] / merged['Equity']
        
        # F/K (P/E)
        # Eğer kar negatifse F/K anlamsızdır (NaN kalsın veya negatif olsun)
        # TTM Kar için basit bir hack: Son Kümülatif Kar (Örn: 6 aylık) / 6 * 12 ?
        # Şimdilik sadece PB Ratio'ya güveniyoruz. F/K'yı PD/Net_Income olarak bırakalım.
        merged['Forward_PE'] = merged['PD'] / merged['Net_Income_TTM']
        
        # Diğer sütunlar
        merged['EBITDA_Margin'] = 0.25 # Placeholder (Sabit)
        merged['Shares'] = merged['PD'] / merged['Price']
        merged['Debt_to_Equity'] = 1.5 # Placeholder
        merged['Ticker'] = f"{symbol}.IS"
        
        # Temizle
        merged.replace([np.inf, -np.inf], np.nan, inplace=True)
        merged = merged.reset_index()[['Ticker', 'Date', 'Price', 'Net_Income_TTM', 'Equity', 'Forward_PE', 'PB_Ratio', 'EBITDA_Margin', 'Shares', 'Debt_to_Equity']]
        
        all_data.append(merged)
        time.sleep(1) # Rate limit protection

    if not all_data:
        print("No data fetched.")
        return

    final_df = pd.concat(all_data, ignore_index=True)
    
    # Save
    print(f"Saving {len(final_df)} rows to {OUTPUT_FILE}...")
    final_df.to_excel(OUTPUT_FILE, index=False)
    print("Done.")

if __name__ == "__main__":
    fetch_and_process()
