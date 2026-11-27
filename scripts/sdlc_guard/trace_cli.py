"""Inspect and configure local agent traces.

Usage (via scripts/sdlc_trace.py):
  list [--limit N]
  show <session-prefix> [--tool NAME] [--output] [--json]
  summary [--work-item INT-001] [--session PREFIX] [--json]
  export --work-item INT-001 --out FILE.md
  config show [--json]
  config set level <off|info|debug> [--for 30m]   agents may only run: config set level debug --for <=120m
  config set tz <local|utc> | config set retention_days <N> | config unset <key>   (human only)
  hooks list | hooks enable <group> | hooks disable <group>                         (enable/disable: human only)

"Human only" is enforced by requiring an interactive terminal (stdin is a TTY) and by the agent guard.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from . import guard, trace, trace_config, trace_hooks

HUMAN_ONLY_EXIT = 3


def _instant(ts: Any) -> datetime:
    try:
        dt = datetime.fromisoformat(str(ts))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def load_events(trace_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not trace_dir.is_dir():
        return events
    for f in sorted(trace_dir.rglob("*.jsonl")):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue  # file briefly locked by a hook on Windows; skip this round
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    events.sort(key=lambda e: _instant(e.get("ts", "")))  # by instant: offsets differ between machines / modes
    return events


def by_session(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    sessions: dict[str, list[dict[str, Any]]] = {}
    for ev in events:
        sessions.setdefault(str(ev.get("session_id")), []).append(ev)
    return sessions


def is_blocked(ev: dict[str, Any]) -> bool:
    return ev.get("event") == "PreToolUse" and ev.get("decision", {}).get("allowed") is False


def is_failure(ev: dict[str, Any]) -> bool:
    return ev.get("event") == "PostToolUseFailure"


def is_tool_result(ev: dict[str, Any]) -> bool:
    """A tool call that reached an outcome: completed, failed, or blocked by the guard."""
    return ev.get("event") in {"PostToolUse", "PostToolUseFailure"} or is_blocked(ev)


def summarize(events: list[dict[str, Any]], scrub: Callable[[str], str] = lambda text: text) -> dict[str, Any]:
    results = [e for e in events if is_tool_result(e) and e.get("tool_name")]
    durations = [e["duration_ms"] for e in results if isinstance(e.get("duration_ms"), (int, float))]
    reasons = Counter(r for e in events if is_blocked(e) for r in e["decision"].get("reasons", []))
    # Scrub before cutting: a path split by the cut would no longer match the string being replaced.
    commands = Counter(scrub(e["input"]["command"].splitlines()[0])[:100] for e in results if e.get("input", {}).get("command"))
    return {
        "sessions": len({e.get("session_id") for e in events}),
        "events": len(events),
        "tools": dict(Counter(e["tool_name"] for e in results)),
        "blocked": sum(1 for e in events if is_blocked(e)),
        "failures": sum(1 for e in events if is_failure(e)),
        "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else None,
        "platforms": dict(Counter(e.get("platform") for e in events)),
        "models": dict(Counter(e.get("model") for e in events if e.get("model"))),
        "efforts": dict(Counter(e.get("effort") for e in events if e.get("effort"))),
        "permission_modes": dict(Counter(e.get("permission_mode") for e in events if e.get("permission_mode"))),
        "block_reasons": dict(reasons.most_common(10)),
        "top_commands": dict(commands.most_common(5)),
        "first_ts": events[0].get("ts") if events else None,
        "last_ts": events[-1].get("ts") if events else None,
    }


def _filter(events: list[dict[str, Any]], work_item: str | None = None, session: str | None = None) -> list[dict[str, Any]]:
    if work_item:
        events = [e for e in events if e.get("work_item") == work_item]
    if session:
        events = [e for e in events if str(e.get("session_id", "")).startswith(session)]
    return events


def _clock(ts: str) -> str:
    return ts[11:19] if len(ts) >= 19 else ts


def _stamp_short(ts: str) -> str:
    """2026-11-21T12:34:56.789+07:00 -> 2026-11-21T12:34:56+07:00"""
    return ts[:19] + ts[23:] if len(ts) > 23 else ts


def _describe(ev: dict[str, Any], show_output: bool) -> str:
    inp = ev.get("input", {})
    what = (inp.get("command") or inp.get("file_path") or inp.get("path") or inp.get("summary") or ev.get("prompt") or ev.get("message")
            or ev.get("file_path") or ev.get("reason") or "").splitlines()
    head = f"{_clock(ev.get('ts', ''))}  {ev.get('event', ''):<18} {ev.get('tool_name') or '':<10} {(what[0] if what else '')[:110]}"
    if is_blocked(ev):
        head += "  -> BLOCKED: " + "; ".join(ev["decision"].get("reasons", []))
    elif is_failure(ev):
        head += ("  -> FAILED: " + str(ev.get("error", "")).splitlines()[0]) if ev.get("error") else "  -> FAILED"
    elif ev.get("event") == "PostToolUse":
        head += "  -> ok" + (f" ({ev['duration_ms']}ms)" if "duration_ms" in ev else "")
    if show_output and ev.get("output", {}).get("stdout"):
        head += "\n      | " + ev["output"]["stdout"][:400].replace("\n", "\n      | ")
    return head


def cmd_list(events: list[dict[str, Any]], args: argparse.Namespace, ctx: dict[str, Any]) -> int:
    sessions = by_session(events)
    if not sessions:
        print(f"No traces found in {ctx['trace_dir']}.")
        return 0
    rows = sorted(sessions.items(), key=lambda kv: _instant(kv[1][-1].get("ts", "")), reverse=True)[: args.limit]
    print(f"{'session':<38} {'started':<25} {'platform':<8} {'model':<22} {'effort':<7} {'events':>6} {'tools':>5} {'blocked':>7} {'failed':>6}  work_item")
    for sid, evs in rows:
        s = summarize(evs)
        wi = next((e["work_item"] for e in evs if e.get("work_item")), "-")
        model = next((e["model"] for e in reversed(evs) if e.get("model") not in (None, "unknown")), "-")
        effort = next((e["effort"] for e in reversed(evs) if e.get("effort")), "-")
        print(f"{sid:<38} {_stamp_short(evs[0].get('ts', '')):<25} {evs[0].get('platform', ''):<8} {model:<22} {effort:<7} {len(evs):>6} "
              f"{sum(s['tools'].values()):>5} {s['blocked']:>7} {s['failures']:>6}  {wi}")
    return 0


def cmd_show(events: list[dict[str, Any]], args: argparse.Namespace, ctx: dict[str, Any]) -> int:
    sessions = by_session(events)
    matches = [sid for sid in sessions if sid.startswith(args.session)]
    if len(matches) != 1:
        msg = "no session matches" if not matches else f"ambiguous prefix, matches: {', '.join(sorted(matches)[:5])}"
        print(f"{msg}: {args.session}", file=sys.stderr)
        return 1
    evs = sessions[matches[0]]
    if args.tool:
        evs = [e for e in evs if e.get("tool_name") == args.tool]
    if args.json:
        for ev in evs:
            print(json.dumps(ev, ensure_ascii=False))
        return 0
    model = next((e["model"] for e in reversed(sessions[matches[0]]) if e.get("model") not in (None, "unknown")), "unknown")
    effort = next((e["effort"] for e in reversed(sessions[matches[0]]) if e.get("effort")), "n/a")
    print(f"# session {matches[0]}  model={model} effort={effort}  ({len(evs)} events shown, times {evs[0].get('ts', '')[23:] if evs else ''})")
    for ev in evs:
        print(_describe(ev, args.output))
    return 0


def cmd_summary(events: list[dict[str, Any]], args: argparse.Namespace, ctx: dict[str, Any]) -> int:
    data = summarize(_filter(events, args.work_item, args.session))
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    print(f"sessions={data['sessions']} events={data['events']} blocked={data['blocked']} failures={data['failures']} "
          f"avg_duration_ms={data['avg_duration_ms']}")
    for label in ("models", "efforts", "permission_modes"):
        if data[label]:
            print(f"  {label}: " + ", ".join(f"{k}={v}" for k, v in data[label].items()))
    for name, n in sorted(data["tools"].items(), key=lambda kv: -kv[1]):
        print(f"  tool {name:<14} {n}")
    for reason, n in data["block_reasons"].items():
        print(f"  blocked x{n}: {reason}")
    return 0


def render_markdown(data: dict[str, Any], work_item: str) -> str:
    lines = [
        f"# Agent trace summary — {work_item}",
        "",
        f"_Generated {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %z')} from local traces; secrets redacted, outputs truncated._",
        "",
        "| Metric | Value |", "| :--- | :--- |",
        f"| Sessions | {data['sessions']} |", f"| Events | {data['events']} |",
        f"| Tool calls (completed, failed or blocked) | {sum(data['tools'].values())} |",
        f"| Blocked by guard | {data['blocked']} |", f"| Failed tool calls | {data['failures']} |",
        f"| Avg tool duration (ms) | {data['avg_duration_ms']} |",
        f"| Models | {', '.join(f'{k} ({v})' for k, v in data['models'].items()) or '-'} |",
        f"| Effort levels | {', '.join(f'{k} ({v})' for k, v in data['efforts'].items()) or '-'} |",
        f"| Permission modes | {', '.join(f'{k} ({v})' for k, v in data['permission_modes'].items()) or '-'} |",
        f"| Window | {data['first_ts']} → {data['last_ts']} |",
        "",
        "## Tool calls", "", "| Tool | Count |", "| :--- | ---: |",
        *[f"| {t} | {n} |" for t, n in sorted(data["tools"].items(), key=lambda kv: -kv[1])],
        "",
        "## Guard blocks", "",
        *([f"- x{n}: {r}" for r, n in data["block_reasons"].items()] or ["- none"]),
        "",
        "## Most frequent commands", "",
        *([f"- `{c}` (x{n})" for c, n in data["top_commands"].items()] or ["- none"]),
        "",
    ]
    return "\n".join(lines)


def scrub_paths(text: str, repo_root: Path | str, home: Path | str | None = None) -> str:
    """Replace machine-specific absolute paths so an exported summary is safe to commit to a public repo."""
    for base, token in ((repo_root, "<repo>"), (home if home is not None else Path.home(), "~")):
        raw = str(base).rstrip("/\\")
        if not raw or raw in {"/", "\\"}:
            continue
        for variant in {raw, raw.replace("\\", "/"), raw.replace("/", "\\")}:
            text = text.replace(variant, token)
    return text


def cmd_export(events: list[dict[str, Any]], args: argparse.Namespace, ctx: dict[str, Any]) -> int:
    def scrub(text: str) -> str:
        return scrub_paths(text, guard.REPO_ROOT)

    data = summarize(_filter(events, args.work_item), scrub)
    if not data["events"]:
        print(f"No trace events for work item {args.work_item}.", file=sys.stderr)
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(scrub(render_markdown(data, args.work_item)))
    print(f"Wrote {out}")
    return 0


# ---------------------------------------------------------------- config / hooks (human-gated)

def _human_only(what: str) -> int:
    print(f"refused: {what} is human-only. Run it yourself in an interactive terminal "
          "(agents may only run 'config show' and 'config set level debug --for <=120m').", file=sys.stderr)
    return HUMAN_ONLY_EXIT


def _effective(ctx: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    path = trace_config.config_path(ctx["state_dir"])
    return trace_config.effective(ctx["env"], trace_config.load(path), ctx["now"]), path


def cmd_config(events: list[dict[str, Any]], args: argparse.Namespace, ctx: dict[str, Any]) -> int:
    eff, path = _effective(ctx)
    if args.action == "show":
        if args.json:
            print(json.dumps({**eff, "config_file": str(path)}, indent=2, ensure_ascii=False))
            return 0
        exp = f", expires {eff['expires_at']}" if eff["expires_at"] else (", ttl expired -> default" if eff["expired"] else "")
        print(f"level:      {eff['level']} (source: {eff['level_source']}{exp})")
        print(f"timezone:   {eff['tz']} (source: {eff['tz_source']})")
        print(f"retention:  {eff['retention_days']} days (source: {eff['retention_source']})")
        print(f"config file: {path}")
        if eff["env_overrides"] or eff["level_source"] == "env":
            print("note: SDLC_TRACE_LEVEL is set in the environment and overrides the config file level")
        return 0

    if args.action == "unset":
        if args.key not in trace_config.SETTABLE_KEYS:
            print(f"unknown key {args.key!r}; keys: {', '.join(trace_config.SETTABLE_KEYS)}", file=sys.stderr)
            return 2
        if not ctx["is_tty"]():
            return _human_only(f"'config unset {args.key}'")
        _audit(ctx, f"{args.key} {eff.get(args.key if args.key != 'retention_days' else 'retention_days')} -> (unset) by human (tty)")
        trace_config.unset(path, args.key)
        print(f"unset {args.key}")
        return 0

    # set
    key, value = args.key, args.value
    if key not in trace_config.SETTABLE_KEYS:
        print(f"unknown key {key!r}; keys: {', '.join(trace_config.SETTABLE_KEYS)}", file=sys.stderr)
        return 2
    minutes: int | None = None
    if args.for_:
        if key != "level":
            print("--for only applies to 'level'", file=sys.stderr)
            return 2
        try:
            minutes = trace_config.parse_duration_minutes(args.for_)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        if minutes > trace_config.MAX_TTL_MINUTES:
            print(f"--for may not exceed {trace_config.MAX_TTL_MINUTES} minutes", file=sys.stderr)
            return 2
    problem = None
    if key == "level" and value not in trace_config.LEVELS:
        problem = f"level must be one of {', '.join(trace_config.LEVELS)}"
    elif key == "tz" and value not in trace_config.TZ_MODES:
        problem = f"tz must be one of {', '.join(trace_config.TZ_MODES)}"
    elif key == "retention_days" and not (value.isdigit() and int(value) >= 1):
        problem = "retention_days must be a whole number >= 1"
    if problem:
        print(problem, file=sys.stderr)
        return 2

    agent_ok = key == "level" and value == "debug" and minutes is not None
    if not agent_ok and not ctx["is_tty"]():
        return _human_only(f"'config set {key} {value}'" + (" without --for" if key == "level" and value == "debug" else ""))
    if agent_ok and not ctx["is_tty"]():
        cfg = trace_config.load(path)
        if eff["level_source"] == "config" and str(cfg.get("updated_by", "")).startswith("human"):
            print("refused: a level set by a human is in force (a temporary agent override could re-enable capture "
                  "the human turned off, or shorten a persistent setting). Ask the human to change it.", file=sys.stderr)
            return HUMAN_ONLY_EXIT
    who = "human (tty)" if ctx["is_tty"]() else "agent (ttl)"
    old = eff.get({"level": "level", "tz": "tz", "retention_days": "retention_days"}[key])
    _audit(ctx, f"{key} {old} -> {value}" + (f" for {minutes}m" if minutes else "") + f" by {who}")  # logged before it can switch tracing off
    if key == "level":
        trace_config.set_level(path, value, minutes=minutes, by=who, now=ctx["now"])
    else:
        trace_config.set_value(path, key, value, by=who, now=ctx["now"])
    print(f"{key} = {value}" + (f" for {minutes} minutes (then back to default)" if minutes else ""))
    if key == "level" and ctx["env"].get("SDLC_TRACE_LEVEL", "").strip().lower() in trace_config.LEVELS:
        print("note: SDLC_TRACE_LEVEL is set in the environment and still overrides this value", file=sys.stderr)
    return 0


def _audit(ctx: dict[str, Any], reason: str) -> None:
    trace.safe_record(
        {"session_id": "config", "hook_event_name": "TraceConfigChange", "reason": reason},
        platform="orchestrator", repo_root=ctx["repo_root"], env=ctx["env"], now=ctx["now"],
    )


def _settings_local(ctx: dict[str, Any]) -> Path:
    return Path(ctx["repo_root"]) / ".claude" / "settings.local.json"


def _load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def _has_trace_handler(entries: list[Any]) -> bool:
    cmd = trace_hooks.claude_handler("trace")["command"]
    return any(h.get("command") == cmd for e in entries if isinstance(e, dict) for h in e.get("hooks", []) if isinstance(h, dict))


def cmd_hooks(events: list[dict[str, Any]], args: argparse.Namespace, ctx: dict[str, Any]) -> int:
    path = _settings_local(ctx)
    try:
        settings = _load_settings(path)
    except (ValueError, OSError) as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return 2
    hooks = settings.get("hooks", {}) if isinstance(settings.get("hooks"), dict) else {}

    if args.action == "list":
        print("Tier 1 (always on, in .claude/settings.json / .codex/hooks.json):")
        print("  claude: " + ", ".join(trace_hooks.CLAUDE_TIER1_ASYNC + trace_hooks.CLAUDE_TIER1_SYNC))
        print("  codex:  " + ", ".join(trace_hooks.CODEX_TIER1_ASYNC + trace_hooks.CODEX_TIER1_SYNC))
        print(f"Tier 2 (opt-in for Claude Code, stored in {path.name}):")
        for group, evs in trace_hooks.CLAUDE_TIER2.items():
            on = all(_has_trace_handler(hooks.get(e, [])) for e in evs)
            print(f"  {group:<14} {', '.join(evs):<40} [{'enabled' if on else 'disabled'}]")
        print("Never traced: " + ", ".join(trace_hooks.FORBIDDEN_TRACE_EVENTS))
        return 0

    if args.group not in trace_hooks.CLAUDE_TIER2:
        print(f"unknown group {args.group!r}; groups: {', '.join(trace_hooks.CLAUDE_TIER2)}", file=sys.stderr)
        return 2
    if not ctx["is_tty"]():
        return _human_only(f"'hooks {args.action} {args.group}'")

    cmd = trace_hooks.claude_handler("trace")["command"]
    for event in trace_hooks.CLAUDE_TIER2[args.group]:
        entries = list(hooks.get(event, []))
        if args.action == "enable":
            if not _has_trace_handler(entries):
                entries.append(trace_hooks.claude_trace_entry(event))
        else:
            kept = []
            for entry in entries:
                inner = [h for h in entry.get("hooks", []) if h.get("command") != cmd]
                if inner:
                    kept.append({**entry, "hooks": inner})
            entries = kept
        if entries:
            hooks[event] = entries
        else:
            hooks.pop(event, None)
    if hooks:
        settings["hooks"] = hooks
    else:
        settings.pop("hooks", None)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"{args.action}d tier-2 group '{args.group}' in {path}. Restart Claude Code (or run /hooks) to pick it up.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sdlc_trace.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", help="trace directory (default: SDLC_TRACE_DIR or .sdlc/traces)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("show"); p.add_argument("session"); p.add_argument("--tool"); p.add_argument("--output", action="store_true"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("summary"); p.add_argument("--work-item"); p.add_argument("--session"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("export"); p.add_argument("--work-item", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("config", help="show or change trace settings")
    csub = p.add_subparsers(dest="action", required=True)
    c = csub.add_parser("show"); c.add_argument("--json", action="store_true")
    c = csub.add_parser("set"); c.add_argument("key"); c.add_argument("value"); c.add_argument("--for", dest="for_", metavar="DURATION", help="e.g. 30m or 2h (max 120m); level only")
    c = csub.add_parser("unset"); c.add_argument("key")
    p = sub.add_parser("hooks", help="list or toggle optional (tier 2) trace hooks")
    hsub = p.add_subparsers(dest="action", required=True)
    hsub.add_parser("list")
    for name in ("enable", "disable"):
        h = hsub.add_parser(name); h.add_argument("group")
    return parser


def main(
    argv: list[str],
    trace_dir: Path | None = None,
    is_tty: Callable[[], bool] | None = None,
    repo_root: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    env = os.environ if env is None else env
    root = Path(repo_root) if repo_root is not None else guard.REPO_ROOT
    directory = trace_dir or (Path(args.dir) if args.dir else trace.trace_root(root, env))
    ctx = {
        "trace_dir": directory,
        "state_dir": directory.parent,
        "repo_root": root,
        "env": env,
        "now": now,
        "is_tty": is_tty or (lambda: bool(sys.stdin and sys.stdin.isatty())),
    }
    handlers = {"list": cmd_list, "show": cmd_show, "summary": cmd_summary, "export": cmd_export, "config": cmd_config, "hooks": cmd_hooks}
    events = load_events(directory) if args.cmd in {"list", "show", "summary", "export"} else []
    return handlers[args.cmd](events, args, ctx)
