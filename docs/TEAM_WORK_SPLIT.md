# Team work split: Aakriti, Dhruv, Aditya and Anshika

This divides the project's planned effort (108 person-days, from `PROJECT_PLAN.md`) and the work still open into **four equal shares of 27 person-days each**, with a mix of requirements, build and testing for everyone so that each member can explain a complete slice in the viva.

This is a **plan for who owns what**, not a record of who did what. It does not claim that anyone has already worked these hours. Actual hours go in [`PROJECT_TRACKING.md`](PROJECT_TRACKING.md).

## 1. Shares at a glance

| Member | Main role | Planned person-days | Share |
|---|---|---:|---:|
| Aakriti | Requirements, design and documentation lead | 27 | 25% |
| Dhruv | Backend, database and security lead | 27 | 25% |
| Aditya | Frontend, user experience and deployment lead | 27 | 25% |
| Anshika | Quality, testing and project-management lead | 27 | 25% |
| **Total** | | **108** | **100%** |

## 2. Work packages (WBS) by owner

| WBS | Work package | Total days | Aakriti | Dhruv | Aditya | Anshika |
|---|---|---:|---:|---:|---:|---:|
| 1 | Scope, SRS review, elicitation, MoSCoW | 10 | **10** | | | |
| 2 | Architecture, ER, UML and DFD diagrams, project plan | 9 | **9** | | | |
| 3 | Database, identity and vendor governance | 17 | | **17** | | |
| 4 | Marketplace and vendor listing management | 14 | | | **9** | 5 |
| 5 | Cart, checkout and order lifecycle | 15 | | **10** | | 5 |
| 6 | React role workspaces and integration | 18 | | | **18** | |
| 7 | Verification, fixes and security review | 15 | | | | **15** |
| 8 | Course evidence, setup and demonstration | 10 | **8** | | | 2 |
| | **Total** | **108** | **27** | **27** | **27** | **27** |

## 3. What each person owns

**Aakriti: requirements, design and documentation**
- SRS, MoSCoW and the requirements traceability table (`REQUIREMENTS.md`, `OPEN_DECISIONS.md`).
- The four UML and data diagrams: use case, sequence, DFD and ER (`docs/diagrams/`), and the PERT diagram.
- The requirement elicitation fieldwork: run the student questionnaire and the vendor and admin interviews, then fill in `REQUIREMENT_ELICITATION.md`.
- Course evidence: `COMPLETION_REPORT.md`, `SDLC_AND_ETHICS.md`, `AI_ENGINEERING.md`, and the viva walkthrough of the whole document set.

**Dhruv: backend, database and security**
- Data model, migrations 0001 to 0014 and the hosted PostgreSQL database.
- Authentication: sign-in, student self sign-up with the name.yearcourse@bmu.edu.in rule, password change and admin password reset.
- Vendor governance: applications, documents, approve or reject, agreement validity, stop and restart, approval history.
- Orders: the one-vendor cart, server-side prices, stock locking, the order lifecycle and notifications.
- Deployment of the backend on Render (`render.yaml`, `copy_data`, `sync_photos`, keep-awake ping).

**Aditya: frontend, experience and deployment**
- The React site: student, vendor and admin workspaces, the Marketplace, Menu, Discover, Vendors and Tech pages, the bag and order tracking.
- Vendor listing screens: item photos, stock controls, delivery places, and the dish and shop photo system.
- Bilingual interface (English and Hindi), the brand and logo, accessibility and phone layouts.
- Deployment of the website on Vercel (`vercel.json`) and the frontend lint clean-up.

**Anshika: quality, testing and project management**
- The test suites: API and security tests, Playwright browser tests and the performance test (`TEST_PLAN.md`).
- Static analysis and dependency scans (Ruff, ESLint, Bandit, pip-audit, npm audit) and the defect log.
- Sprint planning evidence, planned-versus-actual tracking, burndown and retrospectives (`PROJECT_TRACKING.md`, `PROJECT_PLAN.md`).
- Risk register, QA and maintenance document (`QUALITY_MAINTENANCE.md`), and the demonstration script.

## 4. Open work, two items each

| # | Open item | Owner | Support |
|---|---|---|---|
| 1 | Run the elicitation questionnaire and interviews and write up the findings | Aakriti | Anshika |
| 2 | Refresh the SRS, ER and sequence diagrams for self sign-up, history and Tech page changes | Aakriti | Dhruv |
| 3 | Vendor terms confirmation screen (minimum order and delivery terms) | Dhruv | Aditya |
| 4 | Charts and exportable reports for the admin and vendors | Dhruv | Aditya |
| 5 | Fix the 25 ESLint findings and the 320 px home page overflow | Aditya | Anshika |
| 6 | Remaining 11 dish photos, the headphones photo, and the Greenox menu from the vendor | Aditya | Aakriti |
| 7 | Fill the time log, planned-versus-actual table and burndown; hold sprint retrospectives | Anshika | All |
| 8 | Production hardening: rotate the database password, upgrade the free plans or export before the 30-day expiry, custom domain | Anshika | Dhruv |

## 5. Shared duties

- Every member reviews at least one other member's pull request or commit before it is merged.
- Every member records their own hours weekly in the time log.
- Each member prepares to explain their own area and to demonstrate one full user journey (student order, vendor fulfilment, admin approval) in the viva, because the handout grades the group project through questions on the work presented.

## 6. If the split needs to change

The shares are equal in planned days. If someone's load changes, move whole packages or items between members, keep each member at 27 days, and update this table and the planned-versus-actual table.
