#!/usr/bin/env python3
"""
MASTER QUALITY CHECKER
Tüm kod kalitesi analizlerini birleştiren ana script.
"""

from datetime import datetime
from pathlib import Path
import sys

# Add scripts/quality to path
sys.path.insert(0, str(Path(__file__).parent))


def run_full_quality_analysis():
    """Tüm kod kalitesi analizlerini çalıştır ve kapsamlı rapor oluştur."""
    print("="*70)
    print("🔍 BIST30 AI TRADER - CODE QUALITY ANALYSIS")
    print("="*70)
    print(f"Tarih: {datetime.now().isoformat()}")
    print("="*70)
    
    # Import all analyzers
    from check_dry_violations import DRYAnalyzer
    from check_srp_violations import SRPAnalyzer
    from check_complexity import ComplexityAnalyzer
    from check_code_smells import CodeSmellDetector
    
    # Analizleri çalıştır
    results = {}
    
    print("\n🔍 1/4: DRY Analysis...")
    dry_analyzer = DRYAnalyzer(min_lines=5)
    results['dry'] = dry_analyzer.analyze_project()
    
    print("\n🔍 2/4: SRP Analysis...")
    srp_analyzer = SRPAnalyzer()
    results['srp'] = srp_analyzer.analyze_project()
    
    print("\n🔍 3/4: Complexity Analysis...")
    complexity_analyzer = ComplexityAnalyzer()
    results['complexity'] = complexity_analyzer.analyze_project()
    
    print("\n🔍 4/4: Code Smell Detection...")
    smell_detector = CodeSmellDetector()
    results['smells'] = smell_detector.analyze_project()
    
    # Skorlama
    scores = _calculate_quality_scores(results)
    
    # Final Rapor
    _generate_final_report(results, scores)
    
    return results, scores


def _calculate_quality_scores(results: dict) -> dict:
    """Kalite skorlarını hesapla."""
    scores = {}
    
    # DRY Score (100 - duplicate satır sayısı)
    dry_duplicates = len(results['dry'])
    duplicate_lines = sum(g.lines * (g.occurrences - 1) for g in results['dry'])
    scores['dry'] = max(0, 100 - (duplicate_lines / 10))  # Her 10 satır duplicate -1 puan
    
    # SRP Score
    srp_violations = len(results['srp'])
    scores['srp'] = max(0, 100 - (srp_violations * 5))  # Her ihlal -5 puan
    
    # Complexity Score
    complex_funcs = len(results['complexity'])
    if results['complexity']:
        avg_complexity = sum(f.cyclomatic_complexity for f in results['complexity']) / len(results['complexity'])
    else:
        avg_complexity = 0
    scores['complexity'] = max(0, 100 - (complex_funcs * 2) - (avg_complexity - 10) * 2)
    
    # Code Smell Score
    smells = results['smells']
    high_severity = len([s for s in smells if s.severity == 'high'])
    medium_severity = len([s for s in smells if s.severity == 'medium'])
    low_severity = len([s for s in smells if s.severity == 'low'])
    scores['smells'] = max(0, 100 - (high_severity * 10) - (medium_severity * 3) - (low_severity * 1))
    
    # Genel skor (ağırlıklı ortalama)
    weights = {
        'dry': 0.30,
        'srp': 0.25,
        'complexity': 0.25,
        'smells': 0.20
    }
    scores['overall'] = sum(scores[k] * weights[k] for k in weights)
    
    return scores


def _generate_final_report(results: dict, scores: dict):
    """Final kalite raporu oluştur."""
    print("\n" + "="*70)
    print("📊 FINAL KOD KALİTESİ RAPORU")
    print("="*70)
    
    # Skorlar
    print(f"\n🎯 KALİTE SKORLARI:")
    print(f"   DRY (Don't Repeat Yourself):      {scores['dry']:.1f}/100")
    print(f"   SRP (Single Responsibility):      {scores['srp']:.1f}/100")
    print(f"   Complexity (Cyclomatic):          {scores['complexity']:.1f}/100")
    print(f"   Code Smells:                      {scores['smells']:.1f}/100")
    print(f"\n   🏆 GENEL SKOR:                    {scores['overall']:.1f}/100")
    
    # Grade
    overall = scores['overall']
    if overall >= 90:
        grade = "A (Mükemmel) ✅"
        message = "Kod kalitesi harika! Birkaç küçük iyileştirme yapılabilir."
    elif overall >= 80:
        grade = "B (İyi) 🟢"
        message = "Kod kalitesi iyi. Bazı refactoring'ler faydalı olabilir."
    elif overall >= 70:
        grade = "C (Orta) 🟡"
        message = "Kod çalışıyor ama bakım zorlaşabilir. Refactoring önerilir."
    elif overall >= 60:
        grade = "D (Zayıf) 🟠"
        message = "Kod kalitesi zayıf. Ciddi refactoring gerekli."
    else:
        grade = "F (Başarısız) 🔴"
        message = "Kod kalitesi çok düşük. Kapsamlı refactoring şart."
    
    print(f"\n📝 NOT: {grade}")
    print(f"   {message}")
    
    # İstatistikler
    print(f"\n📊 DETAYLI İSTATİSTİKLER:")
    print(f"   Duplicate kod grupları: {len(results['dry'])}")
    print(f"   SRP ihlalleri: {len(results['srp'])}")
    print(f"   Karmaşık fonksiyonlar: {len(results['complexity'])}")
    print(f"   Code smell'ler: {len(results['smells'])}")
    
    # Öncelikli aksiyonlar
    print(f"\n🎯 ÖNCELİKLİ AKSIYONLAR:")
    actions = []
    
    if scores['dry'] < 80:
        duplicate_lines = sum(g.lines * (g.occurrences - 1) for g in results['dry'])
        actions.append(f"1. DRY ihlallerini düzelt (~{duplicate_lines} satır duplicate kod)")
    
    if scores['srp'] < 80:
        actions.append(f"2. SRP ihlallerini düzelt ({len(results['srp'])} sınıf çok fazla sorumluluk taşıyor)")
    
    if scores['complexity'] < 80:
        actions.append(f"3. Karmaşık fonksiyonları basitleştir ({len(results['complexity'])} fonksiyon çok karmaşık)")
    
    high_smells = [s for s in results['smells'] if s.severity == 'high']
    if high_smells:
        actions.append(f"4. Kritik code smell'leri düzelt ({len(high_smells)} adet)")
    
    if actions:
        for action in actions:
            print(f"   {action}")
    else:
        print("   ✅ Öncelikli aksiyon yok, kod kalitesi iyi!")
    
    # Markdown raporu kaydet
    report_content = f"""# Code Quality Analysis Report

Date: {datetime.now().isoformat()}

## Overall Score: {scores['overall']:.1f}/100 ({grade})

{message}

## Detailed Scores

| Metric | Score | Status |
|--------|-------|--------|
| DRY | {scores['dry']:.1f}/100 | {'✅' if scores['dry'] >= 80 else '⚠️'} |
| SRP | {scores['srp']:.1f}/100 | {'✅' if scores['srp'] >= 80 else '⚠️'} |
| Complexity | {scores['complexity']:.1f}/100 | {'✅' if scores['complexity'] >= 80 else '⚠️'} |
| Code Smells | {scores['smells']:.1f}/100 | {'✅' if scores['smells'] >= 80 else '⚠️'} |

## Statistics

- Duplicate code groups: {len(results['dry'])}
- SRP violations: {len(results['srp'])}
- Complex functions: {len(results['complexity'])}
- Code smells: {len(results['smells'])}

## Priority Actions
"""
    
    if actions:
        for action in actions:
            report_content += f"\n{action}"
    else:
        report_content += "\n✅ No priority actions needed!"
    
    # Kaydet
    report_file = Path('CODE_QUALITY_REPORT.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n💾 Detaylı rapor kaydedildi: {report_file}")


if __name__ == "__main__":
    results, scores = run_full_quality_analysis()
