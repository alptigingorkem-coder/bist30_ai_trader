#!/usr/bin/env python3
"""
BIST30 AI Trader - Paper Trading Readiness Check
Master script that runs all validation checks and provides GO/NO-GO decision.
"""

from datetime import datetime
from pathlib import Path
import sys


def run_full_readiness_check():
    """Tüm kontrolleri çalıştır ve final GO/NO-GO kararı ver."""
    print("=" * 70)
    print("📊 BIST30 AI TRADER - PAPER TRADING READINESS CHECK")
    print("=" * 70)
    print(f"Tarih: {datetime.now().isoformat()}")
    print(f"Versiyon: README güncel (Multi-model, TimescaleDB, FastAPI)")
    print("=" * 70)

    # Tüm validation script'lerini import et
    from check_project_structure import check_project_structure
    from check_infrastructure import check_infrastructure
    from check_models import check_trained_models
    from check_paper_trading_script import check_paper_trading_script
    from check_walk_forward_results import check_walk_forward_results
    from check_config_params import check_config_parameters

    # Testleri çalıştır
    results = {
        '1. Proje Yapılanması': check_project_structure(),
        '2. Altyapı': check_infrastructure(),
        '3. Model Eğitimleri': check_trained_models(),
        '4. Paper Trading Script': check_paper_trading_script(),
        '5. Walk-Forward Sonuçları': check_walk_forward_results(),
        '6. Config Parametreleri': check_config_parameters()
    }

    # Skorları topla
    weights = {
        '1. Proje Yapılanması': 5,
        '2. Altyapı': 8,
        '3. Model Eğitimleri': 10,  # En kritik
        '4. Paper Trading Script': 10,  # En kritik
        '5. Walk-Forward Sonuçları': 10,  # En kritik
        '6. Config Parametreleri': 7
    }

    print("\n" + "=" * 70)
    print("📊 DETAYLI SONUÇLAR")
    print("=" * 70)

    total_score = 0
    total_weight = 0
    
    for category, result in results.items():
        status = result.get('status', 'UNKNOWN')
        score = result.get('score', 0)
        weight = weights[category]
        
        status_emoji = {
            'PASS': '✅',
            'PARTIAL': '🟡',
            'FAIL': '❌',
            'UNKNOWN': '❓'
        }[status]
        
        # Calculate weighted contribution
        weighted_contribution = (score / 100.0) * weight
        
        print(f"\n{status_emoji} {category}")
        print(f"   Skor: {score:.1f}%")
        print(f"   Ağırlık: {weight}/10")
        print(f"   Katkı: {weighted_contribution:.1f}")
        
        if 'reason' in result:
            print(f"   Sebep: {result['reason']}")
        if 'message' in result:
            print(f"   Mesaj: {result['message']}")
        
        total_score += weighted_contribution
        total_weight += weight

    # Final skor (percentage)
    final_score = (total_score / total_weight) * 100
    
    print("\n" + "=" * 70)
    print("🎯 FİNAL KARAR")
    print("=" * 70)
    print(f"\nGenel Skor: {final_score:.1f}%")

    # GO/NO-GO kararı
    if final_score >= 90:
        decision = "GO"
        color = "🟢"
        message = generate_go_message()
    elif final_score >= 75:
        decision = "CONDITIONAL GO"
        color = "🟡"
        message = generate_conditional_message(results)
    else:
        decision = "NO-GO"
        color = "🔴"
        message = generate_nogo_message(results)

    print(f"\n{color} Karar: **{decision}**")
    print(message)

    # Markdown raporu kaydet
    save_report(final_score, decision, message, results, weights)

    # Exit code
    if decision == "GO":
        sys.exit(0)
    else:
        sys.exit(1)


def generate_go_message():
    """Generate GO decision message."""
    return """
✅ ✅ ✅ PAPER TRADING'E HAZIR! ✅ ✅ ✅

Sistem tüm kritik kontrolleri başarıyla geçti.
Paper trading güvenle başlatılabilir.

SONRAKİ ADIMLAR:
1. Git snapshot: git tag v1.0-paper-trading
2. Branch oluştur: git checkout -b production/paper-trading
3. Master'a push: git push origin master --tags
4. Paper trading başlat:
   python scripts/ops/paper_trading_runner.py

5. 2 hafta günlük takip:
   - Günlük performance logları
   - Weekly rapor oluştur
   - Anomali tespiti

6. 2 hafta sonra değerlendirme:
   - Sharpe >1.5 → Canlıya geç (küçük sermaye)
   - Sharpe 1.0-1.5 → 1 ay daha paper trading
   - Sharpe <1.0 → Model revizyonu
"""


def generate_conditional_message(results):
    """Generate CONDITIONAL GO message."""
    message = """
🟡 KOŞULLU HAZIR (Küçük düzeltmelerle başlayabilir)

Sistem genel olarak iyi durumda ama bazı iyileştirmeler yapılmalı.

EKSİKLİKLER:
"""
    # Eksikleri listele
    for category, result in results.items():
        if result.get('status') in ['FAIL', 'PARTIAL']:
            message += f"\n  - {category}"
            if 'reason' in result:
                message += f": {result['reason']}"
    
    message += """

AKSIYONLAR:
1. Yukarıdaki eksiklikleri düzeltin
2. Bu script'i tekrar çalıştırın
3. %90+ aldıktan sonra paper trading başlatın

TAHMİNİ SÜRE: 1-2 gün
"""
    return message


def generate_nogo_message(results):
    """Generate NO-GO message."""
    failed_count = sum(1 for r in results.values() if r.get('status') == 'FAIL')
    
    message = f"""
❌ ❌ ❌ HAZIR DEĞİL! ❌ ❌ ❌

{failed_count} kritik sorun tespit edildi.
Paper trading'e geçmek riskli.

KRİTİK SORUNLAR:
"""
    # Kritik sorunları listele
    for category, result in results.items():
        if result.get('status') == 'FAIL':
            message += f"\n  🔴 {category}"
            if 'reason' in result:
                message += f": {result['reason']}"
            if 'action' in result:
                message += f"\n     → {result['action']}"
    
    message += """

SONRAKİ ADIMLAR:
1. Tüm FAIL durumlarını düzeltin
2. Model eğitimlerini tamamlayın
3. Walk-forward validation çalıştırın
4. Bu script'i tekrar çalıştırın

TAHMİNİ SÜRE: 3-5 gün
"""
    return message


def save_report(final_score, decision, message, results, weights):
    """Save detailed report to markdown file."""
    report_content = f"""# Paper Trading Readiness Report

Date: {datetime.now().isoformat()}
Version: Multi-Model (LightGBM + CatBoost + TFT)

## Decision: {decision}

Final Score: {final_score:.1f}%

{message}

## Detailed Results

| Category | Status | Score | Weight |
|----------|--------|-------|--------|
"""
    
    for category, result in results.items():
        status = result.get('status', 'UNKNOWN')
        score = result.get('score', 0)
        weight = weights[category]
        report_content += f"| {category} | {status} | {score:.1f}% | {weight}/10 |\n"
    
    # Kaydet
    report_file = Path('PAPER_TRADING_READINESS_REPORT.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n💾 Detaylı rapor kaydedildi: {report_file}")


if __name__ == "__main__":
    run_full_readiness_check()
