#!/usr/bin/env python3
"""
SRP (Single Responsibility Principle) Violation Checker
Her sınıf/fonksiyonun tek bir sorumluluğu olup olmadığını kontrol eder.
"""

import ast
from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class Responsibility:
    """Bir sorumluluk."""
    name: str
    indicators: List[str]  # Kod içinde aranan kelimeler


@dataclass
class ClassAnalysis:
    """Sınıf analizi."""
    name: str
    file: str
    line: int
    methods: List[str]
    responsibilities: List[Responsibility]
    lines_of_code: int
    complexity_score: float


class SRPAnalyzer:
    """SRP ihlallerini tespit eder."""
    
    # Farklı sorumluluklar
    RESPONSIBILITIES = [
        Responsibility("Data Access", ["fetch", "load", "save", "query", "insert", "update", "delete"]),
        Responsibility("Business Logic", ["calculate", "compute", "process", "validate", "check"]),
        Responsibility("Presentation", ["format", "render", "display", "print", "show"]),
        Responsibility("Logging", ["log", "debug", "info", "warning", "error"]),
        Responsibility("Error Handling", ["try", "except", "catch", "raise", "throw"]),
        Responsibility("Configuration", ["config", "setup", "initialize", "configure"]),
        Responsibility("Communication", ["send", "receive", "request", "response", "api", "http"]),
        Responsibility("File Operations", ["read", "write", "open", "close", "file"]),
    ]
    
    def analyze_project(self, project_root: Path = Path.cwd()):
        """Tüm projeyi SRP ihlalleri için analiz et."""
        print("="*70)
        print("2️⃣ SRP (Single Responsibility Principle) ANALİZİ")
        print("="*70)
        
        python_files = [
            f for f in project_root.rglob("*.py")
            if '__pycache__' not in str(f) and 'venv' not in str(f) and '.venv' not in str(f)
        ]
        
        violations = []
        for py_file in python_files:
            violations.extend(self._analyze_file(py_file))
        
        # Rapor
        self._report_violations(violations)
        
        return violations
    
    def _analyze_file(self, filepath: Path) -> List[ClassAnalysis]:
        """Bir dosyadaki sınıfları analiz et."""
        violations = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
        except:
            return violations
        
        rel_path = filepath.relative_to(Path.cwd())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                analysis = self._analyze_class(node, str(rel_path))
                
                # SRP ihlali mi?
                if len(analysis.responsibilities) > 2:  # >2 sorumluluk = ihlal
                    violations.append(analysis)
        
        return violations
    
    def _analyze_class(self, node: ast.ClassDef, filepath: str) -> ClassAnalysis:
        """Bir sınıfı analiz et."""
        # Method'ları topla
        methods = [
            m.name for m in node.body
            if isinstance(m, ast.FunctionDef)
        ]
        
        # Kod satırı
        lines = node.end_lineno - node.lineno
        
        # Sorumlulukları tespit et
        responsibilities = self._detect_responsibilities(node)
        
        # Complexity score
        complexity = self._calculate_complexity(node)
        
        return ClassAnalysis(
            name=node.name,
            file=filepath,
            line=node.lineno,
            methods=methods,
            responsibilities=responsibilities,
            lines_of_code=lines,
            complexity_score=complexity
        )
    
    def _detect_responsibilities(self, node: ast.ClassDef) -> List[Responsibility]:
        """Sınıfın sorumluluklarını tespit et."""
        # Tüm kodu string'e çevir
        code_text = ast.unparse(node).lower()
        
        detected = []
        for resp in self.RESPONSIBILITIES:
            # Indicator'lardan herhangi biri var mı?
            if any(indicator in code_text for indicator in resp.indicators):
                detected.append(resp)
        
        return detected
    
    def _calculate_complexity(self, node: ast.ClassDef) -> float:
        """Sınıfın complexity score'unu hesapla."""
        # Basit metrik: method sayısı + kod satırı / 100
        method_count = len([
            m for m in node.body
            if isinstance(m, ast.FunctionDef)
        ])
        lines = node.end_lineno - node.lineno
        
        complexity = (method_count * 2) + (lines / 100)
        return complexity
    
    def _report_violations(self, violations: List[ClassAnalysis]):
        """SRP ihlallerini raporla."""
        if not violations:
            print("\n✅ SRP İHLALİ BULUNAMADI!")
            print("   Tüm sınıflar tek sorumluluk prensibi ile uyumlu.")
            return
        
        # Severity'e göre sırala (en çok sorumluluk + en büyük)
        violations.sort(
            key=lambda v: (len(v.responsibilities), v.lines_of_code),
            reverse=True
        )
        
        print(f"\n⚠️  {len(violations)} SRP İHLALİ TESPİT EDİLDİ")
        print(f"\n🔴 EN KRİTİK 10 İHLAL:")
        
        for i, v in enumerate(violations[:10], 1):
            severity = self._get_severity(v)
            print(f"\n{i}. {v.file}:{v.line}")
            print(f"   Sınıf: {v.name}")
            print(f"   Satır sayısı: {v.lines_of_code}")
            print(f"   Method sayısı: {len(v.methods)}")
            print(f"   Sorumluluk sayısı: {len(v.responsibilities)} {severity}")
            print(f"   Complexity: {v.complexity_score:.1f}")
            
            print(f"\n   Tespit edilen sorumluluklar:")
            for resp in v.responsibilities:
                print(f"     - {resp.name}")
            
            # Refactoring önerisi
            print(f"\n   💡 ÖNERİ:")
            suggestions = self._suggest_refactoring(v)
            for sug in suggestions:
                print(f"     - {sug}")
    
    def _get_severity(self, analysis: ClassAnalysis) -> str:
        """Severity emoji'si döndür."""
        count = len(analysis.responsibilities)
        if count >= 5:
            return "🔴 KRİTİK"
        elif count >= 3:
            return "🟠 YÜKSEK"
        else:
            return "🟡 ORTA"
    
    def _suggest_refactoring(self, analysis: ClassAnalysis) -> List[str]:
        """Refactoring önerileri üret."""
        suggestions = []
        resp_names = [r.name for r in analysis.responsibilities]
        
        # Data Access varsa
        if "Data Access" in resp_names:
            suggestions.append(f"Repository pattern: {analysis.name}Repository oluştur")
        
        # Presentation varsa
        if "Presentation" in resp_names:
            suggestions.append(f"Formatter class: {analysis.name}Formatter oluştur")
        
        # Business Logic + Data Access varsa
        if "Business Logic" in resp_names and "Data Access" in resp_names:
            suggestions.append(f"Service layer: {analysis.name}Service + {analysis.name}Repository'ye böl")
        
        # Çok büyükse
        if analysis.lines_of_code > 500:
            suggestions.append(f"Sınıf çok büyük ({analysis.lines_of_code} satır), küçük sınıflara böl")
        
        # Çok method varsa
        if len(analysis.methods) > 20:
            suggestions.append(f"Çok fazla method ({len(analysis.methods)}), ilgili method'ları grupla ve ayrı sınıflara taşı")
        
        return suggestions if suggestions else ["Sınıfı daha küçük, odaklanmış sınıflara böl"]


if __name__ == "__main__":
    analyzer = SRPAnalyzer()
    violations = analyzer.analyze_project()
