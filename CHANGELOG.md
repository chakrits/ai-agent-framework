# Changelog

All notable changes to this project are documented here. This file is maintained by
[release-please](https://github.com/googleapis/release-please) from [Conventional Commits](https://www.conventionalcommits.org/).

## [0.2.0](https://github.com/chakrits/ai-agent-framework/compare/v0.1.0...v0.2.0) (2026-11-21)


### Features

* trace v1.1 with model/effort, local timestamps, more hook events and level control ([c78aed9](https://github.com/chakrits/ai-agent-framework/commit/c78aed92ad498b7c2ebc415d60a18aac485a04a1))

## 0.1.0 (2026-11-21)

### Features

* AI-native SDLC framework: canonical `.agents/` core, thin Claude Code / Codex / Antigravity adapters, artifact contracts, dynamic routing
* Cross-platform guardrails (Windows, macOS, Linux, WSL): PreToolUse guard, path normalization, bash/PowerShell/cmd command analysis, SessionStart doctor, pre-commit gate
* Agent trace: local, redacted JSONL record of prompts, commands, outputs and guard decisions, with a `traces` CLI
* Versioning with release-please and Conventional Commits enforcement
