# 🤖 BIST30 AI Trader

> AI-powered algorithmic trading system for BIST30 (Borsa Istanbul 30) stocks using advanced machine learning models and quantitative strategies.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

BIST30 AI Trader is a sophisticated algorithmic trading system designed for the Turkish stock market (BIST30). It combines multiple machine learning models (LightGBM, CatBoost, TFT) with advanced portfolio management, risk controls, and backtesting capabilities.

### Key Capabilities

- **Multi-Model Ensemble**: LightGBM, CatBoost, and Temporal Fusion Transformer (TFT) models
- **Ranking-Based Selection**: Daily stock ranking and portfolio optimization
- **Advanced Risk Management**: Position sizing, stop-loss, and portfolio constraints
- **Macro Regime Detection**: Market regime-aware trading decisions
- **Walk-Forward Validation**: Robust out-of-sample testing
- **Real-Time Trading**: Paper trading and live execution support
- **Comprehensive Backtesting**: Historical performance analysis with detailed metrics

## ✨ Features

### Machine Learning Models

- **LightGBM Ranker**: Fast gradient boosting for daily stock ranking
- **CatBoost Ranker**: Categorical feature handling with ranking objectives
- **TFT (Temporal Fusion Transformer)**: Deep learning for time series forecasting
- **Ensemble Methods**: Model combination and weighted predictions

### Trading System

- **Portfolio Management**: Dynamic position sizing and rebalancing
- **Risk Controls**: Max drawdown limits, position limits, sector diversification
- **Slippage Modeling**: Realistic market impact and execution costs
- **Macro Gate**: Market regime filtering for trade execution
- **Kelly Criterion**: Optimal position sizing based on win rate and odds

### Analysis & Monitoring

- **Feature Importance Analysis**: SHAP values and model interpretability
- **Performance Metrics**: Sharpe ratio, max drawdown, win rate, NDCG@5
- **Visualization**: Interactive charts and performance reports
- **MLflow Integration**: Experiment tracking and model versioning

### Infrastructure

- **TimescaleDB**: Time-series data storage and efficient querying
- **FastAPI**: RESTful API and WebSocket support
- **Docker**: Containerized deployment
- **Pytest**: Comprehensive test suite with property-based testing

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     BIST30 AI Trader                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Data       │  │   Feature    │  │   Models     │    │
│  │   Loader     │─▶│  Engineering │─▶│  (ML/DL)     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         │                                     │            │
│         ▼                                     ▼            │
│  ┌──────────────┐                    ┌──────────────┐    │
│  │ TimescaleDB  │                    │   Ranking    │    │
│  │  (Market     │                    │   Engine     │    │
│  │   Data)      │                    └──────────────┘    │
│  └──────────────┘                            │            │
│                                               ▼            │
│                                      ┌──────────────┐    │
│                                      │  Portfolio   │    │
│                                      │  Manager     │    │
│                                      └──────────────┘    │
│                                               │            │
│         ┌─────────────────────────────────────┘            │
│         ▼                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Backtest    │  │ Paper Trade  │  │ Live Trade   │    │
│  │  Engine      │  │  Engine      │  │  Engine      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Installation

### Prerequisites

- Python 3.12+
- PostgreSQL with TimescaleDB extension
- (Optional) AMD GPU with ROCm for TFT training
- (Optional) Docker and Docker Compose

### Local Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/bist30_ai_trader.git
cd bist30_ai_trader
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
# Start TimescaleDB (via Docker)
docker-compose up -d timescaledb

# Run migrations
python scripts/migration/migrate_to_db.py
```

### Docker Installation

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

## ⚡ Quick Start

### 1. Train Models

```bash
# Train LightGBM ranker
python scripts/training/train_models.py

# Train CatBoost ranker
python scripts/training/train_catboost.py

# Train TFT model (requires GPU)
python scripts/training/train_tft.py
```

### 2. Run Backtest

```bash
# Run comprehensive backtest
python scripts/analysis/run_backtest.py

# Walk-forward validation
python scripts/training/walk_forward_validation.py
```

### 3. Analyze Results

```bash
# Generate performance report
python scripts/analysis/get_training_metrics.py

# Feature importance analysis
python scripts/analysis/run_feature_importance.py --config configs/banking.py
```

### 4. Paper Trading

```bash
# Start paper trading
python scripts/ops/paper_trading_runner.py
```

## 📁 Project Structure

```
bist30_ai_trader/
├── api/                    # FastAPI server and WebSocket
├── core/                   # Core trading logic
│   ├── backtest/          # Backtesting engine
│   ├── execution.py       # Order execution
│   ├── feature_store.py   # Feature management
│   ├── macro_gate.py      # Regime detection
│   ├── position_sizing.py # Kelly criterion
│   └── risk_manager.py    # Risk controls
├── models/                 # ML model implementations
├── utils/                  # Utility functions
│   ├── data_loader.py     # Data loading
│   ├── db_manager.py      # Database connection
│   └── feature_engineering.py
├── scripts/                # Executable scripts
│   ├── analysis/          # Analysis tools
│   ├── training/          # Model training
│   ├── validation/        # System validation
│   ├── maintenance/       # Code maintenance
│   └── ops/               # Operations
├── configs/                # Sector-specific configs
├── tests/                  # Test suite
├── docs/                   # Documentation
└── reports/                # Generated reports
```

For detailed structure, see [project_structure_report.md](project_structure_report.md).

## 📖 Usage

### Training Models

```python
from utils.data_loader import DataLoader
from models.ranking_model import RankingModel

# Load data
loader = DataLoader(start_date="2020-01-01")
data = loader.fetch_stock_data("THYAO")

# Train model
model = RankingModel()
model.train(data)
model.save("models/saved/ranker.pkl")
```

### Running Backtest

```python
from core.backtest.engine import BacktestEngine

# Initialize engine
engine = BacktestEngine(
    initial_capital=100000,
    commission=0.001,
    slippage_model="adaptive"
)

# Run backtest
results = engine.run(
    start_date="2023-01-01",
    end_date="2023-12-31"
)

print(f"Total Return: {results['total_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
```

### Feature Importance Analysis

```bash
# Analyze feature importance for a specific config
python scripts/analysis/run_feature_importance.py \
    --config configs/banking.py \
    --output reports/feature_importance/

# Generate visualizations
python scripts/analysis/run_feature_importance.py \
    --config configs/banking.py \
    --visualize \
    --top-n 20
```

## ⚙️ Configuration

### Main Configuration (`config.py`)

```python
# Trading parameters
TIMEFRAME = "1d"
TRAIN_START_DATE = "2020-01-01"
TRAIN_END_DATE = "2023-12-31"

# Portfolio settings
INITIAL_CAPITAL = 100000
MAX_POSITIONS = 5
POSITION_SIZE_METHOD = "kelly"

# Risk management
MAX_POSITION_SIZE = 0.25
STOP_LOSS_PCT = 0.10
MAX_DRAWDOWN_LIMIT = 0.20
```

### Sector Configurations (`configs/`)

Sector-specific configurations for different stock groups:
- `banking.py` - Banking sector
- `holding.py` - Holding companies
- `industrial.py` - Industrial stocks
- `energy.py` - Energy sector
- And more...

### Environment Variables (`.env`)

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bist30_trader
DB_USER=postgres
DB_PASSWORD=your_password

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## 📚 Documentation

- [Feature Importance Analysis](docs/feature_importance_analysis.md)
- [Cleanup System Guide](docs/cleanup_config_guide.md)
- [API Documentation](docs/api.md)
- [Model Training Guide](docs/training.md)
- [Backtest Guide](docs/backtest.md)
- [Architecture Overview](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)

### Maintenance Tools

The project includes comprehensive maintenance tools:

```bash
# Find unused files
python scripts/maintenance/find_unused_files.py

# Detect duplicate code
python scripts/maintenance/find_duplicate_code.py

# Generate cleanup report
python scripts/maintenance/generate_cleanup_report.py
```

See [Maintenance README](scripts/maintenance/README.md) for details.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_ranking_model.py

# Run property-based tests
pytest tests/ -k "property"
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Standards

- Follow PEP 8 style guide
- Add docstrings to all functions and classes
- Write tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- BIST (Borsa Istanbul) for market data
- Open-source ML libraries: LightGBM, CatBoost, PyTorch
- TimescaleDB for time-series data management
- FastAPI for modern API development

## 📞 Contact

For questions or support, please open an issue on GitHub.

---

**Disclaimer**: This software is for educational and research purposes only. Trading stocks involves risk. Past performance does not guarantee future results. Always do your own research and consult with financial advisors before making investment decisions.
