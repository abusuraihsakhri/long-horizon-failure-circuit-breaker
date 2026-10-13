"""
Enterprise Security, PHI Outbound Guard, and HMAC-SHA256 Audit Trail.

"""
import os
import re
import json
import time
import hmac
import hashlib
import copy
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

PHI_PATTERNS = [
    re.compile(r"\b(?:MRN|mrn)[:#\s-]*\d{4,10}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\b(?:Patient\s+Name|Patient)[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+\b", re.IGNORECASE),
    re.compile(r"\b(?:John\s+Doe|Jane\s+Smith|Alice\s+Johnson)\b", re.IGNORECASE),
]


class SecurityException(Exception):
    """Raised when outbound data violates HIPAA Safe Harbor or contains raw PHI."""
    pass


class ResourceLimitExceededException(Exception):
    """Raised when computational parameters exceed safety bounds."""
    pass


def assert_no_phi(text: str) -> None:
    if not text:
        return
    for pattern in PHI_PATTERNS:
        if pattern.search(str(text)):
            raise SecurityException(f"PHI Outbound Guard Violation: Sensitive identifier detected with pattern {pattern.pattern}")


class PHIGuard:
    @staticmethod
    def assert_no_phi(text: str) -> None:
        assert_no_phi(text)

    @staticmethod
    def redact_phi(text: str) -> str:
        res = str(text)
        for pattern in PHI_PATTERNS:
            res = pattern.sub("[REDACTED_IDENTIFIER]", res)
        return res


class AuditTrail:
    """Cryptographic Tamper-Evident HMAC-SHA256 Audit Trail."""
    def __init__(self, secret_key: Optional[str] = None):
        resolved_key = secret_key or os.getenv("AUDIT_SECRET_KEY")
        if not resolved_key:
            raise SecurityException(
                "AUDIT_SECRET_KEY environment variable or secret_key argument is required. "
                "Never use a hardcoded default in production."
            )
        if len(resolved_key) < 16:
            raise SecurityException("AUDIT_SECRET_KEY must be at least 16 characters for cryptographic strength.")
        self.secret_key = resolved_key.encode("utf-8")
        self.logs: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    _SIGNED_FIELDS = (
        "audit_id", "timestamp", "actor", "actor_tier",
        "event_type", "payload_hash", "prev_hash"
    )

    def _signature(self, entry: Dict[str, Any]) -> str:
        """Sign canonical JSON to avoid delimiter ambiguity between fields."""
        signed = {field: entry[field] for field in self._SIGNED_FIELDS}
        message = json.dumps(signed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hmac.new(self.secret_key, message.encode("utf-8"), hashlib.sha256).hexdigest()

    def log(self, actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        for value in (actor, actor_tier, event_type):
            assert_no_phi(value)
        payload_str = json.dumps(details, sort_keys=True)
        assert_no_phi(payload_str)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        with self._lock:
            entry = {
                "audit_id": f"AUDIT-{int(time.time()*1000)}-{len(self.logs)+1}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": actor,
                "actor_tier": actor_tier,
                "event_type": event_type,
                "payload_hash": payload_hash,
                "prev_hash": self.logs[-1]["current_hash"] if self.logs else "GENESIS_BLOCK_0000000000000000",
            }
            entry["current_hash"] = self._signature(entry)
            self.logs.append(entry)
            return copy.deepcopy(entry)

    def verify_integrity(self) -> bool:
        """Verify every signed field and the continuity of the in-memory chain."""
        with self._lock:
            previous = "GENESIS_BLOCK_0000000000000000"
            for entry in self.logs:
                try:
                    if entry["prev_hash"] != previous:
                        return False
                    if not hmac.compare_digest(entry["current_hash"], self._signature(entry)):
                        return False
                    previous = entry["current_hash"]
                except (KeyError, TypeError, ValueError):
                    return False
            return True

    def get_trail(self) -> List[Dict[str, Any]]:
        """Return a snapshot so API callers cannot mutate the internal chain."""
        with self._lock:
            return copy.deepcopy(self.logs)


_GLOBAL_AUDIT: Optional[AuditTrail] = None


def _get_global_audit() -> AuditTrail:
    """Lazily initialize the global audit trail, requiring AUDIT_SECRET_KEY to be set."""
    global _GLOBAL_AUDIT
    if _GLOBAL_AUDIT is None:
        _GLOBAL_AUDIT = AuditTrail()
    return _GLOBAL_AUDIT


class AuditLogger:
    @staticmethod
    def log(actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        return _get_global_audit().log(actor, actor_tier, event_type, details)

    @staticmethod
    def get_trail() -> List[Dict[str, Any]]:
        return _get_global_audit().get_trail()

    @staticmethod
    def verify_integrity() -> bool:
        return _get_global_audit().verify_integrity()


class ActionExecutor:
    @staticmethod
    def execute_with_audit(actor: str, actor_tier: str, action_type: str, fn, *args, **kwargs):
        res = fn(*args, **kwargs)
        AuditLogger.log(actor, actor_tier, action_type, {"status": "SUCCESS"})
        return res
