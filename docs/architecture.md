# Architecture Overview

## System Architecture

BIST30 AI Trader follows a modular, layered architecture designed for scalability, maintainability, and extensibility.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   FastAPI    │  │  WebSocket   │  │     CLI      │          │
│  │     API      │  │   Interface  │  │   Scripts    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Trading    │  │   Backtest   │  │   Analysis   │          │
│  │   Engine     │  │   Engine     │  │   Tools      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         Business Logic Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Portfolio   │  │     Risk     │  │    Macro     │          │
│  │  Manager     │  │   Manager    │  │    Gate      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Position   │  │  Execution   │  │   Feature    │          │
│  │   Sizing     │  │   Engine     │  │   Store      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                          Model Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   LightGBM   │  │   CatBoost   │  │     TFT      │          │
│  │   Ranker     │  │   Ranker     │  │   (PyTorch)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                          Data Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ TimescaleDB  │  │   Feature    │  │    MLflow    │          │
│  │ (Market Data)│  │    Store     │  │  (Tracking)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Data Layer

**TimescaleDB:**
- Time-series optimized PostgreSQL
- Stores market data (OHLCV)
- Efficient querying with time-based indexes
- Automatic data retention policies

**Feature Store:**
- Precomputed features
- Fundamental data
- Technical indicators
- Macro indicators

**MLflow:**
- Experiment tracking
- Model versioning
- Metric logging
- Artifact storage

### 2. Model Layer

**LightGBM Ranker:**
- Fast gradient boosting
- Ranking objective (NDCG@5)
- Feature importance
- CPU-optimized

**CatBoost Ranker:**
- Categorical feature handling
- Robust to overfitting
- GPU acceleration
- YetiRank loss function

**TFT (Temporal Fusion Transformer):**
- Deep learning for time series
- Attention mechanisms
- Multi-horizon forecasting
- Interpretable predictions

### 3. Business Logic Layer

**Portfolio Manager:**
- Position tracking
- Rebalancing logic
- Capital allocation
- Performance tracking

**Risk Manager:**
- Position limits
- Drawdown monitoring
- Stop-loss execution
- Sector diversification

**Macro Gate:**
- Market regime detection
- Trade filtering
- Risk-on/risk-off signals

**Position Sizing:**
- Kelly criterion
- Risk-based sizing
- Volatility adjustment

**Execution Engine:**
- Order management
- Slippage modeling
- Commission calculation
- Fill simulation

**Feature Store:**
- Feature caching
- Feature versioning
- Feature serving

### 4. Application Layer

**Trading Engine:**
- Live trading logic
- Signal generation
- Order execution
- Position management

**Backtest Engine:**
- Historical simulation
- Performance metrics
- Walk-forward validation
- Vectorized operations

**Analysis Tools:**
- Feature importance
- Model comparison
- Performance analytics
- Visualization

### 5. Presentation Layer

**FastAPI:**
- RESTful API
- Async operations
- Auto-generated docs
- CORS support

**WebSocket:**
- Real-time updates
- Market data streaming
- Trade notifications

**CLI Scripts:**
- Training scripts
- Analysis tools
- Maintenance utilities
- Validation tools

## Data Flow

### Training Pipeline

```
Market Data (TimescaleDB)
    ↓
Data Loader
    ↓
Feature Engineering
    ↓
Feature Store
    ↓
Model Training (LightGBM/CatBoost/TFT)
    ↓
Model Evaluation
    ↓
MLflow (Tracking)
    ↓
Model Registry
```

### Trading Pipeline

```
Market Data (Live/Historical)
    ↓
Feature Engineering
    ↓
Model Prediction
    ↓
Ranking Engine
    ↓
Macro Gate (Filter)
    ↓
Portfolio Manager
    ↓
Position Sizing
    ↓
Risk Manager
    ↓
Execution Engine
    ↓
Order Execution
```

### Backtest Pipeline

```
Historical Data
    ↓
Feature Engineering
    ↓
Model Prediction
    ↓
Backtest Engine
    ↓
Portfolio Simulation
    ↓
Performance Metrics
    ↓
Report Generation
```

## Design Patterns

### 1. Strategy Pattern
- Multiple model implementations
- Interchangeable ranking algorithms
- Flexible position sizing methods

### 2. Factory Pattern
- Model factory for creating instances
- Data loader factory
- Feature engineering factory

### 3. Observer Pattern
- Event-driven architecture
- Market data updates
- Trade notifications

### 4. Repository Pattern
- Data access abstraction
- Database operations
- Feature store access

### 5. Singleton Pattern
- Database connection pool
- Configuration manager
- Logger instances

## Technology Stack

### Backend
- **Python 3.12+**: Core language
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### Machine Learning
- **LightGBM**: Gradient boosting
- **CatBoost**: Gradient boosting
- **PyTorch**: Deep learning
- **scikit-learn**: ML utilities
- **SHAP**: Model interpretability

### Data Storage
- **PostgreSQL**: Relational database
- **TimescaleDB**: Time-series extension
- **Parquet**: Feature storage
- **MLflow**: Experiment tracking

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **pytest**: Testing framework
- **Hypothesis**: Property-based testing

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers
- Load balancing
- Database read replicas
- Distributed training

### Vertical Scaling
- GPU acceleration for TFT
- Vectorized operations
- Efficient data structures
- Caching strategies

### Performance Optimization
- Database indexing
- Query optimization
- Feature caching
- Batch processing
- Async operations

## Security

### Data Security
- Environment variables for secrets
- Database connection encryption
- API authentication (planned)
- Rate limiting (planned)

### Code Security
- Input validation
- SQL injection prevention
- XSS protection
- Dependency scanning

## Monitoring & Logging

### Logging
- Structured logging
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Centralized log management
- Performance logging

### Monitoring
- MLflow metrics
- System metrics
- Trading metrics
- Error tracking

## Future Enhancements

### Planned Features
- Real-time data streaming
- Advanced risk models
- Multi-asset support
- Cloud deployment
- Mobile app
- Advanced analytics dashboard

### Technical Improvements
- Microservices architecture
- Event sourcing
- CQRS pattern
- GraphQL API
- Kubernetes deployment

## Related Documentation

- [Main README](../README.md)
- [API Documentation](api.md)
- [Deployment Guide](deployment.md)
- [Training Guide](training.md)
