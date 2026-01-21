"""
Pytest configuration and shared fixtures for AEGIS tests.

This module provides common test fixtures and configuration
for the AEGIS test suite, including property-based testing setup.
"""

import pytest
from hypothesis import settings, Verbosity

# Configure Hypothesis for property-based testing
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=1000, verbosity=Verbosity.verbose)
settings.load_profile("default")


@pytest.fixture
def sample_source_code():
    """Fixture providing sample AEGIS source code for testing."""
    return """x = 10
y = x + 5
print y"""


@pytest.fixture
def simple_assignment():
    """Fixture providing a simple assignment statement."""
    return "x = 42"


@pytest.fixture
def arithmetic_expression():
    """Fixture providing an arithmetic expression."""
    return "result = 10 + 5 * 2"