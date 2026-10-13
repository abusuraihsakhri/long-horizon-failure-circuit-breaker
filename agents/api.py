"""
FastAPI REST API Server for Long Horizon Failure Circuit Breaker.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException, ResourceLimitExceededException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Long Horizon Failure Circuit Breaker API",
    description="Enterprise Distributed Component Platform (Long-Horizon Agent Context & State Architecture)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "long-horizon-failure-circuit-breaker", "domain": "Long-Horizon Agent Context & State Architecture", "standard": "Autonomous Agent State Machine & Token Economy RFC", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    most_recent = next(reversed(supervisor.dossier_registry), None)
    status = (supervisor.dossier_registry[most_recent].overall_urgency.value
              if most_recent is not None else "NO_EVALUATIONS")
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": status,
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except (SecurityException, ResourceLimitExceededException) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
