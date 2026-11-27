# Changelog

All notable changes to this project are documented here. This file is maintained by
[release-please](https://github.com/googleapis/release-please) from [Conventional Commits](https://www.conventionalcommits.org/).

## [0.3.1](https://github.com/chakrits/ai-agent-framework/compare/v0.3.0...v0.3.1) (2026-11-27)


### Bug Fixes

* **agents:** align role prompts with routes and contracts ([f120f49](https://github.com/chakrits/ai-agent-framework/commit/f120f494dab05b36b4239710849d7f1e4eca3775))

## [0.3.0](https://github.com/chakrits/ai-agent-framework/compare/v0.2.0...v0.3.0) (2026-11-22)


### Features

* add antigravity hooks, orchestrator v1 persistence, worktree/docker, live evals and INT-001 pilot after review feedback ([5ae1169](https://github.com/chakrits/ai-agent-framework/commit/5ae1169cfb6e44b1204af7478c9a15db948f89ff))
* **validator:** add --require-digest and --digest-file to validate_work_item ([ee5a055](https://github.com/chakrits/ai-agent-framework/commit/ee5a055cb5e1109fe0677cd85b62106958d5eaef))


### Bug Fixes

* resolve PLAN-006 review rounds 2-6 findings across orchestrator, evals, docker and validators ([16db38c](https://github.com/chakrits/ai-agent-framework/commit/16db38c533a7acc57d34c5c6c68d290d92c42d52))
* **validator:** ignore headings in code fences and require real section content ([3fce192](https://github.com/chakrits/ai-agent-framework/commit/3fce19298fd934dcab4b5fcea6cdefb164e48c1f))
* **validator:** reject empty digest sections and require-flags without work dir ([7872de4](https://github.com/chakrits/ai-agent-framework/commit/7872de481d4b7460596a590f3ad9eba292e33fdd))

## [0.2.0](https://github.com/chakrits/ai-agent-framework/compare/v0.1.0...v0.2.0) (2026-11-21)


### Features

* trace v1.1 with model/effort, local timestamps, more hook events and level control ([c78aed9](https://github.com/chakrits/ai-agent-framework/commit/c78aed92ad498b7c2ebc415d60a18aac485a04a1))

## 0.1.0 (2026-11-21)

### Features

* AI-native SDLC framework: canonical `.agents/` core, thin Claude Code / Codex / Antigravity adapters, artifact contracts, dynamic routing
* Cross-platform guardrails (Windows, macOS, Linux, WSL): PreToolUse guard, path normalization, bash/PowerShell/cmd command analysis, SessionStart doctor, pre-commit gate
* Agent trace: local, redacted JSONL record of prompts, commands, outputs and guard decisions, with a `traces` CLI
* Versioning with release-please and Conventional Commits enforcement
