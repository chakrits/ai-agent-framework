"""Token-based authentication and Gate RBAC authorization for the Orchestrator HTTP API."""

from __future__ import annotations

import hmac
import json
import os
from dataclasses import dataclass
from typing import Mapping


class AuthenticationError(PermissionError):
    """Raised when caller identity cannot be verified (HTTP 401)."""


class AuthorizationError(PermissionError):
    """Raised when authenticated caller lacks permission for the target Gate (HTTP 403)."""


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


def load_token_registry(env: Mapping[str, str] | None = None) -> dict[str, AuthenticatedActor]:
    """Load token -> AuthenticatedActor mapping from SDLC_ORCHESTRATOR_TOKENS_JSON."""
    source = os.environ if env is None else env
    raw = (source.get("SDLC_ORCHESTRATOR_TOKENS_JSON") or "").strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("SDLC_ORCHESTRATOR_TOKENS_JSON must be a JSON object mapping token -> {actor_id, roles}")

    registry: dict[str, AuthenticatedActor] = {}
    for token, info in data.items():
        if not isinstance(token, str) or not token or not isinstance(info, dict):
            continue
        actor_id = str(info.get("actor_id") or "").strip()
        roles = frozenset(str(r).strip().lower() for r in info.get("roles", []) if str(r).strip())
        if actor_id:
            registry[token] = AuthenticatedActor(actor_id=actor_id, roles=roles)
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


def authorize_gate(actor: AuthenticatedActor, gate_name: str) -> None:
    """Verify the authenticated actor holds an allowed role for gate_name."""
    required = GATE_REQUIRED_ROLES.get(gate_name)
    if required is None:
        required = frozenset({"maintainer", "admin"})
    if not (actor.roles & required):
        raise AuthorizationError(
            f"Actor '{actor.actor_id}' with roles {sorted(actor.roles)} is not authorized for '{gate_name}'"
        )
