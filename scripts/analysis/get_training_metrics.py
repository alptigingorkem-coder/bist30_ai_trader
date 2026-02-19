"""
Model Eğitim Metriklerini Toplama ve Raporlama Scripti
Docker konteynerinde çalıştırılabilir
"""
import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def read_mlflow_metric(metric_file):
    """MLflow metrik dosyasından son değeri oku"""
    try:
        with open(metric_file, 'r') as f:
            lines = f.readlines()
            if lines:
                # Format: timestamp value step
                last_line = lines[-1].strip().split()
                if len(last_line) >= 2:
                    return float(last_line[1])
    except Exception as e:
        print(f"  ⚠️  Metrik okunamadı: {metric_file} - {e}")
    return None

def get_tft_metrics():
    """TFT (Temporal Fusion Transformer) model metriklerini topla"""
    print("\n" + "="*60)
    print("🔮 TFT (Temporal Fusion Transformer) Model Metrikleri")
    print("="*60)
    
    # En son run'ı bul
    mlruns_path = Path("mlruns/841538924320409537")
    
    if not mlruns_path.exists():
        print("❌ MLflow runs bulunamadı!")
        return {}
    
    # Tüm run'ları tara
    runs = [d for d in mlruns_path.iterdir() if d.is_dir() and d.name != "models"]
    
    if not runs:
        print("❌ Hiç run bulunamadı!")
        return {}
    
    # En son run'ı seç (en yüksek timestamp)
    latest_run = max(runs, key=lambda x: x.stat().st_mtime)
    
    print(f"\n📁 Run ID: {latest_run.name}")
    
    metrics_path = latest_run / "metrics"
    
    if not metrics_path.exists():
        print("❌ Metrik klasörü bulunamadı!")
        return {}
    
    # Metrikleri oku
    metrics = {}
    
    metric_files = {
        'val_loss': 'Validation Loss',
        'train_loss_epoch': 'Training Loss',
        'val_MAE': 'Validation MAE',
        'val_RMSE': 'Validation RMSE',
        'val_MAPE': 'Validation MAPE',
        'val_SMAPE': 'Validation SMAPE'
    }
    
    for metric_file, metric_name in metric_files.items():
        file_path = metrics_path / metric_file
        if file_path.exists():
            value = read_mlflow_metric(file_path)
            if value is not None:
                metrics[metric_name] = value
                print(f"  ✅ {metric_name:25s}: {value:.6f}")
    
    # Parametreleri oku
    params_path = latest_run / "params"
    if params_path.exists():
        print(f"\n📊 Model Parametreleri:")
        param_files = {
            'learning_rate': 'Learning Rate',
            'hidden_size': 'Hidden Size',
            'attention_head_size': 'Attention Heads',
            'dropout': 'Dropout',
            'lstm_layers': 'LSTM Layers'
        }
        
        for param_file, param_name in param_files.items():
            file_path = params_path / param_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    value = f.read().strip()
                    print(f"  • {param_name:20s}: {value}")
    
    return metrics

def get_lightgbm_metrics():
    """LightGBM model metriklerini topla"""
    print("\n" + "="*60)
    print("🌳 LightGBM Ranking Model Metrikleri")
    print("="*60)
    
    # Model dosyasını kontrol et
    model_path = Path("models/saved/global_ranker.pkl")
    
    if not model_path.exists():
        print("❌ LightGBM model dosyası bulunamadı!")
        return {}
    
    print(f"\n✅ Model Dosyası: {model_path}")
    print(f"   Boyut: {model_path.stat().st_size / 1024:.2f} KB")
    
    # Raporlardan NDCG metriklerini oku
    metrics = {}
    
    # project_metrics_summary.md'den oku
    summary_path = Path("reports/project_metrics_summary.md")
    if summary_path.exists():
        with open(summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # NDCG değerlerini parse et
            if 'NDCG@1' in content:
                import re
                ndcg1_match = re.search(r'NDCG@1.*?\*\*(\d+\.\d+)\*\*', content)
                ndcg3_match = re.search(r'NDCG@3.*?\*\*(\d+\.\d+)\*\*', content)
                ndcg5_match = re.search(r'NDCG@5.*?\*\*(\d+\.\d+)\*\*', content)
                
                if ndcg1_match:
                    metrics['NDCG@1'] = float(ndcg1_match.group(1))
                    print(f"  ✅ NDCG@1 (Top-1 Accuracy): {metrics['NDCG@1']:.4f}")
                
                if ndcg3_match:
                    metrics['NDCG@3'] = float(ndcg3_match.group(1))
                    print(f"  ✅ NDCG@3 (Top-3 Accuracy): {metrics['NDCG@3']:.4f}")
                
                if ndcg5_match:
                    metrics['NDCG@5'] = float(ndcg5_match.group(1))
                    print(f"  ✅ NDCG@5 (Top-5 Accuracy): {metrics['NDCG@5']:.4f}")
    
    return metrics

def get_catboost_metrics():
    """CatBoost model metriklerini topla"""
    print("\n" + "="*60)
    print("🐱 CatBoost Ranking Model Metrikleri")
    print("="*60)
    
    # Model dosyasını kontrol et
    model_path = Path("models/saved/global_ranker_catboost.cbm")
    
    if not model_path.exists():
        print("❌ CatBoost model dosyası bulunamadı!")
        return {}
    
    print(f"\n✅ Model Dosyası: {model_path}")
    print(f"   Boyut: {model_path.stat().st_size / 1024:.2f} KB")
    
    # Raporlardan NDCG metriklerini oku
    metrics = {}
    
    summary_path = Path("reports/project_metrics_summary.md")
    if summary_path.exists():
        with open(summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # CatBoost NDCG değerlerini parse et
            if 'CatBoost' in content:
                import re
                ndcg_match = re.search(r'CatBoost.*?NDCG.*?\*\*(\d+\.\d+)\*\*', content)
                ndcg5_match = re.search(r'CatBoost.*?NDCG@5.*?\*\*(\d+\.\d+)\*\*', content)
                
                if ndcg_match:
                    metrics['NDCG (Base)'] = float(ndcg_match.group(1))
                    print(f"  ✅ NDCG (Base Score): {metrics['NDCG (Base)']:.4f}")
                
                if ndcg5_match:
                    metrics['NDCG@5'] = float(ndcg5_match.group(1))
                    print(f"  ✅ NDCG@5: {metrics['NDCG@5']:.4f}")
    
    return metrics

def generate_summary_report(all_metrics):
    """Tüm metrikleri özetleyen rapor oluştur"""
    print("\n" + "="*60)
    print("📋 MODEL EĞİTİM METRİKLERİ ÖZET RAPORU")
    print("="*60)
    
    # JSON formatında kaydet
    output_file = "reports/training_metrics_summary.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Rapor kaydedildi: {output_file}")
    
    # Konsol özeti
    print("\n" + "-"*60)
    print("🎯 Öne Çıkan Metrikler:")
    print("-"*60)
    
    if 'LightGBM' in all_metrics and 'NDCG@3' in all_metrics['LightGBM']:
        print(f"  • LightGBM NDCG@3: {all_metrics['LightGBM']['NDCG@3']:.4f} (Hedef: >0.60)")
    
    if 'CatBoost' in all_metrics and 'NDCG (Base)' in all_metrics['CatBoost']:
        print(f"  • CatBoost NDCG: {all_metrics['CatBoost']['NDCG (Base)']:.4f} (Hedef: >0.70)")
    
    if 'TFT' in all_metrics and 'Validation Loss' in all_metrics['TFT']:
        print(f"  • TFT Val Loss: {all_metrics['TFT']['Validation Loss']:.6f} (Hedef: <0.01)")
    
    print("\n" + "="*60)

def main():
    """Ana fonksiyon"""
    print("\n" + "="*60)
    print("🚀 BIST30 AI TRADER - MODEL EĞİTİM METRİKLERİ")
    print("="*60)
    
    all_metrics = {}
    
    # LightGBM metrikleri
    lgbm_metrics = get_lightgbm_metrics()
    if lgbm_metrics:
        all_metrics['LightGBM'] = lgbm_metrics
    
    # CatBoost metrikleri
    catboost_metrics = get_catboost_metrics()
    if catboost_metrics:
        all_metrics['CatBoost'] = catboost_metrics
    
    # TFT metrikleri
    tft_metrics = get_tft_metrics()
    if tft_metrics:
        all_metrics['TFT'] = tft_metrics
    
    # Özet rapor
    if all_metrics:
        generate_summary_report(all_metrics)
    else:
        print("\n❌ Hiç metrik bulunamadı!")
    
    print("\n✅ İşlem tamamlandı!\n")

if __name__ == "__main__":
    main()
