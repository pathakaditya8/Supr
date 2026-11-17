# SDLC models, design practice and professional responsibility

## Model comparison and selection

| Model | Strength | Limitation for Supr | Fit |
|---|---|---|---|
| Waterfall | Clear staged approvals and stable baselines | Governance and marketplace details need feedback; late integration defects are costly | Useful for signed-off interface baselines, not the whole build |
| Incremental | Delivers coherent capabilities in slices | Requires careful integration and data-model evolution | Strong fit for role/API increments |
| Spiral | Risk analysis guides iteration | Formal risk cycles add overhead to a small course team | Use risk-driven checks for auth, uploads, and checkout |
| Agile | Frequent review and reprioritization | Needs explicit acceptance criteria and scope control | Selected delivery approach with short, demonstrable increments |

The project uses an incremental Agile workflow: establish requirements and model first; build identity/governance and catalogue; add cart/order; complete role workspaces, validation and course evidence. The source SRS is baseline input, and open business rules are not invented.

## Design qualities

Modules separate access policy, marketplace search, vendor onboarding, listing management, ordering and governance. This keeps high-risk rules (single vendor per cart and active vendor checks) in API paths. Database ownership keys support privacy filtering. Cohesion is improved by role-oriented routes; avoid cross-module imports that cause broad coupling. Further extraction into service modules is a maintainability improvement.

## Coding guidance

- Validate input at API boundaries; never trust browser state for price, status or ownership.
- Use parameterized ORM operations; return safe, understandable error text.
- Keep secrets in environment configuration; use TLS in deployment.
- Keep endpoints and role policy small, names explicit, and status changes centralized.
- Add tests for success, denial and edge conditions around each business invariant.

## Professional responsibility

Use fictional demo identities and minimum necessary personal data. Do not claim the university has verified an agreement automatically. Restrict private order and uploaded-document access. Tell users what happens to their order and whether campus delivery is available. Respect academic integrity: students should understand, review and be able to explain generated code and project decisions; attribution and faculty policy govern submitted work.

