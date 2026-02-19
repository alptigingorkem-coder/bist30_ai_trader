
import yfinance as yf
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Monkey patch
original_init = requests.Session.__init__
def new_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    self.verify = False
requests.Session.__init__ = new_init

def test_minimal():
    print("Testing minimal yfinance fetch for ^GSPC...")
    try:
        data = yf.download("^GSPC", period="5d", progress=False)
        print("Data shape:", data.shape)
        print(data.head())
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_minimal()
