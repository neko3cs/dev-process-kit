# Skill reference

English | [日本語](skills.ja.md)

This page summarizes what the three dev-process-kit skills read, produce, and do not do. Each skill's `SKILL.md` and its `references/` files are the authoritative source for the detailed steps and decision criteria. The skill files are written in Japanese, but the Issues, design documents, and PRs they produce follow the language of the target repository.

| Skill | Phase | Reads | Produces |
| :--- | :--- | :--- | :--- |
| [`dev-process-kit:issue`](#dev-process-kitissue) | File | The user's request, Issue templates | GitHub Issue, Issue comments |
| [`dev-process-kit:design`](#dev-process-kitdesign) | Design | Issue, existing design documents, code | Four design documents, design PR, question comments |
| [`dev-process-kit:implement`](#dev-process-kitimplement) | Implementation | Issue, merged design documents and design PRs | Product code, test code, implementation PR |

None of the skills decide PR format, branch names, test frameworks, or how to run quality gates. They follow the repository's conventions and templates and the user's instructions.

## `dev-process-kit:issue`

Files a request as a GitHub Issue. Source: [`skills/issue/SKILL.md`](../plugins/dev-process-kit/skills/issue/SKILL.md); templates and `gh` operations: [`references/templates-and-gh.md`](../plugins/dev-process-kit/skills/issue/references/templates-and-gh.md)

### When to use

- To turn a feature request or a bug report into an Issue
- To record background, investigation results, or the course of a discussion as a comment on an existing Issue

It runs only when called by name. A general request such as "create an issue" does not start it.

```text
/dev-process-kit:issue The login screen crashes
```

### What it does

- Re-reads the target repository's `.github/ISSUE_TEMPLATE/` every time it files an Issue. If there is none, it uses the templates in the owner's `.github` repository. If neither exists, it writes the body under three headings: a description, the motivation and background, and the acceptance criteria. `config.yml` / `config.yaml` is the chooser's configuration, not a template, so it is never picked. When a template exists, the Issue always follows one, whatever `blank_issues_enabled` says.
- Leaves `type: markdown` elements of Issue Forms out of the body, as GitHub does on submission, and sets the template's `assignees`, `projects`, and `type` as well as its title prefix and labels. A template label that the target repository lacks is left off rather than created, the Issue is still filed, and the skill tells the user which labels it could not add.
- Always fills in required fields. The body is written as a finished request: for an undecided part, the skill picks the most reasonable content and writes it as the request, without markers such as `仮定` (assumption) or `TBD`. It does not stop filing to ask; instead, it asks in an Issue comment whether that content is right.
- Files one Issue per requirement. If the request holds several requirements that each deliver value on their own, it shows how it would split them (a title and requirement per Issue) and asks before filing them as separate Issues. It does not use parent and child Issues; each Issue gets a comment naming the others filed with it.
- Checks a checkbox that can be verified from the content (such as "contains no confidential information") only after reviewing the body. It never checks a box that stands for your own agreement or confirmation (agreeing to a code of conduct, having searched for duplicates, and so on) on your behalf: unless you already said so in the conversation, it quotes the item and asks you before filing. Without your agreement the box stays unchecked, and a required one stops the filing.
- Writes only the request and facts about the repository (code behavior, external specifications, investigation results, rejected options and their technical reasons) in the body and comments. Your own circumstances heard in the conversation (clients or company names, other projects, internal schedules, personal matters) are left out, or generalized when the motivation needs them, unless you explicitly ask for them to be written. Everyone who can read the repository sees an Issue, and notifications go out when it is filed, so deleting it later does not undo that.
- Stops before filing only to split several requirements, to ask about consent checkboxes, or when it is hard to choose among multiple templates, and asks about all applicable points in one question.
- Writes in the language set by the repository's rules or your instructions; failing that, the template's language, then the language of the repository's main documents (the source version, not a translation), then the language of the conversation. Template headings, title prefixes, and labels are used as they are, without translation.
- Does not invent facts such as reproduction results, environments, or measurements; it marks them as unconfirmed.
- Puts the request in the body and moves long investigation results and history into comments. A comment on the same topic is rewritten rather than followed by a new one, but only a comment the agent itself wrote: comments by other people, or ones you wrote yourself from the same account, are never edited; when they go out of date, a new comment adds the update.

### What it does not do

- Settle what to build or work out the acceptance criteria (that happens in `dev-process-kit:design`)
- Go on to design, implementation, or PR creation after filing

## `dev-process-kit:design`

Designs an Issue into four design documents and opens a design PR. Source: [`skills/design/SKILL.md`](../plugins/dev-process-kit/skills/design/SKILL.md); decision criteria: [`references/policy.md`](../plugins/dev-process-kit/skills/design/references/policy.md); PR and branch syncing: [`references/pr-and-sync.md`](../plugins/dev-process-kit/skills/design/references/pr-and-sync.md)

### When to use

- To design an Issue (`/dev-process-kit:design 12`, "design #12")
- To address review comments on a design PR
- To reflect a specification change in the design documents

It runs only when called by name. A general request such as "design #12" or "write docs" does not start it, and `dev-process-kit:implement` does not call it either: when the design falls short, `implement` stops and asks you to run it.

### Documents it produces

| Document | Question it answers | Main contents |
| :--- | :--- | :--- |
| `requirements.md` | Why, for whom, and what to achieve | Purpose, users, usage scenarios, business requirements, functional requirements and acceptance criteria, non-functional targets, out of scope, glossary |
| `specification.md` | What should happen under which conditions | Business rules (tables of inputs and expected results), screen operations, states, meaning and constraints of data, input/output formats, errors and notifications |
| `architecture.md` | Which structure and constraints realize it, and why | Structure and dependencies, design decisions (ADRs), persistence and migration, shared implementation conventions, how non-functional targets are met |
| `tests.md` | What to verify, how far, in which environment, and by which criteria | Test scope, test levels and tools, test environments and external boundaries, quality gates and criteria, exit criteria, key risks and verification limits |

Existing conventions decide where the documents live. Without one, they go under an existing `docs/` directory, or at the repository root if there is none.

### What it does

- If none of the four documents exist, creates them from templates; if they exist, updates only the relevant sections as a diff. It never rewrites an existing document wholesale. When only some of the documents exist, it creates a missing one from its template only if the change belongs in it (for example, `tests.md` for a change to the test plan); a missing document the change does not touch stays missing.
- In a monorepo, can keep a set of the four documents per service, indexed from the `architecture.md` of the set for the whole repository. A document too large to update one section at a time can be split by feature into a directory of the same name, with the original file kept as the index. Either split is proposed and made in its own design PR that changes only the structure.
- If an Issue holds several requirements that each deliver value on their own, stops before designing, shows how to split it, and asks you to file one Issue per requirement with `/dev-process-kit:issue`. It does not create, edit, or close Issues itself.
- Writes the documents as finished work. For undecided design, picks the most reasonable option and writes it as the specification with its reason, without markers such as `仮定` (assumption), `未承認` (unapproved), or `TBD`. It asks in design PR comments whether each choice is right and reflects the answers by rewriting the sections.
- Even when creating design documents from existing code, it does not leave pending-confirmation markers in the documents. It distinguishes current behavior read from the code from newly chosen options in the PR body and PR comments, and asks whether to ratify that behavior as the specification. Before ratification, a mismatch between that description and the code is treated as something to verify rather than as a defect in the code; if a difference turns up after the design PR is merged, it is listed so a person can decide which side to adopt, and you are asked whether to file it as an Issue.
- Writes the documents and the design PR in the language set by the repository's rules or your instructions; failing that, the language of the existing design documents, then of the repository's main documents (the source version, not a translation), then of the conversation. The templates are in Japanese; in another language, their headings and text are translated while the sections, their order, and heading levels stay the same. Headings in existing documents are reused, not translated again. Markers of undecided design are not written in any language.
- When the code and the design documents disagree, treats the documents as correct and reports the difference as a defect in the code. It lists each difference in the design PR body and the final report, and asks you whether to file it as an Issue so that it is still tracked after the PR is merged. It does not file Issues itself: running `/dev-process-kit:issue` is your approval to file one.
- Creates the working branch, commits, pushes, and opens the design PR without asking permission for each operation. The design PR links the Issue with a `Refs #<number>` line of its own so that it does not close the Issue.
- When another design PR is merged into the integration branch first and causes conflicts or needs syncing, incorporates the integration branch by merge or rebase according to repository rules or your instructions (defaulting to merge, using `--force-with-lease` after a rebase, and avoiding rebase/force-push after Ready for review unless required). It keeps already-merged agreements intact, surfaces any semantic contradictions in the PR body and PR comments while keeping the PR in Draft, and renumbers any newly added unmerged ADRs that collide with merged ADR numbers (along with their references in the PR).

### What it does not do

- Implement (write tests or product code)
- Document test cases or test procedures (test code is the source of truth)
- Create an implementation task list (such as `tasks.md`)
- Copy the current code structure (lists of functions, internal call order)
- Merge the design PR (a person decides)

## `dev-process-kit:implement`

Implements from the merged design documents, with one implementation PR per Issue. Source: [`skills/implement/SKILL.md`](../plugins/dev-process-kit/skills/implement/SKILL.md); PR and review handling: [`references/pr-and-review.md`](../plugins/dev-process-kit/skills/implement/references/pr-and-review.md); test definitions: [`unit-test.md`](../plugins/dev-process-kit/skills/implement/references/unit-test.md), [`integration-test.md`](../plugins/dev-process-kit/skills/implement/references/integration-test.md), [`scenario-test.md`](../plugins/dev-process-kit/skills/implement/references/scenario-test.md); quality gate and verification guardrails: [`quality-gate.md`](../plugins/dev-process-kit/skills/implement/references/quality-gate.md)

### When to use

- To implement an Issue whose design PR has been merged (`/dev-process-kit:implement 12`)
- To fix a bug whose correct behavior is already written in the design documents
- To address review comments on an implementation PR

It runs only when called by name. A general request such as "fix #12" does not start it, so it does not start this process in a repository that does not use it.

### What it does

- Looks for the design documents in the same order that `design` uses to place them (existing conventions, under `docs/`, the repository root). It uses that location to tell whether design documents exist and whether a PR is a design PR.
- Reads the Issue and the diff of the related design PRs, and decides the scope of work by matching them against the design documents.
- Does not start implementing if there are no design documents, if the Issue's content is not in the design documents (for a bug report, the correct behavior it expects, not the failure itself), or if `TBD` remains in the scope. Instead, it waits for an unmerged design PR to be merged, or tells you what is missing and asks you to run `/dev-process-kit:design`. It does not write design documents itself.
- Writes tests at the following level for each design document.

  | Design document | Tests |
  | :--- | :--- |
  | Business requirements in `requirements.md` | Scenario tests |
  | `specification.md` | Integration tests (calculation rules may use unit tests) |
  | Detailed design (not documented) | Unit tests |

  Constraints in `architecture.md` are enforced by the build structure or checked in PR review.
- Builds parts with test-driven development (TDD), writing unit tests first and running Red → Green → Refactor for one TODO list item at a time.
- Once a feature works, writes integration tests: inputs and expected results come from the specification, and the parts inside the system boundary are integrated without test doubles. Outside the boundary, it uses the provider's test environment when available; if there is no test environment, it uses test doubles and records the unverified scope in the PR body. If a test environment exists but its credentials are missing in the working environment, it proceeds with test doubles for what can be verified and records the unverified scope and reason in the PR body; because the user decides whether tests connected to the external service are needed, it asks the user in a PR comment (keeping the PR in Draft) unless `tests.md` or user instructions already define the policy, and suggests recording the policy (such as running only in CI with secrets) and verification limits in `tests.md` via a PR comment when needed.
- Once the business flow works end to end, writes scenario tests: the business procedure in the business requirements becomes the test procedure, as UI tests for GUI apps or test scripts for batch jobs.
- Measures coverage with unit and integration tests, not scenario tests.
- Writes tests so they read as a specification: in the same language as the design documents, grouped by the context of the specification, with names that include the expected result.
- Copies the rows of business rule tables directly into test data.
- Sorts design problems found during implementation into two kinds. If the external specification written in the design documents has to change (acceptance criteria, business rule tables, screen behavior, inputs and outputs, constraints in `architecture.md`), or following it as written would fail the acceptance criteria, contradict another document, or lose data, it stops, turns the implementation PR into a Draft, and asks you to run `/dev-process-kit:design`. It resumes after that design PR is merged. Details the documents do not cover (internal design) do not stop it: it decides them, expresses them as unit tests, and lists them in the PR body.
- When you ask for a specification change during implementation, finishes the current Issue under the frozen specification and asks you to file the change as a new Issue.
- Fixes code that disagrees with the design documents within the scope of the Issue. A disagreement found outside that scope is not fixed: it is listed in a PR comment and in the final report, and you are asked to file it as an Issue with `/dev-process-kit:issue`, so that it is still tracked after the implementation PR is merged. It does not file Issues itself.
- Leaves information worth adding to the design documents as a PR comment marked as a candidate, instead of writing it there.
- Rewrites a PR comment on the same topic instead of adding a new one, but only a comment the agent itself wrote. Comments by other people, or ones you wrote yourself from the same account, are never edited; a new comment adds the update instead.
- Writes a `Closes #<number>` line of its own in the implementation PR body from the start. It finds the design PR and implementation PR for the same Issue by these lines, not by full-text search alone, so PRs that merely mention the number are not picked up. The body also lists the test for each acceptance criterion, and separates verified from unverified checks.
- Reads design documents in any language, finding each section by its role rather than its heading. Treats any word or note marking a part as undecided or unapproved as a marker of undecided design, whatever the language (`仮定`, `TBD`, `Assumption`, `Unapproved`, and so on), and stops before implementing it. Writes the PR body and comments in the language set by the repository's rules or your instructions, or else in the language of the design documents.
- With service sets or split documents, reads the target service's set and only the relevant split files, found through the indexes.
- Keeps the PR in Draft and asks in PR comments while anything waits on a human decision. It marks the PR Ready for review only after the quality gates defined in `tests.md`, repository rules, or your instructions pass and automated checks are addressed, following the verification guardrails in `references/quality-gate.md` (never treating unrun or empty checks as passing, never loosening thresholds or hiding exit codes, and separating verified, failed, out-of-scope, and unverified results). When no quality gate is defined, it runs the existing tests, builds, type checks, and linters that can be executed locally, separates what it ran from what it did not run in the PR body's verification section, and suggests defining a quality gate in `tests.md` via a PR comment when needed.
- After Ready for review, pushes once per batch of review fixes.
- Follows the repository's rules or your instructions for how to incorporate the integration branch into the implementation branch (merge or rebase), defaulting to merge. After a rebase, it pushes with `--force-with-lease` and avoids rebasing or force-pushing after Ready for review unless required by repository rules or your instructions.

### What it does not do

- Decide on a specification that is not in the design documents and implement it inside the implementation PR
- Rewrite the design documents to match the code
- Write design documents or open design PRs (`dev-process-kit:design` does, when you run it)
- Write to the Issue (it only reads Issues)
- Decide GO / NO-GO in acceptance testing, or merge the implementation PR (a person decides)
