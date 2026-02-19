import os
import sys
import subprocess
import yfinance as yf
import requests

def run_cmd(cmd):
    print(f"--- CMD: {cmd} ---")
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        print(out.decode())
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode()}")

print("=== User Info ===")
run_cmd("id")
run_cmd("groups")

print("\n=== GPU Device Info ===")
run_cmd("ls -l /dev/kfd")
run_cmd("ls -l /dev/dri")

print("\n=== YFinance Test (GARAN.IS) ===")
try:
    df = yf.download("GARAN.IS", period="5d", progress=False)
    print("Shape:", df.shape)
    print("Columns:", df.columns)
    print("Head:", df.head(2))
except Exception as e:
    print("YF Error:", e)

print("\n=== Requests SSL Test (Isyatirim) ===")
try:
    r = requests.get("https://www.isyatirim.com.tr", timeout=5)
    print("Status:", r.status_code)
except Exception as e:
    print("Req Error:", e)
