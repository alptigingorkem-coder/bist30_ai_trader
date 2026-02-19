#!/usr/bin/env python3
"""Generate comprehensive cleanup report for the project.

This script analyzes the entire project and generates a comprehensive cleanup
report that includes:
- Unused files detection
- File size analysis (small and large files)
- Duplicate code detection
- Script organization analysis
- Merge suggestions for small files
- Estimated improvements and prioritized action items

The report can be exported in Markdown or JSON format, with optional Turkish
language support.

Usage:
    python scripts/maintenance/generate_cleanup_report.py [OPTIONS]
    
Examples:
    # Generate report for current directory
    python scripts/maintenance/generate_cleanup_report.py
    
    # Generate report for specific directory
    python scripts/maintenance/generate_cleanup_report.py --root /path/to/project
    
    # Export to Markdown
    python scripts/maintenance/generate_cleanup_report.py --markdown cleanup_report.md
    
    # Export to JSON
    python scripts/maintenance/generate_cleanup_report.py --json cleanup_report.json
    
    # Generate Turkish report
    python scripts/maintenance/generate_cleanup_report.py --lang tr --markdown rapor.md
    
    # Export to both formats
    python scripts/maintenance/generate_cleanup_report.py --markdown report.md --json report.json
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.maintenance.core import (
    CleanupConfig,
    FileScanner,
    UnusedFileDetector,
    FileSizeAnalyzer,
    DuplicateCodeDetector,
    ScriptCategorizer,
    MergeSuggester,
    AutoCleanupManager,
    ReportGenerator
)


def print_section_header(title, char='='):
    """Print a formatted section header."""
    print(f"\n{char * 80}")
    print(f"{title}")
    print(f"{char * 80}")


def print_summary(report, turkish=False):
    """Print report summary to console."""
    t = {
        'Summary': 'Özet',
        'Total Files': 'Toplam Dosya',
        'Average File Size': 'Ortalama Dosya Boyutu',
        'Unused Files': 'Kullanılmayan Dosyalar',
        'Small Files': 'Küçük Dosyalar',
        'Large Files': 'Büyük Dosyalar',
        'Duplicate Code Groups': 'Tekrarlanan Kod Grupları',
        'lines': 'satır'
    } if turkish else {}
    
    print_section_header(t.get('Summary', 'Summary'))
    print(f"{t.get('Total Files', 'Total Files')}: {report.total_files}")
    print(f"{t.get('Average File Size', 'Average File Size')}: {report.average_file_size:.1f} {t.get('lines', 'lines')}")
    print(f"{t.get('Unused Files', 'Unused Files')}: {len(report.unused_files.unused_files)}")
    print(f"{t.get('Small Files', 'Small Files')}: {len(report.file_sizes.small_files)}")
    print(f"{t.get('Large Files', 'Large Files')}: {len(report.file_sizes.large_files)}")
    print(f"{t.get('Duplicate Code Groups', 'Duplicate Code Groups')}: {len(report.duplicates.duplicate_groups)}")


def print_improvements(report, turkish=False):
    """Print estimated improvements to console."""
    t = {
        'Estimated Improvements': 'Tahmini İyileştirmeler',
        'File Count Reduction': 'Dosya Sayısı Azaltma',
        'Average File Size Increase': 'Ortalama Dosya Boyutu Artışı',
        'Maintainability Improvement': 'Sürdürülebilirlik İyileştirmesi'
    } if turkish else {}
    
    print_section_header(t.get('Estimated Improvements', 'Estimated Improvements'))
    improvements = report.estimated_improvements
    print(f"{t.get('File Count Reduction', 'File Count Reduction')}: {improvements['file_count_reduction_percent']:.1f}%")
    print(f"{t.get('Average File Size Increase', 'Average File Size Increase')}: {improvements['avg_file_size_increase_percent']:.1f}%")
    print(f"{t.get('Maintainability Improvement', 'Maintainability Improvement')}: {improvements['maintainability_improvement_score']:.1f}/100")


def print_actions(report, turkish=False):
    """Print prioritized actions to console."""
    t = {
        'Prioritized Actions': 'Öncelikli Aksiyonlar',
        'Impact': 'Etki',
        'Effort': 'Efor',
        'Remove unused files': 'Kullanılmayan dosyaları kaldır',
        'Eliminate duplicate code': 'Tekrarlanan kodu kaldır',
        'Merge small files': 'Küçük dosyaları birleştir',
        'Split large files': 'Büyük dosyaları böl',
        'Reorganize scripts': 'Scriptleri yeniden düzenle'
    } if turkish else {}
    
    print_section_header(t.get('Prioritized Actions', 'Prioritized Actions'))
    for i, (action, impact, effort) in enumerate(report.prioritized_actions, 1):
        translated_action = t.get(action, action)
        print(f"{i}. {translated_action}")
        print(f"   {t.get('Impact', 'Impact')}: {impact}/10, {t.get('Effort', 'Effort')}: {effort}/10")


def print_details(report, turkish=False):
    """Print detailed findings to console."""
    t = {
        'Detailed Findings': 'Detaylı Bulgular',
        'Unused Files': 'Kullanılmayan Dosyalar',
        'Small Files': 'Küçük Dosyalar',
        'Large Files': 'Büyük Dosyalar',
        'Duplicate Code': 'Tekrarlanan Kod',
        'Merge Suggestions': 'Birleştirme Önerileri',
        'Script Organization': 'Script Organizasyonu',
        'files': 'dosya',
        'lines': 'satır',
        'groups': 'grup',
        'suggestions': 'öneri',
        'Production': 'Üretim',
        'Analysis': 'Analiz',
        'Maintenance': 'Bakım',
        'Integration Tests': 'Entegrasyon Testleri'
    } if turkish else {}
    
    print_section_header(t.get('Detailed Findings', 'Detailed Findings'), '-')
    
    # Unused files
    unused_count = len(report.unused_files.unused_files)
    print(f"\n{t.get('Unused Files', 'Unused Files')}: {unused_count} {t.get('files', 'files')}")
    if unused_count > 0 and unused_count <= 10:
        for file_info in report.unused_files.unused_files[:10]:
            print(f"  - {file_info.path}")
    elif unused_count > 10:
        print(f"  (Showing first 10 of {unused_count})")
        for file_info in report.unused_files.unused_files[:10]:
            print(f"  - {file_info.path}")
    
    # Small files
    small_count = len(report.file_sizes.small_files)
    print(f"\n{t.get('Small Files', 'Small Files')}: {small_count} {t.get('files', 'files')}")
    if small_count > 0:
        print(f"  (Files with < {report.file_sizes.small_files[0].lines if small_count > 0 else 100} {t.get('lines', 'lines')})")
    
    # Large files
    large_count = len(report.file_sizes.large_files)
    print(f"\n{t.get('Large Files', 'Large Files')}: {large_count} {t.get('files', 'files')}")
    if large_count > 0 and large_count <= 10:
        for file_info in report.file_sizes.large_files[:10]:
            print(f"  - {file_info.path} ({file_info.code_lines} {t.get('lines', 'lines')})")
    elif large_count > 10:
        print(f"  (Showing first 10 of {large_count})")
        for file_info in report.file_sizes.large_files[:10]:
            print(f"  - {file_info.path} ({file_info.code_lines} {t.get('lines', 'lines')})")
    
    # Duplicate code
    dup_count = len(report.duplicates.duplicate_groups)
    print(f"\n{t.get('Duplicate Code', 'Duplicate Code')}: {dup_count} {t.get('groups', 'groups')}")
    if dup_count > 0 and dup_count <= 5:
        for group in report.duplicates.duplicate_groups[:5]:
            print(f"  - {group.function_name} ({len(group.locations)} instances)")
    elif dup_count > 5:
        print(f"  (Showing first 5 of {dup_count})")
        for group in report.duplicates.duplicate_groups[:5]:
            print(f"  - {group.function_name} ({len(group.locations)} instances)")
    
    # Merge suggestions
    merge_count = len(report.merge_suggestions.suggestions)
    print(f"\n{t.get('Merge Suggestions', 'Merge Suggestions')}: {merge_count} {t.get('suggestions', 'suggestions')}")
    
    # Script organization
    print(f"\n{t.get('Script Organization', 'Script Organization')}:")
    print(f"  {t.get('Production', 'Production')}: {len(report.script_organization.production.scripts)}")
    print(f"  {t.get('Analysis', 'Analysis')}: {len(report.script_organization.analysis.scripts)}")
    print(f"  {t.get('Maintenance', 'Maintenance')}: {len(report.script_organization.maintenance.scripts)}")
    print(f"  {t.get('Integration Tests', 'Integration Tests')}: {len(report.script_organization.integration_tests.scripts)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate comprehensive cleanup report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--root',
        type=Path,
        default=Path.cwd(),
        help='Root directory to analyze (default: current directory)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to cleanup configuration file'
    )
    
    parser.add_argument(
        '--markdown',
        type=Path,
        help='Export report to Markdown file'
    )
    
    parser.add_argument(
        '--json',
        type=Path,
        help='Export report to JSON file'
    )
    
    parser.add_argument(
        '--lang',
        choices=['en', 'tr'],
        default='en',
        help='Report language (en=English, tr=Turkish, default: en)'
    )
    
    parser.add_argument(
        '--scripts-dir',
        type=Path,
        help='Scripts directory for organization analysis (default: root/scripts)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress information'
    )
    
    args = parser.parse_args()
    
    # Determine if Turkish
    turkish = (args.lang == 'tr')
    
    # Load configuration
    config = CleanupConfig(args.config)
    
    # Create components
    scanner = FileScanner(config)
    unused_detector = UnusedFileDetector(config, scanner)
    size_analyzer = FileSizeAnalyzer(config, scanner)
    duplicate_detector = DuplicateCodeDetector(config, scanner)
    script_categorizer = ScriptCategorizer(config, scanner)
    merge_suggester = MergeSuggester(config, scanner)
    report_generator = ReportGenerator(config)
    
    # Determine scripts directory
    scripts_dir = args.scripts_dir if args.scripts_dir else args.root / 'scripts'
    
    # Run analysis
    print(f"{'Analiz başlatılıyor' if turkish else 'Starting analysis'}: {args.root}")
    print()
    
    if args.verbose:
        print(f"{'Kullanılmayan dosyalar taranıyor' if turkish else 'Scanning for unused files'}...")
    unused_result = unused_detector.find_unused_files(args.root)
    
    if args.verbose:
        print(f"{'Dosya boyutları analiz ediliyor' if turkish else 'Analyzing file sizes'}...")
    size_result = size_analyzer.analyze_sizes(args.root)
    
    if args.verbose:
        print(f"{'Tekrarlanan kod aranıyor' if turkish else 'Detecting duplicate code'}...")
    duplicate_result = duplicate_detector.find_duplicates(args.root)
    
    if args.verbose:
        print(f"{'Scriptler kategorize ediliyor' if turkish else 'Categorizing scripts'}...")
    if scripts_dir.exists():
        script_result = script_categorizer.analyze_organization(scripts_dir)
    else:
        # Create empty result if scripts directory doesn't exist
        from scripts.maintenance.core.script_categorizer import ScriptCategory, ScriptOrganizationResult
        script_result = ScriptOrganizationResult(
            production=ScriptCategory('production', [], 'scripts/'),
            analysis=ScriptCategory('analysis', [], 'scripts/analysis/'),
            maintenance=ScriptCategory('maintenance', [], 'scripts/maintenance/'),
            integration_tests=ScriptCategory('integration_tests', [], 'scripts/tests/'),
            reorganization_plan=[],
            broken_imports=[]
        )
    
    if args.verbose:
        print(f"{'Birleştirme önerileri oluşturuluyor' if turkish else 'Generating merge suggestions'}...")
    merge_result = merge_suggester.suggest_merges(size_result.small_files)
    
    if args.verbose:
        print(f"{'Rapor oluşturuluyor' if turkish else 'Generating report'}...")
    report = report_generator.generate_report(
        unused_result,
        size_result,
        duplicate_result,
        script_result,
        merge_result
    )
    
    # Display console output
    print_summary(report, turkish)
    print_improvements(report, turkish)
    print_actions(report, turkish)
    print_details(report, turkish)
    
    # Export to files
    if args.markdown:
        report_generator.export_markdown(report, args.markdown, turkish)
        print(f"\n{'Markdown raporu dışa aktarıldı' if turkish else 'Markdown report exported to'}: {args.markdown}")
    
    if args.json:
        report_generator.export_json(report, args.json)
        print(f"{'JSON raporu dışa aktarıldı' if turkish else 'JSON report exported to'}: {args.json}")
    
    # Final message
    print()
    if turkish:
        print("=" * 80)
        print("Rapor tamamlandı!")
        print("=" * 80)
        print("\nÖnerilen sonraki adımlar:")
        print("1. Öncelikli aksiyonları gözden geçirin")
        print("2. Kullanılmayan dosyaları kaldırmayı düşünün")
        print("3. Tekrarlanan kodu birleştirin")
        print("4. Küçük dosyaları birleştirmeyi değerlendirin")
    else:
        print("=" * 80)
        print("Report generation complete!")
        print("=" * 80)
        print("\nRecommended next steps:")
        print("1. Review prioritized actions")
        print("2. Consider removing unused files")
        print("3. Consolidate duplicate code")
        print("4. Evaluate merge suggestions for small files")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
