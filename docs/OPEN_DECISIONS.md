# Open design decisions

These are explicitly unresolved by SRS v1.0. The following implementation choices are local, reversible assumptions for the demonstration and are not presented as approved policy.

| Question | Current bounded choice | Owner / decision needed |
|---|---|---|
| Which agreement document and how to verify validity? | Admin records a yes/no result and check timestamp; no external legal verification. | University Admin / project guide |
| Agreement expiration and renewal behavior? | Not modeled; no expiry inference. | University Admin |
| BMU delivery areas, charges and fulfilment point? | Boolean vendor declaration only; no fee, zone or time estimate. | University Admin and vendors |
| Payment handling? | Order request only; payment is handled outside this release. | Project stakeholders |
| Notification provider and retry behavior? | Persistent in-app records only. | Project stakeholders |
| Final field-level database schema? | Schema documented in architecture and models; review needed before production. | Project team and guide |
| Student eligibility proof? | Students can sign up themselves with an address of the form `name.yearcourse@bmu.edu.in` (for example `dhruv.24cse@bmu.edu.in`); the app checks the format only. **There is no email verification**, so anyone can type another student's address, and the account cannot prove it belongs to the owner. Until BMU provides a student directory or verification email, the admin can remove or reset any account. | BMU IT / University Admin |
| File retention and access policy? | Private local files; admin-only route; operational retention period unset. | BMU data owner |
| Order cancellation by vendor? | Vendor may cancel only pending/accepted requests; quantities restored. | Confirm with stakeholders |
| Vendor participation and agreement validity for the four named businesses? | Live database records admin approvals; the reset seed starts pending. Confirm the underlying agreements and current catalog details with each vendor. | BMU Admin and each vendor |
| Lazeez supplied delivery terms (free delivery, ₹100 minimum)? | Recorded as unconfirmed source notes only; not shown as an active order term. | Kolkata's Lazeez |
| Current availability and approval for Lazeez/Kathi menu items? | Full supplied menus are imported in review status with zero stock; vendor must verify before publication. | Each vendor and BMU Admin |
| Greenox current menu catalog? | Import only from manual exports/screenshots or an accessible official outlet catalog; no examples or estimated prices. | User/vendor |
| Domino's outlet prices and availability? | Website national menu imported 2026-11-17 at displayed prices with zero stock; combos and toppings not imported. Confirm the serving outlet's prices and whether promotional and pre-GST beverage prices apply. | Domino's outlet |
| Lazeez add-on/current availability? | PDF prices are imported for roll add-ons, but remain disabled pending vendor confirmation. | Kolkata's Lazeez |

