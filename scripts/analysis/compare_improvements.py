"""
İyileştirme öncesi ve sonrası metrikleri karşılaştırma scripti
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def compare_catboost_ndcg5(current_ndcg5):
    """CatBoost NDCG@5 iyileştirmesini karşılaştır"""
    baseline_file = Path("reports/baseline_improvement_1_catboost_ndcg5.json")
    
    if not baseline_file.exists():
        print("❌ Baseline dosyası bulunamadı!")
        return
    
    with open(baseline_file, 'r') as f:
        baseline = json.load(f)
    
    print("\n" + "="*60)
    print("📊 İYİLEŞTİRME 1: CatBoost NDCG@5 Karşılaştırması")
    print("="*60)
    
    # Baseline NDCG@5 (önceki değerlendirmeden bilinen değer)
    baseline_ndcg5 = 0.4990
    
    diff = current_ndcg5 - baseline_ndcg5
    diff_pct = (diff / baseline_ndcg5) * 100
    
    status = "✅" if diff > 0 else "❌" if diff < 0 else "➖"
    
    print(f"\n🐱 CatBoost NDCG@5 Metrikleri:")
    print("-"*60)
    print(f"  Baseline NDCG@5: {baseline_ndcg5:.4f}")
    print(f"  Current NDCG@5:  {current_ndcg5:.4f}")
    print(f"  {status} Değişim:      {diff:+.4f} ({diff_pct:+.2f}%)")
    print()
    
    # Hedef karşılaştırması
    target = 0.65
    print(f"  🎯 Hedef NDCG@5: {target:.4f}")
    if current_ndcg5 >= target:
        print(f"    ✅ Hedef aşıldı! (+{(current_ndcg5 - target):.4f})")
    else:
        print(f"    ⚠️  Hedefe kalan: {(target - current_ndcg5):.4f}")
    
    # Değerlendirme
    print("\n📝 Değerlendirme:")
    print("-"*60)
    if diff > 0.10:
        print("  ✅ Mükemmel iyileştirme! NDCG@5 önemli ölçüde arttı.")
    elif diff > 0.05:
        print("  ✅ İyi iyileştirme! NDCG@5 kayda değer şekilde arttı.")
    elif diff > 0:
        print("  ➖ Küçük iyileştirme. Daha fazla optimizasyon gerekebilir.")
    else:
        print("  ❌ İyileştirme başarısız. Parametreleri gözden geçirin.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    # Komut satırından NDCG@5 değeri al
    if len(sys.argv) > 1:
        current_ndcg5 = float(sys.argv[1])
        compare_catboost_ndcg5(current_ndcg5)
    else:
        print("❌ Kullanım: python compare_improvements.py <current_ndcg5>")
        print("   Örnek: python compare_improvements.py 0.6299")
