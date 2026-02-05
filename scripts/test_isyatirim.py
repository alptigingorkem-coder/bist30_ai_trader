from isyatirimhisse import fetch_financials
import pandas as pd

symbol = 'AKBNK'

print(f"Fetching Financials for {symbol}...")
try:
    # Parametreler: symbols, start_year, end_year
    fin = fetch_financials(
        symbols=['AKBNK'],
        start_year='2020',
        end_year='2020'
    )
    if fin is not None and not fin.empty:
        print("Financials DataFrame Head:")
        print(fin.head())
        print("Columns:", fin.columns.tolist())
        
        # İçindeki değerlere bakalım. F/K gibi hazır rasyo var mı?
        # Yoksa 'Equity' (Özkanaklar), 'Net Profit' (Net Kar) gibi kalemlerin Türkçe karşılıklarını bulmamız lazım.
        # Genelde 'Dönem Net Karı/Zararı', 'Özkaynaklar' gibi gelir.
        
    else:
        print("Empty dataframe returned.")

except Exception as e:
    print(f"Error fetching financials: {e}")
