"""Comprehensive cleanup report generator."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import json


@dataclass
class CleanupReport:
    """Comprehensive cleanup report."""
    timestamp: datetime
    total_files: int
    average_file_size: float
    unused_files: Any
    file_sizes: Any
    duplicates: Any
    script_organization: Any
    merge_suggestions: Any
    estimated_improvements: Dict[str, Any]
    prioritized_actions: List[Tuple[str, int, int]]


class ReportGenerator:
    """Generates cleanup reports."""
    
    def __init__(self, config):
        self.config = config
        self.turkish_translations = {
            'Cleanup Report': 'Temizlik Raporu',
            'Summary': 'Özet',
            'Total Files': 'Toplam Dosya',
            'Average File Size': 'Ortalama Dosya Boyutu',
            'Unused Files': 'Kullanılmayan Dosyalar',
            'Small Files': 'Küçük Dosyalar',
            'Large Files': 'Büyük Dosyalar',
            'Duplicate Code Groups': 'Tekrarlanan Kod Grupları',
            'Script Organization': 'Script Organizasyonu',
            'Merge Suggestions': 'Birleştirme Önerileri',
            'Estimated Improvements': 'Tahmini İyileştirmeler',
            'Prioritized Actions': 'Öncelikli Aksiyonlar',
            'File Count Reduction': 'Dosya Sayısı Azaltma',
            'Average File Size Increase': 'Ortalama Dosya Boyutu Artışı',
            'Maintainability Improvement': 'Sürdürülebilirlik İyileştirmesi'
        }
    
    def generate_report(self, unused, sizes, duplicates, scripts, merges) -> CleanupReport:
        """Generate comprehensive report."""
        total_files = len(sizes.small_files) + len(sizes.large_files) + \
                     len([f for f in unused.unused_files if f not in sizes.small_files and f not in sizes.large_files])
        
        report = CleanupReport(
            timestamp=datetime.now(),
            total_files=total_files,
            average_file_size=sizes.average_size,
            unused_files=unused,
            file_sizes=sizes,
            duplicates=duplicates,
            script_organization=scripts,
            merge_suggestions=merges,
            estimated_improvements={},
            prioritized_actions=[]
        )
        
        report.estimated_improvements = self.calculate_improvements(report)
        report.prioritized_actions = self.prioritize_actions(report)
        
        return report
    
    def calculate_improvements(self, report: CleanupReport) -> Dict[str, Any]:
        """Calculate estimated improvements."""
        # File count reduction
        unused_count = len(report.unused_files.unused_files)
        merged_count = report.merge_suggestions.total_file_reduction
        file_count_reduction = ((unused_count + merged_count) / report.total_files * 100) if report.total_files > 0 else 0
        
        # Average file size increase (from merging small files)
        if report.merge_suggestions.suggestions:
            avg_merged_size = sum(s.estimated_size for s in report.merge_suggestions.suggestions) / len(report.merge_suggestions.suggestions)
            avg_size_increase = (avg_merged_size / report.average_file_size * 100 - 100) if report.average_file_size > 0 else 0
        else:
            avg_size_increase = 0
        
        # Maintainability score (weighted formula)
        file_reduction_score = min(file_count_reduction, 100) * 0.3
        duplicate_score = (1 - len(report.duplicates.duplicate_groups) / max(report.total_files, 1)) * 100 * 0.3
        size_normalization_score = (1 - (len(report.file_sizes.small_files) + len(report.file_sizes.large_files)) / max(report.total_files, 1)) * 100 * 0.2
        organization_score = (len(report.script_organization.production.scripts) / max(report.total_files, 1)) * 100 * 0.2
        
        maintainability_improvement = file_reduction_score + duplicate_score + size_normalization_score + organization_score
        
        return {
            'file_count_reduction_percent': round(file_count_reduction, 2),
            'avg_file_size_increase_percent': round(avg_size_increase, 2),
            'maintainability_improvement_score': round(maintainability_improvement, 2),
            'unused_files_count': unused_count,
            'files_to_merge': merged_count,
            'duplicate_groups': len(report.duplicates.duplicate_groups)
        }
    
    def prioritize_actions(self, report: CleanupReport) -> List[Tuple[str, int, int]]:
        """Prioritize actions by impact and effort."""
        actions = []
        
        # Remove unused files (high impact, low effort)
        if report.unused_files.unused_files:
            actions.append(('Remove unused files', 8, 2))
        
        # Eliminate duplicate code (high impact, medium effort)
        if report.duplicates.duplicate_groups:
            actions.append(('Eliminate duplicate code', 9, 5))
        
        # Merge small files (medium impact, medium effort)
        if report.merge_suggestions.suggestions:
            actions.append(('Merge small files', 6, 4))
        
        # Split large files (medium impact, high effort)
        if report.file_sizes.large_files:
            actions.append(('Split large files', 5, 7))
        
        # Reorganize scripts (low impact, low effort)
        if report.script_organization.reorganization_plan:
            actions.append(('Reorganize scripts', 4, 3))
        
        # Sort by impact (descending) then effort (ascending)
        actions.sort(key=lambda x: (-x[1], x[2]))
        
        return actions
    
    def export_markdown(self, report: CleanupReport, output_path: Path, turkish: bool = False):
        """Export report as Markdown."""
        t = self.turkish_translations if turkish else {}
        
        # Add action translations
        action_translations = {
            'Remove unused files': 'Kullanılmayan dosyaları kaldır',
            'Eliminate duplicate code': 'Tekrarlanan kodu kaldır',
            'Merge small files': 'Küçük dosyaları birleştir',
            'Split large files': 'Büyük dosyaları böl',
            'Reorganize scripts': 'Scriptleri yeniden düzenle',
            'Impact': 'Etki',
            'Effort': 'Efor',
            'lines': 'satır'
        } if turkish else {}
        
        lines = [
            f"# {t.get('Cleanup Report', 'Cleanup Report')}",
            f"",
            f"**Generated:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## {t.get('Summary', 'Summary')}",
            f"",
            f"- **{t.get('Total Files', 'Total Files')}:** {report.total_files}",
            f"- **{t.get('Average File Size', 'Average File Size')}:** {report.average_file_size:.1f} {action_translations.get('lines', 'lines')}",
            f"- **{t.get('Unused Files', 'Unused Files')}:** {len(report.unused_files.unused_files)}",
            f"- **{t.get('Small Files', 'Small Files')}:** {len(report.file_sizes.small_files)}",
            f"- **{t.get('Large Files', 'Large Files')}:** {len(report.file_sizes.large_files)}",
            f"- **{t.get('Duplicate Code Groups', 'Duplicate Code Groups')}:** {len(report.duplicates.duplicate_groups)}",
            f"",
            f"## {t.get('Estimated Improvements', 'Estimated Improvements')}",
            f"",
            f"- **{t.get('File Count Reduction', 'File Count Reduction')}:** {report.estimated_improvements['file_count_reduction_percent']:.1f}%",
            f"- **{t.get('Average File Size Increase', 'Average File Size Increase')}:** {report.estimated_improvements['avg_file_size_increase_percent']:.1f}%",
            f"- **{t.get('Maintainability Improvement', 'Maintainability Improvement')}:** {report.estimated_improvements['maintainability_improvement_score']:.1f}/100",
            f"",
            f"## {t.get('Prioritized Actions', 'Prioritized Actions')}",
            f""
        ]
        
        for action, impact, effort in report.prioritized_actions:
            translated_action = action_translations.get(action, action)
            impact_label = action_translations.get('Impact', 'Impact')
            effort_label = action_translations.get('Effort', 'Effort')
            lines.append(f"- **{translated_action}** ({impact_label}: {impact}/10, {effort_label}: {effort}/10)")
        
        lines.append("")
        
        output_path.write_text('\n'.join(lines))
    
    def export_json(self, report: CleanupReport, output_path: Path):
        """Export report as JSON."""
        data = {
            'timestamp': report.timestamp.isoformat(),
            'summary': {
                'total_files': report.total_files,
                'average_file_size': report.average_file_size,
                'unused_files_count': len(report.unused_files.unused_files),
                'small_files_count': len(report.file_sizes.small_files),
                'large_files_count': len(report.file_sizes.large_files),
                'duplicate_groups': len(report.duplicates.duplicate_groups)
            },
            'estimated_improvements': report.estimated_improvements,
            'prioritized_actions': [
                {'action': action, 'impact': impact, 'effort': effort}
                for action, impact, effort in report.prioritized_actions
            ]
        }
        
        output_path.write_text(json.dumps(data, indent=2))
    
    def translate_to_turkish(self, report: CleanupReport) -> CleanupReport:
        """Translate report sections to Turkish."""
        # This is a placeholder - actual translation would modify report content
        # For now, we handle translation in export_markdown with the turkish flag
        return report
