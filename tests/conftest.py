"""
Shared pytest fixtures and configuration for long-horizon-failure-circuit-breaker test suite.
"""
import os
import pytest


def pytest_configure(config):
    """Set required environment variables before any tests run."""
    # Ensure AUDIT_SECRET_KEY is set for audit trail tests
    if not os.getenv("AUDIT_SECRET_KEY"):
        os.environ["AUDIT_SECRET_KEY"] = "test-audit-secret-key-2026-pytest"


@pytest.fixture(autouse=True)
def reset_audit_trail():
    """Reset the global audit trail before each test for isolation."""
    from agents.base import _get_global_audit, _GLOBAL_AUDIT
    # Access the global and reset it
    import agents.base as base_module
    if base_module._GLOBAL_AUDIT is not None:
        base_module._GLOBAL_AUDIT = None
    yield
