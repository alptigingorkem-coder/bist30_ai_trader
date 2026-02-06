"""
Optuna pipeline tanı scripti.
Çalıştırın: python scripts/diagnose_optuna.py
Çıktı: logs/optuna/diagnose.log (her adım zaman damgalı; hata olursa traceback)
"""
import os
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO_ROOT)
sys.path.insert(0, REPO_ROOT)

LOG_DIR = os.path.join(REPO_ROOT, "logs", "optuna")
LOG_FILE = os.path.join(LOG_DIR, "diagnose.log")

def log(msg):
    line = f"[{datetime.now().isoformat()}] {msg}"
    print(line)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"Diagnose started {datetime.now().isoformat()}\n")
    log("STEP 0: Import...")
    try:
        import research.optuna_nested_walk_forward as m
        log("STEP 0 OK: Import başarılı.")
    except Exception as e:
        log(f"STEP 0 HATA: {e}")
        import traceback
        log(traceback.format_exc())
        return

    log("STEP 1: load_data() - Bu adım birkaç dakika sürebilir (yfinance + FE)...")
    try:
        data = m.load_data()
        log(f"STEP 1 OK: {len(data)} satır, {data.index.nunique()} benzersiz tarih.")
    except Exception as e:
        log(f"STEP 1 HATA: {e}")
        import traceback
        log(traceback.format_exc())
        return

    log("STEP 2: Tek Optuna trial (TimeSeriesSplit + LightGBM)...")
    try:
        import optuna
        study = optuna.create_study(direction="maximize")
        study.optimize(lambda t: m.objective(t, data), n_trials=1, timeout=300)
        log(f"STEP 2 OK: Best value = {study.best_value}")
    except Exception as e:
        log(f"STEP 2 HATA: {e}")
        import traceback
        log(traceback.format_exc())
        return

    log("TAMAMLANDI. Tüm adımlar başarılı.")
    log(f"Log dosyası: {LOG_FILE}")

if __name__ == "__main__":
    main()
