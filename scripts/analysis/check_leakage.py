
import ast
import os

def check_leakage_in_code():
    """
    Backtest ve feature engineering kodlarında 
    potansiyel leakage pattern'lerini tespit et.
    """
    
    leakage_patterns = {
        "Tehlikeli Pattern'ler": [
            "df['Target'] = df['Close'].shift(-1)",  # Gelecek günün kapanışı
            "df['NextDay_Return'] = df['Return'].shift(-1)",  # Gelecek getiri
            ".shift(-",  # Negatif shift (gelecek verisi)
            "future_",  # 'future_' ile başlayan değişkenler
            "next_day",  # 'next_day' içeren değişkenler
            "tomorrow",  # 'tomorrow' içeren değişkenler
        ],
        
        "Şüpheli Pattern'ler": [
            "pct_change()",  # Shift kontrol edilmeli
            ".diff()",  # Shift kontrol edilmeli
            "rolling(",  # Window sonrası shift var mı?
            ".expanding(",  # Aynı şekilde
        ]
    }
    
    files_to_check = [
        "core/backtesting.py",
        "core/backtest/engine.py",
        "core/dynamic_backtest.py",
        "utils/feature_engineering.py",
        "utils/features/__init__.py",
        "utils/features/technical.py",
        "utils/features/macro.py",
        "utils/features/targets.py",
    ]
    
    print("="*70)
    print("VERİ SIZINTISI (LEAKAGE) KONTROLÜ")
    print("="*70)
    
    leakage_found = False
    
    for filepath in files_to_check:
        if not os.path.exists(filepath):
            print(f"⚠️  {filepath} bulunamadı, atlanıyor...")
            continue
        
        print(f"\n🔍 İnceleniyor: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Tehlikeli pattern'leri ara
        for pattern in leakage_patterns["Tehlikeli Pattern'ler"]:
            if pattern in content:
                # Target generation is expected to use shift(-1), flag it but check context
                if "Target" in pattern and "targets.py" in filepath:
                     print(f"  ℹ️  INFO: '{pattern}' bulundu (Target dosyasında beklenebilir)")
                else:
                    leakage_found = True
                    print(f"  🔴 TEHLİKELİ: '{pattern}' bulundu!")
                
                # Hangi satırda olduğunu bul
                for i, line in enumerate(lines, 1):
                    if pattern in line:
                        print(f"     Satır {i}: {line.strip()}")
        
        # Şüpheli pattern'leri ara
        for pattern in leakage_patterns["Şüpheli Pattern'ler"]:
            if pattern in content:
                # Don't print suspicious patterns for now to reduce noise, unless critical
                # print(f"  🟡 ŞÜPHELİ: '{pattern}' bulundu (kontrol edin)")
                pass
    
    print("\n" + "="*70)
    if leakage_found:
        print("❌ SONUÇ: VERİ SIZINTISI RİSKİ YÜKSEK!")
        print("   Yukarıdaki satırları inceleyin ve düzeltin.")
    else:
        print("✅ SONUÇ: Açık leakage pattern'i bulunamadı.")
        print("   Ancak manuel inceleme hala önerilir.")
    print("="*70)
    
    return leakage_found

if __name__ == "__main__":
    check_leakage_in_code()
