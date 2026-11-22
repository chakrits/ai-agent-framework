"""Deterministic Stage 6 control-band evaluator reading docs/operating-model/bands.yaml."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True)
class BandEvaluation:
    """Result of deterministic statistical control-band evaluation."""

    metric_name: str
    observed_value: float
    baseline_mean: float
    baseline_stddev: float
    sigma_distance: float
    tier: str          # normal | 1sigma | 2sigma | 3sigma
    action: str        # none | log | diagnose | propose
    mode: str          # none | read_only | gated_pr
    breached: bool
    routes: tuple[str, ...] = ()


def _parse_inline_dict_or_list(val: str) -> Any:
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",")]
    return val.strip("'\"")


def load_bands_config(bands_path: Path) -> dict[str, Any]:
    """Parse docs/operating-model/bands.yaml cleanly using Python stdlib."""
    metrics: dict[str, Any] = {}
    current_metric: str | None = None
    in_tiers = False
    current_tier: str | None = None

    for raw_line in bands_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if ":" not in stripped:
            continue
        key, val = (p.strip() for p in stripped.split(":", 1))

        if indent == 2 and key != "metrics":
            current_metric = key
            metrics[current_metric] = {"tiers": {}}
            in_tiers = False
            current_tier = None
        elif indent == 4 and current_metric:
            if key == "tiers":
                in_tiers = True
            else:
                in_tiers = False
                metrics[current_metric][key] = int(val) if val.isdigit() else _parse_inline_dict_or_list(val)
        elif indent == 6 and current_metric and in_tiers:
            current_tier = key
            metrics[current_metric]["tiers"][current_tier] = {}
        elif indent == 8 and current_metric and in_tiers and current_tier:
            if key == "threshold":
                metrics[current_metric]["tiers"][current_tier][key] = float(val)
            else:
                metrics[current_metric]["tiers"][current_tier][key] = _parse_inline_dict_or_list(val)

    return {"metrics": metrics}


def evaluate_control_band(
    metric_name: str,
    baseline_samples: Sequence[float],
    observed_value: float,
    bands_config: dict[str, Any] | None = None,
) -> BandEvaluation:
    """Compute sigma distance over baseline samples and map deterministically to bands.yaml tiers."""
    if len(baseline_samples) < 2:
        raise ValueError("baseline_samples must contain at least 2 observations")

    mean = sum(baseline_samples) / len(baseline_samples)
    variance = sum((x - mean) ** 2 for x in baseline_samples) / len(baseline_samples)
    stddev = math.sqrt(variance)

    if stddev == 0.0:
        sigma = 0.0 if observed_value == mean else (3.0 if observed_value > mean else 0.0)
    else:
        sigma = max(0.0, (observed_value - mean) / stddev)

    defaults: dict[str, tuple[str, str, bool]] = {
        "3sigma": ("propose", "gated_pr", True),
        "2sigma": ("diagnose", "read_only", True),
        "1sigma": ("log", "none", True),
        "normal": ("none", "none", False),
    }

    metric_cfg = bands_config.get("metrics", {}).get(metric_name, {}) if bands_config else {}
    tiers_cfg = metric_cfg.get("tiers", {}) if isinstance(metric_cfg, dict) else {}

    t3 = float(tiers_cfg.get("3sigma", {}).get("threshold", 3.0))
    t2 = float(tiers_cfg.get("2sigma", {}).get("threshold", 2.0))
    t1 = float(tiers_cfg.get("1sigma", {}).get("threshold", 1.0))

    if sigma >= t3:
        tier = "3sigma"
    elif sigma >= t2:
        tier = "2sigma"
    elif sigma >= t1:
        tier = "1sigma"
    else:
        tier = "normal"

    action, mode, breached = defaults[tier]
    routes: tuple[str, ...] = ()
    if bands_config and tier != "normal":
        tier_cfg = tiers_cfg.get(tier, {})
        action = str(tier_cfg.get("action", action))
        mode = str(tier_cfg.get("mode", mode))
        routes = tuple(str(r) for r in tier_cfg.get("routes", []))

    return BandEvaluation(
        metric_name=metric_name,
        observed_value=round(observed_value, 6),
        baseline_mean=round(mean, 6),
        baseline_stddev=round(stddev, 6),
        sigma_distance=round(sigma, 3),
        tier=tier,
        action=action,
        mode=mode,
        breached=breached,
        routes=routes,
    )


def draft_incident_intent(
    evaluation: BandEvaluation,
    intent_id: str,
    affected_systems: str,
    evidence_summary: str,
) -> str:
    """Generate a Stage 1 intent.md draft from a Stage 6 control-band breach for human triage."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    risk_tier = "high" if evaluation.tier == "3sigma" else "medium"
    return f"""---
intent_id: {intent_id}
title: "Remediate {evaluation.metric_name} ({evaluation.tier} band breach)"
work_type: bug_fix
risk_tier: {risk_tier}
status: draft
owner: ops-maintain-agent
---

# Intent: Remediate {evaluation.metric_name} ({evaluation.tier} breach)

## Header & Context
| Item | Detail |
| :--- | :--- |
| **Intent ID** | `{intent_id}` |
| **Stakeholders** | On-call Engineer, PO, SA, Dev, QA |
| **Source Request** | Stage 6 Control Band `{evaluation.metric_name}` (`{evaluation.tier}`, observed={evaluation.observed_value}, baseline_mean={evaluation.baseline_mean}) |

## Problem Statement & Objective
- **Problem:** Metric `{evaluation.metric_name}` reached `{evaluation.observed_value}` (`{evaluation.sigma_distance}` sigma above baseline `{evaluation.baseline_mean}`). {evidence_summary}
- **Objective:** Restore `{evaluation.metric_name}` within normal control band (`< 1sigma`) and add a permanent regression eval case.

## Business Flow Summary
| # | Flow Type | Flow Name | Description | Pre-condition | Post-condition |
| :-: | :--- | :--- | :--- | :--- | :--- |
| 1 | Main | Incident Remediation | Diagnose root cause and deploy bounded fix via Gate 3 | Breach detected in `{evaluation.metric_name}` | Metric returns within baseline; eval added |

## Requirements & Acceptance Criteria
| URD ID | Requirement Summary | Measurable Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- |
| `URD-001` | Resolve root cause of `{evaluation.metric_name}` anomaly | Failing reproduction test added and passes after fix; `{evaluation.metric_name}` < 1σ | High |

## Business Rules & Constraints
| Rule ID | Description | Boundary / Constraint |
| :--- | :--- | :--- |
| `BR-001` | Affected systems: {affected_systems} | Changes must pass Gate 3 PR review; no direct push to main |

## Out of Scope
- Unrelated refactoring outside `{affected_systems}`

## Risks & Open Questions
- [ ] Confirm whether immediate rollback runbook is required while fix is developed.

## Gate 1 Approval
- **Reviewer:** `[On-call / PO Name]`
- **Decision:** `Pending`
- **Timestamp:** `{today}`
"""


def write_draft_intent(output_path: Path, content: str) -> Path:
    """Persist a generated draft intent.md to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path
