@echo off
title BIST30 AI TRADER - PAPER TRADING (LIVE)
color 0A

echo ========================================================
echo   BIST30 AI TRADER - PAPER TRADING BASLATILIYOR...
echo   Versiyon: v1.0 (Verified)
echo ========================================================
echo.

:: 1. Sanal Ortam Kontrolu (Eger venv kullaniyorsaniz aktif edin, yoksa global python kullanilir)
:: call venv\Scripts\activate.bat

:: 2. Gerekli kutuphaneleri kontrol et (Opsiyonel, hiz icin kapali)
:: pip install -r requirements.txt

:: 3. Gunluk Analiz ve Shadow Trading (Paper Mode)
echo [1/2] Shadow Trading Motoru Calistiriliyor...
python paper_trading/position_runner.py
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo [HATA] position_runner.py calisirken bir sorun olustu!
    pause
    exit /b
)

:: 4. Raporu Ac
echo.
echo [2/2] Raporlar hazirlaniyor...
:: Eger HTML rapor varsa ac, yoksa sadece log goster
if exist "reports\latest_signal_report.html" (
    start reports\latest_signal_report.html
)

echo.
echo ========================================================
echo   ISLEM TAMAMLANDI.
echo   Sinyaller "reports/" klasorunde ve ekranda mevcuttur.
echo ========================================================
echo.
pause
