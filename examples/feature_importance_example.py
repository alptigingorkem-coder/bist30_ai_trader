#!/usr/bin/env python3
"""
LightGBM Feature Importance Analizi - Örnek Kullanım

Bu script, SHAP tabanlı feature importance analizi sisteminin
adım adım kullanımını gösterir.
"""

import sys
sys.path.append('..')  # Proje root'una erişim için

from scripts.analysis.feature_importance_analyzer import FeatureImportanceAnalyzer
from scripts.analysis.feature_importance_config import AnalysisConfig
import config

import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime

print("=" * 80)
print("LightGBM Feature Importance Analizi - Örnek Kullanım")
print("=" * 80)
print()

# ============================================================================
# 1. TEMEL KULLANIM
# ============================================================================

print("1. TEMEL KULLANIM")
print("-" * 80)

# Basit yapılandırma ile analiz
print("\n→ Basit yapılandırma ile analiz başlatılıyor...")

analyzer = FeatureImportanceAnalyzer(
    config_module=config,
    analysis_config=None  # Varsayılan ayarlar kullanılacak
)

# Analizi çalıştır
result = analyzer.run_analysis()

print(f"\n✓ Analiz tamamlandı!")
print(f"  - Baseline NDCG@3: {result.baseline_ndcg3:.4f}")
print(f"  - Optimized NDCG@3: {result.optimized_ndcg3:.4f}")
print(f"  - İyileştirme: {result.improvement_pct:.2f}%")
print(f"  - Blacklisted features: {len(result.blacklist)}/{result.total_features}")

# ============================================================================
# 2. ÖZEL YAPILANDIRMA İLE KULLANIM
# ============================================================================

print("\n\n2. ÖZEL YAPILANDIRMA İLE KULLANIM")
print("-" * 80)

# Özel yapılandırma oluştur
analysis_config = AnalysisConfig(
    sample_size=2000,  # Daha yüksek doğruluk için
    importance_threshold=0.001,  # Dengeli filtreleme
    start_date="2023-01-01",
    end_date="2023-12-31",
    tickers=["THYAO", "AKBNK", "EREGL"],  # Belirli ticker'lar
    output_dir="reports/custom_analysis",
    save_models=True  # Modelleri kaydet
)

print("\n→ Özel yapılandırma:")
print(f"  - Sample size: {analysis_config.sample_size}")
print(f"  - Threshold: {analysis_config.importance_threshold}")
print(f"  - Tickers: {', '.join(analysis_config.tickers)}")
print(f"  - Date range: {analysis_config.start_date} to {analysis_config.end_date}")

# Analyzer oluştur ve çalıştır
analyzer_custom = FeatureImportanceAnalyzer(
    config_module=config,
    analysis_config=analysis_config
)

print("\n→ Analiz başlatılıyor...")
result_custom = analyzer_custom.run_analysis()

print(f"\n✓ Özel analiz tamamlandı!")
print(f"  - Baseline NDCG@3: {result_custom.baseline_ndcg3:.4f}")
print(f"  - Optimized NDCG@3: {result_custom.optimized_ndcg3:.4f}")
print(f"  - İyileştirme: {result_custom.improvement_pct:.2f}%")

# ============================================================================
# 3. SONUÇLARI İNCELEME
# ============================================================================

print("\n\n3. SONUÇLARI İNCELEME")
print("-" * 80)

# Feature importance tablosunu incele
print("\n→ Top 10 En Önemli Feature'lar:")
print()
top_10 = result.importance_df.head(10)
for idx, row in top_10.iterrows():
    print(f"  {idx+1:2d}. {row['feature']:30s} {row['importance']:.6f}")

# Blacklist'i incele
print(f"\n→ Blacklist'e Alınan Feature'lar ({len(result.blacklist)}):")
if len(result.blacklist) <= 10:
    for feature in result.blacklist:
        print(f"  - {feature}")
else:
    for feature in result.blacklist[:5]:
        print(f"  - {feature}")
    print(f"  ... ve {len(result.blacklist) - 5} feature daha")

# Metadata'yı incele
print(f"\n→ Analiz Metadata:")
print(f"  - Timestamp: {result.timestamp}")
print(f"  - Duration: {result.analysis_duration:.2f} seconds")
print(f"  - Data size: {result.data_size} rows")
print(f"  - Tickers: {', '.join(result.tickers_analyzed)}")

# ============================================================================
# 4. BLACKLIST DOSYASINI OKUMA
# ============================================================================

print("\n\n4. BLACKLIST DOSYASINI OKUMA")
print("-" * 80)

# Kaydedilmiş blacklist'i yükle
blacklist_path = "models/saved/feature_blacklist.json"
try:
    with open(blacklist_path, 'r') as f:
        blacklist = json.load(f)
    
    print(f"\n→ Blacklist dosyası yüklendi: {blacklist_path}")
    print(f"  - Feature sayısı: {len(blacklist)}")
    print(f"  - İlk 5 feature:")
    for feature in blacklist[:5]:
        print(f"    - {feature}")
except FileNotFoundError:
    print(f"\n⚠ Blacklist dosyası bulunamadı: {blacklist_path}")

# ============================================================================
# 5. FEATURE IMPORTANCE GRAFİĞİ OLUŞTURMA
# ============================================================================

print("\n\n5. FEATURE IMPORTANCE GRAFİĞİ OLUŞTURMA")
print("-" * 80)

# Top 20 feature'ı görselleştir
top_20 = result.importance_df.head(20)

plt.figure(figsize=(12, 8))
plt.barh(range(len(top_20)), top_20['importance'])
plt.yticks(range(len(top_20)), top_20['feature'])
plt.xlabel('SHAP Importance')
plt.title('Top 20 Most Important Features')
plt.gca().invert_yaxis()
plt.tight_layout()

output_file = "reports/feature_importance/custom_top_features.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n→ Grafik kaydedildi: {output_file}")

# ============================================================================
# 6. MODEL KARŞILAŞTIRMA ANALİZİ
# ============================================================================

print("\n\n6. MODEL KARŞILAŞTIRMA ANALİZİ")
print("-" * 80)

# Karşılaştırma metrikleri
comparison = {
    'Metric': ['NDCG@3', 'Feature Count', 'Improvement'],
    'Baseline': [
        f"{result.baseline_ndcg3:.4f}",
        str(result.total_features),
        "-"
    ],
    'Optimized': [
        f"{result.optimized_ndcg3:.4f}",
        str(result.remaining_features),
        f"+{result.improvement_pct:.2f}%"
    ]
}

df_comparison = pd.DataFrame(comparison)
print("\n→ Model Karşılaştırması:")
print(df_comparison.to_string(index=False))

# Feature azalma yüzdesi
feature_reduction = (result.blacklisted_features / result.total_features) * 100
print(f"\n→ Feature Azalma: {feature_reduction:.1f}%")
print(f"  ({result.total_features} → {result.remaining_features} features)")

# ============================================================================
# 7. ÇOKLU THRESHOLD KARŞILAŞTIRMASI
# ============================================================================

print("\n\n7. ÇOKLU THRESHOLD KARŞILAŞTIRMASI")
print("-" * 80)

thresholds = [0.0005, 0.001, 0.005, 0.01]
threshold_results = []

print("\n→ Farklı threshold değerleri test ediliyor...")

for threshold in thresholds:
    print(f"\n  Testing threshold: {threshold}")
    
    config_test = AnalysisConfig(
        sample_size=1000,
        importance_threshold=threshold,
        tickers=["THYAO", "AKBNK"],  # Hızlı test için az ticker
        output_dir=f"reports/threshold_{threshold}"
    )
    
    analyzer_test = FeatureImportanceAnalyzer(
        config_module=config,
        analysis_config=config_test
    )
    
    result_test = analyzer_test.run_analysis()
    
    threshold_results.append({
        'Threshold': threshold,
        'Blacklisted': len(result_test.blacklist),
        'Remaining': result_test.remaining_features,
        'NDCG@3': result_test.optimized_ndcg3,
        'Improvement': result_test.improvement_pct
    })
    
    print(f"    Blacklisted: {len(result_test.blacklist)}, "
          f"NDCG@3: {result_test.optimized_ndcg3:.4f}, "
          f"Improvement: {result_test.improvement_pct:.2f}%")

# Sonuçları tablo olarak göster
df_thresholds = pd.DataFrame(threshold_results)
print("\n→ Threshold Karşılaştırma Tablosu:")
print(df_thresholds.to_string(index=False))

# En iyi threshold'u bul
best_idx = df_thresholds['Improvement'].idxmax()
best_threshold = df_thresholds.loc[best_idx, 'Threshold']
best_improvement = df_thresholds.loc[best_idx, 'Improvement']

print(f"\n→ En İyi Threshold: {best_threshold}")
print(f"  İyileştirme: {best_improvement:.2f}%")

# ============================================================================
# 8. RANKINGMODEL ENTEGRASYONU
# ============================================================================

print("\n\n8. RANKINGMODEL ENTEGRASYONU")
print("-" * 80)

print("\n→ RankingModel blacklist entegrasyonu:")
print("  1. Blacklist otomatik olarak 'models/saved/feature_blacklist.json' konumuna kaydedildi")
print("  2. RankingModel bu dosyayı otomatik olarak okur")
print("  3. Blacklist'teki feature'lar model eğitiminde filtrelenir")
print()
print("  Örnek kullanım:")
print("  ```python")
print("  from models.ranking_model import RankingModel")
print("  ")
print("  # Blacklist otomatik olarak yüklenir")
print("  model = RankingModel(data, config)")
print("  model.prepare_data(is_training=True)")
print("  # Blacklist'teki feature'lar filtrelenmiş olacak")
print("  ```")

# ============================================================================
# 9. ÖNERİLER VE SONRAKI ADIMLAR
# ============================================================================

print("\n\n9. ÖNERİLER VE SONRAKI ADIMLAR")
print("-" * 80)

if result.improvement_pct > 0:
    print("\n✓ Feature selection başarılı!")
    print("\n  Önerilen adımlar:")
    print("  1. Blacklist'i production'a deploy et")
    print("  2. Yeni modeli eğit ve test et")
    print("  3. A/B test yap")
    print("  4. Performansı izle")
elif result.improvement_pct < 0:
    print("\n⚠ Performans düşüşü tespit edildi!")
    print("\n  Önerilen adımlar:")
    print("  1. Threshold değerini düşür (daha az feature filtrele)")
    print("  2. Sample size'ı artır (daha doğru SHAP değerleri)")
    print("  3. Farklı tarih aralığı dene")
    print("  4. Feature engineering yap")
else:
    print("\n→ Performans değişmedi")
    print("\n  Önerilen adımlar:")
    print("  1. Threshold'u artır (daha fazla feature filtrele)")
    print("  2. Yeni feature'lar ekle")
    print("  3. Farklı feature selection yöntemleri dene")

# ============================================================================
# 10. ÖZET
# ============================================================================

print("\n\n10. ÖZET")
print("=" * 80)

print(f"\n→ Analiz Özeti:")
print(f"  - Toplam feature: {result.total_features}")
print(f"  - Blacklisted: {result.blacklisted_features} ({feature_reduction:.1f}%)")
print(f"  - Remaining: {result.remaining_features}")
print(f"  - Baseline NDCG@3: {result.baseline_ndcg3:.4f}")
print(f"  - Optimized NDCG@3: {result.optimized_ndcg3:.4f}")
print(f"  - İyileştirme: {result.improvement_pct:.2f}%")
print(f"  - Analiz süresi: {result.analysis_duration:.2f} saniye")

print("\n→ Oluşturulan Dosyalar:")
print(f"  - Blacklist: models/saved/feature_blacklist.json")
print(f"  - Rapor: reports/feature_importance/analysis_report_*.md")
print(f"  - Grafikler: reports/feature_importance/*.png")
print(f"  - Metadata: reports/feature_importance/analysis_metadata_*.json")

print("\n" + "=" * 80)
print("Analiz tamamlandı!")
print("=" * 80)
