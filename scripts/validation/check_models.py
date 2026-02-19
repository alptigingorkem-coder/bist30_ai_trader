#!/usr/bin/env python3
"""
Model Training Validation
Checks if all required models are trained and up-to-date.
"""

from pathlib import Path
import time


def check_trained_models():
    """README'de belirtilen 3 model'in eğitilmiş olup olmadığını kontrol et."""
    print("=" * 70)
    print("3️⃣ MODEL EĞİTİM KONTROLÜ")
    print("=" * 70)

    models = {
        'LightGBM Ranker': {
            'paths': ['models/saved/ranking_model.pkl', 'models/saved/lgbm_model.pkl', 'models/saved/global_ranker.pkl'],
            'train_script': 'scripts/training/train_models.py',
            'weight': 10  # En kritik
        },
        'CatBoost Ranker': {
            'paths': ['models/saved/global_ranker_catboost.cbm'],
            'train_script': 'scripts/training/train_catboost.py',
            'weight': 8
        },
        'TFT': {
            'paths': ['models/saved/tft_model.ckpt', 'models/saved/tft_model.pth'],
            'train_script': 'scripts/training/train_tft.py',
            'weight': 6  # GPU gerektirebilir
        }
    }

    checks = {}
    
    for model_name, info in models.items():
        print(f"\n🤖 {model_name}:")
        
        # Check multiple possible paths
        model_path = None
        for path in info['paths']:
            if Path(path).exists():
                model_path = Path(path)
                break
        
        if model_path:
            # Model var, yaşını kontrol et
            age_days = (time.time() - model_path.stat().st_mtime) / 86400
            
            if age_days < 7:
                print(f"  ✅ Model mevcut ve güncel (yaş: {age_days:.1f} gün)")
                checks[model_name] = 100
            elif age_days < 30:
                print(f"  🟡 Model mevcut ama biraz eski (yaş: {age_days:.1f} gün)")
                print(f"  💡 Yeniden eğitmeyi düşünün: python {info['train_script']}")
                checks[model_name] = 75
            else:
                print(f"  ⚠️ Model çok eski (yaş: {age_days:.1f} gün)")
                print(f"  🔴 Mutlaka yeniden eğitin: python {info['train_script']}")
                checks[model_name] = 30
        else:
            print(f"  ❌ Model BULUNAMADI (denenen: {', '.join(info['paths'])})")
            print(f"  🔴 Eğitin: python {info['train_script']}")
            checks[model_name] = 0

    # Ağırlıklı skor
    total_weight = sum(info['weight'] for info in models.values())
    weighted_score = sum(
        checks[name] * info['weight'] / 100
        for name, info in models.items()
    )
    final_score = (weighted_score / total_weight) * 100
    
    print(f"\n📊 Model Skoru: {final_score:.1f}%")
    
    if final_score >= 90:
        status = 'PASS'
        message = "✅ Tüm modeller eğitilmiş ve güncel"
    elif final_score >= 70:
        status = 'PARTIAL'
        message = "🟡 Bazı modeller eski, yeniden eğitim önerilir"
    else:
        status = 'FAIL'
        message = "❌ Model eğitimleri eksik"
    
    print(f"\n{message}")
    
    return {
        'status': status,
        'score': final_score,
        'models': checks
    }


if __name__ == "__main__":
    result = check_trained_models()
    print(f"\nFinal Status: {result['status']}")
