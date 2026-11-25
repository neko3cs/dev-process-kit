# Getting Started

English | [日本語](getting-started.ja.md)

This guide installs dev-process-kit and takes one request from an Issue all the way to a merged implementation PR. For the thinking behind the phases, see [Philosophy](philosophy.md); for details on each skill, see the [Skill reference](skills.md).

## Prerequisites

- Your project is a GitHub repository.
- [GitHub CLI (`gh`)](https://cli.github.com/) is installed and authenticated with `gh auth login`.
- You can use one of the supported harnesses: Claude Code, Codex, GitHub Copilot CLI, or Antigravity.

## The flow at a glance

After installation, the phases run from top to bottom. Phases marked "—" are done by a person. Each phase name links to its step on this page.

| No. | Phase | Skill | What happens |
| :--- | :--- | :--- | :--- |
| 1 | [File](#2-file-the-request-as-an-issue) | `issue` | The request is recorded in an Issue. What to build and the acceptance criteria are not decided here |
| 2 | [Design](#3-open-a-design-pr) | `design` | The Issue is designed into four documents and a design PR is opened. The documents are written as finished work, and choices made on undecided points are asked about in PR comments |
| 3 | [Design agreement](#4-review-and-merge-the-design-pr-your-part) | — | A person reviews and merges the design PR. The merge means the specification is agreed and frozen |
| 4 | [Implementation](#5-open-an-implementation-pr) | `implement` | Only the agreed design documents are implemented, with one implementation PR per Issue. The PR stays in Draft while a decision is pending |
| 5 | [Acceptance testing](#6-run-acceptance-tests-and-merge-the-implementation-pr-your-part) | — | A person runs acceptance tests against the acceptance criteria in `requirements.md` and decides GO / NO-GO. NO-GO sends the work back to implementation |
| 6 | [Implementation agreement](#6-run-acceptance-tests-and-merge-the-implementation-pr-your-part) | — | A person reviews and merges the implementation PR. The merge completes the Issue |

## 1. Install

Add the marketplace for your harness, then install the plugin.

```sh
# Claude Code
claude plugin marketplace add neko3cs/dev-process-kit
claude plugin install dev-process-kit@dev-process-kit

# Codex
codex plugin marketplace add neko3cs/dev-process-kit
codex plugin add dev-process-kit@dev-process-kit

# GitHub Copilot CLI
copilot plugin marketplace add neko3cs/dev-process-kit
copilot plugin install dev-process-kit@dev-process-kit

# Antigravity (AGY CLI 1.3.3 or later)
agy plugin install https://github.com/neko3cs/dev-process-kit/plugins/dev-process-kit
```

How you invoke a skill depends on the harness.

| Harness | Example |
| :--- | :--- |
| Claude Code, GitHub Copilot CLI | `/dev-process-kit:issue` |
| Codex | `$dev-process-kit:issue` |

The examples below use the Claude Code form. Each skill runs only when you call it by name. A general request such as "create an issue" or "fix #12" does not start it, so nothing happens in a repository that does not use this process.

## 2. File the request as an Issue

Describe what you want, as it is.

```text
/dev-process-kit:issue Make overdue tasks stand out in the task list
```

`dev-process-kit:issue` creates the Issue following the repository's Issue templates. Without a template, it writes the body under three headings: a description, the motivation and background, and the acceptance criteria. For anything undecided, it picks the most reasonable content and writes it as the request, without assumption markers. It does not stop to ask; it asks in an Issue comment whether that content is right.

You use the number of the new Issue (#12 here) in the next phase.

## 3. Open a design PR

```text
/dev-process-kit:design 12
```

`dev-process-kit:design` reads the Issue, creates or updates `requirements.md`, `specification.md`, `architecture.md`, and `tests.md`, and opens a design PR that contains only design documents. In a repository with no design documents yet, it creates all four from templates.

The design documents are written as finished work. For undecided points, the skill picks the most reasonable option and writes it as the specification, with no assumption or unapproved markers, then asks in design PR comments whether that choice is right. Answers are reflected by rewriting the relevant sections, so merging the design PR means everything written in it is agreed.

## 4. Review and merge the design PR (your part)

Read the design PR and answer the question comments. If something needs changing, leave review comments and ask `dev-process-kit:design` again.

```text
Address the review comments on the design PR
```

When you are satisfied, merge the design PR. **This merge means the specification is agreed and frozen.**

## 5. Open an implementation PR

```text
/dev-process-kit:implement 12
```

`dev-process-kit:implement` works from the merged design documents: it builds parts test-first with unit tests (TDD), verifies the specification and business requirements with integration and scenario tests, and opens one implementation PR per Issue. The PR body contains `Closes #12` and the tests that correspond to each acceptance criterion.

If the external specification in the design documents has a gap or an error, `dev-process-kit:implement` stops. It turns the implementation PR into a Draft, tells you which section needs fixing, and asks you to run `/dev-process-kit:design 12`. Once you review and merge that design PR, run `/dev-process-kit:implement 12` again to resume the implementation. Details that the design documents do not cover (internal design) do not stop it: it decides them, expresses them as unit tests, and lists them in the PR body.

If you want to change the specification while the implementation is in progress, the current Issue is finished under the frozen specification. File the change as a new Issue and start again from design.

## 6. Run acceptance tests and merge the implementation PR (your part)

Run acceptance tests against the acceptance criteria in `requirements.md` and decide GO / NO-GO.

- **NO-GO**: Leave review comments on the implementation PR and ask `dev-process-kit:implement` to address them (for example, "address the review on PR #13").
- **GO**: Review and merge the implementation PR. The merge completes Issue #12.

## Fixing bugs

For a bug whose correct behavior is already written in the design documents, file an Issue and fix it with `dev-process-kit:implement`, without going through design. Code that disagrees with the design documents is treated as a defect in the code.

## Read next

- [Philosophy](philosophy.md) — why the work follows these phases
- [Skill reference](skills.md) — what each skill reads, produces, and does not do
