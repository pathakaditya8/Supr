# Menu and ordering data model

Superseded by the full entity-relationship diagram in [`ER.md`](ER.md), which covers every table, including the menu and ordering tables that were drawn here. (The earlier diagram in this file did not render: Mermaid does not accept semicolon-separated attributes.)

Key point kept from the earlier version: cart prices are recalculated from the current variant and add-on records, and checkout saves a name and unit-price snapshot on `ORDER_ITEMS`, so later menu changes never alter an existing order.
