"""
Basic setup tests to verify the testing framework is working correctly.
"""

import pytest
from hypothesis import given, strategies as st


def test_pytest_works():
    """Verify pytest is working."""
    assert True


@pytest.mark.property
@given(x=st.integers())
def test_hypothesis_works(x):
    """Verify hypothesis is working."""
    assert isinstance(x, int)


def test_imports():
    """Verify we can import from the maintenance package."""
    import scripts.maintenance
    assert hasattr(scripts.maintenance, '__version__')
