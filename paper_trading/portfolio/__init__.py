"""
Portfolio module for BIST30 AI Trader.

This module contains refactored portfolio management components following
the Single Responsibility Principle (SRP).

Components:
- PortfolioRepository: Data persistence (load/save)
- PortfolioValidator: Validation logic
- PortfolioService: Business logic (trade execution)
- PortfolioFormatter: Presentation and reporting
- PortfolioMetrics: Statistical analysis
"""

from paper_trading.portfolio.portfolio_repository import PortfolioRepository
from paper_trading.portfolio.portfolio_validator import PortfolioValidator
from paper_trading.portfolio.portfolio_service import PortfolioService
from paper_trading.portfolio.portfolio_formatter import PortfolioFormatter
from paper_trading.portfolio.portfolio_metrics import PortfolioMetrics

__all__ = [
    "PortfolioRepository",
    "PortfolioValidator",
    "PortfolioService",
    "PortfolioFormatter",
    "PortfolioMetrics",
]
