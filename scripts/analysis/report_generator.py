"""
Report Generator Module

This module generates Markdown reports for feature importance analysis results.

Requirements: 4.4, 4.5, 10.1
"""

import os
from datetime import datetime
from typing import Optional
import logging

from scripts.analysis.feature_importance_config import AnalysisResult

log = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates Markdown reports for feature importance analysis.
    
    This class creates comprehensive reports that include:
    - Analysis metadata (timestamp, duration, configuration)
    - Feature statistics (total, blacklisted, remaining)
    - Model performance comparison (baseline vs optimized)
    - Top features by importance
    
    Requirements: 4.4, 4.5, 10.1
    """
    
    def __init__(self, output_dir: str = "reports/feature_importance"):
        """
        Initialize the report generator.
        
        Args:
            output_dir: Directory where reports will be saved
            
        Requirements: 4.4
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        log.info(f"ReportGenerator initialized with output_dir: {output_dir}")
    
    def generate_report(self, analysis_result: AnalysisResult, 
                       filename: Optional[str] = None) -> str:
        """
        Generate a comprehensive Markdown report from analysis results.
        
        The report includes:
        - Total feature count
        - Blacklisted feature count
        - Baseline NDCG@3
        - Optimized NDCG@3
        - Improvement percentage
        - Top features by importance
        - Configuration details
        - Analysis metadata
        
        Args:
            analysis_result: Analysis results to report
            filename: Report filename (None generates timestamp-based name)
            
        Returns:
            Path to the generated report file
            
        Requirements: 4.4, 4.5, 10.1
        """
        # Generate filename with timestamp if not provided
        if filename is None:
            timestamp_str = analysis_result.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"feature_importance_report_{timestamp_str}.md"
        
        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Generate report content
        report_content = self._create_report_content(analysis_result)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        log.info(f"Report generated successfully: {filepath}")
        return filepath
    
    def _create_report_content(self, result: AnalysisResult) -> str:
        """
        Create the Markdown content for the report.
        
        Args:
            result: Analysis results
            
        Returns:
            Formatted Markdown report content
            
        Requirements: 4.4, 4.5
        """
        # Format timestamp
        timestamp_str = result.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate percentages
        blacklist_pct = (result.blacklisted_features / result.total_features * 100) if result.total_features > 0 else 0
        remaining_pct = (result.remaining_features / result.total_features * 100) if result.total_features > 0 else 0
        
        # Format duration
        duration_str = self._format_duration(result.analysis_duration)
        
        # Get top features
        top_features_table = self._create_top_features_table(result.importance_df)
        
        # Build report
        report = f"""# Feature Importance Analysis Report

## Analysis Overview

**Analysis Date:** {timestamp_str}  
**Analysis Duration:** {duration_str}  
**Tickers Analyzed:** {len(result.tickers_analyzed)} ({', '.join(result.tickers_analyzed[:5])}{', ...' if len(result.tickers_analyzed) > 5 else ''})  
**Data Points:** {result.data_size:,}

---

## Feature Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Features** | {result.total_features} | 100.0% |
| **Blacklisted Features** | {result.blacklisted_features} | {blacklist_pct:.1f}% |
| **Remaining Features** | {result.remaining_features} | {remaining_pct:.1f}% |

---

## Model Performance Comparison

### Baseline Model (All Features)
- **NDCG@3:** {result.baseline_ndcg3:.4f}
- **Features Used:** {result.total_features}

### Optimized Model (After Feature Selection)
- **NDCG@3:** {result.optimized_ndcg3:.4f}
- **Features Used:** {result.remaining_features}

### Performance Improvement
- **Absolute Change:** {result.optimized_ndcg3 - result.baseline_ndcg3:+.4f}
- **Relative Improvement:** {result.improvement_pct:+.2f}%

{self._get_performance_assessment(result.improvement_pct)}

---

## Top Features by Importance

{top_features_table}

---

## Configuration

| Parameter | Value |
|-----------|-------|
| **Sample Size** | {result.config.get('sample_size', 'N/A')} |
| **Importance Threshold** | {result.config.get('importance_threshold', 'N/A')} |
| **Start Date** | {result.config.get('start_date', 'N/A')} |
| **End Date** | {result.config.get('end_date', 'N/A')} |
| **Output Directory** | {result.config.get('output_dir', 'N/A')} |

---

## Blacklisted Features

Total blacklisted features: **{result.blacklisted_features}**

{self._create_blacklist_section(result.blacklist)}

---

## Summary

This analysis identified **{result.blacklisted_features}** low-contribution features that were removed from the model. The optimized model using **{result.remaining_features}** features achieved a NDCG@3 score of **{result.optimized_ndcg3:.4f}**, representing a **{result.improvement_pct:+.2f}%** change compared to the baseline model.

{self._get_recommendation(result)}

---

*Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        return report
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
    
    def _create_top_features_table(self, importance_df, top_n: int = 20) -> str:
        """
        Create a Markdown table of top features.
        
        Args:
            importance_df: DataFrame with feature importance
            top_n: Number of top features to include
            
        Returns:
            Markdown table string
        """
        if importance_df is None or len(importance_df) == 0:
            return "*No feature importance data available*"
        
        # Get top N features
        top_features = importance_df.head(top_n)
        
        # Create table
        table = "| Rank | Feature | Importance |\n"
        table += "|------|---------|------------|\n"
        
        for idx, (_, row) in enumerate(top_features.iterrows(), 1):
            feature_name = row.get('feature', 'Unknown')
            importance = row.get('importance', 0.0)
            table += f"| {idx} | {feature_name} | {importance:.6f} |\n"
        
        return table
    
    def _create_blacklist_section(self, blacklist: list) -> str:
        """
        Create the blacklisted features section.
        
        Args:
            blacklist: List of blacklisted feature names
            
        Returns:
            Formatted blacklist section
        """
        if not blacklist:
            return "*No features were blacklisted*"
        
        # Show first 50 features, then indicate if there are more
        display_count = min(50, len(blacklist))
        
        section = "<details>\n<summary>Click to expand blacklisted features list</summary>\n\n"
        
        for i in range(0, display_count, 5):
            batch = blacklist[i:i+5]
            section += "- " + ", ".join(f"`{f}`" for f in batch) + "\n"
        
        if len(blacklist) > display_count:
            section += f"\n*... and {len(blacklist) - display_count} more features*\n"
        
        section += "\n</details>"
        
        return section
    
    def _get_performance_assessment(self, improvement_pct: float) -> str:
        """
        Get a qualitative assessment of the performance change.
        
        Args:
            improvement_pct: Percentage improvement
            
        Returns:
            Assessment message
        """
        if improvement_pct > 5:
            return "✅ **Excellent improvement!** The feature selection significantly improved model performance."
        elif improvement_pct > 1:
            return "✅ **Good improvement.** The feature selection provided a meaningful performance boost."
        elif improvement_pct > 0:
            return "✓ **Slight improvement.** The feature selection provided a small performance gain."
        elif improvement_pct > -1:
            return "⚠️ **Minimal change.** The feature selection had negligible impact on performance."
        elif improvement_pct > -5:
            return "⚠️ **Slight degradation.** The feature selection slightly reduced performance. Consider adjusting the threshold."
        else:
            return "❌ **Significant degradation.** The feature selection notably reduced performance. Review the threshold and blacklisted features."
    
    def _get_recommendation(self, result: AnalysisResult) -> str:
        """
        Generate recommendations based on results.
        
        Args:
            result: Analysis results
            
        Returns:
            Recommendation text
        """
        recommendations = []
        
        # Check blacklist size
        blacklist_pct = (result.blacklisted_features / result.total_features * 100) if result.total_features > 0 else 0
        if blacklist_pct > 80:
            recommendations.append("- ⚠️ Over 80% of features were blacklisted. Consider lowering the importance threshold.")
        elif blacklist_pct < 5:
            recommendations.append("- Consider increasing the importance threshold to remove more low-contribution features.")
        
        # Check performance
        if result.improvement_pct < 0:
            recommendations.append("- ⚠️ Performance decreased. Review blacklisted features and consider adjusting the threshold.")
        elif result.improvement_pct > 5:
            recommendations.append("- ✅ Excellent results! Consider deploying the optimized model to production.")
        
        # Check if target met
        if result.optimized_ndcg3 >= 0.65:
            recommendations.append("- 🎯 Target NDCG@3 of 0.65 achieved! The optimization goal has been met.")
        else:
            target_gap = 0.65 - result.optimized_ndcg3
            recommendations.append(f"- Target NDCG@3 of 0.65 not yet reached (gap: {target_gap:.4f}). Further optimization may be needed.")
        
        if recommendations:
            return "### Recommendations\n\n" + "\n".join(recommendations)
        else:
            return ""
