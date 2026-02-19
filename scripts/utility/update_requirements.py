import subprocess
import sys
import os

def update_requirements():
    """
    Kullanılan paketleri tespit et ve requirements.txt'e ekle.
    """
    
    print("="*70)
    print("REQUIREMENTS.TXT GÜNCELLEME")
    print("="*70)
    
    # Eksik paketler
    missing_packages = [
        'pandas_datareader>=0.10.0',
        'torch>=2.0.0',
        # 'torchvision>=0.15.0', # Visualization not strictly needed maybe
        'pytorch-forecasting>=0.10.0',
        'fastapi>=0.100.0',
        'pydantic>=2.0.0',
        'uvicorn>=0.20.0',
        'catboost>=1.2.0',
        'shap>=0.41.0',
        'optuna>=3.0.0',
        'yfinance>=0.2.0',
        'pandas-ta>=0.3.14b',
        'quantstats>=0.0.59',
        'mlflow>=2.0.0',
        'seaborn>=0.12.0',
        'pykap>=0.0.5', # User mentioned pykap
    ]
    
    # Mevcut requirements oku
    req_path = 'requirements.txt'
    if not os.path.exists(req_path):
        req_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'requirements.txt')
    
    try:
        with open(req_path, 'r') as f:
            current = f.read()
    except FileNotFoundError:
        current = ""
        print(f"⚠️ {req_path} bulunamadı, yeni oluşturulacak.")
    
    # Eksikleri ekle
    additions = []
    for pkg in missing_packages:
        pkg_name = pkg.split('>=')[0].split('==')[0]
        
        if pkg_name not in current:
            additions.append(pkg)
            print(f"➕ Ekleniyor: {pkg}")
    
    if additions:
        with open(req_path, 'a') as f:
            f.write("\n# Otomatik eklenenler (Entegrasyon Fix):\n")
            for pkg in additions:
                f.write(f"{pkg}\n")
        
        print(f"\n✅ {len(additions)} paket eklendi: {req_path}")
        print("\n💡 Yüklemek için:")
        print("   pip install -r requirements.txt")
    else:
        print(f"\n✅ Tüm paketler zaten mevcut: {req_path}")

if __name__ == "__main__":
    update_requirements()
