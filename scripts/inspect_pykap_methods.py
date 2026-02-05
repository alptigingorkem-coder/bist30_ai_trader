
from pykap.bist import BISTCompany
import inspect

# Metodların imzalarını al
methods = ['get_historical_disclosure_list', 'get_financial_reports', 'get_expected_disclosure_list']

akbnk = BISTCompany(ticker='AKBNK')

for method_name in methods:
    method = getattr(akbnk, method_name, None)
    if method:
        try:
            sig = inspect.signature(method)
            print(f"{method_name}: {sig}")
        except Exception as e:
            print(f"{method_name}: Error getting signature - {e}")

# Ayrıca parametresiz çağırmayı dene
print("\n--- Testing without params ---")
try:
    disclosures = akbnk.get_historical_disclosure_list()
    print(f"get_historical_disclosure_list() returned: {type(disclosures)}, len={len(disclosures) if disclosures else 0}")
    if disclosures and len(disclosures) > 0:
        print(f"Sample keys: {disclosures[0].keys() if isinstance(disclosures[0], dict) else disclosures[0]}")
except Exception as e:
    print(f"get_historical_disclosure_list() error: {e}")
