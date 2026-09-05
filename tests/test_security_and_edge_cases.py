"""
Security and edge case tests for long-horizon-failure-circuit-breaker.
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import math
from agents.base import PHIGuard, AuditLogger, SecurityException, ResourceLimitExceededException, AuditTrail
from agents.models import SystemTaskPayload
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, _validate_metric_bounds


class TestAuditTrailSecurity:
    """Tests for HMAC audit trail security requirements."""

    def test_audit_trail_requires_secret_key(self):
        """AuditTrail should fail without AUDIT_SECRET_KEY."""
        original = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with pytest.raises(SecurityException, match="AUDIT_SECRET_KEY"):
                AuditTrail()
        finally:
            if original:
                os.environ["AUDIT_SECRET_KEY"] = original

    def test_audit_trail_rejects_short_key(self):
        """AuditTrail should reject keys shorter than 16 characters."""
        with pytest.raises(SecurityException, match="at least 16 characters"):
            AuditTrail(secret_key="short")

    def test_audit_trail_accepts_valid_key(self):
        """AuditTrail should accept keys of sufficient length."""
        trail = AuditTrail(secret_key="valid-test-key-1234567890")
        assert trail.secret_key == b"valid-test-key-1234567890"

    def test_audit_trail_logs_and_verifies(self):
        """Audit trail should maintain integrity across multiple entries."""
        trail = AuditTrail(secret_key="test-key-1234567890123456")
        trail.log("test_actor", "tier1", "TEST_EVENT", {"data": "value1"})
        trail.log("test_actor", "tier1", "TEST_EVENT", {"data": "value2"})
        assert len(trail.get_trail()) == 2
        assert trail.verify_integrity() is True


class TestMetricValidation:
    """Tests for input metric validation."""

    def test_nan_primary_metric_rejected(self):
        """NaN values should be rejected for primary_metric."""
        with pytest.raises(ValueError, match="finite"):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=float("nan"))

    def test_infinity_primary_metric_rejected(self):
        """Infinity values should be rejected for primary_metric."""
        with pytest.raises(ValueError, match="finite"):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=float("inf"))

    def test_nan_secondary_metric_rejected(self):
        """NaN values should be rejected for secondary_metric."""
        with pytest.raises(ValueError, match="finite"):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=10.0, secondary_metric=float("nan"))

    def test_valid_metrics_accepted(self):
        """Valid finite metrics should be accepted."""
        payload = SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=10.0, secondary_metric=5.0)
        assert payload.primary_metric == 10.0
        assert payload.secondary_metric == 5.0

    def test_empty_task_id_rejected(self):
        """Empty task_id should be rejected."""
        with pytest.raises(ValueError, match="empty"):
            SystemTaskPayload(task_id="", target_identifier="K1", primary_metric=10.0)

    def test_whitespace_only_target_rejected(self):
        """Whitespace-only target_identifier should be rejected."""
        with pytest.raises(ValueError, match="empty"):
            SystemTaskPayload(task_id="T1", target_identifier="   ", primary_metric=10.0)


class TestWorkerBoundsChecking:
    """Tests for worker bounds checking."""

    def test_invariant_qc_rejects_nan(self):
        """InvariantQCWorker should reject NaN metrics."""
        payload = SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=10.0)
        # Bypass pydantic validation by setting attribute directly
        object.__setattr__(payload, 'primary_metric', float("nan"))
        with pytest.raises(ResourceLimitExceededException, match="finite"):
            InvariantQCWorker.evaluate(payload)

    def test_invariant_qc_rejects_extreme_values(self):
        """InvariantQCWorker should reject extremely large metrics."""
        payload = SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=1e15)
        with pytest.raises(ResourceLimitExceededException, match="exceeds maximum"):
            InvariantQCWorker.evaluate(payload)

    def test_safety_worker_rejects_nan(self):
        """SafetyEscalationWorker should reject NaN metrics."""
        payload = SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=10.0, secondary_metric=5.0)
        object.__setattr__(payload, 'secondary_metric', float("inf"))
        with pytest.raises(ResourceLimitExceededException, match="finite"):
            SafetyEscalationWorker.evaluate(payload)


class TestPHIGuardEnhanced:
    """Enhanced PHI guard tests."""

    def test_phi_guard_detects_mrn(self):
        """PHI guard should detect Medical Record Numbers."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_phi_guard_detects_ssn(self):
        """PHI guard should detect Social Security Numbers."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phi_guard_detects_phone(self):
        """PHI guard should detect phone numbers."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call (555) 123-4567")

    def test_phi_guard_detects_email(self):
        """PHI guard should detect email addresses."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("patient@hospital.org")

    def test_phi_guard_allows_safe_text(self):
        """PHI guard should allow safe analytical text."""
        PHIGuard.assert_no_phi("Analytical specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("Metric value 28.5 within normal bounds")

    def test_phi_redaction(self):
        """PHI redaction should replace sensitive data."""
        redacted = PHIGuard.redact_phi("Patient MRN-12345678 and SSN 123-45-6789")
        assert "MRN" not in redacted or "REDACTED" in redacted
        assert "123-45-6789" not in redacted
