# Skill Regression Evaluations (`evals/`)

This directory contains regression evaluation scenarios for `dev-process-kit:issue`, `dev-process-kit:design`, and `dev-process-kit:implement`. Each scenario tests a key decision branch in `SKILL.md` and `references/` so that edits to skill instructions do not silently break stop conditions, PR conventions, or workflow rules.

## Structure

- `scenarios/issue.json` — Scenarios for `dev-process-kit:issue`
- `scenarios/design.json` — Scenarios for `dev-process-kit:design`
- `scenarios/implement.json` — Scenarios for `dev-process-kit:implement`
- `lib/mock-gh.py` — Fixture-driven mock for `gh` that responds from `gh-state.json` and logs every invocation to `gh-calls.jsonl`
- `validate.py` — Validates scenario JSON files and lists all scenarios
- `run.sh` — Builds an isolated temporary git repository + bare `origin` remote + mock `gh` for each scenario, runs the selected harness (`claude`, `codex`, or `copilot`), runs automated assertions, and prints the manual review checklist

## Usage

Validate scenario definitions and list all scenarios:

```sh
python3 evals/validate.py
evals/run.sh --list
```

Run a single scenario, one skill's scenarios, or all scenarios:

```sh
evals/run.sh --harness claude --scenario implement-no-design-docs
evals/run.sh --harness claude --skill implement
evals/run.sh --harness claude --all
```

Other supported harnesses:

```sh
evals/run.sh --harness codex --scenario design-multi-req-issue-stop
evals/run.sh --harness copilot --scenario issue-multiple-requirements
```

Prepare an isolated workspace without invoking a harness (for interactive inspection or manual runs):

```sh
evals/run.sh --setup-only --scenario implement-tbd-remaining
```

## Reviewing Results

Each run writes artifacts under `${TMPDIR:-/tmp}/dev-process-kit-evals/<timestamp>/<scenario-id>/`:

- `response.txt` — Final response from the agent
- `gh-calls.jsonl` — Every `gh` command executed (including `--body` / `--body-file` contents)
- `gh-state.json` — Final mock GitHub state (created Issues/PRs/comments)
- `repo/` — Working git repository after the run

`run.sh` automatically verifies deterministic assertions under `expected.checks` (`gh_must_call`, `gh_must_not_call`, `git_must_not_push`, `git_branch_must_stay`, `git_must_not_modify`), and prints the `expected.must` / `expected.must_not` checklist so you can verify semantic behavior in `response.txt`, `gh-calls.jsonl`, and `repo/`.

## Adding a Scenario

1. Add a scenario entry to `evals/scenarios/<skill>.json` with `id`, `title`, `branch`, `prompt_args`, `setup`, and `expected`.
2. Run `python3 evals/validate.py` to confirm the schema and regexes are valid.
3. Run the new scenario with `evals/run.sh --harness claude --scenario <id>` to confirm it behaves as expected.
