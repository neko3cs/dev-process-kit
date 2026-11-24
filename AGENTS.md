# AGENTS.md

## Development Rules

- When a release changes plugin contents, bump `version` to the same value in all three manifests: `plugins/dev-process-kit/.claude-plugin/plugin.json`, `plugins/dev-process-kit/.codex-plugin/plugin.json`, and `plugins/dev-process-kit/plugin.json`. Claude Code delivers an update only when the version changes, so new commits pushed under the old version never reach installed users. Codex (`codex plugin marketplace upgrade`, checked on 0.168.0) refreshes the cache even without a bump, and GitHub Copilot CLI (`copilot plugin update`, checked on 1.0.114) re-fetches the plugin on every update regardless of version, so a missed bump breaks only Claude Code users and goes unnoticed.
- Do not set `version` on the marketplace entries. If both an entry and `plugin.json` set it, Claude Code uses the `plugin.json` value without warning.
- Skills must not reference anything outside this plugin: other skills (such as `create-pullrequest`, `test-as-tdd`, `test-code`) or author-specific templates (such as `neko3cs/.github`). Do not replace such a reference with a hint at a specific method or an instruction to look for related skills either; that still steers how users work. When the process needs a method, define it inside the plugin, as `implement/references/unit-test.md` does for TDD; what is forbidden is naming or linking an outside skill, not having the content. Leave PR format, test frameworks and tools, and quality gates to the user's repository rules and instructions.
- Refer to skills inside this plugin by their namespaced name (`dev-process-kit:design`, not `design`). Users may also have same-name skills from neko3cs/skills installed. GitHub Copilot CLI lists plugin skills without the namespace, and a same-name project or personal skill silently hides the plugin's skill; `/dev-process-kit:design` then does not reach the plugin's `design` (verified on 1.0.114).
- Do not hand the process core over to users as "their own method": a merged design PR freezes the spec, one implementation PR per Issue, pending decisions stay in Draft, an external-spec problem found during implementation (anything written in the design documents) stops it and goes to a separate design PR that the user starts with `dev-process-kit:design`, internal design the documents do not cover is decided in unit tests without stopping, a spec change the user asks for mid-implementation becomes a new Issue while the current one finishes under the frozen spec, and the definitions of unit, integration, and scenario tests in `implement/references/` (unit tests are written before the code with TDD; integration and scenario tests usually after it; scenario tests are excluded from coverage). The owner explicitly rejected treating these as user-specific; leaving test practice to users was dropped because quality then varied from session to session.
- All three skills run only when the user invokes them by name: keep `disable-model-invocation: true` in each `SKILL.md` and `policy.allow_implicit_invocation: false` in each `agents/openai.yaml` (Codex). The owner does not want the process to start in repositories that do not use it (Issue #27).
- Skills must not invoke each other or follow another skill's procedure in its place; `implement` stops and asks the user to run `dev-process-kit:design` instead of writing design documents. Claude Code 2.1.330 refuses a Skill tool call to a skill with `disable-model-invocation: true` and tells the model not to replicate it by other means. The owner also rejected sharing design's procedure through a reference file, because design documents should change only when the user knows the external spec is changing.
- `README.md` and `docs/*.md` are written in English and are the source of truth; their Japanese versions are `README.ja.md` and `docs/*.ja.md`. When you change a page in either language, update the other language in the same PR. This intentionally overrides the global instruction that `README.md` must be Japanese: the owner chose English as the source for this repository.

## Implicit Constraints

- `.claude-plugin/marketplace.json` (Claude Code), `.agents/plugins/marketplace.json` (Codex), and `.github/plugin/marketplace.json` (GitHub Copilot CLI) are all intentional. Do not delete any of them as a duplicate, and keep their plugin entries in sync. Each harness has its own location and search order, and one harness reading another's file is incidental, so the owner chose one dedicated file per harness. Codex can read the Claude file as a legacy format, but OpenAI recommends `.agents/plugins/marketplace.json`. Copilot CLI 1.0.114 searches `marketplace.json`, `.plugin/marketplace.json`, `.github/plugin/marketplace.json`, then `.claude-plugin/marketplace.json`, and never `.agents/plugins/`. Claude Code 2.1.318 reads only `.claude-plugin/marketplace.json`, and Codex 0.168.0 ignores `marketplace.json`, `.plugin/`, and `.github/plugin/` (all verified).
- `plugins/dev-process-kit/plugin.json` is the Antigravity manifest (Agent Plugins spec, `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`). The schema sets `additionalProperties: false`, so add only keys the schema defines; harness-specific keys such as `skills` or `interface` belong in `.codex-plugin/plugin.json`.
- Codex 0.168.0 prefers the root `plugin.json` over `.codex-plugin/plugin.json` when both exist (verified: with only the root file's `version` changed, `codex plugin list` showed the root value). Keep `.codex-plugin/plugin.json` anyway, because it was the manifest verified to install on Codex before the root file was added.
- GitHub Copilot CLI 1.0.114 also prefers the root `plugin.json` and falls back to `.claude-plugin/plugin.json` only when the root file is missing (verified the same way with `copilot plugin list`).
- Skills live once under `plugins/dev-process-kit/skills/` and every harness reads them. Do not create per-harness copies.

## Commands

**Required before opening a pull request:** run all of the following checks locally and confirm they pass before opening or marking a PR ready for review:

```sh
.github/scripts/check-plugin-manifests.sh origin/main
claude plugin validate .
claude plugin validate plugins/dev-process-kit
python3 evals/validate.py
evals/run.sh --setup-only --all
```

When a PR changes files under `plugins/dev-process-kit/skills/`, also run the regression evaluation scenarios for every modified skill (see below) before opening the PR.

- When testing Codex installs, point `CODEX_HOME` at a temporary directory so that `codex plugin marketplace add` and `codex plugin add` don't write to the user's `~/.codex/config.toml`. `codex exec` cannot run slash commands; invoke skills as `$dev-process-kit:<skill>`.
- When testing GitHub Copilot CLI installs, point `COPILOT_HOME` at a temporary directory for the same reason. `copilot -p "/dev-process-kit:<skill> ..."` invokes a skill non-interactively. A marketplace added from a local path is loaded live from that directory (nothing is copied), so `copilot plugin update` cannot be tested that way, and `file://` URLs are rejected.

## Skill Regression Evaluations

Regression scenarios for `issue`, `design`, and `implement` live under `evals/scenarios/*.json`. Running them is **required before opening a PR that modifies `plugins/dev-process-kit/skills/`** (run `--skill <skill>` for each modified skill, or `--all` before a release) to catch regressions in stop conditions, PR handling, and workflow rules:

```sh
# Validate scenario definitions and inspect the list
python3 evals/validate.py
evals/run.sh --list

# Run scenarios for a changed skill, a single scenario, or the full suite
evals/run.sh --harness claude --skill implement
evals/run.sh --harness claude --scenario implement-no-design-docs
evals/run.sh --harness claude --all

# Also supports --harness codex and --harness copilot (uses isolated temp homes)
evals/run.sh --harness codex --skill design
```

- `evals/run.sh` builds an isolated temporary git repository with a bare `origin` remote and a fixture-driven mock `gh` (`evals/lib/mock-gh.py`) under `${TMPDIR:-/tmp}/dev-process-kit-evals/`, so runs never touch real GitHub Issues/PRs or this repository. Use `--setup-only` to prepare the isolated workspace for manual interactive testing.
- Confirm that all automated checks (`expected.checks`) pass, and review `response.txt` and `gh-calls.jsonl` against the `expected.must` / `expected.must_not` checklist printed by `run.sh`.
- When adding a new branch or stop condition to a `SKILL.md`, add a corresponding regression scenario to `evals/scenarios/<skill>.json` and verify it with `python3 evals/validate.py`.
