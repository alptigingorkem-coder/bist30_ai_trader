#!/usr/bin/env python3
"""
Code Smell Detector
Kod kalitesi sorunlarını (code smell) tespit eder.
"""

import ast
from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class CodeSmell:
    """Bir code smell."""
    type: str
    severity: str  # 'high', 'medium', 'low'
    file: str
    line: int
    description: str
    suggestion: str


class CodeSmellDetector:
    """Code smell'leri tespit eder."""
    
    def analyze_project(self, project_root: Path = Path.cwd()):
        """Tüm projeyi code smell'ler için analiz et."""
        print("="*70)
        print("4️⃣ CODE SMELL ANALİZİ")
        print("="*70)
        
        python_files = [
            f for f in project_root.rglob("*.py")
            if '__pycache__' not in str(f) and 'venv' not in str(f) and '.venv' not in str(f)
        ]
        
        all_smells = []
        for py_file in python_files:
            all_smells.extend(self._analyze_file(py_file))
        
        # Rapor
        self._report_smells(all_smells)
        
        return all_smells
    
    def _analyze_file(self, filepath: Path) -> List[CodeSmell]:
        """Bir dosyayı code smell'ler için analiz et."""
        smells = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
        except:
            return smells
        
        rel_path = filepath.relative_to(Path.cwd())
        
        # Çeşitli smell'leri kontrol et
        smells.extend(self._check_long_functions(tree, str(rel_path)))
        smells.extend(self._check_god_classes(tree, str(rel_path)))
        smells.extend(self._check_magic_numbers(tree, str(rel_path), content))
        smells.extend(self._check_long_parameter_list(tree, str(rel_path)))
        smells.extend(self._check_dead_code(tree, str(rel_path)))
        smells.extend(self._check_commented_code(content, str(rel_path)))
        
        return smells
    
    def _check_long_functions(self, tree: ast.AST, filepath: str) -> List[CodeSmell]:
        """Çok uzun fonksiyonları tespit et."""
        smells = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                lines = node.end_lineno - node.lineno
                if lines > 50:
                    smells.append(CodeSmell(
                        type="Long Function",
                        severity='high' if lines > 100 else 'medium',
                        file=filepath,
                        line=node.lineno,
                        description=f"Fonksiyon çok uzun: {lines} satır",
                        suggestion="Fonksiyonu daha küçük, odaklanmış fonksiyonlara böl"
                    ))
        
        return smells
    
    def _check_god_classes(self, tree: ast.AST, filepath: str) -> List[CodeSmell]:
        """God class'ları tespit et (çok büyük sınıflar)."""
        smells = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                lines = node.end_lineno - node.lineno
                methods = len([m for m in node.body if isinstance(m, ast.FunctionDef)])
                
                if lines > 500 or methods > 20:
                    smells.append(CodeSmell(
                        type="God Class",
                        severity='high',
                        file=filepath,
                        line=node.lineno,
                        description=f"Çok büyük sınıf: {lines} satır, {methods} method",
                        suggestion="Sınıfı daha küçük, cohesive sınıflara böl (SRP uygula)"
                    ))
        
        return smells
    
    def _check_magic_numbers(self, tree: ast.AST, filepath: str, content: str) -> List[CodeSmell]:
        """Magic number'ları tespit et."""
        smells = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                # Numeric constant ve string constant değil
                if isinstance(node.value, (int, float)) and abs(node.value) > 1:
                    # Context kontrol et (config, test dosyası değilse)
                    if 'config' not in filepath.lower() and 'test' not in filepath.lower():
                        smells.append(CodeSmell(
                            type="Magic Number",
                            severity='low',
                            file=filepath,
                            line=node.lineno,
                            description=f"Magic number: {node.value}",
                            suggestion=f"Named constant kullan: THRESHOLD = {node.value}"
                        ))
        
        return smells[:10]  # İlk 10 ile sınırla (çok fazla olabilir)
    
    def _check_long_parameter_list(self, tree: ast.AST, filepath: str) -> List[CodeSmell]:
        """Çok parametre alan fonksiyonları tespit et."""
        smells = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if param_count > 5:
                    smells.append(CodeSmell(
                        type="Long Parameter List",
                        severity='medium',
                        file=filepath,
                        line=node.lineno,
                        description=f"{node.name}() çok fazla parametre alıyor: {param_count}",
                        suggestion="Parameter object pattern kullan veya builder pattern"
                    ))
        
        return smells
    
    def _check_dead_code(self, tree: ast.AST, filepath: str) -> List[CodeSmell]:
        """Ölü kod tespit et (kullanılmayan değişkenler)."""
        smells = []
        
        # Basit heuristic: private fonksiyonlar çağrılıyor mu?
        defined_private_funcs = set()
        called_funcs = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('_'):
                defined_private_funcs.add(node.name)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_funcs.add(node.func.id)
        
        unused = defined_private_funcs - called_funcs
        
        for func_name in unused:
            # Linenumber bulmak için tekrar traverse et
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    smells.append(CodeSmell(
                        type="Dead Code",
                        severity='low',
                        file=filepath,
                        line=node.lineno,
                        description=f"Private fonksiyon kullanılmıyor: {func_name}()",
                        suggestion="Kullanılmıyorsa sil"
                    ))
        
        return smells
    
    def _check_commented_code(self, content: str, filepath: str) -> List[CodeSmell]:
        """Commented out kod tespit et."""
        smells = []
        lines = content.split('\n')
        commented_code_count = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Comment ve kod gibi görünüyor mu?
            if stripped.startswith('#') and any(keyword in stripped
                                               for keyword in ['def ', 'class ', 'import ', 'if ', 'for ', 'while ', '=']):
                commented_code_count += 1
                if commented_code_count == 5:  # 5 satır toplandığında rapor et
                    smells.append(CodeSmell(
                        type="Commented Code",
                        severity='low',
                        file=filepath,
                        line=i - 4,
                        description="Commented out kod bloğu tespit edildi",
                        suggestion="Git kullanıyorsanız, commented kod'u silin (git history'de kalır)"
                    ))
                    commented_code_count = 0
        
        return smells
    
    def _report_smells(self, smells: List[CodeSmell]):
        """Code smell raporunu yazdır."""
        if not smells:
            print("\n✅ CODE SMELL BULUNAMADI!")
            print("   Kod temiz ve best practice'lere uygun.")
            return
        
        # Severity'e göre grupla
        by_severity = {'high': [], 'medium': [], 'low': []}
        for smell in smells:
            by_severity[smell.severity].append(smell)
        
        # Type'a göre grupla
        by_type = {}
        for smell in smells:
            if smell.type not in by_type:
                by_type[smell.type] = []
            by_type[smell.type].append(smell)
        
        # Özet
        print(f"\n📊 TOPLAM {len(smells)} CODE SMELL TESPİT EDİLDİ:")
        print(f"   🔴 Yüksek Severity: {len(by_severity['high'])}")
        print(f"   🟠 Orta Severity: {len(by_severity['medium'])}")
        print(f"   🟡 Düşük Severity: {len(by_severity['low'])}")
        
        print(f"\n📋 SMELL TİPLERİ:")
        for smell_type, smell_list in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"   {smell_type}: {len(smell_list)}")
        
        # En kritik 20'yi göster
        print(f"\n🔴 EN KRİTİK 20 CODE SMELL:")
        
        # High severity'leri önce göster
        sorted_smells = (
            by_severity['high'] +
            by_severity['medium'] +
            by_severity['low']
        )
        
        for i, smell in enumerate(sorted_smells[:20], 1):
            severity_emoji = {
                'high': '🔴',
                'medium': '🟠',
                'low': '🟡'
            }[smell.severity]
            
            print(f"\n{i}. {severity_emoji} [{smell.type}]")
            print(f"   📁 {smell.file}:{smell.line}")
            print(f"   ⚠️  {smell.description}")
            print(f"   💡 {smell.suggestion}")


if __name__ == "__main__":
    detector = CodeSmellDetector()
    smells = detector.analyze_project()
