from pykap.bist import BISTCompany

try:
    akbnk = BISTCompany(ticker='AKBNK')
    print("BISTCompany methods:", [m for m in dir(akbnk) if not m.startswith('__')])
except Exception as e:
    print(f"Error: {e}")
