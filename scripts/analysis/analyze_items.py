from isyatirimhisse import fetch_financials, fetch_stock_data
import pandas as pd

try:
    # 1. Bilanço Kalemlerini Listele
    print("Fetching Financials for AKBNK (Group 2)...")
    fin = fetch_financials(symbols=['AKBNK'], start_year='2022', end_year='2022', financial_group='2')
    if fin is not None:
        items = fin['FINANCIAL_ITEM_NAME_EN'].unique().tolist()
        print("Financial Items (First 20):")
        print(items[:20])
        
        # Kritik kalemleri ara
        print("Search 'Profit':", [x for x in items if 'Profit' in str(x)])
        print("Search 'Equity':", [x for x in items if 'Equity' in str(x)])

    print("-" * 30)

    # 2. Stock Data Test
    # Parametreleri bilmiyoruz, help yok. Tahmin: symbol, start_date, end_date
    # co_varnames'e bakalım önce
    print("Stock Data Params:", fetch_stock_data.__code__.co_varnames[:fetch_stock_data.__code__.co_argcount])
    
    # Parametre sıralamasına göre çağıralım: symbol, start_date, end_date, frequency?
    # Varsayalım.
    stock = fetch_stock_data(
        symbols=['AKBNK'], 
        start_date='01-01-2023', # DD-MM-YYYY formatı yaygın
        end_date='31-01-2023'
    )
    if stock is not None:
        print("Stock Data Head:")
        print(stock.head())
        print("Stock Columns:", stock.columns.tolist())

except Exception as e:
    print(f"Error: {e}")
