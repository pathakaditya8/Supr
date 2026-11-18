# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Primary: BMU students.** They are on or near the BML Munjal University campus (Sidhrawali, Gurugram), usually between classes and on a phone, and want to find food from nearby vendors, see straight away whether a vendor delivers to campus, send an order request and follow it to the end. The same students sometimes need a laptop or phone repaired or bought and do not know which nearby shop to trust or call.

**Food vendors.** Small campus-area food businesses (currently Kolkata's Lazeez, Kathi Junction, Domino's and Greenox). They apply to join, keep their menu, stock and delivery points up to date, and move orders through preparation to delivery or pickup.

**University Admin.** Reviews vendor applications and documents, records whether the agreement is valid, approves or rejects with remarks, can stop and restart a vendor, moderates listings, manages student accounts and reads the approval history.

## Product Purpose

Supr is a BMU-scoped marketplace that brings the food spots and laptop and phone help around campus into one place. Students browse real menus and services, send order requests and track them; vendors manage their own shop; the University Admin governs who is allowed on the platform.

It is currently a **course project for CSE3005 (Software Engineering)** that **may go live for real BMU students and vendors later**. Success now is a complete, defensible system covering requirements, design, implementation, testing and project management; success later is real students ordering from real vendors.

## Positioning

- Vendors are applied for and reviewed by BMU before their menu goes live, so students are not browsing an open directory.
- Delivery to campus is stated up front by each vendor, not discovered at checkout.
- It is honest about what it does not control: nearby shops that have not joined (the laptop and phone shops) are shown as *listed from public information, not on Supr yet* and cannot take orders, instead of pretending to be partners.

## Operating Context

- Orders are **requests**, not paid transactions. No online payment is collected; payment is arranged directly with the vendor.
- Order lifecycle: placed, accepted, being prepared, ready, then (campus delivery only) on the way, then delivered or collected. Cancelled and rejected orders end the flow. Campus deliveries can show arrival at a gate (college main gate or hostel gate). Students follow this on the Your orders page and keep past orders in Order history.
- A cart holds items from one vendor only.
- Vendors declare whether they deliver to BMU and which campus drop-off points they serve.
- Notifications are stored in the app; there is no email delivery.
- The work is assessed against the CSE3005 handout: SDLC, requirements (MoSCoW), UML and data flow diagrams, testing, project management (WBS, CPM, PERT, risk), quality and maintenance, and AI-assisted engineering.

## Capabilities and Constraints

- Web application: React and TypeScript frontend, FastAPI backend, SQLite by default with PostgreSQL selectable through `DATABASE_URL`.
- Roles: student, vendor, University Admin, each limited by the API to its own data.
- Languages: English and Hindi, switchable from the header; menu data stays as entered.
- Food menu pages and the Tech page are separate; food pages show food only.
- Laptop and phone shops have vendor status `listed`: visible with contact details and published prices only, never orderable. Their prices are shown only where the shop published one; otherwise "Price on request".
- Product photos are illustrative stock photos (Unsplash, credited) grouped by dish type and diet, or a shop's own photo; the dish name on a coloured tile is the fallback.
- Out of scope for this release: online payment, live courier tracking, native mobile apps, expansion beyond BMU, delivery fees or zones, automated legal verification of agreements.
- **Open decisions** (not settled): which agreement document counts and how its validity is verified; agreement expiry and renewal; delivery areas, charges and fulfilment point; student eligibility proof (students may sign up with a name.yearcourse@bmu.edu.in address, but ownership of the address is not verified); where and how it is deployed and who hosts it; whether the listed laptop and phone shops will be invited to join. See `docs/OPEN_DECISIONS.md`.

## Brand Commitments

- Name: **Supr**, written "supr." in the wordmark, with the descriptor "BMU Campus Market".
- Logo: a small shop front with a striped awning and a hand-drawn "s", chosen with the project owner; it appears in the header, footer, door-opening intro and browser tab.
- Lines already in use: "Your campus, a little closer." and "Campus life, well fed."
- The landing page may borrow the structure of Zomato's restaurant listing, but the project owner was explicit that the rest of the site keeps Supr's own identity.

## Evidence on Hand

- Menus: Kolkata's Lazeez (128 items) and Kathi Junction (72 items) transcribed from supplied menu files in `docs/menu-sources/`; Domino's (121 items) captured from its public website on 2026-11-17. See `docs/MENU_IMPORT_REPORT.md`.
- Five laptop and phone shops researched from public listings, with sources in `docs/TECH_SHOPS_REPORT.md`.
- Shop images: Lazeez storefront and Domino's logo supplied by the project owner; Kathi Junction badge cropped from its menu photo; Hi-Tech Computer and Make My Lappy logos from their own websites.
- Project record: requirements and traceability, design diagrams (use case, sequence, DFD, ER), test plan with results, completion report, planning documents.
- **Absences that must not be invented:** no signed vendor agreements, no vendor-confirmed delivery terms or minimum orders, no real order history, no testimonials or ratings, no Greenox menu, no confirmed contact from the listed laptop and phone shops.

## Product Principles

1. **Only show what is true.** Prices, delivery, availability and vendor status appear only when someone actually established them; unknowns are labelled, not filled in.
2. **BMU's trust comes first.** Review before listing, clear status for every vendor, and an audit trail for every decision.
3. **Say plainly what happens next.** Order requests, who confirms them, what stage an order is in, and that payment is arranged with the vendor.
4. **Serve a student on a phone between classes.** Short paths from craving to order request, readable at a glance, nothing that needs training.
5. **Prove it works.** Every claim about the system is backed by a test or a recorded check.

## Accessibility & Inclusion

English and Hindi are both required; no further standard (such as WCAG level) has been committed yet. A dark theme is available (header button, remembered, defaults to the device setting) and was checked page by page for text contrast.
