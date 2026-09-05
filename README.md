# Long Horizon Failure Circuit Breaker

> **Domain:** Autonomous Agent Systems & Context State Architecture
> **Reference Guidelines & Standards:** `Distributed Systems RFC & State Machine Verification`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Long Horizon Failure Circuit Breaker** is an advanced analytical and computational platform implementing tool call velocity & repetition similarity infinite recursion circuit breaker for autonomous agent systems.

The system provides:
- Multi-worker consensus evaluation with specialized domain agents
- Cryptographic tamper-evident HMAC-SHA256 audit trail
- Zero-PHI outbound guard for HIPAA compliance
- FastAPI REST API with Prometheus telemetry
- CLI for interactive and batch processing

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification**: Multi-tier categorization (ROUTINE, ELEVATED, CRITICAL_STAT) with automated action recommendations.
- **Validation & Guardrails**: Rigorous input bounds checking, NaN/infinity rejection, and anomaly detection.
- **Multi-Worker Consensus**: Three specialized workers (InvariantQC, SafetyEscalation, ProtocolConformance) evaluate each task.

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/long-horizon-failure-circuit-breaker.git
cd long-horizon-failure-circuit-breaker

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

---

## 🔐 Security Configuration

**IMPORTANT**: The audit trail requires a secret key to be set via environment variable:

```bash
# Set a strong secret key (minimum 16 characters)
export AUDIT_SECRET_KEY="your-strong-secret-key-here-min-16-chars"
```

Without this key, the system will fail to initialize the audit trail. This is intentional to prevent accidental deployment with a hardcoded default key.

---

## 💻 CLI Quickstart & Usage

### 1. Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. System Configuration Query
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--task-id`: Unique task identifier (required, non-empty)
- `--target`: Target identifier (required, non-empty)
- `--primary`: Primary metric value (finite float)
- `--secondary`: Secondary metric value (finite float)
- `--critical`: Flag for critical/emergency status
- `--status`: Status descriptor (e.g., NOMINAL, DISCORDANT_ANOMALY)

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition. Requires `AUDIT_SECRET_KEY` environment variable.
* **Input Validation:** Rejects NaN, infinity, and out-of-bounds metric values that could bypass threshold checks.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

**Set the audit key for testing:**
```bash
export AUDIT_SECRET_KEY="test-audit-secret-key-2026"
```

**Run the automated test suite:**
```bash
pytest -v
```

**Execute high-throughput batch simulation benchmarks:**
```bash
python simulator.py 1000
```

**Test the REST API:**
```bash
# Start the server
python cli.py serve &

# Test health endpoint
curl http://localhost:8000/health

# Submit a task
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"task-id": "API-001", "target_identifier": "KEY-01", "primary_metric": 28.5, "secondary_metric": 14.2, "status_descriptor": "DISCORDANT", "is_critical_flag": true}'
```

---

## 🐳 Container Deployment

```bash
docker build -t long-horizon-failure-circuit-breaker .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-production-key-here-min-16-chars" long-horizon-failure-circuit-breaker
```

Or using docker-compose:
```bash
# Update docker-compose.yml with your production key
docker-compose up -d
```

---

## 📁 Project Structure

```
long-horizon-failure-circuit-breaker/
├── agents/                    # Core agent system
│   ├── __init__.py           # Package version
│   ├── api.py                # FastAPI REST endpoints
│   ├── base.py               # Security, PHI guard, audit trail
│   ├── learning.py           # Bayesian calibration engine
│   ├── llm_factory.py        # LLM provider factory
│   ├── metrics.py            # Prometheus metrics collector
│   ├── models.py             # Pydantic data models
│   ├── streamer.py           # WebSocket telemetry streamer
│   ├── supervisor.py         # Master orchestrator
│   └── workers.py            # Specialized worker agents
├── circuit_breaker/          # Alternative implementation
│   ├── agents.py             # Coordinator and sub-agents
│   ├── cli.py                # Alternative CLI
│   ├── engine.py             # Core algorithmic engine
│   ├── models.py             # Data models
│   └── server.py             # FastAPI server factory
├── tests/                    # Test suite
│   ├── conftest.py           # Shared fixtures
│   ├── test_circuit_breaker.py
│   ├── test_enrichment.py
│   ├── test_long_horizon_failure_circuit_breaker.py
│   └── test_security_and_edge_cases.py
├── web/                      # Operations console
│   └── index.html            # Web UI
├── .github/workflows/        # CI/CD
│   └── ci.yml
├── cli.py                    # Main CLI entry point
├── circuit_breaker_app.py    # App launcher
├── enrichment.py             # Enrichment feature engines
├── simulator.py              # High-throughput simulator
├── pyproject.toml            # Project configuration
├── Dockerfile                # Container build
├── docker-compose.yml        # Container orchestration
└── README.md                 # This file
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
