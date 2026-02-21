#!/usr/bin/env python3
"""
Function Complexity Analyzer
Çok karmaşık fonksiyonları tespit eder (Cyclomatic Complexity).
"""

import ast
from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class FunctionComplexity:
    """Fonksiyon complexity analizi."""
    name: str
    file: str
    line: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    lines_of_code: int
    parameters: int
    nested_depth: int


class ComplexityAnalyzer:
    """Fonksiyon complexity'sini analiz eder."""
    
    def analyze_project(self, project_root: Path = Path.cwd()):
        """Tüm projeyi complexity için analiz et."""
        print("="*70)
        print("3️⃣ FUNCTION COMPLEXITY ANALİZİ")
        print("="*70)
        
        python_files = [
            f for f in project_root.rglob("*.py")
            if '__pycache__' not in str(f) and 'venv' not in str(f) and '.venv' not in str(f)
        ]
        
        all_functions = []
        for py_file in python_files:
            all_functions.extend(self._analyze_file(py_file))
        
        # En karmaşık fonksiyonlar
        complex_functions = [
            f for f in all_functions
            if f.cyclomatic_complexity > 10  # Threshold: 10
        ]
        
        # Rapor
        self._report_complexity(complex_functions, all_functions)
        
        return complex_functions
    
    def _analyze_file(self, filepath: Path) -> List[FunctionComplexity]:
        """Bir dosyadaki fonksiyonları analiz et."""
        functions = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
        except:
            return functions
        
        rel_path = filepath.relative_to(Path.cwd())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                complexity.file = str(rel_path)
                functions.append(complexity)
        
        return functions
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> FunctionComplexity:
        """Bir fonksiyonun complexity'sini hesapla."""
        # Cyclomatic Complexity: decision points sayısı
        cyclomatic = 1  # Başlangıç
        
        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                cyclomatic += 1
            elif isinstance(child, ast.BoolOp):
                cyclomatic += len(child.values) - 1
        
        # Cognitive Complexity: nested yapılar
        cognitive = self._calculate_cognitive_complexity(node)
        
        # Nested depth
        nested_depth = self._calculate_nested_depth(node)
        
        # LOC
        lines = node.end_lineno - node.lineno
        
        # Parameter sayısı
        params = len(node.args.args)
        
        return FunctionComplexity(
            name=node.name,
            file="",  # Sonra set edilecek
            line=node.lineno,
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            lines_of_code=lines,
            parameters=params,
            nested_depth=nested_depth
        )
    
    def _calculate_cognitive_complexity(self, node: ast.FunctionDef) -> int:
        """Cognitive complexity hesapla (nested yapıların ağırlığı)."""
        complexity = 0
        
        def traverse(node, depth=0):
            nonlocal complexity
            # Nested yapılar daha ağır
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += (1 + depth)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For)):
                    traverse(child, depth + 1)
                else:
                    traverse(child, depth)
        
        traverse(node)
        return complexity
    
    def _calculate_nested_depth(self, node: ast.FunctionDef) -> int:
        """Maximum nested depth hesapla."""
        max_depth = 0
        
        def traverse(node, depth=0):
            nonlocal max_depth
            if depth > max_depth:
                max_depth = depth
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                    traverse(child, depth + 1)
                else:
                    traverse(child, depth)
        
        traverse(node)
        return max_depth
    
    def _report_complexity(self,
                          complex_functions: List[FunctionComplexity],
                          all_functions: List[FunctionComplexity]):
        """Complexity raporunu yazdır."""
        if not complex_functions:
            print("\n✅ KARMAŞIK FONKSİYON BULUNAMADI!")
            print("   Tüm fonksiyonlar kabul edilebilir complexity'de.")
            return
        
        # İstatistikler
        avg_complexity = sum(f.cyclomatic_complexity for f in all_functions) / len(all_functions)
        
        print(f"\n📊 GENEL İSTATİSTİKLER:")
        print(f"   Toplam fonksiyon: {len(all_functions)}")
        print(f"   Karmaşık fonksiyon: {len(complex_functions)} (%{len(complex_functions)/len(all_functions)*100:.1f})")
        print(f"   Ortalama Cyclomatic: {avg_complexity:.1f}")
        
        # En karmaşık fonksiyonlar
        complex_functions.sort(key=lambda f: f.cyclomatic_complexity, reverse=True)
        
        print(f"\n🔴 EN KARMAŞIK 15 FONKSİYON:")
        print(f"\n{'Fonksiyon':<40} {'Dosya':<40} {'CC':>4} {'Cog':>4} {'LOC':>4} {'Params':>6} {'Depth':>5}")
        print("-" * 110)
        
        for func in complex_functions[:15]:
            severity = self._get_complexity_severity(func.cyclomatic_complexity)
            print(f"{func.name[:39]:<40} "
                  f"{func.file[:39]:<40} "
                  f"{func.cyclomatic_complexity:>4} "
                  f"{func.cognitive_complexity:>4} "
                  f"{func.lines_of_code:>4} "
                  f"{func.parameters:>6} "
                  f"{func.nested_depth:>5} "
                  f"{severity}")
        
        print("\n💡 COMPLEXITY REHBERİ:")
        print("   CC (Cyclomatic Complexity):")
        print("     1-10: ✅ Basit (test kolay)")
        print("     11-20: 🟡 Orta (dikkat)")
        print("     21-50: 🟠 Karmaşık (refactor önerilir)")
        print("     50+: 🔴 Çok karmaşık (mutlaka refactor)")
        print("\n   Cog (Cognitive Complexity):")
        print("     0-5: ✅ Anlaşılır")
        print("     6-15: 🟡 Orta")
        print("     16+: 🔴 Anlaşılması zor")
        
        # Refactoring önerileri
        print(f"\n💡 REFACTORING ÖNERİLERİ:")
        for func in complex_functions[:5]:
            print(f"\n📌 {func.name} ({func.file}:{func.line})")
            suggestions = self._suggest_simplification(func)
            for sug in suggestions:
                print(f"   - {sug}")
    
    def _get_complexity_severity(self, complexity: int) -> str:
        """Complexity severity emoji'si."""
        if complexity > 50:
            return "🔴"
        elif complexity > 20:
            return "🟠"
        elif complexity > 10:
            return "🟡"
        else:
            return "✅"
    
    def _suggest_simplification(self, func: FunctionComplexity) -> List[str]:
        """Simplification önerileri."""
        suggestions = []
        
        if func.cyclomatic_complexity > 20:
            suggestions.append("Extract method: Karmaşık blokları ayrı fonksiyonlara taşı")
        
        if func.nested_depth > 3:
            suggestions.append("Guard clauses: Early return kullanarak nested depth'i azalt")
        
        if func.parameters > 5:
            suggestions.append(f"Too many parameters ({func.parameters}): Parameter object pattern kullan")
        
        if func.lines_of_code > 100:
            suggestions.append(f"Fonksiyon çok uzun ({func.lines_of_code} satır): Daha küçük fonksiyonlara böl")
        
        if func.cognitive_complexity > 15:
            suggestions.append("Cognitive complexity yüksek: Nested if'leri basitleştir, polymorphism kullan")
        
        return suggestions


if __name__ == "__main__":
    analyzer = ComplexityAnalyzer()
    complex_funcs = analyzer.analyze_project()
