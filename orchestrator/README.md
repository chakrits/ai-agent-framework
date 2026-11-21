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

## Optional HTTP Service (FastAPI)

```bash
pip install -r orchestrator/requirements.txt
uvicorn orchestrator.api.main:app --reload
```
