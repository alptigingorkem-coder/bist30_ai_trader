import sys
import subprocess

def generate_integration_report():
    """
    Tüm entegrasyon testlerinin sonuçlarını topla ve rapor oluştur.
    """
    
    print("="*70)
    print("NİHAİ ENTEGRASYON RAPORU")
    print("="*70)
    
    python_cmd = sys.executable
    tests = [
        ('Import Bağımlılıkları', f'{python_cmd} scripts/check_integration.py'),
        ('Config Kullanımı', f'{python_cmd} scripts/check_config_usage.py'),
        ('Regime Entegrasyonu', f'{python_cmd} scripts/test_regime_integration.py'),
        ('Runtime Test', f'{python_cmd} scripts/verify_integration.py'),
        ('Requirements', f'{python_cmd} scripts/check_requirements.py'),
    ]
    
    results = {}
    
    for test_name, command in tests:
        print(f"\n{'='*70}")
        print(f"Çalıştırılıyor: {test_name}")
        print(f"{'='*70}")
        
        # increase timeout just in case
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
            
            print(result.stdout)
            if result.stderr:
                print("Hata Çıktısı:")
                print(result.stderr)
            
            results[test_name] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except subprocess.TimeoutExpired:
            print(f"❌ ZAMAN AŞIMI: {test_name} 120 saniyede tamamlanamadı.")
            results[test_name] = {'success': False, 'output': 'Timeout', 'error': 'Timeout'}
        except Exception as e:
            print(f"❌ HATA: {e}")
            results[test_name] = {'success': False, 'output': str(e), 'error': str(e)}

    
    # Özet
    print("\n" + "="*70)
    print("ENTEGRASYON SONUÇ ÖZETİ")
    print("="*70)
    
    total = len(tests)
    passed = sum(1 for r in results.values() if r['success'])
    
    for test_name, result in results.items():
        status = "✅ GEÇTİ" if result['success'] else "❌ BAŞARISIZ"
        print(f"{status}  {test_name}")
    
    print(f"\nToplam: {passed}/{total} test geçildi")
    
    if passed == total:
        print("\n🎉 TÜM ENTEGRASYON TESTLERİ BAŞARILI!")
        print("   Sistem üretime hazır.")
    else:
        print(f"\n⚠️ {total - passed} test başarısız!")
        print("   Hataları düzeltin ve tekrar test edin.")
    
    return passed == total

if __name__ == "__main__":
    success = generate_integration_report()
    sys.exit(0 if success else 1)
