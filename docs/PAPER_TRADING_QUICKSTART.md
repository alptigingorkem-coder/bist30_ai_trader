# 🚀 Paper Trading Hızlı Başlangıç

> 5 dakikada paper trading'i başlat!

## ⚡ Hızlı Başlangıç

### ⚠️ ÖNEMLİ: Sadece BİR KEZ Başlat!

Paper trading sistemini **bir kez başlatmanız yeterli**. Sistem:
- ✅ Her gün saat 18:05'te otomatik çalışır
- ✅ Tüm işlemleri otomatik kaydeder
- ❌ Her gün yeniden başlatmanıza gerek YOK

### 1. Sistem Kontrolü (30 saniye)

```bash
python3 scripts/validation/paper_trading_readiness.py
```

**Beklenen:** Skor >75%

### 2. Paper Trading Başlat (10 saniye) - SADECE BİR KEZ!

```bash
# Arka planda çalıştır
nohup python3 scripts/ops/paper_trading_runner.py > logs/paper_trading.out 2>&1 &

# Process ID'yi kaydet
echo $! > paper_trading.pid

# Çıktı:
# [1] 12345
```

**🎉 Tamamlandı!** Sistem artık otomatik çalışıyor. Her gün 18:05'te işlem yapacak.

### 3. Çalıştığını Doğrula (5 saniye)

```bash
# Process kontrolü
ps aux | grep paper_trading_runner

# Log kontrolü
tail -20 logs/paper_trading_$(date +%Y%m%d).log
```

**Beklenen çıktı:**
```
🚀 Paper Trader Başlatıldı (Sanal Bakiye: 10,000.00 TL)
✅ Model yüklendi: models/saved/global_ranker.pkl
🕒 Gün Sonu (EOD) Trader Modu Başlatıldı.
```

---

## 📊 Günlük Komutlar (Opsiyonel İzleme)

**NOT:** Sistem zaten otomatik çalışıyor. Bunlar sadece izleme için.

### Sabah Rutini (09:00) - Opsiyonel

```bash
# 1. Sistem durumu
ps aux | grep paper_trading_runner

# 2. Portfolio kontrolü
python3 scripts/analysis/check_portfolio_status.py

# 3. Dünkü işlemler
tail -50 logs/paper_trading_$(date -d "yesterday" +%Y%m%d).log | grep "ALIM\|SATIŞ"
```

### Akşam Rutini (18:30) - Opsiyonel

```bash
# 1. Bugünkü işlemler
tail -50 logs/paper_trading_$(date +%Y%m%d).log | grep "ALIM\|SATIŞ"

# 2. Günlük rapor
python3 scripts/analysis/generate_daily_report.py

# 3. Performans
python3 scripts/analysis/calculate_daily_sharpe.py
```

### Haftalık Rutin (Pazar) - Opsiyonel

```bash
# Haftalık rapor
python3 scripts/analysis/generate_weekly_report.py \
    --start-date $(date -d "7 days ago" +%Y-%m-%d) \
    --end-date $(date +%Y-%m-%d)
```

---

## 🛑 Sistemi Durdurma

```bash
# Process ID'den durdur
kill $(cat paper_trading.pid)

# Veya isimden durdur
pkill -f paper_trading_runner

# Durduğunu doğrula
ps aux | grep paper_trading_runner
```

---

## 🔄 Yeniden Başlatma

```bash
# 1. Durdur
pkill -f paper_trading_runner

# 2. Bekle
sleep 5

# 3. Başlat
nohup python3 scripts/ops/paper_trading_runner.py > logs/paper_trading.out 2>&1 &
echo $! > paper_trading.pid
```

---

## 🚨 Acil Durum

### Sistem Çöktü

```bash
# 1. Log'u kontrol et
tail -100 logs/paper_trading_$(date +%Y%m%d).log

# 2. Hata bul
grep "ERROR\|Exception" logs/paper_trading_*.log | tail -20

# 3. Yeniden başlat
python3 scripts/ops/paper_trading_runner.py
```

### Günlük Kayıp >%5

```bash
# 1. Kontrol et
python3 scripts/analysis/check_daily_loss.py

# 2. Eğer >%5 ise DURDUR
pkill -f paper_trading_runner

# 3. Analiz yap
tail -200 logs/paper_trading_$(date +%Y%m%d).log

# 4. Sorunu çöz ve yeniden başlat
```

---

## 📱 Tek Komut Monitoring

```bash
# Tüm bilgileri göster
cat << 'EOF' > check_all.sh
#!/bin/bash
echo "=== PAPER TRADING STATUS ==="
echo ""
echo "📊 Sistem Durumu:"
ps aux | grep paper_trading_runner | grep -v grep || echo "❌ Çalışmıyor!"
echo ""
echo "💼 Portfolio:"
python3 scripts/analysis/check_portfolio_status.py
echo ""
echo "📈 Performans:"
python3 scripts/analysis/calculate_daily_sharpe.py
echo ""
echo "📝 Son İşlemler:"
tail -10 logs/paper_trading_$(date +%Y%m%d).log | grep "ALIM\|SATIŞ"
EOF

chmod +x check_all.sh
./check_all.sh
```

---

## 📋 Kontrol Listesi

### ✅ Her Gün

- [ ] Sistem çalışıyor mu?
- [ ] Bugün işlem oldu mu?
- [ ] Günlük kayıp <%5 mi?
- [ ] Log'da hata var mı?

### ✅ Her Hafta

- [ ] Sharpe >1.0 mı?
- [ ] Drawdown <-15% mi?
- [ ] İşlem sayısı normal mi? (10-20)
- [ ] Haftalık rapor oluşturuldu mu?

### ✅ 2 Hafta Sonra

- [ ] Sharpe >1.5 mi? → Canlıya geç
- [ ] Sharpe 1.0-1.5 mi? → 1 ay daha paper trading
- [ ] Sharpe <1.0 mi? → Model revizyonu

---

## 🎯 Hedef Metrikler

| Metrik | Minimum | İdeal |
|--------|---------|-------|
| Sharpe Ratio | >1.0 | >1.5 |
| Max Drawdown | <-20% | <-15% |
| Win Rate | >50% | >55% |
| Günlük İşlem | 1-3 | 2-4 |

---

## 📚 Detaylı Dokümantasyon

- [Tam Paper Trading Rehberi](paper_trading_guide.md)
- [README](../README.md)
- [Architecture](architecture.md)

---

**Başarılar! 🚀**

*Son güncelleme: 2026-02-19*
