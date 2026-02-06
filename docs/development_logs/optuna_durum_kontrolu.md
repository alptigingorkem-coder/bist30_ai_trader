# Optuna Çalıştırma ve Durum Kontrolü

## İlerleme logu (yeni çalıştırmalarda)

Optuna scripti çalışırken ilerlemeyi şu dosyaya yazar:

- **`logs/optuna/progress.txt`**

Örnek içerik:

```
[2026-02-05T...] optimize_and_test_per_year: start
[2026-02-05T...] load_data: start
[2026-02-05T...] load_data: done rows=... dates=...
[2026-02-05T...] optimize: test_year=2023 start
[2026-02-05T...] optimize: test_year=2023 done best_value=...
[2026-02-05T...] optimize: test_year=2024 start
...
[2026-02-05T...] optimize_and_test_per_year: DONE
```

**Optuna’yı çalıştırdıktan sonra** bu dosyayı açarak işlemin nerede olduğunu görebilirsin. Son satır “DONE” ise sorunsuz bitmiş demektir.

## Tanı scripti (hata / yavaşlık tespiti)

Kısa bir test için:

```bash
python scripts/diagnose_optuna.py
```

Bu script:

1. Modül importunu dener  
2. `load_data()` çalıştırır (birkaç dakika sürebilir)  
3. Tek bir Optuna trial çalıştırır  

Tüm çıktı ve hatalar **`logs/optuna/diagnose.log`** dosyasına yazılır. Hata olursa tam traceback burada görünür.

- **STEP 0 HATA** → Import veya bağımlılık sorunu  
- **STEP 1 HATA** → Veri indirme / feature engineering (yfinance, config.TICKERS, vb.)  
- **STEP 2 HATA** → Optuna/LightGBM tarafı  

Script uzun süre hiç çıktı vermeden takılıyorsa büyük ihtimalle **STEP 1** (veri yükleme) aşamasındadır; config’teki tüm hisseler için yfinance + FE uzun sürebilir.

## Optuna’nın hâlâ çalışıp çalışmadığını anlama

### Windows (PowerShell)

```powershell
Get-Process python -ErrorAction SilentlyContinue | Format-Table Id, CPU, StartTime
```

Veya:

```cmd
tasklist | findstr python
```

Python süreci varsa Optuna (veya başka bir script) hâlâ çalışıyor olabilir. Kesin bilgi için `progress.txt` son satırına bakın.

### Tamamlandığını anlama

- **`models/saved/optimized_lgbm_params.joblib`** dosyası oluştuysa Optuna başarıyla bitmiş ve en iyi parametreler kaydedilmiş demektir.

## Kısa özet

| Ne yapmak istiyorsun?              | Ne yapmalısın? |
|------------------------------------|----------------|
| Optuna’nın nerede kaldığını görmek | `logs/optuna/progress.txt` son satırlarına bak |
| Hata / yavaşlık nedenini bulmak    | `python scripts/diagnose_optuna.py` çalıştır, `logs/optuna/diagnose.log` oku |
| Optuna’nın bitip bitmediğini anlamak | `models/saved/optimized_lgbm_params.joblib` var mı bak veya progress’te “DONE” var mı kontrol et |
| Python’un hâlâ çalışıp çalışmadığı | `Get-Process python` veya `tasklist \| findstr python` |
