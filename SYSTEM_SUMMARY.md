# BIST30 AI Trader - Sistem ve Strateji Özeti

Bu belge, projenin stratejik mantığını, performans metriklerini ve teknik mimarisini özetlemektedir.

## 1. Strateji ve Sistem Özeti
**Özet:** BIST30 AI Trader, Borsa İstanbul 30 endeksli hisse senetleri için tasarlanmış, LightGBM tabanlı bir "Ranking" (Sıralama) modelidir. Sistem, teknik ve temel verileri kullanarak hisseleri her gün puanlar ve **Top 5** hisseye odaklanan bir portföy yönetir.

*   **İşlem Türü:** Swing / Pozisyon Takibi (Trend Takibi tabanlı).
*   **Ortalama Pozisyon Tutma Süresi:** ~5-15 İş günü.
*   **Portföy Büyüklüğü:** En iyi 5 Hisse (Konsantrasyon Odaklı).
*   **Risk Yönetimi:** Rejim Bazlı Trailing Stop (Rallide Gevşek, Krizde Sıkı) + Macro Gate (VIX/USDTRY Koruması).

## 2. Temel Performans Metrikleri (OOS Backtest 2021-2024)
Sistemin "Alpha Odaklı" modundaki güncel performans rakamları:

| Metrik | Değer | Benchmark (XU100) |
| :--- | :--- | :--- |
| **Toplam Getiri** | **~-2.13%** | %39.29 |
| **Yıllık Getiri (CAGR)** | **Negatif** | %35.48 |
| **Alpha (Excess)** | **-%37.61** | - |
| **Beta** | **1.10** | - |

## 3. Proje Yapısı ve Mimari
*   **Dil/Framework:** Python 3.12, LightGBM, Pandas.
*   **Model:** LambdaRank (Pairwise Ranking).
*   **Mevcut Durum:** Paper Trading v2.1 (Canlı Test) aşamasında.

### Kritik Dosyalar:
1.  **Strateji:** `daily_run.py` - Günlük sinyal üretimi (Top 5).
2.  **Backtest:** `run_backtest.py` - Tarihsel simülasyon.
3.  **Risk:** `core/risk_manager.py` - Dinamik Stop/TP ve Rejim tespiti.
4.  **Konfigürasyon:** `config.py` - Tüm parametrelerin (Eşikler, Limitler) merkezi.

---
**Son Güncelleme:** 2026-02-03 (v2.1.0)
