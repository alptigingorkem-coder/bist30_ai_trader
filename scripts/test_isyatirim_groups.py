from isyatirimhisse import fetch_financials
import pandas as pd

# Test Sets
tests = [
    ('AKBNK', '1'), 
    ('AKBNK', '2'),
    ('AKBNK', '3'),
    ('THYAO', '1'),
    ('THYAO', '2'),
    ('THYAO', '3')
]

for sym, grp in tests:
    print(f"Testing {sym} with Group {grp}...")
    try:
        fin = fetch_financials(symbols=[sym], start_year='2022', end_year='2022', financial_group=grp)
        if fin is not None and not fin.empty:
            print(f"  [SUCCESS] Found data for {sym} (Group {grp})")
            print("  Columns:", fin.columns.tolist()[:5])
            break # Bulduysak duralım, data structure'ı görelim
    except Exception as e:
        pass
