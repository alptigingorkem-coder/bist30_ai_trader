# Bakım Scriptleri - Kullanıcı Kılavuzu

BIST30 AI Trader projesinde kod kalitesi sorunlarını analiz etmek, tespit etmek ve düzeltmek için kapsamlı otomatik araçlar.

## İçindekiler

- [Genel Bakış](#genel-bakış)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Script Referansı](#script-referansı)
  - [1. find_unused_files.py](#1-find_unused_filespy)
  - [2. find_small_files.py](#2-find_small_filespy)
  - [3. find_large_files.py](#3-find_large_filespy)
  - [4. find_duplicate_code.py](#4-find_duplicate_codepy)
  - [5. organize_scripts.py](#5-organize_scriptspy)
  - [6. suggest_merges.py](#6-suggest_mergespy)
  - [7. auto_cleanup.py](#7-auto_cleanuppy)
  - [8. generate_cleanup_report.py](#8-generate_cleanup_reportpy)
- [Yapılandırma](#yapılandırma)
- [Güvenlik Özellikleri](#güvenlik-özellikleri)
- [En İyi Uygulamalar](#en-iyi-uygulamalar)
- [Sorun Giderme](#sorun-giderme)

## Genel Bakış

Bakım scriptleri, kod tabanınızı temiz, düzenli ve sürdürülebilir tutmak için kapsamlı bir araç seti sağlar. Her script, kod kalitesinin belirli bir yönüne odaklanır:

- **Tespit**: Kullanılmayan dosyaları, boyut sorunlarını ve kopyaları tanımlama
- **Analiz**: Script organizasyonunu ve birleştirme fırsatlarını analiz etme
- **Temizlik**: Geçici dosyaların ve yapıtların otomatik olarak kaldırılması
- **Raporlama**: Kapsamlı temizlik raporları oluşturma

## Hızlı Başlangıç

1. **Bağımlılıkları yükleyin**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Kapsamlı bir rapor oluşturun** (önerilen ilk adım):
   ```bash
   python scripts/maintenance/generate_cleanup_report.py --markdown rapor.md
   ```

3. **Belirli sorunları inceleyin**:
   ```bash
   # Kullanılmayan dosyaları bulun
   python scripts/maintenance/find_unused_files.py
   
   # Kopya kodu bulun
   python scripts/maintenance/find_duplicate_code.py
   ```

4. **Temizlik işlemini gerçekleştirin** (her zaman önce dry-run kullanın):
   ```bash
   # Temizliği önizleyin
   python scripts/maintenance/auto_cleanup.py
   
   # Temizliği gerçekleştirin
   python scripts/maintenance/auto_cleanup.py --execute
   ```
