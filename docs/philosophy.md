# Philosophy

English | [日本語](philosophy.ja.md)

dev-process-kit was built to support the whole software development process, including the parts that spec-driven development (SDD) alone does not cover. It is modeled on the waterfall process that has long been common in Japanese software development: work moves through defined phases, each phase produces documents that are reviewed and signed off, and a change found downstream goes back to the phase it belongs to.

## Wider than SDD

SDD centers on writing the specification first and producing code from it. Real development has phases before and after that.

- Before writing the specification, make clear what is actually required (the requirements).
- Have people agree on the specification, and do not change it unilaterally afterward.
- When a problem with the specification turns up during implementation, go back upstream to fix it.
- Have people judge, through acceptance testing, whether the result works for the business.

dev-process-kit treats everything from requirements definition to acceptance testing as one continuous process. It puts a human review and merge at each phase boundary, separating the work the AI carries out from the decisions people make.

## Follow the waterfall phases

The phases move in one direction, from upstream to downstream.

| Phase | Deliverables | Skill | Boundary |
| :--- | :--- | :--- | :--- |
| Requirements definition | Issue, requirements document (`requirements.md`) | `dev-process-kit:issue`, `dev-process-kit:design` | — |
| Design | Specification (`specification.md`), architecture document (`architecture.md`) | `dev-process-kit:design` | Merging the design PR freezes the specification |
| Implementation and testing | Product code, test code | `dev-process-kit:implement` | — |
| Acceptance testing | GO / NO-GO decision | — (done by a person) | Merging the implementation PR completes the Issue |

### Requirements definition starts from an Issue

Development starts from an Issue. Every request is filed and tracked as an Issue. When what to build is recorded in an Issue, people and AI without the conversation history can later pick up from the same place.

An Issue holds only the request. Parts of the request that are not settled yet are stated as assumptions, and work moves on. The agreement on what to build and the acceptance criteria go into the requirements document (`requirements.md`). The requirements document is written in the same design PR as the specification and the architecture document, and all three are agreed together when that PR is merged.

### Design defines the specification the requirements call for

Design starts once the requirements are settled. It defines how the system or app should behave to meet the requirements, and records this in three documents.

| Document | Question it answers |
| :--- | :--- |
| Requirements document (`requirements.md`) | Why, for whom, and what to achieve |
| Specification (`specification.md`) | What should happen under which conditions |
| Architecture document (`architecture.md`) | Which structure and constraints realize it, and why |

Design documents are not a copy of the current code. They record the commitments people made and the reasons behind those decisions. Where something is undecided, the AI writes a provisional proposal and asks people in design PR comments whether to adopt it.

### Merging the design PR freezes the specification

When a person reviews and merges the design PR, the specification is agreed and frozen. Implementation works only from the frozen specification.

When the code and the design documents disagree, the design documents win, and the difference is treated as a defect in the code. Users check the documents, not the code.

### When the specification changes, stop and go back upstream

If a gap or an error in the specification turns up during implementation, the implementation PR does not settle on a provisional specification and carry on. Implementation stops, and the specification is fixed in a separate design PR. Implementation resumes only after that design PR is merged and the specification is frozen again.

This rework follows the same idea as sending a specification change back to an upstream phase in waterfall. It is also the rule that keeps the AI from rewriting the specification for the convenience of the implementation.

### One implementation PR per Issue

Each Issue gets exactly one implementation PR. While anything still waits on a human decision, the PR stays in Draft, so that by the time it is merged, the Issue is complete.

## Tests are defined in test code

Test cases and test procedures are not written as documents; they are defined in test code. Tests are written together with the implementation. Putting as much of the test specification into code as possible lets the same tests run as regression tests on every change.

This plugin decides which design document is verified at which level of testing. Each design level is paired with the verification that checks it.

| Design | Verification |
| :--- | :--- |
| Business requirements in the requirements document | Scenario tests (the part the system handles) and acceptance tests (the whole business process, people included) |
| Non-functional requirements in the requirements document | Verification that uses the non-functional targets as pass/fail criteria |
| Specification | Integration tests |
| Architecture document | Structural enforcement and review |
| Detailed design (not documented) | Unit tests |

- Detailed design is not documented, because it would become a copy of the code that nobody can maintain. Instead, unit tests are written so they read as a specification.
- Business rules in the specification are written as tables of inputs and expected results. Tests copy the rows of these tables directly, so people can check the tests against the tables.
- The AI can run acceptance tests and collect evidence, but people decide GO / NO-GO.

## What this plugin decides, and what it leaves to you

This plugin decides the flow of the phases and the rules that keep the flow intact. They are not treated as a matter of personal preference that each user can change.

| Decided by this plugin | Left to the repository's conventions and the user's instructions |
| :--- | :--- |
| Requests are filed as Issues | How Issue templates are structured |
| Design is recorded in three design documents | Where the design documents live (existing conventions win) |
| Merging the design PR freezes the specification | PR format and templates |
| One implementation PR per Issue | Branch names and how branches are created |
| The PR stays in Draft while a decision is pending | How implementation is carried out |
| Design problems found during implementation are fixed in a separate design PR | Test frameworks and tools |
| Which design document is verified at which level | How quality gates are run |
