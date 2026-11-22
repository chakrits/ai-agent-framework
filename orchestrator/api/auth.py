"""Token-based authentication, run-scope isolation, and Gate RBAC for the Orchestrator HTTP API."""

from __future__ import annotations

import hmac
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


class AuthenticationError(PermissionError):
    """Raised when caller identity cannot be verified (HTTP 401)."""


class AuthorizationError(PermissionError):
    """Raised when authenticated caller lacks permission for the target run scope or Gate (HTTP 403)."""


GATE_REQUIRED_ROLES: dict[str, frozenset[str]] = {
    "Gate 1: Scope & Intent": frozenset({"po", "ba", "admin"}),
    "Gate 2: Architecture & Spec": frozenset({"sa", "tech_lead", "admin"}),
    "Gate 2: Fast-Track Spec": frozenset({"sa", "tech_lead", "admin"}),
    "Gate 2: Change Plan": frozenset({"sa", "tech_lead", "admin"}),
    "Gate 2: Framework Spec": frozenset({"sa", "tech_lead", "admin"}),
    "Gate 3: Release & Merge": frozenset({"maintainer", "tech_lead", "admin"}),
}


@dataclass(frozen=True)
class AuthenticatedActor:
    """Verified caller identity resolved from a server-side token registry."""

    actor_id: str
    roles: frozenset[str]
    scopes: frozenset[str] = field(default_factory=lambda: frozenset({"default"}))


def _parse_scopes(info: Mapping[str, Any]) -> frozenset[str]:
    raw_scopes = info.get("scopes")
    if isinstance(raw_scopes, list):
        cleaned = frozenset(str(s).strip() for s in raw_scopes if str(s).strip())
        if cleaned:
            return cleaned
    single = str(info.get("scope") or "").strip()
    if single:
        return frozenset({single})
    return frozenset({"default"})


def load_token_registry(env: Mapping[str, str] | None = None) -> dict[str, AuthenticatedActor]:
    """Load token -> AuthenticatedActor mapping from SDLC_ORCHESTRATOR_TOKENS_JSON or SDLC_ORCHESTRATOR_TOKENS_FILE."""
    source = os.environ if env is None else env
    raw = (source.get("SDLC_ORCHESTRATOR_TOKENS_JSON") or "").strip()
    if not raw:
        file_path = (source.get("SDLC_ORCHESTRATOR_TOKENS_FILE") or "").strip()
        if file_path and Path(file_path).is_file():
            raw = Path(file_path).read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Token registry must be a JSON object mapping token -> {actor_id, roles, scopes?}")

    registry: dict[str, AuthenticatedActor] = {}
    for token, info in data.items():
        if not isinstance(token, str) or not token or not isinstance(info, dict):
            continue
        actor_id = str(info.get("actor_id") or "").strip()
        roles = frozenset(str(r).strip().lower() for r in info.get("roles", []) if str(r).strip())
        scopes = _parse_scopes(info)
        if actor_id:
            registry[token] = AuthenticatedActor(actor_id=actor_id, roles=roles, scopes=scopes)
    return registry


def authenticate_bearer(authorization_header: str | None, registry: Mapping[str, AuthenticatedActor]) -> AuthenticatedActor:
    """Verify Authorization: Bearer <token> using constant-time token lookup."""
    if not authorization_header or not authorization_header.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization: Bearer token")
    token = authorization_header[len("Bearer ") :].strip()
    if not token:
        raise AuthenticationError("Empty bearer token")

    for known_token, actor in registry.items():
        if hmac.compare_digest(token, known_token):
            return actor
    raise AuthenticationError("Invalid bearer token")


def authorize_run_scope(actor: AuthenticatedActor, run_scope: str) -> None:
    """Verify the authenticated actor is permitted to access or mutate runs in run_scope."""
    target_scope = (run_scope or "default").strip() or "default"
    if "admin" in actor.roles or "*" in actor.scopes or target_scope in actor.scopes:
        return
    raise AuthorizationError(
        f"Actor '{actor.actor_id}' with scopes {sorted(actor.scopes)} cannot access run in scope '{target_scope}'"
    )


def authorize_gate(actor: AuthenticatedActor, gate_name: str, run_scope: str = "default") -> None:
    """Verify the authenticated actor holds both run-scope access and an allowed role for gate_name."""
    authorize_run_scope(actor, run_scope)
    required = GATE_REQUIRED_ROLES.get(gate_name, frozenset({"maintainer", "admin"}))
    if not (actor.roles & required):
        raise AuthorizationError(
            f"Actor '{actor.actor_id}' with roles {sorted(actor.roles)} is not authorized for '{gate_name}'"
        )
