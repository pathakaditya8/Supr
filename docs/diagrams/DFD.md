# Data flow diagrams

Data flow diagrams for Supr at three levels, as required by the CSE3005 handout: a **context diagram**, a **Level-0 DFD** that splits the system into its major processes, and **Level-1 DFDs** that break two of those processes down further. They are traced from the implemented API (`backend/app/main.py`) and data model (see [`ER.md`](ER.md)), state on 2026-11-17.

**Notation** (Mermaid has no dedicated DFD shapes, so these are used consistently):

| Symbol | Meaning |
|---|---|
| Rectangle | External entity (a person outside the system) |
| Circle | Process, numbered |
| Cylinder | Data store, labelled D1–D8 |
| Labelled arrow | Data flow |

**Balancing:** every data flow between an external entity and Supr in the context diagram appears in the Level-0 diagram, and every flow into or out of processes 4 and 5 in Level 0 appears in their Level-1 diagrams.

## Context diagram

The whole system is one process. Payment, couriers and email are outside scope, so the only external entities are the three user roles.

```mermaid
flowchart LR
  S[Student]
  V[Local vendor]
  A[University Admin]
  P0(("0 Supr BMU Campus Market"))

  S -->|credentials, search and filters, cart selections, order request, cancellation| P0
  P0 -->|catalogue and vendor details, cart total, order status, notifications| S
  V -->|credentials, application and documents, menu items, photos and stock, delivery points, order status updates| P0
  P0 -->|application decision, incoming orders, notifications| V
  A -->|credentials, application decision and agreement check, stop or restart, listing moderation, student accounts| P0
  P0 -->|applications and documents, approval history, marketplace metrics| A
```

## Level-0 DFD

The system split into its seven main processes and eight data stores.

Level 0 has around 50 labelled flows, so it renders large. Open the rendered SVG and zoom in, or export it from mermaid.live as SVG for print.

```mermaid
flowchart LR
  S[Student]
  V[Local vendor]
  A[University Admin]

  P1(("1 Authenticate users"))
  P2(("2 Browse catalogue"))
  P3(("3 Manage vendor shop"))
  P4(("4 Govern marketplace"))
  P5(("5 Place orders"))
  P6(("6 Fulfil orders"))
  P7(("7 Notify users"))

  D1[("D1 Users")]
  D2[("D2 Vendors")]
  D3[("D3 Menu items, variants, add-ons")]
  D4[("D4 Applications and documents")]
  D5[("D5 Approval history and audit log")]
  D6[("D6 Carts and orders")]
  D7[("D7 Uploaded files")]
  D8[("D8 Notifications")]

  S -->|credentials| P1
  V -->|credentials| P1
  A -->|credentials| P1
  P1 <-->|account lookup| D1

  S -->|search and filters| P2
  D2 -->|approved vendors| P2
  D3 -->|published menu items| P2
  P2 -->|catalogue and vendor details| S

  V -->|application and documents| P3
  V -->|menu items, photos and stock| P3
  V -->|delivery points| P3
  P3 -->|application| D4
  P3 -->|document and photo files| D7
  P3 -->|menu changes| D3
  P3 -->|delivery points| D2

  A -->|decision and agreement check| P4
  A -->|stop or restart| P4
  A -->|listing moderation| P4
  A -->|student accounts| P4
  D4 -->|pending applications| P4
  D7 -->|documents| P4
  P4 -->|vendor status| D2
  P4 -->|decision| D4
  P4 -->|listing status| D3
  P4 <-->|student accounts| D1
  D2 -->|vendor status and counts| P4
  P4 -->|history and audit entries| D5
  D6 -->|order totals| P4
  P4 -->|applications, documents, history, metrics| A

  S -->|cart selections, order request, cancellation| P5
  D3 -->|prices and stock| P5
  D2 -->|vendor status and delivery points| P5
  P5 -->|cart, order and item snapshots| D6
  P5 -->|stock reduction, or restore on cancellation| D3
  P5 -->|cart total and order confirmation| S

  V -->|order status updates| P6
  D6 -->|this vendor's orders| P6
  P6 -->|new status| D6
  P6 -->|restored stock| D3
  P6 -->|incoming orders| V
  P6 -->|order status| S

  P3 -->|application event| P7
  P4 -->|decision event| P7
  P5 -->|new order or cancellation event| P7
  P6 -->|status change event| P7
  P7 -->|notification| D8
  D8 -->|notifications| S
  D8 -->|notifications| V
```

## Level-1 DFD: process 5, Place orders

How a cart becomes an order. The one-vendor rule and server-side pricing sit in 5.1 and 5.2; 5.4 reduces stock only if enough remains, so two students cannot buy the same last item.

```mermaid
flowchart TB
  S[Student]
  D2[("D2 Vendors")]
  D3[("D3 Menu items, variants, add-ons")]
  D6[("D6 Carts and orders")]
  P7(("7 Notify users"))

  P51(("5.1 Check item and vendor"))
  P52(("5.2 Price the selection"))
  P53(("5.3 Update one-vendor cart"))
  P54(("5.4 Check out and reserve stock"))
  P55(("5.5 Record order"))

  S -->|item, variant, add-ons, quantity| P51
  D3 -->|status and stock| P51
  D2 -->|vendor status| P51
  P51 -->|valid selection| P52
  D3 -->|variant and add-on prices| P52
  P52 -->|priced line| P53
  D6 -->|current cart and its vendor| P53
  P53 -->|cart line| D6
  P53 -->|cart total, or one-vendor refusal| S

  S -->|order request and delivery point| P54
  D6 -->|cart lines| P54
  D2 -->|supported delivery points| P54
  D3 -->|current prices and stock| P54
  P54 -->|stock reduction| D3
  P54 -->|confirmed lines| P55
  P55 -->|order and item snapshots, emptied cart| D6
  P55 -->|new order or cancellation event| P7
  P55 -->|order confirmation| S
  S -->|cancellation of a pending order| P55
  P55 -->|restored stock on cancellation| D3
```

## Level-1 DFD: process 4, Govern marketplace

The University Admin's governance work. Every decision and participation change is written to D5, which provides the approval history.

```mermaid
flowchart LR
  A[University Admin]
  D1[("D1 Users")]
  D2[("D2 Vendors")]
  D3[("D3 Menu items, variants, add-ons")]
  D4[("D4 Applications and documents")]
  D5[("D5 Approval history and audit log")]
  D6[("D6 Carts and orders")]
  D7[("D7 Uploaded files")]
  P7(("7 Notify users"))

  P41(("4.1 Review applications"))
  P42(("4.2 Record decision"))
  P43(("4.3 Control participation"))
  P44(("4.4 Moderate listings"))
  P45(("4.5 Manage student accounts"))
  P46(("4.6 Report history and metrics"))

  D4 -->|pending applications| P41
  D7 -->|documents| P41
  P41 -->|applications and documents| A
  A -->|decision and agreement check| P42
  P42 -->|decision| D4
  P42 -->|vendor status and agreement| D2
  P42 -->|history and audit entries| D5
  P42 -->|decision event| P7

  A -->|stop or restart| P43
  D2 -->|current vendor status| P43
  P43 -->|vendor status| D2
  P43 -->|history and audit entries| D5
  P43 -->|decision event| P7

  A -->|listing moderation| P44
  P44 -->|listing status| D3

  A -->|student accounts| P45
  P45 <-->|student accounts| D1

  D5 -->|approval history| P46
  D6 -->|order totals| P46
  D2 -->|vendor status and counts| P46
  D1 -->|student count| P46
  D4 -->|application counts| P46
  P46 -->|history and metrics| A
```
