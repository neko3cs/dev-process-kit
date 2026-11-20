# AGENTS.md

## Development Rules

- When a release changes plugin contents, bump `version` to the same value in all three manifests: `plugins/dev-process-kit/.claude-plugin/plugin.json`, `plugins/dev-process-kit/.codex-plugin/plugin.json`, and `plugins/dev-process-kit/plugin.json`. Claude Code delivers an update only when the version changes, so new commits pushed under the old version never reach installed users. Codex (`codex plugin marketplace upgrade`, checked on 0.168.0) refreshes the cache even without a bump, and GitHub Copilot CLI (`copilot plugin update`, checked on 1.0.114) re-fetches the plugin on every update regardless of version, so a missed bump breaks only Claude Code users and goes unnoticed.
- Do not set `version` on the marketplace entries. If both an entry and `plugin.json` set it, Claude Code uses the `plugin.json` value without warning.
- Skills must not reference anything outside this plugin: other skills (such as `create-pullrequest`, `test-as-tdd`, `test-code`) or author-specific templates (such as `neko3cs/.github`). Do not replace such a reference with a hint at a specific method or an instruction to look for related skills either; that still steers how users work. Leave PR format, implementation technique, and testing to the user's repository rules and instructions.
- Refer to skills inside this plugin by their namespaced name (`dev-process-kit:design`, not `design`). Users may also have same-name skills from neko3cs/skills installed. GitHub Copilot CLI lists plugin skills without the namespace, and a same-name project or personal skill silently hides the plugin's skill; `/dev-process-kit:design` then does not reach the plugin's `design` (verified on 1.0.114).
- Do not hand the process core over to users as "their own method": a merged design PR freezes the spec, one implementation PR per Issue, pending decisions stay in Draft, and design changes found during implementation go to a separate design PR. The owner explicitly rejected treating these as user-specific.

## Implicit Constraints

- `.claude-plugin/marketplace.json` (Claude Code), `.agents/plugins/marketplace.json` (Codex), and `.github/plugin/marketplace.json` (GitHub Copilot CLI) are all intentional. Do not delete any of them as a duplicate, and keep their plugin entries in sync. Each harness has its own location and search order, and one harness reading another's file is incidental, so the owner chose one dedicated file per harness. Codex can read the Claude file as a legacy format, but OpenAI recommends `.agents/plugins/marketplace.json`. Copilot CLI 1.0.114 searches `marketplace.json`, `.plugin/marketplace.json`, `.github/plugin/marketplace.json`, then `.claude-plugin/marketplace.json`, and never `.agents/plugins/`. Claude Code 2.1.318 reads only `.claude-plugin/marketplace.json`, and Codex 0.168.0 ignores `marketplace.json`, `.plugin/`, and `.github/plugin/` (all verified).
- `plugins/dev-process-kit/plugin.json` is the Antigravity manifest (Agent Plugins spec, `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`). The schema sets `additionalProperties: false`, so add only keys the schema defines; harness-specific keys such as `skills` or `interface` belong in `.codex-plugin/plugin.json`.
- Codex 0.168.0 prefers the root `plugin.json` over `.codex-plugin/plugin.json` when both exist (verified: with only the root file's `version` changed, `codex plugin list` showed the root value). Keep `.codex-plugin/plugin.json` anyway, because it was the manifest verified to install on Codex before the root file was added.
- GitHub Copilot CLI 1.0.114 also prefers the root `plugin.json` and falls back to `.claude-plugin/plugin.json` only when the root file is missing (verified the same way with `copilot plugin list`).
- Skills live once under `plugins/dev-process-kit/skills/` and every harness reads them. Do not create per-harness copies.

## Commands

```sh
claude plugin validate .
claude plugin validate plugins/dev-process-kit
```

- When testing Codex installs, point `CODEX_HOME` at a temporary directory so that `codex plugin marketplace add` and `codex plugin add` don't write to the user's `~/.codex/config.toml`. `codex exec` cannot run slash commands; invoke skills as `$dev-process-kit:<skill>`.
- When testing GitHub Copilot CLI installs, point `COPILOT_HOME` at a temporary directory for the same reason. `copilot -p "/dev-process-kit:<skill> ..."` invokes a skill non-interactively. A marketplace added from a local path is loaded live from that directory (nothing is copied), so `copilot plugin update` cannot be tested that way, and `file://` URLs are rejected.
