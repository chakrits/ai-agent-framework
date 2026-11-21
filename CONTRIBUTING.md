# Contributing

Thanks for helping improve the AI-Native SDLC Agent Framework. Humans and AI agents follow the same rules.

## 1. Set up (Windows / macOS / Linux / WSL)

Requires Python 3.10+ and Git (Windows: Git for Windows).

```bash
python3 scripts/setup.py        # Windows: py -3 scripts\setup.py
```

This sets `core.hooksPath=.githooks` and runs the environment doctor (`scripts/doctor.py`).

## 2. Rules of the road

1. Read [AGENTS.md](AGENTS.md) and the [constitution](docs/operating-model/constitution.md) first. Classify the work with the [core bootloader](docs/workflow/core-bootloader.md).
2. **Spec before code** for features and behavior changes (`intent.md` → `spec.md`).
3. Agents never weaken QA test oracles and never approve or merge their own work.
4. Run the checks before you push:
   ```bash
   python3 scripts/sync-adapters.py --check && python3 scripts/validate-context-budget.py \
     && python3 scripts/validate-contracts.py --check-defaults && python3 evals/run_evals.py \
     && python3 -m unittest discover -s tests
   ```
5. Do not bypass hooks (`--no-verify`) or the guard. If the guard blocks something legitimate, change `scripts/sdlc_guard/policy.json` through a Framework Change.

## 3. Commits: Conventional Commits

Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/) (enforced by the `commit-msg` hook):

```text
<type>(<optional scope>)!: <subject>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
`feat` bumps the minor version, `fix` bumps the patch version, and `!` or a `BREAKING CHANGE:` footer marks a breaking change (while on 0.x, breaking changes bump the minor version).

## 4. Protected files (Framework Changes)

Governance files (constitution, contracts, guard, hooks, CI gates; see `protected_globs` in `scripts/sdlc_guard/policy.json`) need a human maintainer. Pre-commit blocks staging them unless the maintainer sets the override for that single commit:

```bash
SDLC_ALLOW_PROTECTED=1 git commit
```

Agents cannot set this variable (nor `RELEASE_APPROVAL` or `SDLC_GUARD_FAIL_OPEN`) in a command they run; that is deliberate. Mentioning them in quoted text or heredoc data is fine.

## 5. Agent traces (local debugging and audit)

Hooks record what agents asked, ran and received into `.sdlc/traces/` (local, gitignored, secrets redacted, outputs truncated).

```bash
python3 scripts/sdlc_trace.py list
python3 scripts/sdlc_trace.py show <session-prefix> --output
python3 scripts/sdlc_trace.py summary --work-item INT-001
python3 scripts/sdlc_trace.py export --work-item INT-001 --out work/INT-001/trace-summary.md
```

Full guide (Thai): [docs/guides/agent-trace-manual.md](docs/guides/agent-trace-manual.md). Levels: `off`, `info` (default), `debug`. Precedence: env `SDLC_TRACE_LEVEL` > `.sdlc/trace.json` > default.

```bash
python3 scripts/sdlc_trace.py config show
python3 scripts/sdlc_trace.py config set level debug --for 30m   # temporary, reverts itself (agents may run this; max 120m)
python3 scripts/sdlc_trace.py config set level off               # human only (interactive terminal)
```

Also settable in your shell: `SDLC_TRACE_TZ=local|utc`, `SDLC_TRACE_RETENTION_DAYS` (default 30), `SDLC_WORK_ITEM=INT-001`.
Never commit raw traces; commit only an exported, redacted summary as evidence.

## 6. Releases

Versions follow [SemVer](https://semver.org/) and are managed by [release-please](https://github.com/googleapis/release-please): merging to `main` updates a Release PR (`version.txt` + `CHANGELOG.md`); merging that PR creates the `vX.Y.Z` tag and GitHub Release. Do not edit `version.txt` or `CHANGELOG.md` by hand.

**First release (one-time, maintainer):** release-please measures changes from the last release tag, and `0.1.0` is already recorded in `version.txt`, `.release-please-manifest.json` and `CHANGELOG.md`. So, in this order:
1. Leave *Settings → Actions → General → "Allow GitHub Actions to create and approve pull requests"* **off**, commit and push (the first release-please run then fails harmlessly instead of proposing a wrong version).
2. Create the `v0.1.0` tag and GitHub Release on that commit (`gh release create v0.1.0 --title v0.1.0 --notes-file CHANGELOG.md`).
3. Turn the setting on. From then on release-please opens Release PRs relative to `v0.1.0`.

Exported trace summaries (`sdlc_trace.py export`) replace the repository path with `<repo>` and your home directory with `~`; still skim them before committing.

## 7. License

By contributing you agree that your contributions are licensed under the [MIT License](LICENSE).
