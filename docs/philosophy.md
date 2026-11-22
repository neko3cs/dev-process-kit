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

An Issue holds only the request. Even parts of the request that are not settled yet are written as a finished request, with the most reasonable content, and are asked about in Issue comments so that work moves on. The agreement on what to build and the acceptance criteria go into the requirements document (`requirements.md`). The requirements document is written in the same design PR as the specification and the architecture document, and all three are agreed together when that PR is merged.

### Design defines the specification the requirements call for

Design starts once the requirements are settled. It defines how the system or app should behave to meet the requirements, and records this in three documents.

| Document | Question it answers |
| :--- | :--- |
| Requirements document (`requirements.md`) | Why, for whom, and what to achieve |
| Specification (`specification.md`) | What should happen under which conditions |
| Architecture document (`architecture.md`) | Which structure and constraints realize it, and why |

Design documents are not a copy of the current code. They record the commitments people made and the reasons behind those decisions. The AI writes them as finished work, not as drafts full of assumptions. Where something is undecided, it picks the most reasonable option, writes it as the specification, and asks people in design PR comments whether that choice is right.

By default the three documents live in one place. A monorepo can keep a set of the three per service, with a set for the whole repository whose `architecture.md` indexes the others. A document that grows too large to update one section at a time can be split by feature into a directory of the same name, leaving the original file as the index. Either split is made in a design PR that changes only the structure, not the specification.

### Merging the design PR freezes the specification

When a person reviews and merges the design PR, the specification is agreed and frozen. Implementation works only from the frozen specification.

When the code and the design documents disagree, the design documents win, and the difference is treated as a defect in the code. Users check the documents, not the code.

### When the specification changes, stop and go back upstream

If a gap or an error in the specification turns up during implementation, the implementation PR does not settle on a provisional specification and carry on. Implementation stops, the user is told, and the specification is fixed in a separate design PR that the user starts with `dev-process-kit:design`. Implementation resumes only after that design PR is merged and the specification is frozen again.

This rework follows the same idea as sending a specification change back to an upstream phase in waterfall. It is also the rule that keeps the AI from rewriting the specification for the convenience of the implementation.

What stops implementation is a change to the external specification: anything written in the design documents. The design documents cover external design only, so details they do not cover (internal design) are decided during implementation and expressed as unit tests, without stopping. Stopping for every such detail would only add rework.

A specification change that the user asks for in the middle of implementation is not folded into the Issue in progress. That Issue is finished under the frozen specification, and the change goes through design and implementation again as a new Issue, the way a waterfall project finishes the work under way before taking on a change request. The exception is a fatal problem, such as the specification as written losing data, which stops implementation as above.

### One implementation PR per Issue

Each Issue gets exactly one implementation PR. While anything still waits on a human decision, the PR stays in Draft, so that by the time it is merged, the Issue is complete.

An Issue holds one requirement. A request with several requirements that each deliver value on their own becomes several Issues, not one Issue with several PRs or a parent with child Issues; a child read on its own does not say which requirement it serves. The split is decided by requirement, not by the amount of work. The issue skill asks before filing such a split, and the design skill stops on an Issue that still holds several requirements.

## Tests are defined in test code

Test cases and test procedures are not written as documents; they are defined in test code. Putting as much of the test specification into code as possible lets the same tests run as regression tests on every change.

### Each kind of test has a fixed definition

This plugin defines what unit tests, integration tests, and scenario tests verify, how they are designed, and when they are written. The definitions are fixed so that quality does not vary from session to session.

| Test | Also known as | Design approach | Collaborators | When to write | Coverage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Unit test | Component test | White-box | May be isolated with test doubles (mocks, stubs) | Before the implementation (TDD) | Measured |
| Integration test | — | Black-box: inputs and expected results come from the specification | Inside the system boundary, no test doubles; the real parts are integrated | Usually after the implementation | Measured |
| Scenario test | System test | The business procedure defined in the business requirements becomes the test procedure | Runs on the real configuration | Usually after the implementation | Not measured |

- **Unit tests come before the implementation**: unit tests stand in for detailed design, so writing them first keeps the idea of building downstream from what was decided upstream intact between detailed design and code. The procedure is defined down to splitting work into a TODO list, the Red → Green → Refactor cycle, and the three strategies for getting a test to pass (fake it, obvious implementation, and triangulation).
- **Integration and scenario tests may come after the implementation**: their expected results are already fixed by the frozen design documents, so writing them afterward does not make them follow the code. Because the business procedure is the test procedure, a scenario test is unlikely to be wrong as long as the business requirements are right.
- **Scenario tests are not measured for coverage**: a scenario test is the business scenario itself. Changing its steps to raise code coverage would make it impossible to check against the business requirements. Coverage is measured with unit and integration tests.

### Which design document each test level verifies

This plugin decides which design document is verified at which level of testing. Each design level is paired with the verification that checks it.

| Design | Verification |
| :--- | :--- |
| Business requirements in the requirements document | Scenario tests (the part the system handles) and acceptance tests (the whole business process, people included) |
| Non-functional requirements in the requirements document | Verification that uses the non-functional targets as pass/fail criteria |
| Specification | Integration tests |
| Architecture document | Structural enforcement and review |
| Detailed design (not documented) | Unit tests |

- Detailed design is not documented, because it would become a copy of the code that nobody can maintain. Instead, unit tests are written before the implementation so they read as a specification.
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
| The PR stays in Draft while a decision is pending | Coding conventions |
| External specification problems found during implementation stop it and are fixed in a separate design PR; internal design is decided in unit tests | Test frameworks and tools |
| Which design document is verified at which level | How quality gates are run |
| The definition of each kind of test (including TDD for unit tests) | Detailed conventions for writing tests, such as test names |
