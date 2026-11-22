# Stateless SDLC Python Orchestrator

Reads canonical roles, skills, workflows, and constitution directly from `.agents/` and `docs/` (**Zero Dual-Truth**).

## Zero-Dependency CLI Usage

```bash
# List canonical agents
python3 -m orchestrator.cli agents

# Preview dynamic routing (with automatic risk escalation)
python3 -m orchestrator.cli route --work-type bug_fix --risk low --summary "Fix auth token expiry check"

# Run a dry-run feature pipeline (auto-approving HITL gates for smoke test)
python3 -m orchestrator.cli run-dry --work-type new_feature --summary "Add claim status filter" --auto-approve

# Evaluate Stage 6 control band breach
python3 -m orchestrator.cli check-band --metric ci_test_failure_rate --baseline 0.02 0.03 0.02 0.01 --observed 0.10
```

## Optional HTTP Service (FastAPI) & Authentication

Protected `/runs` and `/runs/{run_id}/approve` endpoints enforce Bearer token authentication, run-level `scope` isolation, and Gate RBAC (`Gate 1`: `po`/`ba`, `Gate 2`: `sa`/`tech_lead`, `Gate 3`: `maintainer`/`tech_lead`). Configure tokens via `SDLC_ORCHESTRATOR_TOKENS_JSON` or `SDLC_ORCHESTRATOR_TOKENS_FILE`:

```bash
pip install -r orchestrator/requirements.txt
export SDLC_ORCHESTRATOR_TOKENS_JSON='{"tok-po":{"actor_id":"po-alice","roles":["po"],"scopes":["team-a"]}}'
uvicorn orchestrator.api.main:app --host 127.0.0.1 --port 8000
```

## Docker Compose Profiles

```bash
# Run Orchestrator service only (does not require GRAFANA_ADMIN_PASSWORD)
export SDLC_ORCHESTRATOR_TOKENS_JSON='{"tok-admin":{"actor_id":"admin-1","roles":["admin"],"scopes":["*"]}}'
docker compose --profile orchestrator up --build

# Run Monitoring stack (Loki + Alloy + Grafana; requires GRAFANA_ADMIN_PASSWORD)
export GRAFANA_ADMIN_PASSWORD='change-me-strong-password'
docker compose --profile monitoring up
```

### File-backed token registry

Keep the registry JSON outside the repository and Docker build context. Set
`TOKEN_REGISTRY_FILE` to its absolute host path. The container runs as `sdlc`
(UID 1000). On hosts that preserve Linux ownership, grant that UID read access
(for example, owner UID 1000 with mode `0400`). On Docker Desktop or OrbStack,
check that the file is shared with the VM and readable by the container user.

```bash
docker compose --profile orchestrator run --rm --build --service-ports \
  --volume "${TOKEN_REGISTRY_FILE:?Set TOKEN_REGISTRY_FILE}:/run/secrets/orchestrator-tokens.json:ro" \
  --env SDLC_ORCHESTRATOR_TOKENS_FILE=/run/secrets/orchestrator-tokens.json \
  --env SDLC_ORCHESTRATOR_TOKENS_JSON= orchestrator
```

For a smoke test, use a temporary registry with a throwaway token. With the
service running, `GET /health` should return `200`. For an example token named
`smoke-token`, the following requests should return `401` and `404` respectively.
The second status shows that authentication succeeded before looking up the
nonexistent run.

```bash
curl --silent --output /dev/null --write-out '%{http_code}\n' \
  http://127.0.0.1:8000/runs/file-registry-smoke-missing
curl --silent --output /dev/null --write-out '%{http_code}\n' \
  --header 'Authorization: Bearer smoke-token' \
  http://127.0.0.1:8000/runs/file-registry-smoke-missing
```
