# Long Horizon Failure Circuit Breaker

A deterministic, rule-based task evaluator for experimenting with supervision and escalation in multi-worker systems. This repository does **not** currently implement a stateful tool-call circuit breaker, loop detection, or autonomous recovery.

## What it does

The primary Python implementation (`agents/`) evaluates tasks using three rule-based workers:

| Worker | Trigger | Result |
| --- | --- | --- |
| InvariantQCWorker | Primary metric > 25 | Elevated |
| SafetyEscalationWorker | Secondary metric > 12 or critical flag | Elevated; critical if flag set |
| ProtocolConformanceWorker | Descriptor includes DISCORDANT, ANOMALY, MUTANT, VIOLATION, FAIL or REJECT | Elevated |

The highest triggered urgency determines the overall classification. A separate legacy implementation in `circuit_breaker/` is retained for compatibility and uses a secondary threshold of **10**, rather than 12.

- **Python CLI:** single-task evaluation, CSV batch processing, mock chat responder, and in-process audit verification.
- **FastAPI:** `/health`, `/metrics` (JSON counters), `/api/audit`, `/api/chat` and `/api/audit/logs`.
- **HMAC-SHA256 audit:** signed, chained entries held in process memory; signatures and chain links are verified. Restarting the process loses the ledger. It is not an independently anchored compliance record.
- **Privacy screening:** heuristic regular expressions for selected identifier formats, not complete PHI detection or a HIPAA-compliance solution.
- **Browser evaluator:** `web/index.html`, a standalone JavaScript demonstration matching the primary Python implementation's decision rules. It does not use a backend, create audit entries or calculate HMACs. Inputs remain in the browser unless you export them.

## Installation

Tested in CI with Python 3.10–3.12. The package metadata permits Python 3.9.

```bash
python -m pip install -e '.[dev]'
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
python -m pytest -q
```

Set the same variable in PowerShell with `$env:AUDIT_SECRET_KEY`. Keep it private; do not commit `.env` files.

## Usage

```bash
long-horizon-failure-circuit-breaker audit --task-id TASK-01 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
long-horizon-failure-circuit-breaker chat "System status"
long-horizon-failure-circuit-breaker batch -i sample.csv -o results.csv
long-horizon-failure-circuit-breaker verify-audit
long-horizon-failure-circuit-breaker serve --host 127.0.0.1 --port 8000
```

Example HTTP request (while the API is running):

```bash
curl -X POST http://127.0.0.1:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"task_id":"TASK-01","target_identifier":"KEY-01","primary_metric":28.5,"secondary_metric":14.2,"status_descriptor":"DISCORDANT","is_critical_flag":true}'
```

CSV fields include `task_id`, `target_identifier`, `primary_metric`, `secondary_metric`, `status_descriptor`, `is_critical_flag`. Boolean values (`true`/`false`, `1`/`0`, `yes`/`no`) are parsed explicitly. Ambiguous values fail rather than silently escalating a case.

The alternative implementation remains available using `python -m circuit_breaker.cli` or `python circuit_breaker_app.py`.

## Browser demonstration and Pages

Open `web/index.html` in a modern browser for local evaluation and JSON export. The static page can run on GitHub Pages. `.github/workflows/pages.yml` deploys `web/` from `master` when Pages is enabled with **GitHub Actions** as its build source. A live application link will be added only after the deployment is verified.

Do not enter patient-identifiable data. Browser evaluation and regex screening do not establish clinical, operational, or regulatory validation.

## Container deployment

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
docker compose up --build -d
```

Compose requires an externally supplied secret. Before exposing the unauthenticated API to untrusted networks, add authentication, TLS, rate limiting, and persistent audit storage.

## Technology and verification

Python, Pydantic 2, FastAPI, Uvicorn, Pytest, vanilla JavaScript and Node's built-in test runner. CI exercises the Python package on 3.10–3.12 and browser unit tests. No third-party LLM API is called: only the deterministic `mock` responder is implemented. The separate `enrichment.py` module contains threshold-driven demonstrations.

The browser relies on standard JavaScript and Blob APIs supported in current Chrome, Firefox, Safari and Edge. It does not load external fonts or require network access.

## License

MIT — see [LICENSE](LICENSE).
