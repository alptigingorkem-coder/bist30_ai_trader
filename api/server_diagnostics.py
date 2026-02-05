
import yfinance as yf
import pandas as pd
import time

TICKERS = [
    "AKBNK.IS", "ALARK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS",
    "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS",
    "GUBRF.IS", "HEKTS.IS", "ISCTR.IS", "KCHOL.IS", "KONTR.IS",
    "KOZAL.IS", "KRDMD.IS", "ODAS.IS", "OYAKC.IS", "PETKM.IS",
    "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TAVHL.IS",
    "TCELL.IS", "THYAO.IS", "TOASO.IS", "TSKB.IS", "TTKOM.IS",
    "TUPRS.IS", "YKBNK.IS"
]

def test_fetch():
    print(f"Testing fetch for {len(TICKERS)} tickers...")
    start_time = time.time()
    
    tickers_str = " ".join(TICKERS)
    try:
        df = yf.download(tickers_str, period="1d", interval="1m", progress=False)
        end_time = time.time()
        print(f"Fetch completed in {end_time - start_time:.2f} seconds.")
        
        if df.empty:
            print("DATAFRAME IS EMPTY!")
            return

        print("Dataframe shape:", df.shape)
        # print("Columns:", df.columns)
        
        # Check for NaNs
        nan_cols = df['Close'].isna().sum()
        print("NaN counts per ticker in Close:", nan_cols[nan_cols > 0])
        
        # Try processing one
        print("Sample data check (GARAN.IS):")
        if 'GARAN.IS' in df['Close'].columns:
            print(df['Close']['GARAN.IS'].tail())
        else:
            print("GARAN.IS not found in columns")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fetch()
