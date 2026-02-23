"""
Pytest configuration for shared fixtures.

This file makes fixtures available to all test files without explicit imports.
"""

# Import all fixtures to make them available globally
from tests.fixtures.portfolio_fixtures import *
from tests.fixtures.health_fixtures import *
from tests.fixtures.data_fixtures import *
