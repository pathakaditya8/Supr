# Project management plan

All numbers below are planning estimates for a four-person student team, not actual cost, expenditure or elapsed project evidence. Re-estimate after faculty milestone feedback.

## WBS and sprint plan

Work is divided equally (27 person-days each) among Aakriti, Dhruv, Aditya and Anshika by module of the website; see [`TEAM_WORK_SPLIT.md`](TEAM_WORK_SPLIT.md) for who owns each module.

| WBS | Work package | Deliverable | Estimate |
|---|---|---|---:|
| 1 | Scope, SRS review, elicitation and MoSCoW | Requirements baseline/open decisions | 10 person-days |
| 2 | Architecture, ER/UML/DFD and project plan | Design and management docs | 9 person-days |
| 3 | Database, identity and vendor governance | Models, auth, application review | 17 person-days |
| 4 | Marketplace and vendor listing management | Search/filter/catalogue/shop | 14 person-days |
| 5 | Cart, checkout and order lifecycle | Single-vendor cart/order APIs | 15 person-days |
| 6 | React role workspaces and integration | Student/vendor/admin UX | 18 person-days |
| 7 | Verification, fixes and security review | Test evidence and issue register | 15 person-days |
| 8 | Course evidence, setup and demonstration | README, completion report | 10 person-days |
| | **Total** | | **108 person-days** |

| Sprint | Goal | Acceptance evidence |
|---|---|---|
| 0 (1 week) | Baseline SRS, MoSCoW, architecture, repo setup | Approved scope and diagrams |
| 1 (2 weeks) | User roles, secure auth, vendor application | Role tests and pending application flow |
| 2 (2 weeks) | Admin review, audit, catalogue and vendor listings | Decision audit and searchable approved products |
| 3 (2 weeks) | One-vendor cart, transactional order and fulfilment | Checkout and status lifecycle scenarios |
| 4 (2 weeks) | Dashboards, notifications, analytics, responsive UX | Role review and demo data |
| 5 (2 weeks) | Verification, repair, security/performance checks, docs | Actual test report and traceability update |

## Time, effort and cost estimate

Planning assumption: four students, 12 working weeks, 9 hours per person each week yields 432 person-hours. At 25% coordination/learning/rework overhead reserve, productive feature effort is approximately 324 hours. The WBS effort estimate is 108 person-days at 3 hours/day. Both views are intentionally approximate and need team calibration.

Example replacement-cost estimate only: 324 productive hours × ₹500/hour = ₹1,62,000 labor-equivalent. Add ₹0 for local SQLite/demo hosting and ₹0 assumed for open-source tools; cloud hosting, domains, support and taxes are excluded. This is not actual expenditure or a vendor quote.

## Monitoring and control

At sprint start, confirm capacity and acceptance criteria. Maintain an issue list by requirement ID, owner, severity and due sprint. Review progress weekly using accepted stories, unresolved blockers, defect age, requirement coverage, and planned vs actual hours. Reforecast when estimates vary by >20%; protect Must requirements and record scope changes. Faculty review is a milestone, not evidence of software correctness.

## CPM and critical path

Durations use working days, single project-team workstream. FS = finish-to-start dependency.

| ID | Activity | Duration | Predecessor | ES | EF | LS | LF | Slack |
|---|---|---:|---|---:|---:|---:|---:|---:|
| A | SRS analysis / decision log | 5 | — | 0 | 5 | 0 | 5 | 0 |
| B | Data model and architecture | 4 | A | 5 | 9 | 5 | 9 | 0 |
| C | Identity and access | 6 | B | 9 | 15 | 9 | 15 | 0 |
| D | Vendor application/governance | 6 | C | 15 | 21 | 15 | 21 | 0 |
| E | Catalogue/listing APIs | 7 | B | 9 | 16 | 14 | 21 | 5 |
| F | Cart and orders | 7 | D,E | 21 | 28 | 21 | 28 | 0 |
| G | Frontend integration | 8 | E,F | 28 | 36 | 28 | 36 | 0 |
| H | Verification and repair | 6 | G | 36 | 42 | 36 | 42 | 0 |
| I | Final documentation/demo | 4 | H | 42 | 46 | 42 | 46 | 0 |

Critical path: A → B → C → D → F → G → H → I = **46 working days**. E has five days of calculated slack. Estimate assumes one team sequence and no holidays; actual calendar time varies by parallelism and course schedule.

## PERT estimates

`TE = (O + 4M + P) / 6`; estimates are working days.

| Activity | O | M | P | TE |
|---|---:|---:|---:|---:|
| Requirements and design | 4 | 5 | 8 | 5.33 |
| Identity/governance | 8 | 12 | 18 | 12.33 |
| Catalogue and listings | 5 | 7 | 12 | 7.50 |
| Cart/order lifecycle | 5 | 7 | 14 | 7.83 |
| Frontend integration | 6 | 8 | 15 | 8.83 |
| Verification and documentation | 7 | 10 | 17 | 10.67 |

The PERT network is drawn in [`diagrams/PERT.md`](diagrams/PERT.md) with the critical-path duration (45.0 days), variance and standard deviation (3.24 days). Observed sprint data goes in [`PROJECT_TRACKING.md`](PROJECT_TRACKING.md).

Text description: Requirements/design → Identity/governance → Cart/orders → Frontend integration → Verification/docs; Catalogue/listings branches from design and joins before cart/orders. PERT values need replacement with observed sprint data.

## Risk register

| Risk | Likelihood / impact | Response / trigger |
|---|---|---|
| Ambiguous agreement and delivery policy | Medium / High | Keep bounded assumptions and decision log; trigger: stakeholders request charges/expiry |
| Role or order ownership defect | Medium / High | Test deny paths and owner scoping; trigger: unauthorized record exposure |
| Checkout oversell/race | Medium / High | Transactional update and stock constraints; trigger: simultaneous last-item orders |
| Unsafe document upload | Medium / High | Extension/size allowlist, random names, admin-only access; trigger: unsupported or large file |
| Integration slips | High / Medium | API contracts early, thin vertical slices; trigger: >1 sprint blocked integration |
| Time underestimation | Medium / Medium | Track weekly capacity and defer Could items; trigger: >20% variance |
| Sensitive student/vendor data exposure | Low / High | Minimum data and explicit role filters; trigger: audit/test discovers cross-user response |

