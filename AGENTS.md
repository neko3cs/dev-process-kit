# AGENTS.md

## Development Rules

- When a release changes plugin contents, bump `version` to the same value in both `plugins/dev-process-kit/.claude-plugin/plugin.json` and `plugins/dev-process-kit/.codex-plugin/plugin.json`. Claude Code delivers an update only when the version changes, so new commits pushed under the old version never reach installed users. Codex (`codex plugin marketplace upgrade`, checked on 0.168.0) refreshes the cache even without a bump, so a missed bump breaks only Claude Code users and goes unnoticed.
- Do not set `version` on the marketplace entries. If both an entry and `plugin.json` set it, Claude Code uses the `plugin.json` value without warning.

## Implicit Constraints

- `.claude-plugin/marketplace.json` (Claude Code) and `.agents/plugins/marketplace.json` (Codex) are both intentional. Codex can read the Claude file as a legacy format, but OpenAI recommends `.agents/plugins/marketplace.json`. Do not delete either as a duplicate, and keep their plugin entries in sync.
- Codex uses the compatibility manifest `.codex-plugin/plugin.json` rather than the newer root `plugin.json` layout, because only the compatibility manifest was verified to install on Codex 0.168.0.
- Skills live once under `plugins/dev-process-kit/skills/` and both harnesses read them. Do not create per-harness copies.

## Commands

```sh
claude plugin validate .
claude plugin validate plugins/dev-process-kit
claude -p "/dev-process-kit:hello" --plugin-dir plugins/dev-process-kit
```

- When testing Codex installs, point `CODEX_HOME` at a temporary directory so that `codex plugin marketplace add` and `codex plugin add` don't write to the user's `~/.codex/config.toml`. `codex exec` cannot run slash commands; invoke skills as `$dev-process-kit:<skill>`.
