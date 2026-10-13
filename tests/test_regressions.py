"""Regressions for audit signing, CSV input and API error handling."""
import csv
from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from agents.base import AuditTrail, SecurityException
from agents.llm_factory import LLMFactory
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from circuit_breaker.csv_utils import parse_bool, append_unique_fields


def test_signature_validation_detects_changed_fields():
    trail = AuditTrail(secret_key="a-long-valid-test-secret")
    trail.log("supervisor", "supervisor", "EVALUATED", {"task": "KEY-01"})
    trail.log("supervisor", "supervisor", "EVALUATED", {"task": "KEY-02"})
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "intruder"
    assert not trail.verify_integrity()


def test_signature_validation_detects_forged_chain():
    trail = AuditTrail(secret_key="a-long-valid-test-secret")
    trail.log("supervisor", "supervisor", "EVALUATED", {"task": "KEY-01"})
    trail.logs[0]["current_hash"] = "0" * 64
    assert not trail.verify_integrity()


def test_audit_snapshot_cannot_mutate_internal_ledger():
    trail = AuditTrail(secret_key="a-long-valid-test-secret")
    trail.log("supervisor", "supervisor", "EVALUATED", {"task": "KEY-01"})
    copy = trail.get_trail()
    copy[0]["actor"] = "intruder"
    copy.clear()
    assert len(trail.get_trail()) == 1
    assert trail.verify_integrity()


@pytest.mark.parametrize(("raw", "expected"), [
    ("false", False), ("False", False), (" 0 ", False), ("no", False),
    ("true", True), ("TRUE", True), ("1", True), ("yes", True),
    ("", False), (False, False), (True, True),
])
def test_csv_boolean_values(raw, expected):
    assert parse_bool(raw) is expected


@pytest.mark.parametrize("raw", ["unknown", "t", "2"])
def test_csv_boolean_rejects_ambiguous_values(raw):
    with pytest.raises(ValueError, match="Invalid boolean"):
        parse_bool(raw)


def test_duplicate_headers_removed():
    assert append_unique_fields(["task_id", "audit_hash"], ["audit_hash", "overall_urgency"]) == [
        "task_id", "audit_hash", "overall_urgency"]


@pytest.mark.parametrize("main_path,critical_column", [
    ("cli", "overall_urgency"),
    ("circuit_breaker.cli", "overall_status"),
])
def test_batch_false_does_not_trigger_critical(tmp_path, main_path, critical_column):
    from importlib import import_module
    main = import_module(main_path).main
    input_path = tmp_path / "in.csv"
    output_path = tmp_path / "out.csv"
    with input_path.open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "task_id", "target_identifier", "primary_metric", "secondary_metric",
            "status_descriptor", "is_critical_flag"
        ])
        w.writeheader()
        w.writerow(dict(task_id="T-01", target_identifier="KEY-01",
                        primary_metric=10, secondary_metric=4,
                        status_descriptor="NOMINAL", is_critical_flag="False"))
    assert main(["batch", "-i", str(input_path), "-o", str(output_path)]) == 0
    with output_path.open(newline="", encoding="utf8") as f:
        row = next(csv.DictReader(f))
    assert "CRITICAL" not in row[critical_column]


def test_supervisor_rejects_phi_in_attributes():
    supervisor = SystemSupervisor()
    payload = SystemTaskPayload(task_id="T-01", target_identifier="KEY-01",
                                primary_metric=3, attributes={"notes": "MRN-12345678"})
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)


def test_unimplemented_provider_is_rejected():
    with pytest.raises(ValueError, match="not implemented"):
        LLMFactory.create("openai")


def test_api_rejects_sensitive_identifiers():
    from fastapi.testclient import TestClient
    from agents.api import app
    client = TestClient(app)
    response = client.post("/api/audit", json={
        "task_id": "T-01", "target_identifier": "KEY-01",
        "primary_metric": 1, "attributes": {"notes": "MRN-12345678"}
    })
    assert response.status_code == 422
    assert "PHI" in response.json()["detail"]


def test_concurrent_signing_preserves_chain():
    trail = AuditTrail(secret_key="a-long-valid-test-secret")
    def record(number):
        return trail.log("supervisor", "supervisor", "EVALUATED", {"task": number})
    with ThreadPoolExecutor(max_workers=12) as executor:
        list(executor.map(record, range(100)))
    assert len(trail.get_trail()) == 100
    assert trail.verify_integrity()
