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

__all__ = ["PortfolioRepository"]
