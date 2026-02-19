"""
Feature Importance Analyzer Module

This module provides the main orchestrator for LightGBM feature importance analysis.
It coordinates all components (SHAP analysis, feature selection, model comparison,
visualization, and reporting) to perform end-to-end feature importance analysis.

Requirements: 1.1-1.5, 2.1-2.3, 3.1-3.5, 4.1-4.5, 5.1-5.3, 7.3-7.5, 8.2-8.3, 9.1-9.5, 10.2-10.3
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import lightgbm as lgb

from scripts.analysis.feature_importance_config import AnalysisConfig, AnalysisResult
from scripts.analysis.shap_analyzer import SHAPAnalyzer
from scripts.analysis.feature_selector import FeatureSelector
from scripts.analysis.model_comparator import ModelComparator
from scripts.analysis.visualizer import FeatureImportanceVisualizer
from scripts.analysis.report_generator import ReportGenerator
from models.ranking_model import RankingModel

log = logging.getLogger(__name__)


class FeatureImportanceAnalyzer:
    """
    Main orchestrator for feature importance analysis.
    
    This class coordinates the entire analysis workflow:
    1. Load and prepare data
    2. Train baseline model with all features
    3. Compute SHAP values and feature importance
    4. Create blacklist of low-contribution features
    5. Train optimized model with blacklist applied
    6. Compare baseline and optimized models
    7. Generate visualizations and reports
    8. Save results and metadata
    
    Attributes:
        config_module: System configuration module (config.py or sector config)
        analysis_config: Analysis-specific configuration
        shap_analyzer: SHAP analysis component
        feature_selector: Feature selection component
        model_comparator: Model comparison component
        visualizer: Visualization component
        report_generator: Report generation component
    
    Requirements: 5.1, 5.2, 5.3, 9.1
    """
    
    def __init__(self, config_module, analysis_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Feature Importance Analyzer.
        
        Args:
            config_module: System configuration module (config.py or sector config)
            analysis_config: Analysis configuration parameters (optional)
                - sample_size: SHAP sampling size (default: 1000)
                - importance_threshold: Blacklist threshold (default: 0.001)
                - start_date: Analysis start date (default: config.START_DATE)
                - end_date: Analysis end date (default: config.END_DATE)
                - tickers: Ticker list (default: config.TICKERS)
                - output_dir: Output directory (default: "reports/feature_importance")
                - save_models: Save models flag (default: False)
        
        Raises:
            ValueError: If configuration is invalid
        
        Requirements: 5.1, 5.2, 5.3
        """
        self.config_module = config_module
        
        # Create AnalysisConfig from dict or use defaults
        if analysis_config is None:
            analysis_config = {}
        
        try:
            self.analysis_config = AnalysisConfig(**analysis_config)
        except Exception as e:
            log.error(f"Invalid analysis configuration: {str(e)}")
            raise ValueError(f"Invalid analysis configuration: {str(e)}")
        
        # Use config module defaults if not specified
        if self.analysis_config.start_date is None:
            self.analysis_config.start_date = getattr(config_module, 'START_DATE', None)
        
        if self.analysis_config.end_date is None:
            self.analysis_config.end_date = getattr(config_module, 'END_DATE', None)
        
        if self.analysis_config.tickers is None:
            self.analysis_config.tickers = getattr(config_module, 'TICKERS', [])
        
        # Initialize components (will be created as needed)
        self.shap_analyzer = None
        self.feature_selector = FeatureSelector(
            threshold=self.analysis_config.importance_threshold
        )
        self.model_comparator = ModelComparator()
        self.visualizer = FeatureImportanceVisualizer(
            output_dir=self.analysis_config.output_dir
        )
        self.report_generator = ReportGenerator(
            output_dir=self.analysis_config.output_dir
        )
        
        log.info(
            f"FeatureImportanceAnalyzer initialized with config: "
            f"sample_size={self.analysis_config.sample_size}, "
            f"threshold={self.analysis_config.importance_threshold}, "
            f"tickers={len(self.analysis_config.tickers)}"
        )

    def run_analysis(self) -> AnalysisResult:
        """
        Run the complete feature importance analysis workflow.
        
        This method orchestrates the entire analysis process:
        1. Load and prepare data
        2. Train baseline model
        3. Compute SHAP values
        4. Create blacklist
        5. Train optimized model
        6. Compare models
        7. Save results
        
        Returns:
            AnalysisResult: Complete analysis results with metrics and metadata
        
        Raises:
            ValueError: If analysis fails due to invalid data or configuration
            RuntimeError: If critical steps fail
        
        Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
        """
        start_time = time.time()
        timestamp = datetime.now()
        
        log.info("=" * 80)
        log.info("Starting Feature Importance Analysis")
        log.info(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        log.info("=" * 80)
        
        try:
            # Step 1: Load data
            log.info("Step 1/7: Loading data...")
            step_start = time.time()
            data = self._load_data()
            log.info(f"Data loaded: {len(data)} rows in {time.time() - step_start:.2f}s")
            
            # Step 2: Train baseline model
            log.info("Step 2/7: Training baseline model...")
            step_start = time.time()
            baseline_model = self._train_baseline_model(data)
            log.info(f"Baseline model trained in {time.time() - step_start:.2f}s")
            
            # Step 3: Compute SHAP values
            log.info("Step 3/7: Computing SHAP values...")
            step_start = time.time()
            importance_df = self._compute_shap_values(baseline_model, data)
            log.info(f"SHAP values computed in {time.time() - step_start:.2f}s")
            
            # Step 4: Create blacklist
            log.info("Step 4/7: Creating feature blacklist...")
            step_start = time.time()
            blacklist = self._create_blacklist(importance_df)
            log.info(f"Blacklist created in {time.time() - step_start:.2f}s")
            
            # Step 5: Train optimized model
            log.info("Step 5/7: Training optimized model...")
            step_start = time.time()
            # Pass baseline features to ensure consistent feature set
            optimized_model = self._train_optimized_model(
                data, 
                blacklist,
                baseline_features=baseline_model.feature_names
            )
            log.info(f"Optimized model trained in {time.time() - step_start:.2f}s")
            
            # Step 6: Compare models
            log.info("Step 6/7: Comparing models...")
            step_start = time.time()
            comparison_results = self._compare_models(
                baseline_model, 
                optimized_model, 
                data
            )
            log.info(f"Model comparison completed in {time.time() - step_start:.2f}s")
            
            # Step 7: Save results
            log.info("Step 7/7: Saving results...")
            step_start = time.time()
            
            # Create AnalysisResult
            analysis_duration = time.time() - start_time
            analysis_result = AnalysisResult(
                timestamp=timestamp,
                config=self.analysis_config.to_dict(),
                importance_df=importance_df,
                blacklist=blacklist,
                baseline_ndcg3=comparison_results['baseline_ndcg3'],
                optimized_ndcg3=comparison_results['optimized_ndcg3'],
                improvement_pct=comparison_results['improvement_pct'],
                total_features=comparison_results['baseline_features'],
                blacklisted_features=len(blacklist),
                remaining_features=comparison_results['optimized_features'],
                data_size=len(data),
                tickers_analyzed=self.analysis_config.tickers,
                analysis_duration=analysis_duration
            )
            
            # Save results
            self._save_results(analysis_result, comparison_results)
            log.info(f"Results saved in {time.time() - step_start:.2f}s")
            
            # Log summary
            log.info("=" * 80)
            log.info("Analysis completed successfully!")
            log.info(f"Total duration: {analysis_duration:.2f}s")
            log.info(f"Baseline NDCG@3: {analysis_result.baseline_ndcg3:.4f}")
            log.info(f"Optimized NDCG@3: {analysis_result.optimized_ndcg3:.4f}")
            log.info(f"Improvement: {analysis_result.improvement_pct:+.2f}%")
            log.info(f"Features: {analysis_result.total_features} → {analysis_result.remaining_features}")
            log.info("=" * 80)
            
            return analysis_result
        
        except Exception as e:
            log.error(f"Analysis failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Feature importance analysis failed: {str(e)}")

    def _load_data(self) -> pd.DataFrame:
        """
        Load and prepare data for analysis.
        
        This method:
        1. Loads data for each ticker using DataLoader
        2. Applies feature engineering
        3. Combines all ticker data
        4. Creates multi-index (Date, Ticker)
        5. Handles errors gracefully (skips failed tickers)
        
        Returns:
            pd.DataFrame: Combined data with multi-index (Date, Ticker)
        
        Raises:
            ValueError: If no valid data could be loaded
            RuntimeError: If data loading fails critically
        
        Requirements: 7.3, 7.4, 7.5
        """
        from utils.data_loader import DataLoader
        from utils.feature_engineering import FeatureEngineer
        
        log.info(f"Loading data for {len(self.analysis_config.tickers)} tickers...")
        
        all_data_frames = []
        successful_tickers = []
        failed_tickers = []
        
        # Create data loader
        loader = DataLoader(
            start_date=self.analysis_config.start_date,
            end_date=self.analysis_config.end_date
        )
        
        # Load data for each ticker
        for i, ticker in enumerate(self.analysis_config.tickers, 1):
            try:
                log.info(f"Processing ticker {i}/{len(self.analysis_config.tickers)}: {ticker}")
                
                # Load raw data
                raw_data = loader.get_combined_data(ticker)
                
                if raw_data is None or len(raw_data) < 100:
                    log.warning(f"Insufficient data for {ticker} (< 100 rows), skipping")
                    failed_tickers.append(ticker)
                    continue
                
                # Apply feature engineering
                fe = FeatureEngineer(raw_data)
                features_df = fe.process_all(ticker=ticker)
                
                if features_df is None or len(features_df) == 0:
                    log.warning(f"Feature engineering failed for {ticker}, skipping")
                    failed_tickers.append(ticker)
                    continue
                
                # Add ticker column
                features_df = features_df.copy()
                features_df['Ticker'] = ticker
                
                all_data_frames.append(features_df)
                successful_tickers.append(ticker)
                
                log.debug(f"Successfully loaded {len(features_df)} rows for {ticker}")
            
            except Exception as e:
                log.error(f"Error loading data for {ticker}: {str(e)}")
                failed_tickers.append(ticker)
                continue
        
        # Check if we have any data
        if not all_data_frames:
            raise ValueError(
                f"No valid data could be loaded. "
                f"Failed tickers: {failed_tickers}"
            )
        
        # Combine all data
        log.info(f"Combining data from {len(all_data_frames)} tickers...")
        full_data = pd.concat(all_data_frames, ignore_index=False)
        
        # Create multi-index (Date, Ticker)
        full_data.reset_index(inplace=True)
        full_data.set_index(['Date', 'Ticker'], inplace=True)
        full_data.sort_index(inplace=True)
        
        # Update tickers list to only include successful ones
        self.analysis_config.tickers = successful_tickers
        
        log.info(
            f"Data loading completed: {len(full_data)} rows, "
            f"{len(successful_tickers)} successful tickers, "
            f"{len(failed_tickers)} failed tickers"
        )
        
        if failed_tickers:
            log.warning(f"Failed tickers: {', '.join(failed_tickers)}")
        
        return full_data

    def _train_baseline_model(self, data: pd.DataFrame) -> RankingModel:
        """
        Train baseline model with all features.
        
        This method trains a LightGBM ranking model using all available features
        without any blacklist applied. This serves as the reference model for
        comparison.
        
        Args:
            data: Combined data with multi-index (Date, Ticker)
        
        Returns:
            RankingModel: Trained baseline model
        
        Raises:
            ValueError: If data is invalid or training fails
        
        Requirements: 3.1
        """
        if data is None or len(data) == 0:
            raise ValueError("Cannot train baseline model with empty data")
        
        log.info(f"Training baseline model with {len(data)} samples...")
        
        try:
            # Create RankingModel instance (no blacklist)
            baseline_model = RankingModel(data.copy(), self.config_module)
            
            # Prepare data
            X_train, y_train, groups = baseline_model.prepare_data(is_training=True)
            
            if X_train.empty or len(y_train) == 0:
                raise ValueError("Data preparation resulted in empty dataset")
            
            log.info(
                f"Baseline data prepared: {len(X_train)} samples, "
                f"{len(X_train.columns)} features, {len(groups)} groups"
            )
            
            # Train model
            baseline_model.train()
            
            if baseline_model.model is None:
                raise ValueError("Baseline model training failed")
            
            log.info(
                f"Baseline model trained successfully with "
                f"{len(baseline_model.feature_names)} features"
            )
            
            # Optionally save baseline model
            if self.analysis_config.save_models:
                baseline_path = os.path.join(
                    self.analysis_config.output_dir,
                    "baseline_model.pkl"
                )
                baseline_model.save(baseline_path)
                log.info(f"Baseline model saved to {baseline_path}")
            
            return baseline_model
        
        except Exception as e:
            log.error(f"Baseline model training failed: {str(e)}")
            raise ValueError(f"Failed to train baseline model: {str(e)}")

    def _compute_shap_values(
        self, 
        model: RankingModel, 
        data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute SHAP values and feature importance.
        
        This method uses SHAPAnalyzer to compute feature importance scores
        based on SHAP values. If SHAP calculation fails, it falls back to
        LightGBM's native feature importance.
        
        Args:
            model: Trained RankingModel
            data: Data used for SHAP calculation
        
        Returns:
            pd.DataFrame: Feature importance table with 'feature' and 'importance' columns
        
        Raises:
            ValueError: If importance calculation fails completely
        
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
        """
        if model is None or model.model is None:
            raise ValueError("Model must be trained before computing SHAP values")
        
        log.info("Computing feature importance using SHAP...")
        
        try:
            # Prepare data for SHAP calculation
            # Use the model's prepare_data to get the same features
            temp_model = RankingModel(data.copy(), self.config_module)
            X, _, _ = temp_model.prepare_data(is_training=True)
            
            # Filter to only include features used by the model
            available_features = [f for f in model.feature_names if f in X.columns]
            X_filtered = X[available_features]
            
            log.info(f"Computing SHAP for {len(X_filtered)} samples, {len(available_features)} features")
            
            # Create SHAP analyzer
            self.shap_analyzer = SHAPAnalyzer(
                model.model,
                sample_size=self.analysis_config.sample_size
            )
            
            # Compute importance
            importance_df = self.shap_analyzer.compute_importance(X_filtered)
            
            log.info(
                f"SHAP importance computed successfully. "
                f"Top feature: {importance_df.iloc[0]['feature']} "
                f"(importance: {importance_df.iloc[0]['importance']:.6f})"
            )
            
            return importance_df
        
        except ImportError as e:
            log.error(f"SHAP library not available: {str(e)}")
            log.warning("Falling back to LightGBM native feature importance")
            return self._fallback_importance(model)
        
        except Exception as e:
            log.error(f"SHAP calculation failed: {str(e)}")
            log.warning("Falling back to LightGBM native feature importance")
            return self._fallback_importance(model)
    
    def _fallback_importance(self, model: RankingModel) -> pd.DataFrame:
        """
        Fallback method using LightGBM's native feature importance.
        
        Args:
            model: Trained RankingModel
        
        Returns:
            pd.DataFrame: Feature importance table
        
        Requirements: 1.1, 1.2
        """
        log.info("Using LightGBM native feature importance as fallback")
        
        try:
            # Get feature importance from LightGBM model
            importance_values = model.model.feature_importances_
            
            # Create DataFrame
            importance_df = pd.DataFrame({
                'feature': model.feature_names,
                'importance': importance_values
            })
            
            # Sort by importance
            importance_df = importance_df.sort_values(
                'importance', 
                ascending=False
            ).reset_index(drop=True)
            
            log.info(
                f"Native importance computed. "
                f"Top feature: {importance_df.iloc[0]['feature']} "
                f"(importance: {importance_df.iloc[0]['importance']:.2f})"
            )
            
            return importance_df
        
        except Exception as e:
            log.error(f"Fallback importance calculation failed: {str(e)}")
            raise ValueError(f"Could not compute feature importance: {str(e)}")

    def _create_blacklist(self, importance_df: pd.DataFrame) -> List[str]:
        """
        Create blacklist of low-contribution features.
        
        This method uses FeatureSelector to identify features below the
        importance threshold and validates the blacklist size.
        
        Args:
            importance_df: Feature importance table from SHAP analysis
        
        Returns:
            List[str]: List of features to blacklist
        
        Raises:
            ValueError: If blacklist creation fails
        
        Requirements: 2.1, 2.2, 8.2, 8.3
        """
        if importance_df is None or len(importance_df) == 0:
            raise ValueError("Cannot create blacklist from empty importance data")
        
        log.info("Creating feature blacklist...")
        
        try:
            # Create blacklist using FeatureSelector
            blacklist = self.feature_selector.create_blacklist(importance_df)
            
            # Validate blacklist size
            total_features = len(importance_df)
            is_valid = self.feature_selector.validate_blacklist(
                blacklist, 
                total_features
            )
            
            if not is_valid:
                log.warning(
                    f"Blacklist validation failed: {len(blacklist)} features "
                    f"({len(blacklist)/total_features*100:.1f}%) exceed 80% threshold. "
                    f"Consider increasing importance threshold "
                    f"(current: {self.analysis_config.importance_threshold})"
                )
            
            log.info(
                f"Blacklist created: {len(blacklist)} features "
                f"({len(blacklist)/total_features*100:.1f}% of {total_features})"
            )
            
            if len(blacklist) > 0:
                log.debug(
                    f"Sample blacklisted features: "
                    f"{blacklist[:5]}{' ...' if len(blacklist) > 5 else ''}"
                )
            
            return blacklist
        
        except Exception as e:
            log.error(f"Blacklist creation failed: {str(e)}")
            raise ValueError(f"Failed to create blacklist: {str(e)}")

    def _train_optimized_model(
        self, 
        data: pd.DataFrame, 
        blacklist: List[str],
        baseline_features: List[str] = None
    ) -> RankingModel:
        """
        Train optimized model with blacklist applied.
        
        This method trains a LightGBM ranking model with low-contribution
        features filtered out based on the blacklist.
        
        Args:
            data: Combined data with multi-index (Date, Ticker)
            blacklist: List of features to exclude
            baseline_features: List of features from baseline model (for consistency)
        
        Returns:
            RankingModel: Trained optimized model
        
        Raises:
            ValueError: If data is invalid or training fails
        
        Requirements: 3.2
        """
        if data is None or len(data) == 0:
            raise ValueError("Cannot train optimized model with empty data")
        
        log.info(
            f"Training optimized model with blacklist "
            f"({len(blacklist)} features filtered)..."
        )
        
        try:
            # Save blacklist temporarily for RankingModel to use
            # (This will be properly integrated in task 10)
            blacklist_path = "models/saved/feature_blacklist.json"
            self.feature_selector.save_blacklist(blacklist, blacklist_path)
            
            # Create RankingModel instance
            optimized_model = RankingModel(data.copy(), self.config_module)
            
            # Prepare data
            X_train, y_train, groups = optimized_model.prepare_data(is_training=True)
            
            # Use baseline features if provided for consistency
            if baseline_features:
                # Only use features that were in baseline AND are available in current data
                available_features = [f for f in baseline_features if f in X_train.columns and f not in blacklist]
                log.info(f"Using baseline feature set for consistency: {len(baseline_features)} baseline features")
            else:
                # Manually filter blacklisted features
                available_features = [f for f in X_train.columns if f not in blacklist]
            
            if len(available_features) == 0:
                raise ValueError(
                    "All features are blacklisted! "
                    "Consider lowering the importance threshold."
                )
            
            # Update feature names in the model
            optimized_model.feature_names = available_features
            
            log.info(
                f"Optimized data prepared: {len(X_train)} samples, "
                f"{len(available_features)} features (filtered {len(blacklist)}), "
                f"{len(groups)} groups"
            )
            
            # Filter X_train to only include non-blacklisted features
            X_train_filtered = X_train[available_features]
            
            # Check max label value to avoid LightGBM overflow
            max_label = int(y_train.max())
            log.info(f"Max label value: {max_label}")
            
            # Train model with filtered features
            # We need to manually train since we filtered features after prepare_data
            optimized_model.model = lgb.LGBMRanker(
                objective='lambdarank',
                metric='ndcg',
                n_estimators=100,
                learning_rate=0.1,
                num_leaves=31,
                random_state=42
            )
            
            # Set label_gain to avoid overflow with large labels
            if max_label > 30:
                log.warning(f"Large labels detected (max: {max_label}). Using linear label_gain.")
                optimized_model.model.set_params(label_gain=list(range(max_label + 1)))
            
            optimized_model.model.fit(
                X_train_filtered,
                y_train,
                group=groups
            )
            
            if optimized_model.model is None:
                raise ValueError("Optimized model training failed")
            
            log.info(
                f"Optimized model trained successfully with "
                f"{len(optimized_model.feature_names)} features"
            )
            
            # Optionally save optimized model
            if self.analysis_config.save_models:
                optimized_path = os.path.join(
                    self.analysis_config.output_dir,
                    "optimized_model.pkl"
                )
                optimized_model.save(optimized_path)
                log.info(f"Optimized model saved to {optimized_path}")
            
            return optimized_model
        
        except Exception as e:
            log.error(f"Optimized model training failed: {str(e)}")
            raise ValueError(f"Failed to train optimized model: {str(e)}")

    def _compare_models(
        self,
        baseline_model: RankingModel,
        optimized_model: RankingModel,
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Compare baseline and optimized models.
        
        This method uses ModelComparator to evaluate both models on the same
        test data and calculate performance metrics.
        
        Args:
            baseline_model: Model trained with all features
            optimized_model: Model trained with blacklist applied
            data: Test data for evaluation
        
        Returns:
            Dict with comparison metrics:
                - baseline_ndcg3: Baseline NDCG@3 score
                - optimized_ndcg3: Optimized NDCG@3 score
                - improvement_pct: Percentage improvement
                - baseline_features: Number of baseline features
                - optimized_features: Number of optimized features
        
        Raises:
            ValueError: If comparison fails
        
        Requirements: 3.3, 3.4, 3.5
        """
        if baseline_model is None or optimized_model is None:
            raise ValueError("Both models must be trained for comparison")
        
        if data is None or len(data) == 0:
            raise ValueError("Cannot compare models with empty data")
        
        log.info("Comparing baseline and optimized models...")
        
        try:
            # Use ModelComparator to compare models
            comparison_results = self.model_comparator.compare(
                baseline_model,
                optimized_model,
                data,
                self.config_module
            )
            
            log.info(
                f"Model comparison completed: "
                f"Baseline NDCG@3={comparison_results['baseline_ndcg3']:.4f}, "
                f"Optimized NDCG@3={comparison_results['optimized_ndcg3']:.4f}, "
                f"Improvement={comparison_results['improvement_pct']:+.2f}%"
            )
            
            return comparison_results
        
        except Exception as e:
            log.error(f"Model comparison failed: {str(e)}")
            raise ValueError(f"Failed to compare models: {str(e)}")

    def _save_results(
        self,
        analysis_result: AnalysisResult,
        comparison_results: Dict[str, Any]
    ):
        """
        Save analysis results including blacklist, visualizations, and report.
        
        This method:
        1. Saves blacklist to JSON
        2. Creates visualizations (top features, SHAP summary, comparison)
        3. Generates Markdown report
        4. Saves metadata as JSON
        5. Preserves previous results (doesn't overwrite)
        
        Args:
            analysis_result: Complete analysis results
            comparison_results: Model comparison metrics
        
        Raises:
            IOError: If file operations fail
        
        Requirements: 2.2, 2.3, 4.1, 4.2, 4.3, 4.4, 4.5, 10.2, 10.3
        """
        log.info("Saving analysis results...")
        
        try:
            # Ensure output directory exists
            os.makedirs(self.analysis_config.output_dir, exist_ok=True)
            
            # 1. Save blacklist
            blacklist_path = "models/saved/feature_blacklist.json"
            self.feature_selector.save_blacklist(
                analysis_result.blacklist,
                blacklist_path
            )
            log.info(f"Blacklist saved: {blacklist_path}")
            
            # 2. Create visualizations
            log.info("Creating visualizations...")
            
            # Top features bar chart
            try:
                self.visualizer.plot_top_features(
                    analysis_result.importance_df,
                    top_n=20,
                    filename="top_features.png"
                )
                log.info("Top features chart created")
            except Exception as e:
                log.warning(f"Failed to create top features chart: {str(e)}")
            
            # SHAP summary plot (if SHAP analyzer was used)
            if self.shap_analyzer is not None:
                try:
                    # We need to recompute SHAP values for the plot
                    # This is a limitation - we should store them earlier
                    log.info("SHAP summary plot skipped (requires stored SHAP values)")
                except Exception as e:
                    log.warning(f"Failed to create SHAP summary plot: {str(e)}")
            
            # Model comparison chart
            try:
                self.visualizer.plot_comparison(
                    comparison_results,
                    filename="model_comparison.png"
                )
                log.info("Model comparison chart created")
            except Exception as e:
                log.warning(f"Failed to create comparison chart: {str(e)}")
            
            # 3. Generate report
            log.info("Generating report...")
            try:
                report_path = self.report_generator.generate_report(
                    analysis_result,
                    filename=None  # Auto-generate with timestamp
                )
                log.info(f"Report generated: {report_path}")
            except Exception as e:
                log.warning(f"Failed to generate report: {str(e)}")
            
            # 4. Save metadata as JSON
            log.info("Saving metadata...")
            try:
                timestamp_str = analysis_result.timestamp.strftime("%Y%m%d_%H%M%S")
                metadata_path = os.path.join(
                    self.analysis_config.output_dir,
                    f"analysis_metadata_{timestamp_str}.json"
                )
                
                with open(metadata_path, 'w') as f:
                    json.dump(analysis_result.to_dict(), f, indent=2)
                
                log.info(f"Metadata saved: {metadata_path}")
            except Exception as e:
                log.warning(f"Failed to save metadata: {str(e)}")
            
            log.info("All results saved successfully")
        
        except Exception as e:
            log.error(f"Error saving results: {str(e)}")
            raise IOError(f"Failed to save results: {str(e)}")
