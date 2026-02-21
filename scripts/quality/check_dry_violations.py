#!/usr/bin/env python3
"""
DRY (Don't Repeat Yourself) Violation Checker
Tekrar eden kod bloklarını tespit eder ve refactoring önerir.
"""

import ast
import hashlib
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class CodeBlock:
    """Bir kod bloğu."""
    file: str
    start_line: int
    end_line: int
    code: str
    hash: str
    type: str  # 'function', 'method', 'block'


@dataclass
class DuplicateGroup:
    """Duplicate kod grubu."""
    blocks: List[CodeBlock]
    similarity: float
    lines: int
    occurrences: int


class DRYAnalyzer:
    """DRY prensibi ihlallerini tespit eder."""
    
    def __init__(self, min_lines: int = 5, similarity_threshold: float = 0.85):
        self.min_lines = min_lines
        self.similarity_threshold = similarity_threshold
        self.duplicates: Dict[str, List[CodeBlock]] = defaultdict(list)
    
    def analyze_project(self, project_root: Path = Path.cwd()):
        """Tüm projeyi DRY ihlalleri için analiz et."""
        print("="*70)
        print("1️⃣ DRY (Don't Repeat Yourself) ANALİZİ")
        print("="*70)
        
        python_files = [
            f for f in project_root.rglob("*.py")
            if '__pycache__' not in str(f) and 'venv' not in str(f) and '.venv' not in str(f)
        ]
        
        print(f"\n📁 {len(python_files)} Python dosyası analiz ediliyor...")
        
        # Fonksiyon ve method'ları analiz et
        for py_file in python_files:
            self._analyze_file(py_file)
        
        # Duplicate'leri grupla
        duplicate_groups = self._group_duplicates()
        
        # Rapor
        self._report_duplicates(duplicate_groups)
        
        return duplicate_groups
    
    def _analyze_file(self, filepath: Path):
        """Tek bir dosyayı analiz et."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(filepath))
        except:
            return
        
        rel_path = filepath.relative_to(Path.cwd())
        
        # Fonksiyonları çıkar
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Fonksiyon kodunu al
                try:
                    code = ast.get_source_segment(content, node)
                    if code and len(code.split('\n')) >= self.min_lines:
                        # Normalize et (whitespace, comments ignore)
                        normalized = self._normalize_code(code)
                        code_hash = hashlib.md5(normalized.encode()).hexdigest()
                        
                        block = CodeBlock(
                            file=str(rel_path),
                            start_line=node.lineno,
                            end_line=node.end_lineno,
                            code=code,
                            hash=code_hash,
                            type='function'
                        )
                        self.duplicates[code_hash].append(block)
                except:
                    pass
    
    def _normalize_code(self, code: str) -> str:
        """Kodu normalize et (whitespace, variable names ignore)."""
        # Basit normalizasyon: whitespace'leri tek space'e indir
        lines = []
        for line in code.split('\n'):
            # Comment'leri çıkar
            if '#' in line:
                line = line[:line.index('#')]
            # Whitespace normalize
            line = ' '.join(line.split())
            if line:
                lines.append(line)
        return '\n'.join(lines)
    
    def _group_duplicates(self) -> List[DuplicateGroup]:
        """Duplicate'leri grupla."""
        groups = []
        
        for code_hash, blocks in self.duplicates.items():
            if len(blocks) > 1:  # Duplicate var
                # Similarity hesapla (exact match için 1.0)
                similarity = 1.0
                
                group = DuplicateGroup(
                    blocks=blocks,
                    similarity=similarity,
                    lines=len(blocks[0].code.split('\n')),
                    occurrences=len(blocks)
                )
                groups.append(group)
        
        # En çok tekrar edene göre sırala
        groups.sort(key=lambda g: g.occurrences * g.lines, reverse=True)
        
        return groups
    
    def _report_duplicates(self, groups: List[DuplicateGroup]):
        """Duplicate raporunu yazdır."""
        if not groups:
            print("\n✅ DRY İHLALİ BULUNAMADI!")
            print("   Tüm fonksiyonlar unique.")
            return
        
        total_duplicates = len(groups)
        total_lines = sum(g.lines * (g.occurrences - 1) for g in groups)
        
        print(f"\n⚠️  {total_duplicates} DUPLICATE KOD GRUBU TESPİT EDİLDİ")
        print(f"📊 Toplam gereksiz kod: ~{total_lines} satır")
        
        print(f"\n🔴 EN KRİTİK 10 DUPLICATE:")
        
        for i, group in enumerate(groups[:10], 1):
            impact = group.lines * (group.occurrences - 1)
            print(f"\n{i}. Duplicate Grup:")
            print(f"   Tekrar sayısı: {group.occurrences}x")
            print(f"   Satır sayısı: {group.lines}")
            print(f"   Etki: {impact} gereksiz satır")
            print(f"   Similarity: {group.similarity*100:.0f}%")
            print(f"   Lokasyonlar:")
            
            for block in group.blocks[:5]:  # İlk 5 lokasyon
                print(f"     - {block.file}:{block.start_line}-{block.end_line}")
            
            if len(group.blocks) > 5:
                print(f"     ... ve {len(group.blocks) - 5} yer daha")
            
            # Refactoring önerisi
            common_location = self._suggest_refactoring_location(group)
            print(f"\n   💡 ÖNERİ: Bu kodu {common_location} taşı")
            print(f"      Ortak fonksiyon adı: {self._suggest_function_name(group)}")
        
        return groups
    
    def _suggest_refactoring_location(self, group: DuplicateGroup) -> str:
        """Refactoring için en uygun lokasyonu öner."""
        files = [block.file for block in group.blocks]
        
        # En çok kullanılan klasör
        folders = ['/'.join(f.split('/')[:-1]) for f in files]
        most_common_folder = max(set(folders), key=folders.count)
        
        # Uygun dosya öner
        if 'utils' in most_common_folder:
            return f"{most_common_folder}/shared.py"
        elif 'core' in most_common_folder:
            return f"{most_common_folder}/helpers.py"
        else:
            return "utils/common.py"
    
    def _suggest_function_name(self, group: DuplicateGroup) -> str:
        """Fonksiyon adı öner."""
        # İlk bloğun koduna bak
        code = group.blocks[0].code
        
        # Anahtar kelimeleri çıkar
        keywords = []
        if 'calculate' in code.lower():
            keywords.append('calculate')
        if 'process' in code.lower():
            keywords.append('process')
        if 'validate' in code.lower():
            keywords.append('validate')
        if 'format' in code.lower():
            keywords.append('format')
        
        if keywords:
            return f"shared_{keywords[0]}_helper()"
        else:
            return "extract_common_logic()"


if __name__ == "__main__":
    analyzer = DRYAnalyzer(min_lines=5)
    duplicates = analyzer.analyze_project()
