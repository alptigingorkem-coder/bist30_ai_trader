"""
Integration tests for ReportGenerator

Tests the report generator with realistic data and scenarios.
"""

import os
import tempfile
import shutil
from datetime import datetime
import pandas as pd
import pytest

from scripts.analysis.report_generator import ReportGenerator
from scripts.analysis.feature_importance_config import AnalysisResult


class TestReportGeneratorIntegration:
    """Integration test suite for ReportGenerator"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def realistic_result(self):
        """Create a realistic AnalysisResult with actual feature names"""
        # Simulate realistic feature importance data
        features = [
            'rsi_14', 'macd_signal', 'bb_width', 'volume_sma_20', 'price_momentum_5',
            'atr_14', 'obv_change', 'stoch_k', 'cci_20', 'adx_14',
            'williams_r', 'mfi_14', 'trix', 'kama', 'ppo',
            'roc_10', 'tsi', 'ultimate_osc', 'vwap_diff', 'chaikin_osc',
            'aroon_up', 'aroon_down', 'dpo', 'kst', 'mass_index',
            'pvo', 'eom', 'force_index', 'nvi', 'pvi'
        ]
        
        importance_df = pd.DataFrame({
            'feature': features,
            'importance': [0.085, 0.072, 0.068, 0.055, 0.048,
                          0.042, 0.038, 0.035, 0.031, 0.028,
                          0.025, 0.022, 0.019, 0.016, 0.013,
                          0.010, 0.008, 0.006, 0.004, 0.003,
                          0.002, 0.0015, 0.001, 0.0008, 0.0006,
                          0.0004, 0.0003, 0.0002, 0.0001, 0.00005]
        })
        
        blacklist = features[20:]  # Last 10 features
        
        return AnalysisResult(
            timestamp=datetime(2024, 1, 15, 14, 30, 0),
            config={
                'sample_size': 1000,
                'importance_threshold': 0.002,
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'output_dir': 'reports/feature_importance',
                'save_models': False
            },
            importance_df=importance_df,
            blacklist=blacklist,
            baseline_ndcg3=0.6217,
            optimized_ndcg3=0.6543,
            improvement_pct=5.24,
            total_features=30,
            blacklisted_features=10,
            remaining_features=20,
            data_size=12500,
            tickers_analyzed=['THYAO', 'GARAN', 'AKBNK', 'EREGL', 'SAHOL'],
            analysis_duration=245.8
        )
    
    def test_full_report_generation_workflow(self, temp_dir, realistic_result):
        """Test complete report generation workflow with realistic data"""
        generator = ReportGenerator(output_dir=temp_dir)
        
        # Generate report
        filepath = generator.generate_report(realistic_result)
        
        # Verify file exists
        assert os.path.exists(filepath)
        
        # Read and verify content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify all key sections are present
        assert '# Feature Importance Analysis Report' in content
        assert 'rsi_14' in content  # Top feature
        assert 'THYAO' in content  # Ticker
        assert '0.6217' in content  # Baseline NDCG
        assert '0.6543' in content  # Optimized NDCG
        assert '5.24%' in content or '+5.24%' in content  # Improvement
        
        # Verify file size is reasonable (should be several KB)
        file_size = os.path.getsize(filepath)
        assert file_size > 1000  # At least 1KB
        assert file_size < 100000  # Less than 100KB
    
    def test_report_with_negative_improvement(self, temp_dir):
        """Test report generation when performance degrades"""
        importance_df = pd.DataFrame({
            'feature': [f'feature_{i}' for i in range(20)],
            'importance': [0.1 - i * 0.005 for i in range(20)]
        })
        
        result = AnalysisResult(
            timestamp=datetime.now(),
            config={
                'sample_size': 1000,
                'importance_threshold': 0.05,
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'output_dir': temp_dir
            },
            importance_df=importance_df,
            blacklist=[f'feature_{i}' for i in range(10, 20)],
            baseline_ndcg3=0.6500,
            optimized_ndcg3=0.6200,
            improvement_pct=-4.62,
            total_features=20,
            blacklisted_features=10,
            remaining_features=10,
            data_size=5000,
            tickers_analyzed=['TEST1', 'TEST2'],
            analysis_duration=120.0
        )
        
        generator = ReportGenerator(output_dir=temp_dir)
        filepath = generator.generate_report(result)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should contain warning about degradation
        assert 'degradation' in content.lower() or 'reduced' in content.lower()
        assert '⚠️' in content or '❌' in content
    
    def test_report_with_target_achieved(self, temp_dir):
        """Test report when NDCG@3 target of 0.65 is achieved"""
        importance_df = pd.DataFrame({
            'feature': [f'feature_{i}' for i in range(15)],
            'importance': [0.08 - i * 0.005 for i in range(15)]
        })
        
        result = AnalysisResult(
            timestamp=datetime.now(),
            config={
                'sample_size': 1000,
                'importance_threshold': 0.001,
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'output_dir': temp_dir
            },
            importance_df=importance_df,
            blacklist=['feature_12', 'feature_13', 'feature_14'],
            baseline_ndcg3=0.6217,
            optimized_ndcg3=0.6580,
            improvement_pct=5.84,
            total_features=15,
            blacklisted_features=3,
            remaining_features=12,
            data_size=8000,
            tickers_analyzed=['THYAO', 'GARAN', 'AKBNK'],
            analysis_duration=180.0
        )
        
        generator = ReportGenerator(output_dir=temp_dir)
        filepath = generator.generate_report(result)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should mention target achievement
        assert '0.65' in content
        assert 'achieved' in content.lower() or 'met' in content.lower()
        assert '🎯' in content
    
    def test_report_with_many_tickers(self, temp_dir):
        """Test report with many tickers (should truncate in display)"""
        importance_df = pd.DataFrame({
            'feature': [f'feature_{i}' for i in range(10)],
            'importance': [0.1 - i * 0.01 for i in range(10)]
        })
        
        many_tickers = [f'TICKER{i:02d}' for i in range(20)]
        
        result = AnalysisResult(
            timestamp=datetime.now(),
            config={
                'sample_size': 1000,
                'importance_threshold': 0.001,
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'output_dir': temp_dir
            },
            importance_df=importance_df,
            blacklist=['feature_8', 'feature_9'],
            baseline_ndcg3=0.62,
            optimized_ndcg3=0.64,
            improvement_pct=3.23,
            total_features=10,
            blacklisted_features=2,
            remaining_features=8,
            data_size=15000,
            tickers_analyzed=many_tickers,
            analysis_duration=300.0
        )
        
        generator = ReportGenerator(output_dir=temp_dir)
        filepath = generator.generate_report(result)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should show ticker count
        assert '20' in content
        # Should truncate ticker list
        assert '...' in content
    
    def test_report_with_large_blacklist(self, temp_dir):
        """Test report with large blacklist (>50 features)"""
        num_features = 100
        importance_df = pd.DataFrame({
            'feature': [f'feature_{i:03d}' for i in range(num_features)],
            'importance': [0.1 - i * 0.001 for i in range(num_features)]
        })
        
        blacklist = [f'feature_{i:03d}' for i in range(40, num_features)]
        
        result = AnalysisResult(
            timestamp=datetime.now(),
            config={
                'sample_size': 1000,
                'importance_threshold': 0.04,
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'output_dir': temp_dir
            },
            importance_df=importance_df,
            blacklist=blacklist,
            baseline_ndcg3=0.62,
            optimized_ndcg3=0.64,
            improvement_pct=3.23,
            total_features=num_features,
            blacklisted_features=len(blacklist),
            remaining_features=num_features - len(blacklist),
            data_size=10000,
            tickers_analyzed=['TEST'],
            analysis_duration=200.0
        )
        
        generator = ReportGenerator(output_dir=temp_dir)
        filepath = generator.generate_report(result)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should use collapsible section
        assert '<details>' in content
        assert 'more features' in content
    
    def test_sequential_reports_preserve_history(self, temp_dir, realistic_result):
        """Test that generating multiple reports preserves previous ones (Requirement 10.3)"""
        generator = ReportGenerator(output_dir=temp_dir)
        
        # Generate first report
        filepath1 = generator.generate_report(realistic_result, filename="report_v1.md")
        
        # Generate second report with different data
        realistic_result.optimized_ndcg3 = 0.6700
        realistic_result.improvement_pct = 7.77
        filepath2 = generator.generate_report(realistic_result, filename="report_v2.md")
        
        # Both files should exist
        assert os.path.exists(filepath1)
        assert os.path.exists(filepath2)
        
        # Files should have different content
        with open(filepath1, 'r') as f1, open(filepath2, 'r') as f2:
            content1 = f1.read()
            content2 = f2.read()
        
        assert content1 != content2
        assert '0.6543' in content1
        assert '0.6700' in content2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
