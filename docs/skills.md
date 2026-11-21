# Skill reference

English | [日本語](skills.ja.md)

This page summarizes what the three dev-process-kit skills read, produce, and do not do. Each skill's `SKILL.md` is the authoritative source for the detailed steps and decision criteria. The skill files are written in Japanese.

| Skill | Phase | Reads | Produces |
| :--- | :--- | :--- | :--- |
| [`dev-process-kit:issue`](#dev-process-kitissue) | File | The user's request, Issue templates | GitHub Issue, Issue comments |
| [`dev-process-kit:design`](#dev-process-kitdesign) | Design | Issue, existing design documents, code | Three design documents, design PR, question comments |
| [`dev-process-kit:implement`](#dev-process-kitimplement) | Implementation | Issue, merged design documents and design PRs | Product code, test code, implementation PR |

None of the skills decide PR format, branch names, test frameworks, or how to run quality gates. They follow the repository's conventions and templates and the user's instructions.

## `dev-process-kit:issue`

Files a request as a GitHub Issue. Source: [`skills/issue/SKILL.md`](../plugins/dev-process-kit/skills/issue/SKILL.md)

### When to use

- To turn a feature request or a bug report into an Issue
- To record background, investigation results, or the course of a discussion as a comment on an existing Issue

```text
/dev-process-kit:issue The login screen crashes
```

### What it does

- Re-reads the target repository's `.github/ISSUE_TEMPLATE/` every time it files an Issue. If there is none, it uses the templates in the owner's `.github` repository. If neither exists, it writes the body under three headings: a description, the motivation and background, and the acceptance criteria.
- Always fills in required fields. The body is written as a finished request: for an undecided part, the skill picks the most reasonable content and writes it as the request, without markers such as `仮定` (assumption) or `TBD`. It does not stop filing to ask; instead, it asks in an Issue comment whether that content is right.
- Does not invent facts such as reproduction results, environments, or measurements; it marks them as unconfirmed.
- Puts the request in the body and moves long investigation results and history into comments. A comment on the same topic is rewritten rather than followed by a new one.

### What it does not do

- Settle what to build or work out the acceptance criteria (that happens in `dev-process-kit:design`)
- Go on to design, implementation, or PR creation after filing

## `dev-process-kit:design`

Designs an Issue into three design documents and opens a design PR. Source: [`skills/design/SKILL.md`](../plugins/dev-process-kit/skills/design/SKILL.md); decision criteria: [`references/policy.md`](../plugins/dev-process-kit/skills/design/references/policy.md)

### When to use

- To design an Issue (`/dev-process-kit:design 12`, "design #12")
- To address review comments on a design PR
- To reflect a specification change in the design documents

### Documents it produces

| Document | Question it answers | Main contents |
| :--- | :--- | :--- |
| `requirements.md` | Why, for whom, and what to achieve | Purpose, users, usage scenarios, business requirements, functional requirements and acceptance criteria, non-functional targets, out of scope, glossary |
| `specification.md` | What should happen under which conditions | Business rules (tables of inputs and expected results), screen operations, states, meaning and constraints of data, input/output formats, errors and notifications |
| `architecture.md` | Which structure and constraints realize it, and why | Structure and dependencies, design decisions (ADRs), persistence and migration, shared implementation conventions, how non-functional targets are met, verification policy and key risks |

Existing conventions decide where the documents live. Without one, they go under an existing `docs/` directory, or at the repository root if there is none.

### What it does

- If none of the three documents exist, creates them from templates; if they exist, updates only the relevant sections as a diff. It never rewrites an existing document wholesale.
- Writes the documents as finished work. For undecided design, picks the most reasonable option and writes it as the specification with its reason, without markers such as `仮定` (assumption), `未承認` (unapproved), or `TBD`. It asks in design PR comments whether each choice is right and reflects the answers by rewriting the sections.
- When the code and the design documents disagree, treats the documents as correct and reports the difference as a defect in the code.
- Creates the working branch, commits, pushes, and opens the design PR without asking permission for each operation. The design PR links the Issue with `Refs #<number>` so that it does not close the Issue.

### What it does not do

- Implement (write tests or product code)
- Document test cases or test procedures (test code is the source of truth)
- Create an implementation task list (such as `tasks.md`)
- Copy the current code structure (lists of functions, internal call order)
- Merge the design PR (a person decides)

## `dev-process-kit:implement`

Implements from the merged design documents, with one implementation PR per Issue. Source: [`skills/implement/SKILL.md`](../plugins/dev-process-kit/skills/implement/SKILL.md); test definitions: [`unit-test.md`](../plugins/dev-process-kit/skills/implement/references/unit-test.md), [`integration-test.md`](../plugins/dev-process-kit/skills/implement/references/integration-test.md), [`scenario-test.md`](../plugins/dev-process-kit/skills/implement/references/scenario-test.md)

### When to use

- To implement an Issue whose design PR has been merged (`/dev-process-kit:implement 12`)
- To fix a bug whose correct behavior is already written in the design documents
- To address review comments on an implementation PR

### What it does

- Looks for the design documents in the same order that `design` uses to place them (existing conventions, under `docs/`, the repository root). It uses that location to tell whether design documents exist and whether a PR is a design PR.
- Reads the Issue and the diff of the related design PRs, and decides the scope of work by matching them against the design documents.
- Does not start implementing if there are no design documents, if the Issue's content is not in the design documents, or if `TBD` remains in the scope. Instead, it opens a design PR or waits for an unmerged design PR to be merged.
- Writes tests at the following level for each design document.

  | Design document | Tests |
  | :--- | :--- |
  | Business requirements in `requirements.md` | Scenario tests |
  | `specification.md` | Integration tests (calculation rules may use unit tests) |
  | Detailed design (not documented) | Unit tests |

  Constraints in `architecture.md` are enforced by the build structure or checked in PR review.
- Builds parts with test-driven development (TDD), writing unit tests first and running Red → Green → Refactor for one TODO list item at a time.
- Once a feature works, writes integration tests: inputs and expected results come from the specification, and the parts inside the system boundary are integrated without test doubles.
- Once the business flow works end to end, writes scenario tests: the business procedure in the business requirements becomes the test procedure, as UI tests for GUI apps or test scripts for batch jobs.
- Measures coverage with unit and integration tests, not scenario tests.
- Writes tests so they read as a specification: in the same language as the design documents, grouped by the context of the specification, with names that include the expected result.
- Copies the rows of business rule tables directly into test data.
- If a gap or an error in the design turns up during implementation, stops, turns the implementation PR into a Draft, and fixes the design in a separate design PR. It resumes after that PR is merged.
- Writes `Closes #<number>` in the implementation PR body from the start. The body also lists the test for each acceptance criterion, and separates verified from unverified checks.
- Keeps the PR in Draft and asks in PR comments while anything waits on a human decision. It marks the PR Ready for review only after the quality gates pass and automated checks are addressed.
- After Ready for review, pushes once per batch of review fixes.

### What it does not do

- Decide on a specification that is not in the design documents and implement it inside the implementation PR
- Rewrite the design documents to match the code
- Write to the Issue (it only reads Issues)
- Decide GO / NO-GO in acceptance testing, or merge the implementation PR (a person decides)
