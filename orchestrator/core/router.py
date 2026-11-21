"""Dynamic work classifier and risk-based router aligned with docs/workflow/dynamic-routing.md."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorkType(str, Enum):
    NEW_FEATURE = "new_feature"
    BUG_FIX = "bug_fix"
    API_SCHEMA_CHANGE = "api_schema_change"
    CONFIG_DATA_CHANGE = "config_data_change"
    TEST_OR_DOCS_ONLY = "test_or_docs_only"
    FRAMEWORK_CHANGE = "framework_change"


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


HIGH_RISK_KEYWORDS = (
    "auth",
    "authentication",
    "authorization",
    "permission",
    "payment",
    "billing",
    "schema",
    "migration",
    "secret",
    "pii",
    "production",
)


@dataclass(frozen=True)
class RouteStage:
    """A single stage node in the execution graph (supports parallel agent lists and retry loops)."""

    stage_id: str
    agents: tuple[str, ...]
    parallel: bool = False
    retry_on_fail: bool = False
    human_gate_after: str | None = None


@dataclass(frozen=True)
class RoutePlan:
    """Resolved route plan produced by the dynamic router."""

    work_type: WorkType
    risk_tier: RiskTier
    escalated: bool
    escalation_reason: str | None
    stages: tuple[RouteStage, ...]


def classify_and_route(
    work_type: WorkType | str,
    requested_risk: RiskTier | str = RiskTier.MEDIUM,
    summary: str = "",
) -> RoutePlan:
    """Determine effective risk tier (with escalation rules) and minimum safe SDLC stages."""
    wtype = WorkType(work_type)
    risk = RiskTier(requested_risk)
    escalated = False
    reason: str | None = None

    lowered = summary.lower()
    matched_kw = [kw for kw in HIGH_RISK_KEYWORDS if kw in lowered]
    if risk != RiskTier.HIGH and matched_kw:
        risk = RiskTier.HIGH
        escalated = True
        reason = f"Escalated to HIGH risk due to sensitive scope keywords: {', '.join(matched_kw)}"

    if wtype in {WorkType.API_SCHEMA_CHANGE, WorkType.FRAMEWORK_CHANGE} and risk == RiskTier.LOW:
        risk = RiskTier.HIGH
        escalated = True
        reason = f"{wtype.value} requires elevated governance"

    stages = _stages_for(wtype, risk)
    return RoutePlan(
        work_type=wtype,
        risk_tier=risk,
        escalated=escalated,
        escalation_reason=reason,
        stages=stages,
    )


def _stages_for(wtype: WorkType, risk: RiskTier) -> tuple[RouteStage, ...]:
    review_stage = RouteStage(
        stage_id="review_and_security",
        agents=("code-reviewer-agent", "security-audit-agent") if risk != RiskTier.LOW else ("code-reviewer-agent",),
        parallel=risk != RiskTier.LOW,
        human_gate_after="Gate 3: Release & Merge",
    )

    if wtype == WorkType.NEW_FEATURE:
        return (
            RouteStage("plan", ("ba-po-agent",), human_gate_after="Gate 1: Scope & Intent"),
            RouteStage("design", ("sa-architect-agent",), human_gate_after="Gate 2: Architecture & Spec"),
            RouteStage("tdd_design", ("qa-function-agent",)),
            RouteStage("build", ("dev-coding-agent",), retry_on_fail=True),
            review_stage,
        )

    if wtype == WorkType.API_SCHEMA_CHANGE:
        return (
            RouteStage("plan", ("ba-po-agent",), human_gate_after="Gate 1: Scope & Intent"),
            RouteStage("design", ("sa-architect-agent",), human_gate_after="Gate 2: Architecture & Spec"),
            RouteStage("tdd_design", ("qa-function-agent",)),
            RouteStage("build", ("dev-coding-agent",), retry_on_fail=True),
            review_stage,
        )

    if wtype == WorkType.BUG_FIX:
        stages: list[RouteStage] = []
        if risk == RiskTier.HIGH:
            stages.append(RouteStage("impact_check", ("sa-architect-agent",), human_gate_after="Gate 2: Fast-Track Spec"))
        stages.extend(
            [
                RouteStage("reproduce_oracle", ("qa-function-agent",)),
                RouteStage("fix_and_verify", ("dev-coding-agent",), retry_on_fail=True),
                review_stage,
            ]
        )
        return tuple(stages)

    if wtype == WorkType.CONFIG_DATA_CHANGE:
        return (
            RouteStage("impact_check", ("sa-architect-agent",), human_gate_after="Gate 2: Change Plan" if risk == RiskTier.HIGH else None),
            RouteStage("apply_and_verify", ("dev-coding-agent",), retry_on_fail=True),
            review_stage,
        )

    if wtype == WorkType.TEST_OR_DOCS_ONLY:
        return (
            RouteStage("author_tests_or_docs", ("qa-function-agent",)),
            RouteStage("lightweight_review", ("code-reviewer-agent",), human_gate_after="Gate 3: Release & Merge"),
        )

    # FRAMEWORK_CHANGE
    return (
        RouteStage("spec_update", ("sa-architect-agent",), human_gate_after="Gate 2: Framework Spec"),
        RouteStage("implement_framework", ("dev-coding-agent",), retry_on_fail=True),
        review_stage,
    )
