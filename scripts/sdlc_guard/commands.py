"""Best-effort static analysis of shell commands for bash/sh/zsh (POSIX), PowerShell and cmd.exe.

This is a guardrail, not a sandbox: scripts, aliases or obfuscation can evade it. Git pre-commit, CI and
branch protection remain the final enforcement layer on every platform.
"""

from __future__ import annotations

import base64
import re
import shlex
from dataclasses import dataclass, field
from typing import Mapping

# Environment variables that only a human may set (overrides for gates / guard).
HUMAN_ONLY_OVERRIDES = ("RELEASE_APPROVAL", "SDLC_ALLOW_PROTECTED", "SDLC_GUARD_FAIL_OPEN")

_PREFIX_COMMANDS = {"sudo", "env", "command", "nohup", "time", "exec", "builtin", "nice"}
_POSIX_ALL_ARGS = {"rm", "rmdir", "unlink", "touch", "truncate", "tee", "shred", "mv", "chmod", "chown"}
_POSIX_LAST_ARG = {"cp", "install", "ln", "rsync", "scp"}
_POSIX_SKIP_FIRST = {"chmod", "chown"}
_PS_WRITE = {
    "set-content", "add-content", "clear-content", "out-file", "new-item", "remove-item", "move-item",
    "rename-item", "copy-item", "tee-object", "sc", "ac", "clc", "ni", "ri", "rm", "rmdir", "del", "erase",
    "rd", "mi", "move", "mv", "rni", "ren", "cpi", "copy", "cp", "tee",
}
_PS_COPY_LIKE = {"copy-item", "cpi", "copy", "cp", "move-item", "mi", "move", "mv"}
_PS_PATH_PARAMS = {"-path", "-literalpath", "-filepath", "-destination", "-pspath"}
_PS_SWITCHES = {
    "-force", "-recurse", "-whatif", "-confirm", "-nonewline", "-append", "-passthru", "-noclobber",
    "-verbose", "-container", "-asjob", "-erroraction",
}
_CMD_WRITE_ALL = {"del", "erase", "rd", "rmdir", "ren", "rename"}
_CMD_WRITE_LAST = {"copy", "move", "xcopy", "robocopy"}
_GIT_PATH_SUBCOMMANDS = {"checkout", "restore", "rm", "mv"}

_REDIRECT_RE = re.compile(r"^(?:\d|&|\*)?>>?(.*)$")
# Assignments are only counted where they take effect: at the start of a command segment, not inside
# quoted arguments or heredoc bodies.
_PS_ASSIGN_RE = re.compile(r"^\s*\$env:([A-Za-z_][A-Za-z0-9_]*)\s*=|SetEnvironmentVariable\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
_PS_SET_ITEM_RE = re.compile(r"^\s*(?:set-item|si|new-item|ni)\s+(?:-path\s+)?env:([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
_CMD_ASSIGN_RE = re.compile(r"^\s*(?:set|setx)\s+\"?([A-Za-z_][A-Za-z0-9_]*)[=\s]", re.IGNORECASE)
_POSIX_ASSIGN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=")
_POSIX_EXPORTERS = {"export", "declare", "typeset", "readonly", "local"}
# A shell interpreter anywhere in command position on the heredoc line (start, or after | ; & ( xargs sudo env).
_SHELL_HEREDOC_RE = re.compile(r"(?:^|[|;&(]|\bxargs|\bsudo|\benv)\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*(?:\S*/)?(?:ba|z|da|k)?sh\b")
_HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def _strip_heredocs(command: str) -> str:
    """Drop heredoc bodies (data, not commands) so text inside them is never analysed as commands."""
    out: list[str] = []
    terminator: str | None = None
    strip_tabs = False
    keep_body = False
    for line in command.split("\n"):
        if terminator is not None:
            check = line.lstrip("\t") if strip_tabs else line
            if check.rstrip() == terminator:
                terminator = None
            elif keep_body:
                out.append(line)
            continue
        out.append(line)
        m = _HEREDOC_RE.search(line)
        if m:
            terminator = m.group(2)
            strip_tabs = "<<-" in line[m.start() : m.start() + 4]
            # A heredoc fed to a shell interpreter is executable code, so it must still be analysed.
            keep_body = bool(_SHELL_HEREDOC_RE.search(line))
    return "\n".join(out)
_PROD_RE = re.compile(r"\bprod(?:uction)?\b", re.IGNORECASE)


@dataclass
class CommandFacts:
    family: str
    raw: str
    segments: list[list[str]] = field(default_factory=list)
    write_targets: set[str] = field(default_factory=set)
    path_tokens: set[str] = field(default_factory=set)
    assignments: set[str] = field(default_factory=set)


def _base(token: str) -> str:
    name = token.replace("\\", "/").rsplit("/", 1)[-1].casefold()
    for ext in (".exe", ".cmd", ".bat"):
        if name.endswith(ext):
            return name[: -len(ext)]
    return name


def split_segments(command: str, family: str) -> list[str]:
    """Split on ; && || | & and newlines, outside quotes, honouring each shell's escape character."""
    escape = {"posix": "\\", "powershell": "`", "cmd": "^"}[family]
    quotes = {"'", '"'} if family != "cmd" else {'"'}
    segs: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(command):
        ch = command[i]
        if ch == escape and quote != "'" and i + 1 < len(command):
            buf.append(ch + command[i + 1])
            i += 2
            continue
        if quote:
            if ch == quote:
                quote = None
            buf.append(ch)
        elif ch in quotes:
            quote = ch
            buf.append(ch)
        elif ch in ";|&\n":
            segs.append("".join(buf))
            buf = []
            if i + 1 < len(command) and command[i + 1] == ch and ch in "|&":
                i += 1
        else:
            buf.append(ch)
        i += 1
    segs.append("".join(buf))
    return [s.strip() for s in segs if s.strip()]


def _windows_tokens(segment: str, family: str) -> list[str]:
    """Quote-aware whitespace split that keeps backslashes (Windows paths) intact."""
    escape = "`" if family == "powershell" else "^"
    quotes = {"'", '"'} if family == "powershell" else {'"'}
    tokens: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    has_token = False
    i = 0
    while i < len(segment):
        ch = segment[i]
        if ch == escape and quote != "'" and i + 1 < len(segment):
            buf.append(segment[i + 1])
            has_token = True
            i += 2
            continue
        if quote:
            if ch == quote:
                quote = None
            else:
                buf.append(ch)
        elif ch in quotes:
            quote = ch
            has_token = True
        elif ch.isspace():
            if has_token:
                tokens.append("".join(buf))
                buf, has_token = [], False
        else:
            buf.append(ch)
            has_token = True
        i += 1
    if has_token:
        tokens.append("".join(buf))
    return tokens


def tokenize(segment: str, family: str) -> list[str]:
    if family == "posix":
        try:
            return shlex.split(segment, posix=True)
        except ValueError:
            return segment.split()
    return _windows_tokens(segment, family)


def detect_family(tool_name: str, command: str, *, windows_host: bool) -> tuple[str, str]:
    """Return (family, inner_command), unwrapping powershell -Command / cmd /c / bash -c wrappers."""
    family = "powershell" if tool_name.casefold() in {"powershell", "pwsh"} else "posix"
    inner = command
    for _ in range(3):
        tokens = tokenize(inner, family if family != "posix" or not windows_host else "posix")
        if not tokens:
            break
        head = _base(tokens[0])
        rest = tokens[1:]
        if head in {"powershell", "pwsh"}:
            new = _unwrap_powershell(rest)
            if new is None:
                break
            family, inner = "powershell", new
        elif head == "cmd":
            idx = next((i for i, t in enumerate(rest) if t.casefold() in {"/c", "/k"}), None)
            if idx is None:
                break
            family, inner = "cmd", " ".join(rest[idx + 1 :])
        elif head in {"bash", "sh", "zsh", "dash"}:
            idx = next((i for i, t in enumerate(rest) if re.fullmatch(r"-[a-z]*c[a-z]*", t)), None)
            if idx is None or idx + 1 >= len(rest):
                break
            family, inner = "posix", rest[idx + 1]
        else:
            break
    return family, inner


def _unwrap_powershell(args: list[str]) -> str | None:
    for i, tok in enumerate(args):
        low = tok.casefold()
        if low in {"-encodedcommand", "-enc", "-e", "-ec"} and i + 1 < len(args):
            try:
                return base64.b64decode(args[i + 1]).decode("utf-16-le")
            except (ValueError, UnicodeDecodeError):
                return args[i + 1]
        if low in {"-command", "-c"} or (low.startswith("-com") and "-command".startswith(low)):
            return " ".join(args[i + 1 :])
    return None


def _positional(tokens: list[str], family: str) -> list[str]:
    out: list[str] = []
    skip_next = False
    for i, tok in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue
        if family == "powershell" and tok.startswith("-") and len(tok) > 1:
            low = tok.split(":", 1)[0].casefold()
            if ":" not in tok and low not in _PS_SWITCHES and i + 1 < len(tokens):
                skip_next = True
            continue
        if family == "cmd" and re.fullmatch(r"/[A-Za-z?\-]+(:\S*)?", tok):
            continue
        if family == "posix" and tok.startswith("-") and len(tok) > 1:
            continue
        out.append(tok)
    return out


def _ps_param_values(tokens: list[str], names: set[str]) -> list[str]:
    vals: list[str] = []
    for i, tok in enumerate(tokens):
        name, _, inline = tok.partition(":")
        if name.casefold() in names:
            if inline:
                vals.append(inline)
            elif i + 1 < len(tokens):
                vals.append(tokens[i + 1])
    return vals


def _strip_prefixes(tokens: list[str], family: str) -> tuple[list[str], set[str]]:
    """Remove leading env assignments / wrapper commands; also return the variable names assigned."""
    assigned: set[str] = set()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        m = _POSIX_ASSIGN_RE.match(tok) if family == "posix" else None
        if m:
            assigned.add(m.group(1).upper())
            i += 1
        elif family == "posix" and _base(tok) in _PREFIX_COMMANDS:
            i += 1
        elif family == "powershell" and tok == "&":
            i += 1
        else:
            break
    rest = tokens[i:]
    if family == "posix" and rest and _base(rest[0]) in _POSIX_EXPORTERS:
        for tok in rest[1:]:
            m = _POSIX_ASSIGN_RE.match(tok)
            if m:
                assigned.add(m.group(1).upper())
    return rest, assigned


def analyze(command: str, family: str) -> CommandFacts:
    facts = CommandFacts(family=family, raw=command)
    if family == "posix":
        command = _strip_heredocs(command)

    for seg in split_segments(command, family):
        if family == "powershell":
            for rx in (_PS_ASSIGN_RE, _PS_SET_ITEM_RE):
                m = rx.search(seg)
                if m:
                    facts.assignments.add(next(g for g in m.groups() if g).upper())
        elif family == "cmd":
            m = _CMD_ASSIGN_RE.match(seg)
            if m:
                facts.assignments.add(m.group(1).upper())
        raw_tokens = tokenize(seg, family)
        tokens: list[str] = []
        i = 0
        while i < len(raw_tokens):
            tok = raw_tokens[i]
            m = _REDIRECT_RE.match(tok)
            if m and tok[0] in "0123456789&*>":
                target = m.group(1) or (raw_tokens[i + 1] if i + 1 < len(raw_tokens) else "")
                if not m.group(1):
                    i += 1
                if target and not target.startswith("&") and target.casefold() not in {"/dev/null", "nul", "$null"}:
                    facts.write_targets.add(target)
                i += 1
                continue
            tokens.append(tok)
            i += 1

        tokens, assigned = _strip_prefixes(tokens, family)
        facts.assignments |= assigned
        if not tokens:
            continue
        facts.segments.append(tokens)

        for tok in tokens[1:]:
            if "=" in tok and tok.startswith("-"):
                facts.path_tokens.add(tok.split("=", 1)[1])
            elif family == "powershell" and tok.startswith("-") and ":" in tok:
                facts.path_tokens.add(tok.split(":", 1)[1])
            elif "=" in tok and re.fullmatch(r"[A-Za-z_]+=.+", tok):
                facts.path_tokens.add(tok.split("=", 1)[1])
            elif not tok.startswith("-"):
                facts.path_tokens.add(tok)

        facts.write_targets.update(_write_targets(tokens, family))
    facts.path_tokens |= facts.write_targets
    return facts


def _write_targets(tokens: list[str], family: str) -> list[str]:
    cmd = _base(tokens[0])
    args = tokens[1:]
    pos = _positional(args, family)
    if family == "powershell":
        if cmd not in _PS_WRITE:
            return []
        params = _ps_param_values(args, _PS_PATH_PARAMS)
        if cmd in _PS_COPY_LIKE:
            dest = _ps_param_values(args, {"-destination"})
            return dest or pos[-1:]
        return params + pos
    if family == "cmd":
        if cmd in _CMD_WRITE_ALL:
            return pos
        if cmd in _CMD_WRITE_LAST:
            return pos[-1:]
        return []
    # POSIX
    if cmd in _POSIX_SKIP_FIRST:
        return pos[1:]
    if cmd in _POSIX_ALL_ARGS:
        return pos
    if cmd in _POSIX_LAST_ARG:
        return pos[-1:]
    if cmd in {"sed", "perl"} and any(a == "-i" or a.startswith("-i") or a == "--in-place" for a in args):
        return pos[1:]
    if cmd == "dd":
        return [a[3:] for a in args if a.startswith("of=")]
    if cmd == "git" and args:
        sub = _git_subcommand(args)
        if sub and sub[0] in _GIT_PATH_SUBCOMMANDS:
            return [a for a in sub[1] if not a.startswith("-") and a != "--"]
    return []


def _git_subcommand(args: list[str]) -> tuple[str, list[str]] | None:
    i = 0
    while i < len(args):
        a = args[i]
        if a in {"-C", "-c", "--git-dir", "--work-tree"}:
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        return a.casefold(), args[i + 1 :]
    return None


def dangerous_command_reasons(
    facts: CommandFacts, env: Mapping[str, str], *, allow_force_with_lease: bool
) -> list[str]:
    reasons: list[str] = []
    for name in sorted(facts.assignments & set(HUMAN_ONLY_OVERRIDES)):
        reasons.append(f"Agents may not set human-only override {name} inline - a human must export it in their own shell.")

    for tokens in facts.segments:
        head = _base(tokens[0])
        joined = " ".join(tokens)
        if head == "git":
            sub = _git_subcommand(tokens[1:])
            if sub:
                name, rest = sub
                low = [t.casefold() for t in rest]
                if name == "push":
                    lease = any(t.startswith("--force-with-lease") or t.startswith("--force-if-includes") for t in low)
                    hard = any(
                        t == "--force" or re.fullmatch(r"-[a-z]*f[a-z]*", t) or (t.startswith("+") and len(t) > 1)
                        for t in low
                    )
                    if hard or (lease and not allow_force_with_lease):
                        reasons.append("Force push is prohibited by repository guardrails.")
                if "--no-verify" in low or (name == "commit" and any(re.fullmatch(r"-[a-z]*n[a-z]*", t) for t in low)):
                    reasons.append("Bypassing Git hooks (--no-verify) is prohibited.")
                if name == "config" and "core.hookspath" in low:
                    key_idx = low.index("core.hookspath")
                    if any(t.startswith("--unset") for t in low) or (
                        "--get" not in low and len(low) > key_idx + 1
                    ):
                        reasons.append("Changing core.hooksPath would disable repository hooks.")
        if "deploy" in joined.casefold() and _PROD_RE.search(joined) and not env.get("RELEASE_APPROVAL"):
            reasons.append("Production deploy requires RELEASE_APPROVAL authorization (Gate 3).")
    return list(dict.fromkeys(reasons))
