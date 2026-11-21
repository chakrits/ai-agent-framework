"""Load canonical agents, skills, workflows, and constitution directly from disk."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AgentSpec:
    """Canonical agent definition parsed from .agents/agents/*.md."""

    name: str
    description: str
    role: str
    stage: str
    skills: tuple[str, ...]
    instructions: str
    source_path: Path


@dataclass(frozen=True)
class SkillSpec:
    """Canonical skill definition parsed from .agents/skills/*/SKILL.md."""

    name: str
    description: str
    body: str
    source_path: Path


@dataclass
class FrameworkBundle:
    """Complete in-memory bundle loaded from the repository's canonical core."""

    root: Path
    constitution: str
    agents: dict[str, AgentSpec] = field(default_factory=dict)
    skills: dict[str, SkillSpec] = field(default_factory=dict)
    workflows: dict[str, str] = field(default_factory=dict)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse minimal YAML frontmatter (key: value and simple string lists) without external deps."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return {}, text

    meta: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw in lines[1:end_idx]:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_list_key is not None:
            meta.setdefault(current_list_key, []).append(stripped[2:].strip().strip("'\""))
            continue
        current_list_key = None
        if ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val == "":
                meta[key] = []
                current_list_key = key
            else:
                meta[key] = val.strip("'\"")

    body = "\n".join(lines[end_idx + 1 :]).lstrip("\n")
    return meta, body


def _load_skills_from_dir(skills_dir: Path) -> dict[str, SkillSpec]:
    loaded: dict[str, SkillSpec] = {}
    if not skills_dir.exists():
        return loaded
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        meta, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        name = str(meta.get("name") or skill_md.parent.name)
        loaded[name] = SkillSpec(
            name=name,
            description=str(meta.get("description", "")),
            body=body,
            source_path=skill_md,
        )
    return loaded


def load_framework(root: Path, project_pack: str | None = None) -> FrameworkBundle:
    """Load canonical .agents/ core, constitution, and optional project pack overlay."""
    agents_dir = root / ".agents"
    constitution_path = root / "docs" / "operating-model" / "constitution.md"
    constitution = constitution_path.read_text(encoding="utf-8") if constitution_path.exists() else ""

    bundle = FrameworkBundle(root=root, constitution=constitution)
    bundle.skills.update(_load_skills_from_dir(agents_dir / "skills"))

    for agent_md in sorted((agents_dir / "agents").glob("*.md")):
        meta, body = parse_frontmatter(agent_md.read_text(encoding="utf-8"))
        name = str(meta.get("name") or agent_md.stem)
        skills_list = tuple(str(s) for s in meta.get("skills", []))
        bundle.agents[name] = AgentSpec(
            name=name,
            description=str(meta.get("description", "")),
            role=str(meta.get("role", name)),
            stage=str(meta.get("stage", "")),
            skills=skills_list,
            instructions=body,
            source_path=agent_md,
        )

    for wf_md in sorted((agents_dir / "workflows").glob("*.md")):
        bundle.workflows[wf_md.stem] = wf_md.read_text(encoding="utf-8")

    if project_pack:
        pack_dir = root / "examples" / "project-packs" / project_pack
        if not pack_dir.exists():
            raise FileNotFoundError(f"Project pack not found: {pack_dir}")
        bundle.skills.update(_load_skills_from_dir(pack_dir / "skills"))

    return bundle


def assemble_agent_prompt(bundle: FrameworkBundle, agent_name: str, task_context: str) -> str:
    """Assemble an agent's effective prompt from canonical core + constitution + bound skills."""
    if agent_name not in bundle.agents:
        raise KeyError(f"Unknown canonical agent: {agent_name}")

    agent = bundle.agents[agent_name]
    sections = [
        f"# Active Role: {agent.name} ({agent.role})",
        "## Governance Constitution",
        bundle.constitution.strip(),
        "## Role Instructions",
        agent.instructions.strip(),
    ]
    for skill_name in agent.skills:
        skill = bundle.skills.get(skill_name)
        if skill:
            sections.append(f"## Skill: {skill.name}\n{skill.body.strip()}")

    sections.append(f"## Task Context\n{task_context.strip()}")
    return "\n\n---\n\n".join(sections)
