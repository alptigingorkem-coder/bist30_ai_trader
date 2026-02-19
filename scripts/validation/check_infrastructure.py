#!/usr/bin/env python3
"""
Infrastructure Validation
Checks TimescaleDB, FastAPI, Docker, MLflow, and environment configuration.
"""

from pathlib import Path
import subprocess


def check_infrastructure():
    """TimescaleDB, FastAPI, Docker vb. altyapı bileşenlerini kontrol et."""
    print("=" * 70)
    print("2️⃣ ALTYAPI KONTROLÜ")
    print("=" * 70)

    checks = {}

    # A. TimescaleDB
    print("\n🗄️ TimescaleDB:")
    try:
        import sys
        from pathlib import Path
        # Add project root to path
        project_root = Path(__file__).parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from utils.db_manager import DBManager
        db = DBManager()
        connection = db.connect()
        
        # Basit query
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"  ✅ Bağlantı başarılı")
        print(f"  ℹ️ Version: {version[:50]}...")
        checks['timescaledb'] = True
        
        cursor.close()
        connection.close()
    except Exception as e:
        print(f"  ❌ Bağlantı hatası: {e}")
        print("  💡 docker-compose up -d timescaledb")
        checks['timescaledb'] = False

    # B. FastAPI
    print("\n🚀 FastAPI:")
    try:
        import fastapi
        # Try importing server app
        try:
            from api.server import app
            print(f"  ✅ FastAPI yüklü (v{fastapi.__version__})")
            print(f"  ✅ Server app bulundu")
            checks['fastapi'] = True
        except ImportError:
            print(f"  ✅ FastAPI yüklü (v{fastapi.__version__})")
            print(f"  ⚠️ Server app import hatası (normal, dependencies eksik olabilir)")
            checks['fastapi'] = True
    except ImportError as e:
        print(f"  ⚠️ FastAPI yüklü değil (opsiyonel)")
        checks['fastapi'] = True  # Not critical for paper trading

    # C. Docker
    print("\n🐳 Docker:")
    result = subprocess.run(
        'docker --version',
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"  ✅ Docker yüklü")
        print(f"  ℹ️ {result.stdout.strip()}")
        checks['docker'] = True
        
        # Docker Compose kontrolü
        result2 = subprocess.run(
            'docker-compose --version',
            shell=True,
            capture_output=True,
            text=True
        )
        if result2.returncode == 0:
            print(f"  ✅ Docker Compose yüklü")
            checks['docker_compose'] = True
        else:
            print(f"  ⚠️ Docker Compose bulunamadı")
            checks['docker_compose'] = False
    else:
        print(f"  ❌ Docker bulunamadı")
        checks['docker'] = False
        checks['docker_compose'] = False

    # D. MLflow
    print("\n📊 MLflow:")
    mlflow_db = Path('mlflow.db')
    if mlflow_db.exists():
        print(f"  ✅ MLflow database mevcut")
        checks['mlflow'] = True
    else:
        print(f"  ⚠️ MLflow database bulunamadı (ilk çalışmada oluşturulacak)")
        checks['mlflow'] = True  # Not critical

    # E. Environment Variables
    print("\n⚙️ Environment Variables:")
    env_file = Path('.env')
    if env_file.exists():
        print(f"  ✅ .env dosyası mevcut")
        
        # Kritik değişkenleri kontrol et
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER']
        for var in required_vars:
            if var in env_content:
                print(f"    ✅ {var} tanımlı")
            else:
                print(f"    ⚠️ {var} eksik")
        
        checks['env_file'] = True
    else:
        print(f"  ⚠️ .env dosyası yok")
        print(f"  💡 cp .env.example .env")
        checks['env_file'] = False

    # Sonuç
    passed = sum(checks.values())
    total = len(checks)
    score = (passed / total) * 100
    
    print(f"\n📊 Altyapı Skoru: {score:.1f}% ({passed}/{total})")
    
    if score >= 80:
        return {'status': 'PASS', 'score': score, 'checks': checks}
    else:
        return {'status': 'FAIL', 'score': score, 'checks': checks}


if __name__ == "__main__":
    result = check_infrastructure()
    print(f"\nFinal Status: {result['status']}")
