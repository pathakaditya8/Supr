# AI-assisted engineering and human validation log

## Method

Use AI as a drafting/review aid; a human owner checks source requirements, business invariants, generated diffs and executed output. AI suggestions are not evidence that a feature is secure, correct, tested or faculty-approved. Keep personally identifying information out of prompts and use fictional seed data.

## Activity register

| Activity | AI contribution | Human validation required |
|---|---|---|
| Coding assistance | Drafted module structure, route scaffolds, UI components and docs | Compare each behavior to SRS; run type checker and tests; inspect ownership/status constraints |
| Code review | Identify edge cases in auth, cart, checkout, governance | Independently reproduce findings and verify fixes |
| Vulnerability scanning | Suggested review targets: signed-token handling, upload path, CORS, SQL/query and role isolation | Run static/security tools and manual access-control tests; no scan result is claimed here |
| Test generation | Drafted API cases for login, roles, catalogue, cart and approval | Execute; confirm fixture isolation and expected state; add missing cases |
| AI-assisted TDD | For a new invariant, write a failing test first, implement minimum change, rerun regression suite | Preserve red/green output and have a reviewer check the requirement mapping |

## Validation record

At this project start, source and documentation were generated from user-provided requirements. No test execution, security scan or independent peer review is asserted. Record any hallucinated requirement, logical defect, correction and final evidence here as work proceeds. Known design review items are listed in `QUALITY_MAINTENANCE.md` and `OPEN_DECISIONS.md`.

## Validation log (2026-11-17)

Defects and mistakes caught while working with an AI coding assistant, and how each was checked. These are recorded as evidence of human-in-the-loop validation: in each case the claim was verified by running code, not by trusting the assistant.

| Finding | How it was caught | Outcome |
|---|---|---|
| Docs claimed features were missing (price filter, product detail, document upload, stop/restart, notifications) that were in fact implemented | Searching the frontend source for each feature before rewriting `COMPLETION_REPORT.md` | Report corrected to match the code |
| Two tests encoded an outdated rule (menus hidden until admin publication) | Test run: 6 passed, 2 failed; compared with the current publishing behaviour | Tests rewritten to the current rule, not deleted |
| Importing the Domino's menu silently hid older vendors' items from the admin listing (250-row cap) | An existing test failed after the import | Cap raised; covered by T-MENU-01 |
| A traceability claim that FR-07 (one-vendor cart) was tested was wrong | Re-reading the cited test | Status corrected; dedicated tests T-SEC-09 and T-E2E-03 added |
| An earlier ER diagram (`MENU_ER.md`) had never rendered | Parsing every diagram with Mermaid | Replaced by a validated full ER diagram |
| A first draft of the second-vendor browser test assumed an error message; the app actually asks the user to confirm clearing the cart | Browser test failure, then reading the add-to-bag code | Test now checks both Cancel and OK paths |
| Heart (favourite) buttons stacked in one spot so students could save the wrong item | Browser test could not click a card's own heart | CSS fixed; regression assertion added (T-E2E-06) |

## Static analysis and dependency scanning (2026-11-17)

| Tool | Result | Human review |
|---|---|---|
| Bandit 1.9.4 | 2 low-severity findings, 0 medium, 0 high | Both are B105 false positives on the literal token type `"bearer"`; confirmed by reading `main.py` lines 85 and 91 |
| pip-audit 2.10.1 | PYSEC-2026-1845 in pytest 8.4.2 | Read the advisory: UNIX shared `/tmp` issue in a test-only tool. Upgraded to pytest 9.x and re-ran the full suite and the scan (clean) |
| npm audit | 0 vulnerabilities | None needed |

## Test-driven development example (2026-11-17)

**Defect noticed:** searching the marketplace for `%` or `_` returned all 321 menu items, and `a_b` returned 22 unrelated items. SQL `LIKE` treats `%` (any text) and `_` (any one character) as wildcards, and the search built its pattern straight from what the student typed.

**1. Red: write the test first.** `backend/tests/test_search.py` states the requirement: a search must only return items that literally contain the typed text, and must never match the whole menu. It also includes a control case (`paneer`) that should keep working.

```
$ python -m pytest tests/test_search.py -q
E  AssertionError: searching '%' matched the whole menu
E  AssertionError: searching '_' matched the whole menu
E  AssertionError: 'a_b' returned items that do not contain it
E  AssertionError: '100%' returned items that do not contain it
E  AssertionError: searching '%%' matched the whole menu
5 failed, 1 passed
```

**2. Green: the smallest change that passes.** Escape `%`, `_` and the escape character before building the pattern, and tell the database which escape character is used (`ilike(term, escape="\\")`).

```
$ python -m pytest tests/test_search.py -q
6 passed, 3 warnings
```

**3. Refactor: clean up while staying green.** The first version used `"\%"` string literals that Python flags with `SyntaxWarning` (the 3 warnings). The escaping was moved into a named helper, `contains_pattern()` in `backend/app/main.py`, with a docstring, and the warnings disappeared.

```
$ python -m pytest tests -q
45 passed, 1 warning      (the remaining warning is the existing Starlette/httpx deprecation)
```

**Human review of the AI's part:** the assistant proposed the fix; it was accepted only after the red run showed the exact failures above, the green run showed them gone, and the full suite confirmed nothing else broke.
