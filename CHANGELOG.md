# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation system
- Main README.md with project overview
- CONTRIBUTING.md for contribution guidelines
- CHANGELOG.md for version tracking
- Architecture documentation
- API documentation
- Deployment guide

## [1.2.0] - 2026-02-19

### Added
- Post-development cleanup system
  - Unused file detector with entry point detection
  - Duplicate code detector
  - File size analyzer
  - Merge suggester
  - Auto cleanup manager
  - Comprehensive reporting in Turkish and English
- Utility modules for code reuse
  - `scripts/analysis/utils.py` - Financial metrics
  - `scripts/validation/utils.py` - File scanning
  - `scripts/training/utils.py` - Model helpers
  - `scripts/utility/verification_utils.py` - Verification tools
- Feature importance analysis system
  - SHAP-based feature importance
  - Model comparison tools
  - Visualization support
  - CLI interface with config support

### Changed
- Refactored duplicate code into shared utility modules
- Improved unused file detection accuracy (86.4% → 1.8% false positives)
- Updated maintenance scripts documentation

### Removed
- 3 unused archive files
- 13 temporary report files
- 2 old test result files
- 6 CatBoost temporary files
- 1 spec implementation summary
- 4 empty directories

### Fixed
- Unused file detector now correctly identifies entry points
- Special directories (tests/, api/, configs/) properly excluded
- Import statements updated after code refactoring

## [1.1.0] - 2026-02-18

### Added
- Walk-forward validation with comprehensive metrics
- CatBoost model training with NDCG@5 optimization
- TFT learning rate scheduling improvements
- Integration test suite
- Property-based testing framework

### Changed
- Improved model evaluation metrics
- Enhanced backtest engine performance
- Updated risk management parameters

### Fixed
- Database connection pooling issues
- Feature engineering edge cases
- Slippage calculation accuracy

## [1.0.0] - 2026-02-14

### Added
- Initial release
- LightGBM ranking model
- CatBoost ranking model
- TFT (Temporal Fusion Transformer) model
- Backtest engine with portfolio management
- Risk management system
- Macro regime detection
- TimescaleDB integration
- FastAPI server with WebSocket support
- MLflow experiment tracking
- Docker deployment support
- Comprehensive test suite

### Features
- Multi-model ensemble trading
- Daily stock ranking
- Kelly criterion position sizing
- Adaptive slippage modeling
- Sector-specific configurations
- Paper trading support
- Performance analytics

## [0.1.0] - 2026-01-15

### Added
- Project initialization
- Basic data loading
- Simple backtesting framework
- Initial model experiments

---

## Version History

- **1.2.0** - Cleanup system and documentation
- **1.1.0** - Walk-forward validation and improvements
- **1.0.0** - Initial production release
- **0.1.0** - Project inception

## Migration Guides

### Upgrading to 1.2.0

1. Update dependencies: `pip install -r requirements.txt`
2. New utility modules available - update imports if using affected functions
3. Cleanup system available - run `python scripts/maintenance/generate_cleanup_report.py`

### Upgrading to 1.1.0

1. Database schema updates - run migrations
2. New walk-forward validation - update training scripts
3. CatBoost model available - retrain if needed

### Upgrading to 1.0.0

1. Fresh installation recommended
2. Set up TimescaleDB
3. Configure environment variables
4. Run initial data migration

## Breaking Changes

### 1.2.0
- None

### 1.1.0
- Database schema changes require migration
- Config file format updated

### 1.0.0
- Complete rewrite from 0.1.0
- New database backend
- New model architecture

## Deprecations

### 1.2.0
- Old cleanup report format (replaced by new system)

### 1.1.0
- Legacy backtest engine (replaced by vectorized version)

## Security

### 1.2.0
- No security issues

### 1.1.0
- Fixed database connection string exposure in logs

### 1.0.0
- Initial security audit completed

---

For more details on each release, see the [GitHub Releases](https://github.com/yourusername/bist30_ai_trader/releases) page.
