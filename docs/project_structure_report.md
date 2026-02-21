# BIST30 AI Trader - Proje Yapısı Raporu

## 1. Tam Dizin Ağacı
```bash
bist30_ai_trader/
    .env
    train_models.sh
    docker-compose.yml
    tickers.json
    .dockerignore
    config.py
    LICENSE
    project_structure_report.md
    run_training.sh
    Dockerfile
    FINAL_INTEGRATION_REPORT.md
    README.md
    integration_test_results.json
    requirements.txt
    PROJECT_STRUCTURE.md
    .gitignore
    SYSTEM_SUMMARY.md
    mlflow.db
    start_paper_trading.sh
    settings.yaml
    run_backtest.sh
    archive/
        api_conflict_backup.py
        research/
            generate_tree.py
            verify_macro_lag.py
            batch_test.py
            batch_runner.py
            validate_monte_carlo.py
            banking_batch_test.py
            monte_carlo_validation.py
            generate_docs.py
            generate_structure.py
            calc_metrics.py
            optimize_regime.py
            monte_carlo.py
            auto_tune.py
            benchmark_architectures.py
            optuna_nested_walk_forward.py
            model_experiments.py
            fetch_fundamentals.py
        shell_scripts/
            setup_linux.sh
            start_paper_trading.bat
    core/
        execution.py
        __init__.py
        backtesting.py
        position_sizing.py
        live_data_engine.py
        dynamic_backtest.py
        risk_manager.py
        macro_gate.py
        feature_store.py
        backtest/
            engine.py
            __init__.py
            metrics.py
            portfolio_engine.py
            visualizer.py
    data/
        fundamental_data.xlsx
        feature_store/
            fundamentals.parquet
        live_cache/
            latest_live.parquet
    docs/
        impact_analysis_regime_detection.md
        development_logs/
            2026-02-05.md
            2026-02-14.md
            2026-02-09.md
            2026-02-03.md
            2026-02-16.md
            README.md
            2026-02-17.md
            optuna_durum_kontrolu.md
            2026-02-06.md
            2026-02-07.md
            2026-02-15.md
    scripts/
        paper_trading_runner.py
        training/
            train_tft.py
            benchmark_vectorized_engine.py
            feature_selection.py
            benchmark_data_loading.py
            optimize_hyperparameters.py
            walk_forward_validation.py
            walk_forward_optimization.py
            train_models.py
            train_catboost.py
            train_tft_fast.py
            convert_checkpoint.py
            validate_model.py
        ops/
            check_env.py
            paper_trading_runner.py
            daily_run.py
            validate_env.py
        migration/
            migrate_to_db.py
        validation/
            check_requirements.py
            debug_volume.py
            check_function_signatures.py
            debug_check_integration.py
            verify_integration.py
            verify_db_records.py
            final_integration_report.py
            check_config_usage.py
            stress_test_bist100.py
            test_regime_integration.py
            check_integration.py
        analysis/
            analyze_items.py
            analyze_distributions.py
            check_evolution_success.py
            run_benchmark.py
            final_validation_report.py
            check_system.py
            generate_structure_report.py
            project_evaluation.py
            analyze_data_gaps.py
            micro_cap_stress_test.py
            inspect_models.py
            check_leakage.py
            compare_benchmark.py
            analyze_performance.py
            run_backtest.py
            check_forward_looking_features.py
            analyze_portfolio.py
            check_data_dates.py
            get_model_metrics.py
            inspect_kap.py
            check_integration.py
            analyze_tft_attention.py
        utility/
            clean_reqs.py
            increase_trade_frequency.py
            fetch_real_fundamental_data.py
            verify_integration.py
            verify_db_records.py
            verify_model_loading.py
            fetch_kap_offline.py
            test_macro_fetch.py
            test_rocm.py
            fix_fundamental_data.py
            audit_repo.py
            migrate_to_db.py
            find_unused_reqs.py
            debug_tft_cats.py
            update_db_schema.py
            shuffle_test.py
            test_regime_integration.py
            verify_slippage.py
            test_regime_detector.py
            test_execution_logic.py
            update_requirements.py
            test_macro_minimal.py
    logs/
        system.log.1
        system.log.3
        system.log
        system.log.2
        paper_trading/
            portfolio_state.json
            daily/
            summary/
    configs/
        banking.py
        holding.py
        aviation.py
        industrial.py
        energy.py
        __init__.py
        automotive.py
        growth.py
        real_estate.py
        retail.py
        telecom.py
        steel.py
    research/
    ui/
        package-lock.json
        next.config.ts
        package.json
        Dockerfile
        postcss.config.mjs
        README.md
        .gitignore
        tsconfig.json
        eslint.config.mjs
        public/
            next.svg
            window.svg
            globe.svg
            vercel.svg
            file.svg
        components/
            predictions/
                PredictionTable.tsx
            charts/
                TradingChart.tsx
            market/
                StockScreener.tsx
            market-depth/
                OrderBook.tsx
                DepthChart.tsx
            news/
                NewsCard.tsx
            alerts/
                AlertModal.tsx
                AlertToast.tsx
            dashboard/
                MarketHeatmap.tsx
                Watchlist.tsx
                AiConfidenceWidget.tsx
                TechnicalPanel.tsx
                SignalFeed.tsx
            layout/
                Sidebar.tsx
                HealthMonitor.tsx
            portfolio/
                RiskMetrics.tsx
                AllocationChart.tsx
                PortfolioSummary.tsx
                PositionsTable.tsx
        app/
            page.tsx
            globals.css
            favicon.ico
            layout.tsx
            settings/
                page.tsx
            predictions/
                page.tsx
            backtest/
                page.tsx
            market/
                page.tsx
            market-depth/
                page.tsx
            analysis/
                page.tsx
            portfolio/
                page.tsx
        lib/
            mockData.ts
            tickerMeta.ts
        store/
            portfolioStore.ts
            marketStore.ts
            alertStore.ts
    results/
        shuffle_test.json
    templates/
        __init__.py
    api/
        server_diagnostics.py
        backtest_jobs.db
        server.py
        ws_client.py
    tests/
        test_strategy_health.py
        test_backtest_engine.py
        test_regime_ml.py
        test_paper_trading.py
        __init__.py
        test_sor.py
        evaluate_models.py
        test_vectorized_backtest.py
        test_feature_engineering.py
        debug_fe.py
        verify_all.py
        test_kap_integration.py
        test_risk_model.py
        test_data_sanitization.py
        test_sharpe_improvement.py
        test_live_integration.py
        debug_versions.py
    utils/
        data_loader.py
        validation.py
        macro_data_loader.py
        __init__.py
        db_manager.py
        kap_data_fetcher.py
        logging_config.py
        feature_engineering.py
        features/
            derived.py
            __init__.py
            fundamental.py
            macro.py
            volatility.py
            transformer.py
            technical.py
    models/
        transformer_model.py
        regime_detector.py
        __init__.py
        ranking_model.py
        ensemble_model.py
        regime_detection.py
        ranking_model_catboost.py
        saved/
            global_ranker_catboost.cbm_features.pkl
            industrial_beta.pkl
            lgbm_model.pkl
            global_ranker_catboost.cbm
            lgbm_model_features.pkl
            holding_beta.pkl
            banking_alpha.pkl
            tft_config.joblib
            banking_beta.pkl
            global_ranker.pkl
            optimized_lgbm_params.joblib
            growth_alpha.pkl
            industrial_alpha.pkl
            growth_beta.pkl
            tft_model.pth
            global_ranker_features.pkl
            holding_alpha.pkl
    paper_trading/
        __init__.py
        portfolio_state.py
        position_engine.py
        strategy_health.py
        position_runner.py
        position_logger.py
        live_execution.py
    reports/
        benchmark_results.json
        walk_forward_optimization_results.csv
        tft_attention_analysis.txt
        quantstats_report.html
        trade_frequency_results.csv
        final_backtest_results.csv
        project_metrics_summary.md
        walk_forward_results.csv
        daily_returns_concatenated.csv
        backtest_log.txt
        min_weight_change_analysis.png
        final_validation_report.json
```

## 2. Python Dosyaları Listesi
```python
Config_Analizi = {
    "config.py": {
        "Satır": 435,
        "Sınıflar": [],
        "Fonksiyonlar": ['_load_settings', '_cfg', 'get_device', '_load_tickers', 'get_segment']... ,
        "Importlar": ['platform', 'os', 'dotenv', 'utils.logging_config', 'json']... 
    },
    "archive/api_conflict_backup.py": {
        "Satır": 154,
        "Sınıflar": ['ConnectionManager', 'Candle'],
        "Fonksiyonlar": ['read_root', 'get_market_data', 'get_portfolio', '__init__', 'disconnect']... ,
        "Importlar": ['os', 'json', 'asyncio', 'typing', 'datetime']... 
    },
    "archive/research/generate_tree.py": {
        "Satır": 36,
        "Sınıflar": [],
        "Fonksiyonlar": ['generate_tree']... ,
        "Importlar": ['os']... 
    },
    "archive/research/verify_macro_lag.py": {
        "Satır": 56,
        "Sınıflar": [],
        "Fonksiyonlar": ['verify_lag']... ,
        "Importlar": ['sys', 'os', 'pandas', 'yfinance', 'data_loader']... 
    },
    "archive/research/batch_test.py": {
        "Satır": 83,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['subprocess', 'config', 'pandas']... 
    },
    "archive/research/batch_runner.py": {
        "Satır": 69,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_metric_from_report', 'run_batch']... ,
        "Importlar": ['os', 'subprocess', 'pandas', 'glob', 're']... 
    },
    "archive/research/validate_monte_carlo.py": {
        "Satır": 105,
        "Sınıflar": [],
        "Fonksiyonlar": ['run_monte_carlo']... ,
        "Importlar": ['pandas', 'numpy', 'matplotlib.pyplot', 'os']... 
    },
    "archive/research/banking_batch_test.py": {
        "Satır": 152,
        "Sınıflar": [],
        "Fonksiyonlar": ['parse_output', 'run_banking_tests', 'save_results']... ,
        "Importlar": ['sys', 'os', 'subprocess', 'pandas', 're']... 
    },
    "archive/research/monte_carlo_validation.py": {
        "Satır": 411,
        "Sınıflar": [],
        "Fonksiyonlar": ['load_daily_returns', 'monte_carlo_simulation', 'stress_test', 'calculate_risk_metrics', 'create_monte_carlo_visualization']... ,
        "Importlar": ['pandas', 'numpy', 'matplotlib.pyplot', 'seaborn', 'scipy']... 
    },
    "archive/research/generate_docs.py": {
        "Satır": 38,
        "Sınıflar": [],
        "Fonksiyonlar": ['convert_md_to_html']... ,
        "Importlar": ['markdown', 'os']... 
    },
    "archive/research/generate_structure.py": {
        "Satır": 31,
        "Sınıflar": [],
        "Fonksiyonlar": ['generate_tree']... ,
        "Importlar": ['os', 'sys']... 
    },
    "archive/research/calc_metrics.py": {
        "Satır": 18,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['pandas']... 
    },
    "archive/research/optimize_regime.py": {
        "Satır": 126,
        "Sınıflar": ['RegimeOptimizer'],
        "Fonksiyonlar": ['__init__', 'load_data', 'objective', 'optimize']... ,
        "Importlar": ['optuna', 'pandas', 'numpy', 'sys', 'os']... 
    },
    "archive/research/monte_carlo.py": {
        "Satır": 57,
        "Sınıflar": ['MonteCarloSimulator'],
        "Fonksiyonlar": ['__init__', 'run_simulation', 'get_stats']... ,
        "Importlar": ['sys', 'os', 'numpy', 'pandas', 'matplotlib.pyplot']... 
    },
    "archive/research/auto_tune.py": {
        "Satır": 327,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_vectorized_macro_gate', 'run_strategy_simulation', 'optimize_model_hyperparameters', 'optimize', 'objective']... ,
        "Importlar": ['optuna', 'pandas', 'numpy', 'os', 'sys']... 
    },
    "archive/research/benchmark_architectures.py": {
        "Satır": 229,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_data', 'backtest_predictions', 'run_benchmark']... ,
        "Importlar": ['pandas', 'numpy', 'sys', 'os', 'config']... 
    },
    "archive/research/optuna_nested_walk_forward.py": {
        "Satır": 631,
        "Sınıflar": [],
        "Fonksiyonlar": ['_progress_log', 'get_adaptive_threshold', 'get_dynamic_stop_loss', 'get_volatility_adjusted_size', 'load_data']... ,
        "Importlar": ['pandas', 'numpy', 'os', 'sys', 'optuna']... 
    },
    "archive/research/model_experiments.py": {
        "Satır": 195,
        "Sınıflar": [],
        "Fonksiyonlar": ['calculate_ndcg', 'evaluate_ensemble', 'tune_lgbm', 'tune_catboost', 'main']... ,
        "Importlar": ['optuna', 'pandas', 'numpy', 'os', 'sys']... 
    },
    "archive/research/fetch_fundamentals.py": {
        "Satır": 181,
        "Sınıflar": [],
        "Fonksiyonlar": ['ensure_data_dir', 'fetch_and_calculate_fundamentals']... ,
        "Importlar": ['sys', 'os', 'yfinance', 'pandas', 'numpy']... 
    },
    "core/execution.py": {
        "Satır": 145,
        "Sınıflar": ['ExecutionManager', 'OrderType', 'Urgency', 'SmartOrderRouter'],
        "Fonksiyonlar": ['__init__', 'calculate_optimal_lots', 'validate_order', 'simulate_slippage', '__init__']... ,
        "Importlar": ['math', 'utils.logging_config', 'enum']... 
    },
    "core/__init__.py": {
        "Satır": 0,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": []... 
    },
    "core/backtesting.py": {
        "Satır": 60,
        "Sınıflar": ['Backtester'],
        "Fonksiyonlar": ['__init__']... ,
        "Importlar": ['core.position_sizing', 'core.backtest.engine', 'core.backtest.metrics', 'core.backtest.visualizer', 'pandas']... 
    },
    "core/position_sizing.py": {
        "Satır": 84,
        "Sınıflar": ['KellyPositionSizer'],
        "Fonksiyonlar": ['__init__', 'add_trade', 'calculate_kelly', 'get_position_size']... ,
        "Importlar": ['numpy', 'pandas', 'utils.logging_config', 'random']... 
    },
    "core/live_data_engine.py": {
        "Satır": 199,
        "Sınıflar": ['DataUnavailabilityError', 'MarketDataValidator', 'LiveDataEngine', 'Config'],
        "Fonksiyonlar": ['validate_dataframe', '__new__', 'fetch_live_data', '_validate_data', '_save_to_cache']... ,
        "Importlar": ['yfinance', 'pandas', 'os', 'time', 'datetime']... 
    },
    "core/dynamic_backtest.py": {
        "Satır": 554,
        "Sınıflar": ['DynamicBacktest'],
        "Fonksiyonlar": ['ensure_cache_dir', 'get_cache_key', 'load_cached_data', 'save_to_cache', 'batch_download_data']... ,
        "Importlar": ['pandas', 'numpy', 'os', 'sys', 'datetime']... 
    },
    "core/risk_manager.py": {
        "Satır": 305,
        "Sınıflar": ['ConfigWrapper', 'RiskManager'],
        "Fonksiyonlar": ['__init__', 'get', '__init__', 'adjust_for_regime', 'calculate_stop_loss']... ,
        "Importlar": ['config', 'pandas', 'numpy', 'logging', 'models.regime_detector']... 
    },
    "core/macro_gate.py": {
        "Satır": 131,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_thresholds', 'vectorized_macro_gate', 'single_step_macro_gate']... ,
        "Importlar": ['__future__', 'typing', 'pandas', 'config']... 
    },
    "core/feature_store.py": {
        "Satır": 93,
        "Sınıflar": ['FeatureStore'],
        "Fonksiyonlar": ['__init__', 'save_fundamentals', 'load_fundamentals', 'import_from_excel', 'get_latest_ratios']... ,
        "Importlar": ['pandas', 'numpy', 'os', 'datetime', 'utils.logging_config']... 
    },
    "core/backtest/engine.py": {
        "Satır": 468,
        "Sınıflar": ['BacktestEngineMixin'],
        "Fonksiyonlar": ['calculate_slippage', '_get_market_indicators', 'run_backtest']... ,
        "Importlar": ['pandas', 'numpy', 'config', 'typing', 'core.risk_manager']... 
    },
    "core/backtest/__init__.py": {
        "Satır": 5,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['core.backtest.engine', 'core.backtest.metrics', 'core.backtest.visualizer']... 
    },
    "core/backtest/metrics.py": {
        "Satır": 145,
        "Sınıflar": ['BacktestMetricsMixin'],
        "Fonksiyonlar": ['calculate_metrics']... ,
        "Importlar": ['numpy', 'pandas']... 
    },
    "core/backtest/portfolio_engine.py": {
        "Satır": 166,
        "Sınıflar": ['PortfolioBacktester'],
        "Fonksiyonlar": ['__init__', 'run_backtest']... ,
        "Importlar": ['pandas', 'numpy', 'config', 'core.risk_manager', 'logging']... 
    },
    "core/backtest/visualizer.py": {
        "Satır": 194,
        "Sınıflar": ['BacktestVisualizerMixin'],
        "Fonksiyonlar": ['plot_results', 'plot_drawdown', 'plot_monthly_heatmap', 'save_trade_log', 'generate_html_report']... ,
        "Importlar": ['os', 'pandas', 'numpy', 'matplotlib.pyplot', 'seaborn']... 
    },
    "scripts/paper_trading_runner.py": {
        "Satır": 47,
        "Sınıflar": [],
        "Fonksiyonlar": ['run_trading_cycle', 'main']... ,
        "Importlar": ['sys', 'os', 'time', 'schedule', 'datetime']... 
    },
    "scripts/training/train_tft.py": {
        "Satır": 213,
        "Sınıflar": [],
        "Fonksiyonlar": ['main']... ,
        "Importlar": ['sys', 'os', 'torch', 'pandas', 'joblib']... 
    },
    "scripts/training/benchmark_vectorized_engine.py": {
        "Satır": 147,
        "Sınıflar": [],
        "Fonksiyonlar": ['iterative_backtest_sim', 'benchmark']... ,
        "Importlar": ['time', 'pandas', 'numpy', 'sys', 'os']... 
    },
    "scripts/training/feature_selection.py": {
        "Satır": 111,
        "Sınıflar": [],
        "Fonksiyonlar": ['run_feature_selection']... ,
        "Importlar": ['sys', 'os', 'pandas', 'numpy', 'joblib']... 
    },
    "scripts/training/benchmark_data_loading.py": {
        "Satır": 59,
        "Sınıflar": [],
        "Fonksiyonlar": ['benchmark']... ,
        "Importlar": ['sys', 'os', 'time', 'pandas', 'config']... 
    },
    "scripts/training/optimize_hyperparameters.py": {
        "Satır": 172,
        "Sınıflar": [],
        "Fonksiyonlar": ['objective']... ,
        "Importlar": ['os', 'sys', 'optuna', 'joblib', 'pandas']... 
    },
    "scripts/training/walk_forward_validation.py": {
        "Satır": 280,
        "Sınıflar": ['MockConfig'],
        "Fonksiyonlar": ['comprehensive_walk_forward', '__init__']... ,
        "Importlar": ['pandas', 'numpy', 'os', 'sys', 'matplotlib.pyplot']... 
    },
    "scripts/training/walk_forward_optimization.py": {
        "Satır": 143,
        "Sınıflar": [],
        "Fonksiyonlar": ['run_walk_forward_optimization']... ,
        "Importlar": ['sys', 'os', 'pandas', 'numpy', 'datetime']... 
    },
    "scripts/training/train_models.py": {
        "Satır": 294,
        "Sınıflar": [],
        "Fonksiyonlar": ['ensure_model_dir', 'train_global_ranker', 'main']... ,
        "Importlar": ['os', 'sys', 'joblib', 'numpy', 'pandas']... 
    },
    "scripts/training/train_catboost.py": {
        "Satır": 103,
        "Sınıflar": [],
        "Fonksiyonlar": ['ensure_model_dir', 'train_catboost_ranker', 'main']... ,
        "Importlar": ['pandas', 'numpy', 'os', 'sys', 'joblib']... 
    },
    "scripts/training/train_tft_fast.py": {
        "Satır": 213,
        "Sınıflar": [],
        "Fonksiyonlar": ['main']... ,
        "Importlar": ['sys', 'os', 'torch', 'pandas', 'joblib']... 
    },
    "scripts/training/convert_checkpoint.py": {
        "Satır": 55,
        "Sınıflar": [],
        "Fonksiyonlar": ['convert_checkpoint']... ,
        "Importlar": ['sys', 'os', 'torch', 'pytorch_forecasting', 'models.transformer_model']... 
    },
    "scripts/training/validate_model.py": {
        "Satır": 90,
        "Sınıflar": [],
        "Fonksiyonlar": ['validate']... ,
        "Importlar": ['pandas', 'numpy', 'joblib', 'os', 'sys']... 
    },
    "scripts/ops/check_env.py": {
        "Satır": 37,
        "Sınıflar": [],
        "Fonksiyonlar": ['run_cmd']... ,
        "Importlar": ['os', 'sys', 'subprocess', 'yfinance', 'requests']... 
    },
    "scripts/ops/paper_trading_runner.py": {
        "Satır": 147,
        "Sınıflar": ['PaperTrader'],
        "Fonksiyonlar": ['__init__', 'load_model', 'update_market_data', 'check_signals', 'run']... ,
        "Importlar": ['time', 'pandas', 'numpy', 'datetime', 'os']... 
    },
    "scripts/ops/daily_run.py": {
        "Satır": 95,
        "Sınıflar": ['LiveTrader'],
        "Fonksiyonlar": ['__init__', 'fetch_latest_data', 'log_paper_trade', 'daily_pipeline']... ,
        "Importlar": ['os', 'sys', 'pandas', 'datetime', 'config']... 
    },
    "scripts/ops/validate_env.py": {
        "Satır": 28,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['sys', 'torch', 'pandas', 'lightgbm', 'pytorch_forecasting']... 
    },
    "scripts/migration/migrate_to_db.py": {
        "Satır": 156,
        "Sınıflar": [],
        "Fonksiyonlar": ['migrate_tickers', 'migrate_fundamentals']... ,
        "Importlar": ['os', 'sys', 'json', 'pandas', 'psycopg2']... 
    },
    "scripts/validation/check_requirements.py": {
        "Satır": 115,
        "Sınıflar": [],
        "Fonksiyonlar": ['check_requirements']... ,
        "Importlar": ['pathlib', 'ast', 'sys', 'os']... 
    },
    "scripts/validation/debug_volume.py": {
        "Satır": 40,
        "Sınıflar": [],
        "Fonksiyonlar": ['debug']... ,
        "Importlar": ['sys', 'os', 'pandas', 'utils.data_loader', 'utils.logging_config']... 
    },
    "scripts/validation/check_function_signatures.py": {
        "Satır": 102,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_python_files', 'check_function_signature_compatibility']... ,
        "Importlar": ['ast', 'inspect', 'pathlib', 'sys', 'os']... 
    },
    "scripts/validation/debug_check_integration.py": {
        "Satır": 35,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_python_files']... ,
        "Importlar": ['os', 'ast', 'sys', 'pathlib']... 
    },
    "scripts/validation/verify_integration.py": {
        "Satır": 209,
        "Sınıflar": [],
        "Fonksiyonlar": ['run_integration_test']... ,
        "Importlar": ['sys', 'logging', 'os', 'datetime', 'config']... 
    },
    "scripts/validation/verify_db_records.py": {
        "Satır": 53,
        "Sınıflar": [],
        "Fonksiyonlar": ['verify_db']... ,
        "Importlar": ['os', 'sys', 'pandas', 'utils.db_manager', 'utils.logging_config']... 
    },
    "scripts/validation/final_integration_report.py": {
        "Satır": 76,
        "Sınıflar": [],
        "Fonksiyonlar": ['generate_integration_report']... ,
        "Importlar": ['sys', 'subprocess']... 
    },
    "scripts/validation/check_config_usage.py": {
        "Satır": 152,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_python_files', 'check_config_usage']... ,
        "Importlar": ['ast', 'pathlib', 'sys', 'os', 'typing']... 
    },
    "scripts/validation/stress_test_bist100.py": {
        "Satır": 140,
        "Sınıflar": [],
        "Fonksiyonlar": ['run_stress_test']... ,
        "Importlar": ['sys', 'os', 'time', 'pandas', 'numpy']... 
    },
    "scripts/validation/test_regime_integration.py": {
        "Satır": 115,
        "Sınıflar": [],
        "Fonksiyonlar": ['check_regime_integration']... ,
        "Importlar": ['sys', 'pathlib']... 
    },
    "scripts/validation/check_integration.py": {
        "Satır": 220,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_python_files', 'check_all_imports', 'extract_imports', 'is_project_module', 'check_module_exists']... ,
        "Importlar": ['os', 'ast', 'importlib', 'sys', 'pathlib']... 
    },
    "scripts/analysis/analyze_items.py": {
        "Satır": 37,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['isyatirimhisse', 'pandas']... 
    },
    "scripts/analysis/analyze_distributions.py": {
        "Satır": 78,
        "Sınıflar": [],
        "Fonksiyonlar": ['analyze_sector_distributions']... ,
        "Importlar": ['sys', 'os', 'core.feature_store', 'pandas', 'numpy']... 
    },
    "scripts/analysis/check_evolution_success.py": {
        "Satır": 112,
        "Sınıflar": [],
        "Fonksiyonlar": ['check_evolution']... ,
        "Importlar": ['sys', 'os', 'random', 'logging', 'core.execution']... 
    },
    "scripts/analysis/run_benchmark.py": {
        "Satır": 383,
        "Sınıflar": [],
        "Fonksiyonlar": ['calculate_metrics', 'load_all_data', 'train_lgbm_ranker', 'simulate_portfolio', 'run_walk_forward_backtest']... ,
        "Importlar": ['os', 'sys', 'pandas', 'numpy', 'joblib']... 
    },
    "scripts/analysis/final_validation_report.py": {
        "Satır": 189,
        "Sınıflar": [],
        "Fonksiyonlar": ['generate_final_validation_report']... ,
        "Importlar": ['json', 'os', 'pandas']... 
    },
    "scripts/analysis/check_system.py": {
        "Satır": 31,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['torch', 'sys', 'os']... 
    },
    "scripts/analysis/generate_structure_report.py": {
        "Satır": 151,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_tree', 'analyze_file', 'main']... ,
        "Importlar": ['os', 'ast', 'sys']... 
    },
    "scripts/analysis/project_evaluation.py": {
        "Satır": 359,
        "Sınıflar": [],
        "Fonksiyonlar": ['evaluate_project_quality', 'analyze_metric']... ,
        "Importlar": ['sys', 'os', 'pandas', 'numpy', 'joblib']... 
    },
    "scripts/analysis/analyze_data_gaps.py": {
        "Satır": 85,
        "Sınıflar": [],
        "Fonksiyonlar": ['analyze_gaps']... ,
        "Importlar": ['sys', 'os', 'pandas', 'yfinance', 'datetime']... 
    },
    "scripts/analysis/micro_cap_stress_test.py": {
        "Satır": 101,
        "Sınıflar": [],
        "Fonksiyonlar": ['run_stress_test']... ,
        "Importlar": ['sys', 'os', 'pandas', 'numpy', 'math']... 
    },
    "scripts/analysis/inspect_models.py": {
        "Satır": 117,
        "Sınıflar": [],
        "Fonksiyonlar": ['inspect_lightgbm', 'inspect_catboost', 'check_lightning_logs']... ,
        "Importlar": ['sys', 'os', 'joblib', 'torch', 'pandas']... 
    },
    "scripts/analysis/check_leakage.py": {
        "Satır": 91,
        "Sınıflar": [],
        "Fonksiyonlar": ['check_leakage_in_code']... ,
        "Importlar": ['ast', 'os']... 
    },
    "scripts/analysis/compare_benchmark.py": {
        "Satır": 129,
        "Sınıflar": [],
        "Fonksiyonlar": ['calculate_max_drawdown', 'calculate_sharpe_ratio', 'compare_benchmark']... ,
        "Importlar": ['pandas', 'numpy', 'yfinance', 'matplotlib.pyplot', 'os']... 
    },
    "scripts/analysis/analyze_performance.py": {
        "Satır": 194,
        "Sınıflar": [],
        "Fonksiyonlar": ['analyze_sector_performance', 'analyze_market_regimes', 'main']... ,
        "Importlar": ['os', 'sys', 'pandas', 'numpy', 'argparse']... 
    },
    "scripts/analysis/run_backtest.py": {
        "Satır": 579,
        "Sınıflar": [],
        "Fonksiyonlar": ['main']... ,
        "Importlar": ['os', 'sys', 'argparse', 'joblib', 'numpy']... 
    },
    "scripts/analysis/check_forward_looking_features.py": {
        "Satır": 172,
        "Sınıflar": [],
        "Fonksiyonlar": ['check_forward_looking_features']... ,
        "Importlar": ['pandas', 'numpy', 'sys', 'os', 'utils.data_loader']... 
    },
    "scripts/analysis/analyze_portfolio.py": {
        "Satır": 39,
        "Sınıflar": [],
        "Fonksiyonlar": ['calculate_max_drawdown', 'calculate_sharpe_ratio', 'analyze']... ,
        "Importlar": ['pandas', 'numpy']... 
    },
    "scripts/analysis/check_data_dates.py": {
        "Satır": 51,
        "Sınıflar": [],
        "Fonksiyonlar": ['check_dates']... ,
        "Importlar": ['sys', 'os', 'pandas', 'config', 'utils.data_loader']... 
    },
    "scripts/analysis/get_model_metrics.py": {
        "Satır": 63,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_latest_metrics']... ,
        "Importlar": ['mlflow', 'pandas', 'os', 'sys']... 
    },
    "scripts/analysis/inspect_kap.py": {
        "Satır": 54,
        "Sınıflar": [],
        "Fonksiyonlar": ['new_init']... ,
        "Importlar": ['sys', 'os', 'datetime', 'requests', 'requests.packages.urllib3.exceptions']... 
    },
    "scripts/analysis/check_integration.py": {
        "Satır": 124,
        "Sınıflar": [],
        "Fonksiyonlar": ['check_gpu', 'check_database', 'check_mlflow', 'check_models']... ,
        "Importlar": ['sys', 'os', 'torch', 'mlflow', 'pandas']... 
    },
    "scripts/analysis/analyze_tft_attention.py": {
        "Satır": 222,
        "Sınıflar": [],
        "Fonksiyonlar": ['analyze_attention']... ,
        "Importlar": ['sys', 'os', 'torch', 'pandas', 'numpy']... 
    },
    "scripts/utility/clean_reqs.py": {
        "Satır": 51,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['os']... 
    },
    "scripts/utility/increase_trade_frequency.py": {
        "Satır": 225,
        "Sınıflar": [],
        "Fonksiyonlar": ['increase_trade_frequency']... ,
        "Importlar": ['pandas', 'numpy', 'os', 'sys', 'matplotlib.pyplot']... 
    },
    "scripts/utility/fetch_real_fundamental_data.py": {
        "Satır": 231,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_financial_group', 'find_item_in_financials', 'fetch_and_process']... ,
        "Importlar": ['pandas', 'numpy', 'isyatirimhisse', 'datetime', 'time']... 
    },
    "scripts/utility/verify_integration.py": {
        "Satır": 81,
        "Sınıflar": [],
        "Fonksiyonlar": ['check_gpu', 'check_database', 'check_dataloader']... ,
        "Importlar": ['sys', 'os', 'torch', 'pandas', 'datetime']... 
    },
    "scripts/utility/verify_db_records.py": {
        "Satır": 18,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['os', 'sys', 'utils.db_manager', 'pandas']... 
    },
    "scripts/utility/verify_model_loading.py": {
        "Satır": 50,
        "Sınıflar": [],
        "Fonksiyonlar": ['verify_loading']... ,
        "Importlar": ['sys', 'os', 'joblib', 'config', 'models.ensemble_model']... 
    },
    "scripts/utility/fetch_kap_offline.py": {
        "Satır": 81,
        "Sınıflar": [],
        "Fonksiyonlar": ['fetch_ticker_history', 'main']... ,
        "Importlar": ['os', 'sys', 'time', 'pandas', 'datetime']... 
    },
    "scripts/utility/test_macro_fetch.py": {
        "Satır": 65,
        "Sınıflar": [],
        "Fonksiyonlar": ['test_macro_fetch']... ,
        "Importlar": ['sys', 'os', 'pandas', 'utils.data_loader', 'utils.logging_config']... 
    },
    "scripts/utility/test_rocm.py": {
        "Satır": 7,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['torch']... 
    },
    "scripts/utility/fix_fundamental_data.py": {
        "Satır": 113,
        "Sınıflar": [],
        "Fonksiyonlar": ['fix_data']... ,
        "Importlar": ['pandas', 'numpy', 'os', 'datetime']... 
    },
    "scripts/utility/audit_repo.py": {
        "Satır": 82,
        "Sınıflar": [],
        "Fonksiyonlar": ['check_file', 'scan_repo']... ,
        "Importlar": ['ast', 'os', 'sys', 'collections']... 
    },
    "scripts/utility/migrate_to_db.py": {
        "Satır": 81,
        "Sınıflar": [],
        "Fonksiyonlar": ['migrate_market_data', 'migrate_fundamentals']... ,
        "Importlar": ['sys', 'os', 'pandas', 'yfinance', 'datetime']... 
    },
    "scripts/utility/find_unused_reqs.py": {
        "Satır": 56,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_imports', 'check_requirements']... ,
        "Importlar": ['pkg_resources', 'ast', 'os', 'sys']... 
    },
    "scripts/utility/debug_tft_cats.py": {
        "Satır": 28,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['torch', 'joblib', 'os', 'sys', 'models.transformer_model']... 
    },
    "scripts/utility/update_db_schema.py": {
        "Satır": 56,
        "Sınıflar": [],
        "Fonksiyonlar": ['update_schema']... ,
        "Importlar": ['os', 'sys', 'psycopg2', 'psycopg2', 'utils.logging_config']... 
    },
    "scripts/utility/shuffle_test.py": {
        "Satır": 294,
        "Sınıflar": [],
        "Fonksiyonlar": ['run_strategy_simulation', 'shuffle_test']... ,
        "Importlar": ['numpy', 'pandas', 'json', 'os', 'sys']... 
    },
    "scripts/utility/test_regime_integration.py": {
        "Satır": 47,
        "Sınıflar": [],
        "Fonksiyonlar": ['test_regime_integration']... ,
        "Importlar": ['sys', 'os', 'pandas', 'numpy', 'models.regime_detector']... 
    },
    "scripts/utility/verify_slippage.py": {
        "Satır": 34,
        "Sınıflar": ['MockEngine'],
        "Fonksiyonlar": ['test_slippage']... ,
        "Importlar": ['pandas', 'sys', 'os', 'core.backtest.engine']... 
    },
    "scripts/utility/test_regime_detector.py": {
        "Satır": 69,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['sys', 'os', 'pandas', 'numpy', 'config']... 
    },
    "scripts/utility/test_execution_logic.py": {
        "Satır": 55,
        "Sınıflar": [],
        "Fonksiyonlar": ['test_execution_manager']... ,
        "Importlar": ['core.execution', 'logging']... 
    },
    "scripts/utility/update_requirements.py": {
        "Satır": 68,
        "Sınıflar": [],
        "Fonksiyonlar": ['update_requirements']... ,
        "Importlar": ['subprocess', 'sys', 'os']... 
    },
    "scripts/utility/test_macro_minimal.py": {
        "Satır": 24,
        "Sınıflar": [],
        "Fonksiyonlar": ['new_init', 'test_minimal']... ,
        "Importlar": ['yfinance', 'requests', 'requests.packages.urllib3.exceptions']... 
    },
    "configs/banking.py": {
        "Satır": 49,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['config']... 
    },
    "configs/holding.py": {
        "Satır": 49,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['config']... 
    },
    "configs/aviation.py": {
        "Satır": 42,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['config']... 
    },
    "configs/industrial.py": {
        "Satır": 48,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['config']... 
    },
    "configs/energy.py": {
        "Satır": 41,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['config']... 
    },
    "configs/__init__.py": {
        "Satır": 33,
        "Sınıflar": [],
        "Fonksiyonlar": ['get_config_for_sector']... ,
        "Importlar": ['banking', 'holding', 'industrial', 'growth', 'aviation']... 
    },
    "configs/automotive.py": {
        "Satır": 42,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['config']... 
    },
    "configs/growth.py": {
        "Satır": 48,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['config']... 
    },
    "configs/real_estate.py": {
        "Satır": 40,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['config']... 
    },
    "configs/retail.py": {
        "Satır": 41,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['config']... 
    },
    "configs/telecom.py": {
        "Satır": 39,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['config']... 
    },
    "configs/steel.py": {
        "Satır": 40,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['config']... 
    },
    "templates/__init__.py": {
        "Satır": 0,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": []... 
    },
    "api/server_diagnostics.py": {
        "Satır": 48,
        "Sınıflar": [],
        "Fonksiyonlar": ['test_fetch']... ,
        "Importlar": ['yfinance', 'pandas', 'time']... 
    },
    "api/server.py": {
        "Satır": 634,
        "Sınıflar": ['BacktestRequest', 'BacktestStatus', 'ConnectionManager'],
        "Fonksiyonlar": ['_init_db', '_save_job', '_load_job', '_load_model', 'run_backtest_job']... ,
        "Importlar": ['os', 'sys', 'sqlite3', 'datetime', 'contextlib']... 
    },
    "api/ws_client.py": {
        "Satır": 33,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['asyncio', 'websockets', 'json']... 
    },
    "tests/test_strategy_health.py": {
        "Satır": 246,
        "Sınıflar": ['TestRollingMetrics', 'TestInvalidationRules', 'TestStateTransitions', 'TestMaxDrawdownTracking', 'TestDynamicConfidenceThreshold', 'TestStatePersistence', 'TestIntegrationHelper', 'MockPortfolio'],
        "Fonksiyonlar": ['test_rolling_metrics_empty', 'test_rolling_metrics_basic', 'test_all_rolling_windows', 'test_expectancy_disabled', 'test_consecutive_losses_paused']... ,
        "Importlar": ['unittest', 'os', 'json', 'tempfile', 'paper_trading.strategy_health']... 
    },
    "tests/test_backtest_engine.py": {
        "Satır": 74,
        "Sınıflar": ['TestBacktestEngine'],
        "Fonksiyonlar": ['setUp', 'test_initial_state', 'test_run_backtest_basic']... ,
        "Importlar": ['unittest', 'pandas', 'numpy', 'datetime', 'sys']... 
    },
    "tests/test_regime_ml.py": {
        "Satır": 38,
        "Sınıflar": [],
        "Fonksiyonlar": ['test_ml_regime']... ,
        "Importlar": ['pandas', 'config', 'utils.data_loader', 'utils.feature_engineering', 'models.regime_detection']... 
    },
    "tests/test_paper_trading.py": {
        "Satır": 128,
        "Sınıflar": [],
        "Fonksiyonlar": ['test_position_flow']... ,
        "Importlar": ['sys', 'os', 'paper_trading.portfolio_state', 'paper_trading.position_engine']... 
    },
    "tests/__init__.py": {
        "Satır": 0,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": []... 
    },
    "tests/test_sor.py": {
        "Satır": 46,
        "Sınıflar": ['TestSmartOrderRouter'],
        "Fonksiyonlar": ['setUp', 'test_high_urgency_market_order', 'test_normal_urgency_limit_order', 'test_low_urgency_passive_order']... ,
        "Importlar": ['unittest', 'core.execution']... 
    },
    "tests/evaluate_models.py": {
        "Satır": 245,
        "Sınıflar": [],
        "Fonksiyonlar": ['evaluate']... ,
        "Importlar": ['os', 'sys', 'pandas', 'numpy', 'joblib']... 
    },
    "tests/test_vectorized_backtest.py": {
        "Satır": 84,
        "Sınıflar": ['TestVectorizedBacktest'],
        "Fonksiyonlar": ['setUp', 'test_run_backtest', 'test_liquidity_filter']... ,
        "Importlar": ['unittest', 'pandas', 'numpy', 'sys', 'os']... 
    },
    "tests/test_feature_engineering.py": {
        "Satır": 86,
        "Sınıflar": ['TestFeatureEngineering'],
        "Fonksiyonlar": ['setUp', 'test_technical_features', 'test_volatility_features', 'test_derived_features', 'test_process_all']... ,
        "Importlar": ['unittest', 'pandas', 'numpy', 'datetime', 'sys']... 
    },
    "tests/debug_fe.py": {
        "Satır": 41,
        "Sınıflar": [],
        "Fonksiyonlar": ['debug_fe']... ,
        "Importlar": ['sys', 'os', 'pandas', 'numpy', 'traceback']... 
    },
    "tests/verify_all.py": {
        "Satır": 116,
        "Sınıflar": ['DummyConfig'],
        "Fonksiyonlar": ['test_imports', 'test_macro_loader', 'test_feature_engineering', 'test_tft_model', 'test_kelly_sizer']... ,
        "Importlar": ['sys', 'os', 'pandas', 'numpy', 'torch']... 
    },
    "tests/test_kap_integration.py": {
        "Satır": 60,
        "Sınıflar": [],
        "Fonksiyonlar": ['test_kap_integration']... ,
        "Importlar": ['sys', 'os', 'pandas', 'utils.kap_data_fetcher', 'datetime']... 
    },
    "tests/test_risk_model.py": {
        "Satır": 88,
        "Sınıflar": ['TestRiskManager'],
        "Fonksiyonlar": ['setUp', 'test_adjust_for_regime', 'test_check_exit_conditions_stop_loss', 'test_check_exit_conditions_trailing_stop', 'test_calculate_position_size']... ,
        "Importlar": ['unittest', 'numpy', 'core.risk_manager', 'config']... 
    },
    "tests/test_data_sanitization.py": {
        "Satır": 47,
        "Sınıflar": [],
        "Fonksiyonlar": ['test_sanitization']... ,
        "Importlar": ['sys', 'os', 'pandas', 'utils.data_loader', 'utils.logging_config']... 
    },
    "tests/test_sharpe_improvement.py": {
        "Satır": 61,
        "Sınıflar": ['TestSharpeImprovement'],
        "Fonksiyonlar": ['setUp', 'test_dynamic_risk_params', 'test_process_signal_signature']... ,
        "Importlar": ['sys', 'os', 'unittest', 'unittest.mock', 'paper_trading.position_engine']... 
    },
    "tests/test_live_integration.py": {
        "Satır": 39,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['sys', 'os', 'pandas', 'core.live_data_engine', 'config']... 
    },
    "tests/debug_versions.py": {
        "Satır": 38,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['torch', 'pytorch_lightning', 'lightning.pytorch', 'pytorch_forecasting', 'pytorch_forecasting']... 
    },
    "utils/data_loader.py": {
        "Satır": 495,
        "Sınıflar": ['DataLoader', 'NoSSLVerification'],
        "Fonksiyonlar": ['__init__', 'fetch_live_data', 'fetch_macro_data', 'get_combined_data', '_check_data_quality']... ,
        "Importlar": ['yfinance', 'pandas', 'numpy', 'config', 'datetime']... 
    },
    "utils/validation.py": {
        "Satır": 65,
        "Sınıflar": ['DataValidator'],
        "Fonksiyonlar": ['validate_ohlcv', 'validate_features']... ,
        "Importlar": ['pandas', 'typing', 'utils.logging_config']... 
    },
    "utils/macro_data_loader.py": {
        "Satır": 111,
        "Sınıflar": ['TurkeyMacroData'],
        "Fonksiyonlar": ['__init__', 'fetch_all']... ,
        "Importlar": ['pandas', 'yfinance', 'evds', 'os', 'utils.logging_config']... 
    },
    "utils/__init__.py": {
        "Satır": 0,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": []... 
    },
    "utils/db_manager.py": {
        "Satır": 356,
        "Sınıflar": ['DBManager'],
        "Fonksiyonlar": ['__init__', '_initialize_pool', 'get_connection', 'return_connection', 'connection']... ,
        "Importlar": ['os', 'psycopg2', 'psycopg2', 'contextlib', 'pandas']... 
    },
    "utils/kap_data_fetcher.py": {
        "Satır": 332,
        "Sınıflar": ['KAPDataFetcher'],
        "Fonksiyonlar": ['__init__', '_get_cache_path', '_is_cache_valid', '_load_cache', '_save_cache']... ,
        "Importlar": ['os', 'json', 'hashlib', 'datetime', 'typing']... 
    },
    "utils/logging_config.py": {
        "Satır": 79,
        "Sınıflar": [],
        "Fonksiyonlar": ['_setup_root_logger', 'get_logger']... ,
        "Importlar": ['logging', 'os', 'sys', 'datetime', 'logging.handlers']... 
    },
    "utils/feature_engineering.py": {
        "Satır": 91,
        "Sınıflar": ['FeatureEngineer'],
        "Fonksiyonlar": ['__init__', 'process_all']... ,
        "Importlar": ['numpy', 'config', 'utils.features.technical', 'utils.features.volatility', 'utils.features.macro']... 
    },
    "utils/features/derived.py": {
        "Satır": 133,
        "Sınıflar": ['DerivedMixin'],
        "Fonksiyonlar": ['add_multi_window_targets', 'add_time_features', 'add_derived_features', 'clean_data']... ,
        "Importlar": ['pandas', 'numpy', 'config']... 
    },
    "utils/features/__init__.py": {
        "Satır": 8,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['utils.features.technical', 'utils.features.volatility', 'utils.features.macro', 'utils.features.fundamental', 'utils.features.derived']... 
    },
    "utils/features/fundamental.py": {
        "Satır": 119,
        "Sınıflar": ['FundamentalMixin'],
        "Fonksiyonlar": ['add_fundamental_features_from_file', '_align_quarterly_data', 'add_kap_features']... ,
        "Importlar": ['pandas', 'numpy', 'config', 'datetime', 'core.feature_store']... 
    },
    "utils/features/macro.py": {
        "Satır": 200,
        "Sınıflar": ['MacroMixin'],
        "Fonksiyonlar": ['add_sector_dummies', 'add_macro_interaction_features', 'add_bank_features', 'add_advanced_market_features', 'add_macro_derived_features']... ,
        "Importlar": ['pandas', 'numpy', 'config']... 
    },
    "utils/features/volatility.py": {
        "Satır": 44,
        "Sınıflar": ['VolatilityMixin'],
        "Fonksiyonlar": ['add_volatility_estimators']... ,
        "Importlar": ['numpy']... 
    },
    "utils/features/transformer.py": {
        "Satır": 78,
        "Sınıflar": ['TransformerMixin'],
        "Fonksiyonlar": ['prepare_tft_dataset', 'add_transformer_features']... ,
        "Importlar": []... 
    },
    "utils/features/technical.py": {
        "Satır": 181,
        "Sınıflar": ['TechnicalMixin'],
        "Fonksiyonlar": ['add_technical_indicators', 'add_custom_indicators', 'add_volume_and_extra_indicators']... ,
        "Importlar": ['pandas', 'pandas_ta', 'numpy', 'config', 'logging']... 
    },
    "models/transformer_model.py": {
        "Satır": 272,
        "Sınıflar": ['BIST30TransformerModel'],
        "Fonksiyonlar": ['__init__', 'create_dataset', 'build_model', 'train', 'predict']... ,
        "Importlar": ['torch', 'pandas', 'os', 'lightning.pytorch', 'pytorch_forecasting']... 
    },
    "models/regime_detector.py": {
        "Satır": 238,
        "Sınıflar": ['RegimeDetector'],
        "Fonksiyonlar": ['__init__', 'detect_regime', '_is_crisis', '_is_volatile', '_is_trend_up']... ,
        "Importlar": ['numpy', 'pandas', 'typing', 'logging']... 
    },
    "models/__init__.py": {
        "Satır": 0,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": []... 
    },
    "models/ranking_model.py": {
        "Satır": 264,
        "Sınıflar": ['RankingModel'],
        "Fonksiyonlar": ['__init__', 'prepare_data', 'train', 'predict', 'save']... ,
        "Importlar": ['pandas', 'numpy', 'lightgbm', 'os', 'joblib']... 
    },
    "models/ensemble_model.py": {
        "Satır": 154,
        "Sınıflar": ['HybridEnsemble'],
        "Fonksiyonlar": ['__init__', 'load_models', 'predict', 'optimize_weights']... ,
        "Importlar": ['os', 'numpy', 'pandas', 'scipy.optimize', 'joblib']... 
    },
    "models/regime_detection.py": {
        "Satır": 389,
        "Sınıflar": ['RegimeDetector', 'MLRegimeClassifier'],
        "Fonksiyonlar": ['__init__', 'calculate_adaptive_thresholds', 'detect_turkey_crisis', 'detect_regimes', '__init__']... ,
        "Importlar": ['pandas', 'numpy', 'config', 'lightgbm', 'optuna']... 
    },
    "models/ranking_model_catboost.py": {
        "Satır": 264,
        "Sınıflar": ['CatBoostRankingModel'],
        "Fonksiyonlar": ['__init__', 'fit', 'predict', 'predict_top_n', 'save']... ,
        "Importlar": ['numpy', 'pandas', 'catboost', 'logging', 'pickle']... 
    },
    "paper_trading/__init__.py": {
        "Satır": 15,
        "Sınıflar": [],
        "Fonksiyonlar": []... ,
        "Importlar": ['portfolio_state', 'position_engine', 'position_logger', 'position_runner']... 
    },
    "paper_trading/portfolio_state.py": {
        "Satır": 703,
        "Sınıflar": ['PortfolioState'],
        "Fonksiyonlar": ['__init__', 'has_position', 'position_count', 'current_total_exposure', 'exposure_ratio']... ,
        "Importlar": ['json', 'os', 'datetime', 'typing', 'utils.logging_config']... 
    },
    "paper_trading/position_engine.py": {
        "Satır": 94,
        "Sınıflar": ['PositionEngine'],
        "Fonksiyonlar": ['__init__', 'process_signal', 'close_unwanted_positions']... ,
        "Importlar": ['datetime', 'paper_trading.portfolio_state', 'core.risk_manager']... 
    },
    "paper_trading/strategy_health.py": {
        "Satır": 765,
        "Sınıflar": ['ConfigWrapper', 'StrategyState', 'StrategyHealth'],
        "Fonksiyonlar": ['check_strategy_health', 'get_strategy_health_monitor', '__init__', 'get', '__init__']... ,
        "Importlar": ['enum', 'typing', 'datetime', 'numpy', 'json']... 
    },
    "paper_trading/position_runner.py": {
        "Satır": 387,
        "Sınıflar": [],
        "Fonksiyonlar": ['load_production_model', 'run_position_aware_session', 'reset_portfolio']... ,
        "Importlar": ['sys', 'os', 'datetime', 'pandas', 'numpy']... 
    },
    "paper_trading/position_logger.py": {
        "Satır": 200,
        "Sınıflar": ['PositionLogger'],
        "Fonksiyonlar": ['__init__', 'log_decision', '_append_to_daily_file', 'flush_session_summary', '_append_to_csv_summary']... ,
        "Importlar": ['json', 'os', 'csv', 'datetime', 'typing']... 
    },
    "paper_trading/live_execution.py": {
        "Satır": 259,
        "Sınıflar": ['LiveExecutionEngine'],
        "Fonksiyonlar": ['pre_trade_checklist', '__init__', 'calculate_lot_size', 'create_order', 'display_pending_orders']... ,
        "Importlar": ['os', 'datetime', 'typing']... 
    },
}
```

## 3. Kritik Dosyaların İçerik Özeti
### config.py
```python
import platform
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


# AMD GPU (ROCm) Fix for RDNA2 (RX 6000 series)
os.environ["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


from utils.logging_config import get_logger

_log = get_logger(__name__)

# ─────────────────────────────────────────────────────────────
# YAML-based Settings Loader
# ─────────────────────────────────────────────────────────────
_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.yaml")
_settings = {}

def _load_settings():
    """settings.yaml'ı yükle, env variable override uygula."""
    global _settings
    try:
        import yaml
        if os.path.exists(_SETTINGS_PATH):
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                _settings = yaml.safe_load(f) or {}
            _log.debug("settings.yaml loaded (%d top-level keys)", len(_settings))
        else:
            _log.warning("settings.yaml not found, using hardcoded defaults")
    except ImportError:
        _log.warning("PyYAML not installed, using hardcoded defaults")
    except Exception as e:
        _log.error("settings.yaml load error: %s", e)

def _cfg(section: str, key: str, default=None):
    """
    Config değeri al: settings.yaml > env variable > hardcoded default.
    Env override: BIST_{SECTION}_{KEY} (büyük harf).
    """
    env_key = f"BIST_{section.upper()}_{key.upper()}"

```
**Yapılar:**
- Sınıflar: 
- Fonksiyonlar: _load_settings, _cfg, get_device, _load_tickers, get_segment, get_sector

### core/backtesting.py
```python
"""
Backtester Orchestrator
Tüm backtesting fonksiyonlarını birleştiren mixin-tabanlı sınıf.

Kullanım:
    from core.backtesting import Backtester
    bt = Backtester(data, initial_capital=10000)
    results = bt.run_backtest(signals)
    metrics = bt.calculate_metrics()

Alt modüller:
    core/backtest/engine.py     — run_backtest, slippage, market impact
    core/backtest/metrics.py    — Sharpe, Sortino, Calmar, Alpha, Beta vb.
    core/backtest/visualizer.py — Grafikler, ısı haritası, HTML rapor
"""
from core.position_sizing import KellyPositionSizer
from core.backtest.engine import BacktestEngineMixin
from core.backtest.metrics import BacktestMetricsMixin
from core.backtest.visualizer import BacktestVisualizerMixin
import pandas as pd
import config
from models.regime_detector import RegimeDetector

class Backtester(
    BacktestEngineMixin,
    BacktestMetricsMixin,
    BacktestVisualizerMixin,
):
    """
    BIST30 AI Trader Backtesting Pipeline.

    Mixin sınıflarını birleştirerek event-driven backtesting, performans metrikleri
    ve görselleştirme fonksiyonlarını tek bir arayüz altında toplar.
    """

    def __init__(
        self, 
        data: pd.DataFrame, 
        initial_capital: float = 10000.0, 
        commission: float = 0.002
    ) -> None:
        """
        Backtester sınıfını başlatır.

        Args:
            data (pd.DataFrame): Backtest edilecek OHLCV verisi.
            initial_capital (float, optional): Başlangıç sermayesi. Varsayılan: 10000.0
            commission (float, optional): İşlem komisyon oranı (0.002 = %0.2). Varsayılan: 0.002
        """
        self.data = data.copy()

```
**Yapılar:**
- Sınıflar: Backtester
- Fonksiyonlar: __init__

### core/risk_manager.py
```python
import config
import pandas as pd
import numpy as np
import logging
from models.regime_detector import RegimeDetector

logger = logging.getLogger(__name__)

class ConfigWrapper:
    def __init__(self, module): self.module = module
    def get(self, name, default=None): return getattr(self.module, name, default)

class RiskManager:
    def __init__(self):
        self.stop_loss_mult = config.ATR_STOP_LOSS_MULTIPLIER
        self.take_profit_mult = config.ATR_TAKE_PROFIT_MULTIPLIER
        self.trailing_stop_mult = config.ATR_TRAILING_STOP_MULTIPLIER
        self.min_holding_periods = config.MIN_HOLDING_PERIODS
        self.max_stop_loss_pct = config.MAX_STOP_LOSS_PCT
        self.trailing_active = config.TRAILING_STOP_ACTIVE
        self.current_regime = None 
        
        # Initialize RegimeDetector
        try:
            self.regime_detector = RegimeDetector(ConfigWrapper(config))
            logger.info("✅ RegimeDetector entegre edildi (RiskManager)")
        except Exception as e:
            logger.warning(f"⚠️ RegimeDetector başlatılamadı: {e}")
            self.regime_detector = None

    def adjust_for_regime(self, regime):
        """
        Piyasa rejimine göre risk parametrelerini dinamik olarak ayarlar.
        Regimler: Sideways, Crash_Bear, Trend_Up
        """
        self.current_regime = regime 
        
        if regime == 'Crash_Bear': # Kriz/Ayı
            self.stop_loss_mult = 1.5 
            self.trailing_stop_mult = 1.0 # 1.5 -> 1.0 (Daha sıkı)
            self.take_profit_mult = 5.0 
            
        elif regime == 'Sideways': # Yatay
            self.stop_loss_mult = 2.0
            self.trailing_stop_mult = 2.0 # 2.5 -> 2.0 (Daha sıkı takip)
            self.take_profit_mult = 3.0
            
        elif regime == 'Trend_Up': # Ralli
            self.stop_loss_mult = config.ATR_STOP_LOSS_MULTIPLIER 
            self.trailing_stop_mult = config.ATR_TRAILING_STOP_MULTIPLIER

```
**Yapılar:**
- Sınıflar: ConfigWrapper, RiskManager
- Fonksiyonlar: __init__, get, __init__, adjust_for_regime, calculate_stop_loss, get_stop_distance, check_exit_conditions, calculate_position_size, check_portfolio_drawdown, check_order_timeout, check_liquidity, calculate_dynamic_slippage

### models/ranking_model.py
```python

import pandas as pd
import numpy as np
import lightgbm as lgb
import os
import joblib

from utils.logging_config import get_logger

log = get_logger(__name__)

class RankingModel:
    def __init__(self, data, config_module):
        self.data = data.copy()
        self.config = config_module
        self.model = None
        self.feature_names = []

    def prepare_data(self, is_training=True):
        """
        Ranking için veriyi hazırlar.
        Veri (Date, Ticker) indeksli olmalı.
        """
        df = self.data.copy()
        
        # Feature Selection
        # Use all available features except meta-data
        # Target Selection from Config
        label_type = getattr(self.config, 'LABEL_TYPE', 'RawRank')
        
        if label_type == 'RiskAdjusted':
             target_col = 'Excess_Return_RiskAdjusted'
        else:
             target_col = 'Excess_Return' 
             
        exclude_cols = self.config.LEAKAGE_COLS + ['Ticker', 'Date', 'FUNDAMENTAL_DATA_AVAILABLE']
        
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        # Prevent Leakage from dynamic target columns
        feature_cols = [c for c in feature_cols if not c.startswith('Excess_Return') and not c.startswith('NextDay')]
        
        # Keep numeric only
        feature_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        self.feature_names = feature_cols
        
        if is_training:
            # Drop NaNs
            # Ensure all forward window targets are present if using multi-window
            windows = getattr(self.config, 'FORWARD_WINDOWS', [1])
            target_cols = [f'Excess_Return_T{win}' for win in windows]

```
**Yapılar:**
- Sınıflar: RankingModel
- Fonksiyonlar: __init__, prepare_data, train, predict, save, load

### models/transformer_model.py
```python

import torch
import pandas as pd
import os
import lightning.pytorch
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer
from pytorch_forecasting.metrics import RMSE, MAE, QuantileLoss
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor

from utils.logging_config import get_logger

log = get_logger(__name__)

class BIST30TransformerModel:
    def __init__(self, config_module):
        self.config = config_module
        self.model = None
        self.dataset_params = None
        
        # GPU Check
        # GPU Check (Config'den al)
        self.device = getattr(self.config, 'DEVICE', torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
        log.info(f"BIST30Transformer Device: {self.device}")

    def create_dataset(self, data, dataset_config, mode='train'):
        """
        TimeSeriesDataSet oluşturur.
        dataset_config: prepare_tft_dataset fonksiyonundan dönen dict
        """
        
        # DataFrame kopyası
        df = data.copy()
        
        # Time Index Creation (Eğer yoksa)
        if 'time_idx' not in df.columns:
            # Date ve Ticker'ı index veya column'dan bul
            if 'Date' in df.columns:
                dates = df['Date']
            elif 'Date' in df.index.names:
                dates = df.index.get_level_values('Date')
            else:
                raise ValueError("Date column or index level not found in data.")
                
            if 'Ticker' in df.columns:
                tickers = df['Ticker']
            elif 'Ticker' in df.index.names:
                tickers = df.index.get_level_values('Ticker')
            else:
                # If no ticker column, assume dummy or handle single series

```
**Yapılar:**
- Sınıflar: BIST30TransformerModel
- Fonksiyonlar: __init__, create_dataset, build_model, train, predict, save, load

### models/ensemble_model.py
```python

import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import joblib
import torch
try:
    from catboost import CatBoostRanker, Pool
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

import config

from utils.logging_config import get_logger

log = get_logger(__name__)

class HybridEnsemble:
    def __init__(self, lgbm_model=None, tft_model=None, catboost_model=None):
        self.lgbm = lgbm_model
        self.tft = tft_model
        self.catboost = catboost_model
        
        # Load weights from config
        # Default distribution: 40% LGBM, 30% TFT, 30% CatBoost if enabled
        # or stick to config if CatBoost not present
        
        # Simple logic: Equal weight if not specified
        self.weights = {
            'lgbm': 0.4, 
            'tft': 0.3, 
            'catboost': 0.3
        }
        log.debug(f"DEBUG: Hybrid Weights set to: {self.weights}")
        
    def load_models(self, lgbm_path, tft_path, tft_config=None, catboost_path=None):
        """Eğitilmiş modelleri yükler"""
        # LightGBM (RankingModel) yükle
        from models.ranking_model import RankingModel
        if os.path.exists(lgbm_path):
             self.lgbm = RankingModel.load(lgbm_path)
             log.info(f"✅ LightGBM modeli yüklendi: {lgbm_path}")
        else:
             log.warning(f"⚠️ LightGBM modeli bulunamadı: {lgbm_path}")
        
        # TFT Model yükle
        if tft_config and tft_path and os.path.exists(tft_path):
            try:

```
**Yapılar:**
- Sınıflar: HybridEnsemble
- Fonksiyonlar: __init__, load_models, predict, optimize_weights

### utils/feature_engineering.py
```python
"""
Feature Engineering Orchestrator
Tüm feature'ları oluşturmak için mixin sınıflarını birleştirir.

Kullanım:
    from utils.feature_engineering import FeatureEngineer
    fe = FeatureEngineer(raw_data)
    processed = fe.process_all(ticker='AKBNK.IS')

Alt modüller:
    utils/features/technical.py   — RSI, MACD, Bollinger, Ichimoku, ADX, OBV, ATR
    utils/features/volatility.py  — Garman-Klass, Rogers-Satchell, Parkinson
    utils/features/macro.py       — Makro etkileşimler, sektör dummies, gate
    utils/features/fundamental.py — Feature Store, KAP bildirimleri
    utils/features/derived.py     — Getiri, lag, hedef değişkenler, temizlik
    utils/features/transformer.py — TFT özel feature'ları
"""
import numpy as np
import config

from utils.features.technical import TechnicalMixin
from utils.features.volatility import VolatilityMixin
from utils.features.macro import MacroMixin
from utils.features.fundamental import FundamentalMixin
from utils.features.derived import DerivedMixin
from utils.features.transformer import TransformerMixin

# Re-export prepare_tft_dataset for backward compatibility
from utils.features.transformer import prepare_tft_dataset  # noqa: F401


class FeatureEngineer(
    TechnicalMixin,
    VolatilityMixin,
    MacroMixin,
    FundamentalMixin,
    DerivedMixin,
    TransformerMixin,
):
    """
    BIST30 AI Trader Feature Engineering Pipeline.
    
    Mixin sınıflarını birleştirerek tüm özellik mühendisliği fonksiyonlarını
    tek bir arayüz altında toplar. process_all() orkestratör metodudur.
    """

    def __init__(self, data):
        self.data = data.copy()

    def process_all(self, ticker=None):

```
**Yapılar:**
- Sınıflar: FeatureEngineer
- Fonksiyonlar: __init__, process_all

### scripts/training/train_models.py
```python
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import joblib
import numpy as np
import pandas as pd

# Konfigürasyonlar
import config
from configs import banking as config_banking

# Araçlar
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.ranking_model import RankingModel

import mlflow
import mlflow.lightgbm

def ensure_model_dir():
    if not os.path.exists("models/saved"):
        os.makedirs("models/saved")

def train_global_ranker():
    print(f"\n{'='*50}")
    print(f"EĞİTİM BAŞLIYOR: GLOBAL DAILY RANKER")
    print(f"Timeframe: {config.TIMEFRAME}")
    print(f"Strict Mode: Veri kesim tarihi {config.TRAIN_END_DATE}")
    print(f"{'='*50}")

    all_data_frames = []
    loader = DataLoader(start_date=config.START_DATE)
    
    # Tüm Tickerlar (config.TICKERS - A1 Core)
    tickers = config.TICKERS
    
    for ticker in tickers:
        print(f"  Veri İşleniyor: {ticker}...")
        raw_data = loader.get_combined_data(ticker)
        
        if raw_data is None or len(raw_data) < 100:
            print(f"  [UYARI] Yetersiz veri: {ticker}")
            continue
            
        # Feature Engineering (Daily Logic will apply due to config change)
        fe = FeatureEngineer(raw_data)
        features_df = fe.process_all(ticker=ticker)
        

```
**Yapılar:**
- Sınıflar: 
- Fonksiyonlar: ensure_model_dir, train_global_ranker, main

### scripts/training/train_tft.py
```python

import sys
import os
import torch
import pandas as pd
import joblib
from datetime import datetime, timedelta
from pytorch_forecasting import TimeSeriesDataSet
from lightning.pytorch.loggers import MLFlowLogger

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from models.transformer_model import BIST30TransformerModel
from utils.logging_config import get_logger

log = get_logger(__name__)

def main():
    log.info("🚀 TFT Model Eğitimi Başlıyor...")
    
    # 1. Veri Hazırlığı
    log.info("Veri yükleniyor...")
    loader = DataLoader()
    
    # fetch_stock_data tek bir hisse için çalışır, döngü gerektirir.
    # Ancak burada tüm hisseleri çekmek istiyoruz.
    # DataLoader.fetch_stock_data(ticker) -> DataFrame
    
    raw_data_list = []
    end_date = datetime.now().strftime('%Y-%m-%d')
    for ticker in config.TICKERS:
        try:
            df = loader.fetch_stock_data(ticker)
            if df is not None and not df.empty:
                df['Ticker'] = ticker
                raw_data_list.append(df)
        except Exception as e:
            log.error(f"{ticker} veri çekme hatası: {e}")
            
    if not raw_data_list:
        log.error("Veri yüklenemedi!")
        return
        
    raw_data = pd.concat(raw_data_list)
    
    # Düzeltme: fetch_stock_data index'i zaten Date olabilir.

```
**Yapılar:**
- Sınıflar: 
- Fonksiyonlar: main

### scripts/analysis/run_backtest.py
```python

import os
import sys
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import joblib
import numpy as np
import pandas as pd

import config
from configs import banking as config_banking
from core.backtesting import Backtester
from core.macro_gate import vectorized_macro_gate
from models.ranking_model import RankingModel
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer

def main():
    if not os.path.exists("reports"):
        os.makedirs("reports")

    print(f"✅ Config yüklendi")
    
    # YENİ: Rejim sistemi kontrolü
    print(f"🔍 Adaptive Regime: {getattr(config, 'USE_ADAPTIVE_REGIME', 'Unknown')}")
    print(f"📊 Regime Thresholds: {getattr(config, 'REGIME_THRESHOLDS', {})}")
    print(f"⚙️ Regime Actions: {getattr(config, 'REGIME_ACTIONS', {})}")
    
    if getattr(config, 'USE_ADAPTIVE_REGIME', False):
        print("✅ Regime-based risk management AKTİF")
    else:
        print("⚠️ UYARI: Regime detection devre dışı!")



    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='oos', choices=['oos', 'is'])
    parser.add_argument('--model', type=str, default='lightgbm', choices=['lightgbm', 'catboost', 'ensemble'], help='Model type to use')
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"BIST30 AI TRADER - DAILY RANKING BACKTEST ({args.mode.upper()})")
    print(f"Model: {args.model.upper()}")
    print(f"{'='*50}")

    # 1. Load Ranking Model
    try:

```
**Yapılar:**
- Sınıflar: 
- Fonksiyonlar: main

## 4. Bağımlılık Haritası
```python
Import_Graph = {
    "config.py": ['utils.logging_config', 'utils.db_manager'],
    "archive/api_conflict_backup.py": ['utils.db_manager', 'utils.logging_config'],
    "archive/research/verify_macro_lag.py": ['config'],
    "archive/research/batch_test.py": ['config'],
    "archive/research/batch_runner.py": ['config'],
    "archive/research/optimize_regime.py": ['utils.data_loader', 'utils.feature_engineering', 'models.regime_detection', 'config'],
    "archive/research/auto_tune.py": ['config', 'utils.data_loader', 'utils.feature_engineering', 'models.ranking_model', 'configs', 'core.backtesting'],
    "archive/research/benchmark_architectures.py": ['config', 'configs', 'utils.data_loader', 'utils.feature_engineering', 'models.ranking_model'],
    "archive/research/optuna_nested_walk_forward.py": ['config', 'utils.data_loader', 'utils.feature_engineering', 'config', 'config'],
    "archive/research/model_experiments.py": ['config', 'utils.data_loader', 'utils.feature_engineering', 'models.ranking_model', 'models.ranking_model_catboost', 'models.ensemble_model', 'configs'],
    "archive/research/fetch_fundamentals.py": ['config'],
    "core/execution.py": ['utils.logging_config'],
    "core/backtesting.py": ['core.position_sizing', 'core.backtest.engine', 'core.backtest.metrics', 'core.backtest.visualizer', 'config', 'models.regime_detector'],
    "core/position_sizing.py": ['utils.logging_config'],
    "core/live_data_engine.py": ['config', 'utils.logging_config'],
    "core/dynamic_backtest.py": ['config', 'configs', 'utils.feature_engineering', 'models.ranking_model', 'core.backtesting', 'models.regime_detector', 'utils.logging_config'],
    "core/risk_manager.py": ['config', 'models.regime_detector'],
    "core/macro_gate.py": ['config'],
    "core/feature_store.py": ['utils.logging_config'],
    "core/backtest/engine.py": ['config', 'core.risk_manager', 'models.regime_detector', 'core.execution'],
    "core/backtest/__init__.py": ['core.backtest.engine', 'core.backtest.metrics', 'core.backtest.visualizer'],
    "core/backtest/portfolio_engine.py": ['config', 'core.risk_manager'],
    "scripts/paper_trading_runner.py": ['utils.logging_config', 'config', 'models.regime_detector'],
    "scripts/training/train_tft.py": ['config', 'utils.data_loader', 'utils.feature_engineering', 'models.transformer_model', 'utils.logging_config', 'utils.features.transformer'],
    "scripts/training/benchmark_vectorized_engine.py": ['core.backtest.portfolio_engine', 'config'],
    "scripts/training/feature_selection.py": ['config', 'utils.data_loader', 'utils.feature_engineering', 'models.ranking_model', 'utils.logging_config', 'configs'],
    "scripts/training/benchmark_data_loading.py": ['config', 'utils.data_loader', 'utils.logging_config'],
    "scripts/training/optimize_hyperparameters.py": ['config', 'configs', 'utils.data_loader', 'utils.feature_engineering', 'models.ranking_model'],
    "scripts/training/walk_forward_validation.py": ['utils.data_loader', 'utils.feature_engineering', 'models.ranking_model', 'core.backtesting', 'config'],
    "scripts/training/walk_forward_optimization.py": ['core.dynamic_backtest', 'utils.logging_config', 'config'],
    "scripts/training/train_models.py": ['config', 'configs', 'utils.data_loader', 'utils.feature_engineering', 'models.ranking_model', 'utils.macro_data_loader', 'models.transformer_model', 'utils.feature_engineering'],
    "scripts/training/train_catboost.py": ['config', 'configs', 'utils.data_loader', 'utils.feature_engineering', 'models.ranking_model_catboost'],
    "scripts/training/train_tft_fast.py": ['config', 'utils.data_loader', 'utils.feature_engineering', 'models.transformer_model', 'utils.logging_config', 'utils.features.transformer'],
    "scripts/training/convert_checkpoint.py": ['models.transformer_model', 'config'],
    "scripts/training/validate_model.py": ['config', 'utils.data_loader', 'utils.feature_engineering'],
    "scripts/ops/paper_trading_runner.py": ['config', 'utils.data_loader', 'utils.feature_engineering', 'core.risk_manager', 'core.execution', 'utils.logging_config'],
    "scripts/ops/daily_run.py": ['config', 'utils.feature_engineering', 'utils.kap_data_fetcher', 'utils.macro_data_loader', 'models.ensemble_model', 'core.position_sizing', 'core.risk_manager'],
    "scripts/migration/migrate_to_db.py": ['utils.db_manager', 'core.feature_store', 'utils.logging_config'],
    "scripts/validation/debug_volume.py": ['utils.data_loader', 'utils.logging_config'],
    "scripts/validation/verify_integration.py": ['config', 'models.regime_detector', 'utils.data_loader', 'models.ensemble_model', 'core.dynamic_backtest', 'utils.feature_engineering'],
    "scripts/validation/verify_db_records.py": ['utils.db_manager', 'utils.logging_config'],
    "scripts/validation/check_config_usage.py": ['config'],
    "scripts/validation/stress_test_bist100.py": ['utils.data_loader', 'core.backtest.portfolio_engine', 'utils.db_manager', 'config', 'utils.logging_config'],
    "scripts/analysis/analyze_distributions.py": ['core.feature_store', 'config'],
    "scripts/analysis/check_evolution_success.py": ['core.execution', 'config'],
    "scripts/analysis/run_benchmark.py": ['config', 'utils.data_loader', 'utils.feature_engineering'],
    "scripts/analysis/project_evaluation.py": ['config', 'utils.data_loader', 'utils.feature_engineering', 'models.ensemble_model', 'utils.logging_config'],
    "scripts/analysis/analyze_data_gaps.py": ['config'],
    "scripts/analysis/micro_cap_stress_test.py": ['core.execution'],
    "scripts/analysis/inspect_models.py": ['models.ranking_model'],
    "scripts/analysis/compare_benchmark.py": ['utils.data_loader'],
    "scripts/analysis/analyze_performance.py": ['config'],
    "scripts/analysis/run_backtest.py": ['config', 'configs', 'core.backtesting', 'core.macro_gate', 'models.ranking_model', 'utils.data_loader', 'utils.feature_engineering', 'models.regime_detector', 'models.ranking_model_catboost', 'models.ensemble_model'],
    "scripts/analysis/check_forward_looking_features.py": ['utils.data_loader', 'utils.feature_engineering', 'config'],
    "scripts/analysis/check_data_dates.py": ['config', 'utils.data_loader'],
    "scripts/analysis/check_integration.py": ['config', 'utils.db_manager', 'utils.logging_config', 'models.ensemble_model'],
    "scripts/analysis/analyze_tft_attention.py": ['models.transformer_model', 'utils.data_loader', 'utils.feature_engineering', 'utils.logging_config', 'config'],
    "scripts/utility/increase_trade_frequency.py": ['utils.data_loader', 'utils.feature_engineering', 'models.ranking_model', 'config'],
    "scripts/utility/verify_integration.py": ['config', 'utils.db_manager', 'utils.data_loader', 'utils.logging_config'],
    "scripts/utility/verify_db_records.py": ['utils.db_manager'],
    "scripts/utility/verify_model_loading.py": ['config', 'models.ensemble_model', 'utils.logging_config'],
    "scripts/utility/fetch_kap_offline.py": ['config', 'utils.kap_data_fetcher'],
    "scripts/utility/test_macro_fetch.py": ['utils.data_loader', 'utils.logging_config', 'config'],
    "scripts/utility/migrate_to_db.py": ['config', 'utils.db_manager', 'utils.logging_config'],
    "scripts/utility/debug_tft_cats.py": ['models.transformer_model'],
    "scripts/utility/update_db_schema.py": ['utils.logging_config'],
    "scripts/utility/shuffle_test.py": ['utils.data_loader', 'utils.feature_engineering', 'config'],
    "scripts/utility/test_regime_integration.py": ['models.regime_detector', 'config'],
    "scripts/utility/verify_slippage.py": ['core.backtest.engine'],
    "scripts/utility/test_regime_detector.py": ['config', 'models.regime_detector'],
    "scripts/utility/test_execution_logic.py": ['core.execution'],
    "configs/banking.py": ['config'],
    "configs/holding.py": ['config'],
    "configs/aviation.py": ['config'],
    "configs/industrial.py": ['config'],
    "configs/energy.py": ['config'],
    "configs/automotive.py": ['config'],
    "configs/growth.py": ['config'],
    "configs/real_estate.py": ['config'],
    "configs/retail.py": ['config'],
    "configs/telecom.py": ['config'],
    "configs/steel.py": ['config'],
    "api/server.py": ['config', 'core.dynamic_backtest', 'utils.logging_config', 'core.live_data_engine', 'models.ensemble_model', 'config'],
    "tests/test_backtest_engine.py": ['core.backtesting', 'config'],
    "tests/test_regime_ml.py": ['config', 'utils.data_loader', 'utils.feature_engineering', 'models.regime_detection'],
    "tests/test_sor.py": ['core.execution'],
    "tests/evaluate_models.py": ['config', 'configs', 'utils.data_loader', 'utils.feature_engineering', 'utils.macro_data_loader', 'models.ranking_model', 'models.transformer_model', 'models.ensemble_model'],
    "tests/test_vectorized_backtest.py": ['core.backtest.portfolio_engine'],
    "tests/test_feature_engineering.py": ['utils.feature_engineering', 'config'],
    "tests/debug_fe.py": ['utils.feature_engineering', 'config'],
    "tests/verify_all.py": ['utils.macro_data_loader', 'utils.feature_engineering', 'config', 'models.transformer_model', 'core.position_sizing', 'models.ensemble_model'],
    "tests/test_kap_integration.py": ['utils.kap_data_fetcher'],
    "tests/test_risk_model.py": ['core.risk_manager', 'config'],
    "tests/test_data_sanitization.py": ['utils.data_loader', 'utils.logging_config'],
    "tests/test_sharpe_improvement.py": ['core.risk_manager', 'config'],
    "tests/test_live_integration.py": ['core.live_data_engine', 'config'],
    "utils/data_loader.py": ['config', 'utils.logging_config', 'utils.db_manager', 'utils.macro_data_loader', 'utils.logging_config', 'utils.validation'],
    "utils/validation.py": ['utils.logging_config'],
    "utils/macro_data_loader.py": ['utils.logging_config'],
    "utils/db_manager.py": ['utils.logging_config'],
    "utils/kap_data_fetcher.py": ['utils.logging_config'],
    "utils/feature_engineering.py": ['config', 'utils.features.technical', 'utils.features.volatility', 'utils.features.macro', 'utils.features.fundamental', 'utils.features.derived', 'utils.features.transformer', 'utils.features.transformer'],
    "utils/features/derived.py": ['config'],
    "utils/features/__init__.py": ['utils.features.technical', 'utils.features.volatility', 'utils.features.macro', 'utils.features.fundamental', 'utils.features.derived', 'utils.features.transformer'],
    "utils/features/fundamental.py": ['config', 'core.feature_store', 'utils.logging_config', 'utils.kap_data_fetcher'],
    "utils/features/macro.py": ['config'],
    "utils/features/technical.py": ['config'],
    "models/transformer_model.py": ['utils.logging_config'],
    "models/ranking_model.py": ['utils.logging_config'],
    "models/ensemble_model.py": ['config', 'utils.logging_config', 'models.ranking_model', 'models.transformer_model'],
    "models/regime_detection.py": ['config', 'utils.logging_config'],
    "paper_trading/portfolio_state.py": ['utils.logging_config'],
    "paper_trading/position_engine.py": ['core.risk_manager'],
    "paper_trading/strategy_health.py": ['utils.logging_config', 'config', 'models.regime_detector'],
    "paper_trading/position_runner.py": ['config', 'utils.logging_config', 'utils.data_loader', 'utils.feature_engineering', 'core.risk_manager', 'utils.db_manager', 'models.regime_detector', 'models.ensemble_model'],
}
```

## 5. Config Dosyası Tam İçeriği
```python
import platform
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


# AMD GPU (ROCm) Fix for RDNA2 (RX 6000 series)
os.environ["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


from utils.logging_config import get_logger

_log = get_logger(__name__)

# ─────────────────────────────────────────────────────────────
# YAML-based Settings Loader
# ─────────────────────────────────────────────────────────────
_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.yaml")
_settings = {}

def _load_settings():
    """settings.yaml'ı yükle, env variable override uygula."""
    global _settings
    try:
        import yaml
        if os.path.exists(_SETTINGS_PATH):
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                _settings = yaml.safe_load(f) or {}
            _log.debug("settings.yaml loaded (%d top-level keys)", len(_settings))
        else:
            _log.warning("settings.yaml not found, using hardcoded defaults")
    except ImportError:
        _log.warning("PyYAML not installed, using hardcoded defaults")
    except Exception as e:
        _log.error("settings.yaml load error: %s", e)

def _cfg(section: str, key: str, default=None):
    """
    Config değeri al: settings.yaml > env variable > hardcoded default.
    Env override: BIST_{SECTION}_{KEY} (büyük harf).
    """
    env_key = f"BIST_{section.upper()}_{key.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        # Tip dönüşümü
        if isinstance(default, bool):
            return env_val.lower() in ("true", "1", "yes")
        if isinstance(default, int):
            return int(env_val)
        if isinstance(default, float):
            return float(env_val)
        return env_val
    
    sect = _settings.get(section, {})
    if isinstance(sect, dict) and key in sect:
        return sect[key]
    return default

_load_settings()

# ─────────────────────────────────────────────────────────────
# Device Detection
# ─────────────────────────────────────────────────────────────
def get_device():
    if not TORCH_AVAILABLE:
        return "cpu"
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
         return torch.device("mps")
    return torch.device("cpu")

DEVICE = get_device()
_log.info("Mevcut Cihaz: %s", DEVICE)


# Sector Classification for Rotation Penalty & Model Dummies
# Sector Classification moved to tickers.json
# Loading logic below
SECTOR_MAP = {}

# --- TIER SISTEMI (SADELEŞTİRİLMİŞ) ---
# Sadece Tier 1 (Core) Aktif
# --- ABLATION STUDY CONFIG ---
ENABLE_MACRO_IN_MODEL = _cfg("features", "enable_macro_in_model", False)

TIERS = {
    'TIER_1': [
        # Pozitif Alpha Üretenler (2024 OOS Backtest Sonuçlarına Göre)
        "TSKB.IS",   # +%11 (En İyi)
        "EREGL.IS",  # +%7.5
        "ODAS.IS",   # +%5.9
        "TTKOM.IS",  # +%5.2
        "AKBNK.IS",  # +%5.1
        # Potansiyeller (Düşük ama Pozitif)
        "EKGYO.IS",  # ~%2-3 (Volatil)
        "SISE.IS",   # ~%2-3
        "KOZAL.IS",  # Mining Sektör Lideri
        "SAHOL.IS",  # Holding
        "YKBNK.IS"   # Banka
    ],
    'TIER_2': [], # Devre dışı
    'TIER_3': []  # Devre dışı
}

# Load tickers from JSON
import json
_TICKERS_JSON_PATH = os.path.join(os.path.dirname(__file__), "tickers.json")

def _load_tickers():
    global SECTOR_MAP
    _loaded_from_db = False
    
    # 1. Try Loading from DB
    try:
        from utils.db_manager import DBManager
        db = DBManager()
        rows = db.get_all_stocks()
        if rows:
            SECTOR_MAP = {row[0]: row[1] for row in rows}
            _log.info(f"Loaded {len(SECTOR_MAP)} tickers from DATABASE.")
            _loaded_from_db = True
    except Exception as e:
        _log.warning(f"DB Load failed ({e}). Falling back to JSON.")

    # 2. Fallback to JSON
    if not _loaded_from_db:
        if os.path.exists(_TICKERS_JSON_PATH):
            try:
                with open(_TICKERS_JSON_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    SECTOR_MAP = {item['symbol']: item['sector'] for item in data}
                _log.info(f"Loaded {len(SECTOR_MAP)} tickers from tickers.json")
            except Exception as e:
                _log.error(f"Error loading tickers.json: {e}")
                SECTOR_MAP = {}
        else:
            _log.warning("tickers.json not found!")

_load_tickers()

# Aktif Hisseler
# Faz 5.1A: Tüm BIST30 hisselerini kullan (Sektör arası korelasyon öğrenimi)
TICKERS = list(SECTOR_MAP.keys())

# Blacklist (Gerekli değil ama kalsın)
BLACKLIST = []

# --- SEKTÖREL SEGMENTASYON ---
SECTORS = {
    'SEGMENT_A1': TICKERS
}

# --- LİKİDİTE AYARLARI (SCALABILITY SAFEGUARD) ---
MIN_DAILY_VOLUME_TL = _cfg("risk", "min_daily_volume_tl", 10_000_000) # 10 Milyon TL
MIN_LIQUIDITY_THRESHOLD = _cfg("risk", "min_liquidity_threshold", 20_000_000) # 20 Milyon TL (Backtest için daha sıkı)

# Sector Classification for Rotation Penalty & Model Dummies
# (SECTOR_MAP yukarı taşındı)

def get_segment(ticker):
    return 'A1'

def get_sector(ticker):
    """FIX 4: Get sector for rotation penalty."""
    # Suffix removal
    clean_ticker = ticker.replace('.IS', '')
    
    # Check both full and clean ticker in map
    if ticker in SECTOR_MAP:
        return SECTOR_MAP[ticker]
    if clean_ticker in SECTOR_MAP:
        # SECTOR_MAP içinde anahtarlar .IS ile bitiyorsa clean_ticker + .IS dene
        # Ama SECTOR_MAP'te anahtarlar .IS'li tanımlanmış.
        # Bu durumda clean_ticker gelirse sonuna .IS ekleyip bakmalı.
        return SECTOR_MAP.get(clean_ticker + '.IS', 'Other')
        
    # Reverse check: Eğer clean_ticker SECTOR_MAP'te varsa
    # (Yukarıdaki SECTOR_MAP'te anahtarlar .IS'li, o yüzden clean_ticker + .IS'i denedik)
    
    return 'Other'


# --- TARİH VE MAKRO VERİ ---
START_DATE = _cfg("dates", "start", "2015-01-01")
END_DATE = None

# Overfitting Önleme (Strict Split)
TRAIN_END_DATE = _cfg("dates", "train_end", "2023-12-31")
TEST_START_DATE = _cfg("dates", "test_start", "2024-01-01")

# KAP Entegrasyonu
ENABLE_KAP_FEATURES = _cfg("features", "enable_kap_features", True)

MACRO_TICKERS = {
    "USDTRY": "TRY=X",
    "VIX": "^VIX",
    "SP500": "^GSPC",
    "XBANK": "XBANK.IS",
    "XU100": "XU100.IS",
    "GOLD": "GC=F",      # Altın (Gold Futures)
    "OIL": "BZ=F"        # Brent Petrol (Oil Futures)
}

# --- PARAMETRELER ---
TIMEFRAME = 'D'

# Teknik İndikatörler
RSI_PERIOD = _cfg("indicators", "rsi_period", 14)
MACD_FAST = _cfg("indicators", "macd_fast", 12)
MACD_SLOW = _cfg("indicators", "macd_slow", 26)
MACD_SIGNAL = _cfg("indicators", "macd_signal", 9)
BB_LENGTH = _cfg("indicators", "bollinger_length", 20)
BB_STD = _cfg("indicators", "bollinger_std", 2)

# Model Target
FORWARD_WINDOW = 1
NUM_QUANTILES = 5

# Model
MODEL_TYPE = _cfg("model", "type", "ensemble")
TARGET_COL = "Excess_Return"
VAL_SIZE = _cfg("model", "val_size", 0.15)
LABEL_TYPE = _cfg("model", "label_type", "Hybrid")
HYBRID_WEIGHT = _cfg("model", "hybrid_weight", 0.85)
FORWARD_WINDOWS = _cfg("model", "forward_windows", [1, 5])
FORWARD_WEIGHTS = _cfg("model", "forward_weights", [0.6, 0.4])

# Leakage sütunları (yapısal, YAML'e taşınmaz)
LEAKAGE_COLS = [
    'NextDay_Close', 'NextDay_Return', 'Excess_Return', 
    'Excess_Return_RiskAdjusted', 'NextDay_XU100_Return', 
    'Log_Return', 'NextDay_Direction', 'ExitReason',
    'ICHIMOKU_ICS_26', 'ICHIMOKU_ICS_9' # Chikou Span is future looking
]

# Hibrit Strateji Eşikleri
HYBRID_THRESHOLDS = {
    'TREND': 0.005,  
    'ALPHA': 0.008   
}

# Risk Yönetimi
COMMISSION_RATE = _cfg("risk", "commission_rate", 0.0025)
REBALANCE_FREQUENCY = _cfg("risk", "rebalance_frequency", "W")
MIN_HOLDING_DAYS = _cfg("risk", "min_holding_days", 7)
MIN_HOLDING_PERIODS = MIN_HOLDING_DAYS
MIN_HOLDING_BY_SECTOR = {
    'BANKING': 1, 'HOLDING': 3, 'INDUSTRIAL': 2, 'GROWTH': 1
}
ATR_PERIOD = _cfg("indicators", "atr_period", 14)

# Dinamik Stop/Profit (ATR Çarpanları)
ATR_STOP_LOSS_MULTIPLIER = _cfg("risk", "stop_loss_atr_mult", 1.5)     # 2.0 -> 1.5
ATR_TAKE_PROFIT_MULTIPLIER = _cfg("risk", "take_profit_atr_mult", 12.0) # 15.0 -> 12.0
ATR_TRAILING_STOP_MULTIPLIER = _cfg("risk", "trailing_stop_atr_mult", 1.8) # 2.0 -> 1.8

# Devre Kesici (Circuit Breaker) - HARD LIMIT
# Devre Kesici (Circuit Breaker) - HARD LIMIT
MAX_DRAWDOWN_LIMIT = _cfg("risk", "max_drawdown_limit", 0.15)  # %15 (Walk-Forward -40% önlemek için!)
MAX_SECTOR_POSITIONS = _cfg("risk", "max_sector_positions", 2)

# Sabit limitler
MAX_STOP_LOSS_PCT = _cfg("risk", "max_stop_loss_pct", 0.10)
TRAILING_STOP_ACTIVE = _cfg("risk", "trailing_stop_active", True)

# Portföy Yapılandırması
PORTFOLIO_SIZE = _cfg("portfolio", "size", 3)
WEIGHTING_STRATEGY = _cfg("portfolio", "weighting", "RiskParity")
RISK_PER_TRADE = _cfg("risk", "risk_per_trade", 0.03)  # %3 (DD azaltmak için)

ENABLE_MOMENTUM_FILTER = _cfg("portfolio", "enable_momentum_filter", False)
MAX_SINGLE_POS_WEIGHT = _cfg("portfolio", "max_single_pos_weight", 0.33)
ENABLE_RISK_SIZING = _cfg("risk", "enable_risk_sizing", True)

CONFIDENCE_THRESHOLDS = {
    'TIER_1': 0.30  # 0.35 -> 0.30 (Ultra Aggressive - Low Confidence OK)
}

# Sektörel farklılaştırma ekle
CONFIDENCE_THRESHOLDS_BY_SECTOR = {
    'BANKING': 0.70,     # Bankalar volatil, daha yüksek eşik
    'HOLDING': 0.65,     # Holdingler stabil
    'INDUSTRIAL': 0.68,  # Sanayi orta
    'GROWTH': 0.75       # Growth en riskli, en yüksek eşik
}

# Segment Ayarları (A1 Core)
SEGMENT_SETTINGS = {
    'A1': {
        'learning_rate_range': (0.05, 0.2),
        'regularization': 'low',
        'feature_focus': [
            # Temel teknik
            'USDTRY', 'VIX', 'Volatility', 'RSI', 'Close', 'MACD',
            # Yeni alpha kaynakları
            'PE', 'EBITDA', 'Revenue', 'Debt',  # Fundamental
            'Gold', 'Oil',  # Cross-asset
            'Sector_Rotation', 'XBANK'  # Sektör
        ],
    }
}

# Rejim
USE_ADAPTIVE_REGIME = _cfg("regime", "use_adaptive", True)

REGIME_THRESHOLDS = {
    # Mevcut parametreler (daha hassas yapıldı)
    "volatility_low": _cfg("regime", "volatility_low", 0.25),      # 0.279 -> 0.25
    "volatility_high": _cfg("regime", "volatility_high", 0.50),    # 0.61 -> 0.50
    "cds_high": 550,                                                # 600 -> 550
    "try_change_high": 0.012,                                       # 0.0147 -> 0.012
    "momentum_threshold": _cfg("regime", "momentum_threshold", 45),
    "min_regime_days": _cfg("regime", "min_regime_days", 3),
    
    # YENİ: VIX bazlı hızlı rejim tespiti
    "vix_crisis": _cfg("regime", "vix_crisis", 35.0),
    "vix_volatile": _cfg("regime", "vix_volatile", 25.0),
    "vix_normal": _cfg("regime", "vix_normal", 20.0),
    
    # YENİ: Trend gücü tespiti
    "sma_trend_threshold": _cfg("regime", "sma_trend_threshold", 0.015),
    "atr_spike_multiplier": _cfg("regime", "atr_spike_multiplier", 1.8),
    
    # YENİ: Yatay piyasa tespiti
    "sideways_range": _cfg("regime", "sideways_range", 0.008),
    "sideways_max_days": _cfg("regime", "sideways_max_days", 15),
}

# Macro Gate
ENABLE_MACRO_GATE = _cfg("macro_gate", "enabled", True)
MACRO_GATE_THRESHOLDS = {
    'VIX_HIGH': _cfg("macro_gate", "vix_high", 40.0),
    'USDTRY_CHANGE_5D': _cfg("macro_gate", "usdtry_change_5d", 0.05),
    'SP500_MOMENTUM': _cfg("macro_gate", "sp500_momentum", -0.06)
}

# Optimize Edilmiş LightGBM Parametreleri
OPTIMIZED_MODEL_PARAMS = {
    'learning_rate': _cfg("lgbm_params", "learning_rate", 0.01538),
    'num_leaves': _cfg("lgbm_params", "num_leaves", 77),
    'max_depth': _cfg("lgbm_params", "max_depth", 6),
    'min_child_samples': _cfg("lgbm_params", "min_child_samples", 66),
    'reg_alpha': _cfg("lgbm_params", "reg_alpha", 0.9187),
    'reg_lambda': _cfg("lgbm_params", "reg_lambda", 0.4115),
    'n_estimators': _cfg("lgbm_params", "n_estimators", 1000),
    'early_stopping_rounds': _cfg("lgbm_params", "early_stopping_rounds", 50)
}

# TFT Parametreleri (GPU Optimized)
TFT_LEARNING_RATE = _cfg("tft_params", "learning_rate", 0.03)
TFT_HIDDEN_SIZE = _cfg("tft_params", "hidden_size", 128)
TFT_ATTENTION_HEADS = _cfg("tft_params", "attention_head_size", 4)
TFT_DROPOUT = _cfg("tft_params", "dropout", 0.15)
TFT_HIDDEN_CONTINUOUS_SIZE = _cfg("tft_params", "hidden_continuous_size", 16)
TFT_LSTM_LAYERS = _cfg("tft_params", "lstm_layers", 2)
TFT_BATCH_SIZE = _cfg("tft_params", "batch_size", 128)

# Sektör Rotasyonu
ENABLE_SECTOR_ROTATION_PENALTY = _cfg("sector_rotation", "enabled", True)
MAX_SECTOR_CONCENTRATION = _cfg("sector_rotation", "max_concentration", 0.70)

# ========================================
# DYNAMIC ENSEMBLE WEIGHTS (HEAD OF QUANT SPEC)
# ========================================
ENSEMBLE_REGIME_WEIGHTS = {
    'TREND_UP':   {'lgbm': 0.2, 'tft': 0.6, 'catboost': 0.2}, # Transformer loves trends
    'TREND_DOWN': {'lgbm': 0.6, 'tft': 0.0, 'catboost': 0.4}, # Defensive (Tree-based)
    'NORMAL':     {'lgbm': 0.4, 'tft': 0.3, 'catboost': 0.3}, # Balanced
    'SIDEWAYS':   {'lgbm': 0.6, 'tft': 0.1, 'catboost': 0.3}, # Trees comprise ranges well
    'VOLATILE':   {'lgbm': 0.5, 'tft': 0.0, 'catboost': 0.5}, # TFT unreliable in chaos
    'CRISIS':     {'lgbm': 1.0, 'tft': 0.0, 'catboost': 0.0}, # Fallback to simplest model
}

# ========================================
# REGIME-BASED TRADING CONTROLS (YENİ!)
# ========================================

# Her rejimde ne yapılacak?
REGIME_ACTIONS = {
    "TREND_UP": {
        "trade": True,
        "position_multiplier": 1.0,      # Tam güç
        "stop_loss_mult": 1.5,           # Normal stop
        "max_positions": 5,              # Max 5 hisse
    },
    
    "NORMAL": {
        "trade": True,
        "position_multiplier": 0.8,      # %80 pozisyon
        "stop_loss_mult": 1.3,           # Biraz daha sıkı
        "max_positions": 4,
    },
    
    "SIDEWAYS": {
        "trade": True,
        "position_multiplier": 0.5,      # Yarı güç (Window 6, 7'deki kayıpları önler)
        "stop_loss_mult": 1.2,           # Dar stop
        "max_positions": 3,
    },
    
    "VOLATILE": {
        "trade": False,                  # TRADE YAPMA! (Window 1, 10'daki felaketleri önler)
        "position_multiplier": 0.0,
        "stop_loss_mult": 1.0,
        "max_positions": 0,
    },
    
    "CRISIS": {
        "trade": False,                  # KEsinlikle DURME!
        "position_multiplier": 0.0,
        "stop_loss_mult": 0.8,           # Mevcut pozisyonları hızlı kes
        "max_positions": 0,
        "force_exit": True,              # Tüm pozisyonları kapat
    },
    
    "TREND_DOWN": {
        "trade": False,                  # Long yapma (short yok)
        "position_multiplier": 0.0,
        "stop_loss_mult": 1.0,
        "max_positions": 0,
    }
}

# Günlük maksimum kayıp (YENİ)
MAX_DAILY_LOSS = _cfg("risk", "max_daily_loss", 0.04)  # %4 günlük kayıp -> DUR


```

## 6. Dosya Durumu
### Kritik Eksikler
- Yok

### Gereksiz Dosyalar
- Yok
