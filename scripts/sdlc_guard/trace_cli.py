"""Inspect local agent traces: list sessions, show a timeline, summarize, and export a shareable summary.

Usage (via scripts/sdlc_trace.py):
  list [--limit N]
  show <session-prefix> [--tool NAME] [--output] [--json]
  summary [--work-item INT-001] [--session PREFIX] [--json]
  export --work-item INT-001 --out FILE.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import guard, trace


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
    events.sort(key=lambda e: e.get("ts", ""))
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


def summarize(events: list[dict[str, Any]]) -> dict[str, Any]:
    results = [e for e in events if is_tool_result(e) and e.get("tool_name")]
    durations = [e["duration_ms"] for e in results if isinstance(e.get("duration_ms"), (int, float))]
    reasons = Counter(r for e in events if is_blocked(e) for r in e["decision"].get("reasons", []))
    commands = Counter(e["input"]["command"].splitlines()[0][:100] for e in results if e.get("input", {}).get("command"))
    return {
        "sessions": len({e.get("session_id") for e in events}),
        "events": len(events),
        "tools": dict(Counter(e["tool_name"] for e in results)),
        "blocked": sum(1 for e in events if is_blocked(e)),
        "failures": sum(1 for e in events if is_failure(e)),
        "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else None,
        "platforms": dict(Counter(e.get("platform") for e in events)),
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


def _describe(ev: dict[str, Any], show_output: bool) -> str:
    inp = ev.get("input", {})
    what = (inp.get("command") or inp.get("file_path") or inp.get("path") or ev.get("prompt") or ev.get("message") or "").splitlines()
    head = f"{_clock(ev.get('ts', ''))}  {ev.get('event', ''):<18} {ev.get('tool_name') or '':<10} {(what[0] if what else '')[:110]}"
    if is_blocked(ev):
        head += "  -> BLOCKED: " + "; ".join(ev["decision"].get("reasons", []))
    elif is_failure(ev):
        head += "  -> FAILED: " + str(ev.get("error", "")).splitlines()[0] if ev.get("error") else "  -> FAILED"
    elif ev.get("event") == "PostToolUse":
        head += "  -> ok" + (f" ({ev['duration_ms']}ms)" if "duration_ms" in ev else "")
    if show_output and ev.get("output", {}).get("stdout"):
        head += "\n      | " + ev["output"]["stdout"][:400].replace("\n", "\n      | ")
    return head


def cmd_list(events: list[dict[str, Any]], args: argparse.Namespace, trace_dir: Path) -> int:
    sessions = by_session(events)
    if not sessions:
        print(f"No traces found in {trace_dir}.")
        return 0
    rows = sorted(sessions.items(), key=lambda kv: kv[1][-1].get("ts", ""), reverse=True)[: args.limit]
    print(f"{'session':<38} {'started (UTC)':<20} {'platform':<8} {'events':>6} {'tools':>5} {'blocked':>7} {'failed':>6}  work_item")
    for sid, evs in rows:
        s = summarize(evs)
        wi = next((e["work_item"] for e in evs if e.get("work_item")), "-")
        print(f"{sid:<38} {evs[0].get('ts', '')[:19]:<20} {evs[0].get('platform', ''):<8} {len(evs):>6} "
              f"{sum(s['tools'].values()):>5} {s['blocked']:>7} {s['failures']:>6}  {wi}")
    return 0


def cmd_show(events: list[dict[str, Any]], args: argparse.Namespace, trace_dir: Path) -> int:
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
    print(f"# session {matches[0]}  ({len(evs)} events shown)")
    for ev in evs:
        print(_describe(ev, args.output))
    return 0


def cmd_summary(events: list[dict[str, Any]], args: argparse.Namespace, trace_dir: Path) -> int:
    data = summarize(_filter(events, args.work_item, args.session))
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    print(f"sessions={data['sessions']} events={data['events']} blocked={data['blocked']} failures={data['failures']} "
          f"avg_duration_ms={data['avg_duration_ms']}")
    for name, n in sorted(data["tools"].items(), key=lambda kv: -kv[1]):
        print(f"  tool {name:<14} {n}")
    for reason, n in data["block_reasons"].items():
        print(f"  blocked x{n}: {reason}")
    return 0


def render_markdown(data: dict[str, Any], work_item: str) -> str:
    lines = [
        f"# Agent trace summary — {work_item}",
        "",
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} from local traces; secrets redacted, outputs truncated._",
        "",
        "| Metric | Value |", "| :--- | :--- |",
        f"| Sessions | {data['sessions']} |", f"| Events | {data['events']} |",
        f"| Tool calls (completed, failed or blocked) | {sum(data['tools'].values())} |",
        f"| Blocked by guard | {data['blocked']} |", f"| Failed tool calls | {data['failures']} |",
        f"| Avg tool duration (ms) | {data['avg_duration_ms']} |",
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


def cmd_export(events: list[dict[str, Any]], args: argparse.Namespace, trace_dir: Path) -> int:
    data = summarize(_filter(events, args.work_item))
    if not data["events"]:
        print(f"No trace events for work item {args.work_item}.", file=sys.stderr)
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(scrub_paths(render_markdown(data, args.work_item), guard.REPO_ROOT))
    print(f"Wrote {out}")
    return 0


def main(argv: list[str], trace_dir: Path | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sdlc_trace.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", help="trace directory (default: SDLC_TRACE_DIR or .sdlc/traces)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("show"); p.add_argument("session"); p.add_argument("--tool"); p.add_argument("--output", action="store_true"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("summary"); p.add_argument("--work-item"); p.add_argument("--session"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("export"); p.add_argument("--work-item", required=True); p.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    directory = trace_dir or (Path(args.dir) if args.dir else trace.trace_root(guard.REPO_ROOT, os.environ))
    events = load_events(directory)
    handler = {"list": cmd_list, "show": cmd_show, "summary": cmd_summary, "export": cmd_export}[args.cmd]
    return handler(events, args, directory)
