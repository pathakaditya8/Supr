# Entity-relationship diagram

The complete Supr database schema: all 15 tables in `backend/app/models.py`, checked column by column against the live database (`backend/supr.db`, Alembic migrations 0001–0010) on 2026-11-17. Table names match the database; `alembic_version` is Alembic's bookkeeping table and is omitted.

**Notation:** crow's-foot cardinality. `||` exactly one, `o|` zero or one, `o{` zero or more, `|{` one or more. `PK` primary key, `FK` foreign key, `UK` unique.

```mermaid
erDiagram
    USERS ||--o| VENDORS : "owns (vendor role)"
    VENDORS ||--o| VENDOR_APPLICATIONS : submits
    VENDOR_APPLICATIONS ||--o{ VENDOR_DOCUMENTS : "is supported by"
    CATEGORIES ||--o{ PRODUCTS : classifies
    VENDORS ||--o{ PRODUCTS : sells
    PRODUCTS ||--o{ PRODUCT_VARIANTS : "offers sizes or styles"
    PRODUCTS ||--o{ PRODUCT_ADDONS : "offers extras"
    USERS ||--o| CARTS : "has (student role)"
    VENDORS |o--o{ CARTS : "is the current vendor of"
    CARTS ||--o{ CART_ITEMS : contains
    PRODUCTS ||--o{ CART_ITEMS : "is selected in"
    PRODUCT_VARIANTS |o--o{ CART_ITEMS : "is chosen in"
    USERS ||--o{ ORDERS : "places (student role)"
    VENDORS ||--o{ ORDERS : receives
    ORDERS ||--|{ ORDER_ITEMS : snapshots
    PRODUCTS ||--o{ ORDER_ITEMS : "is ordered as"
    USERS ||--o{ APPROVAL_HISTORY : "records (admin role)"
    VENDORS ||--o{ APPROVAL_HISTORY : "is subject of"
    VENDOR_APPLICATIONS |o--o{ APPROVAL_HISTORY : "is decided in"
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o{ AUDIT_LOGS : performs
    VENDORS ||--o{ MENU_SECTION_PHOTOS : "illustrates sections with"

    USERS {
        int id PK
        string name
        string email UK
        string phone
        string password_hash "Argon2"
        string role "student, vendor or admin"
        boolean enabled
        datetime created_at
    }
    CATEGORIES {
        int id PK
        string name UK
    }
    VENDORS {
        int id PK
        int user_id FK,UK
        string business_name
        string phone
        text description
        string status "pending, approved, rejected, stopped, listed"
        boolean delivers_to_bmu
        boolean agreement_valid "null until checked"
        datetime agreement_checked_at
        decimal minimum_order_amount
        text delivery_terms_note
        boolean terms_confirmed
        text delivery_points_json "list of campus points"
    }
    VENDOR_APPLICATIONS {
        int id PK
        int vendor_id FK,UK
        text business_address
        string contact_person
        string agreement_reference
        int delivery_partners "at least 2 to apply; null for older applications"
        string status "pending, approved, rejected"
        datetime submitted_at
        datetime decision_at
        text decision_remarks
    }
    VENDOR_DOCUMENTS {
        int id PK
        int application_id FK
        string filename
        string stored_path "random private file key"
        string content_type
        datetime uploaded_at
    }
    PRODUCTS {
        int id PK
        int vendor_id FK
        int category_id FK
        string name
        text description
        decimal price "null until confirmed"
        int stock
        boolean available
        string image_url
        string dietary
        string spice_level
        string allergens
        string portion
        int prep_time_minutes
        string menu_section
        string menu_status "draft, review, published, paused, removed"
        datetime created_at
    }
    PRODUCT_VARIANTS {
        int id PK
        int product_id FK "unique with name"
        string name
        decimal price "at least 0"
        string dietary
        string preparation
        string portion
        boolean available
    }
    PRODUCT_ADDONS {
        int id PK
        int product_id FK "unique with name"
        string name
        decimal price "null or at least 0"
        boolean available
    }
    CARTS {
        int id PK
        int student_id FK,UK "one cart per student"
        int vendor_id FK "null when empty"
        datetime updated_at
    }
    CART_ITEMS {
        int id PK
        int cart_id FK
        int product_id FK
        int variant_id FK "null if no variants"
        text addon_ids_json
        string selection_key
        int quantity "greater than 0"
    }
    ORDERS {
        int id PK
        int student_id FK
        int vendor_id FK
        string status "pending to completed, or rejected or cancelled"
        boolean campus_delivery
        string delivery_location
        string delivery_stage
        decimal subtotal
        datetime created_at
    }
    ORDER_ITEMS {
        int id PK
        int order_id FK
        int product_id FK
        string product_name "snapshot"
        decimal unit_price "snapshot"
        int quantity
        boolean was_available
        string variant_name "snapshot"
        text addons_json "snapshot"
    }
    APPROVAL_HISTORY {
        int id PK
        int admin_id FK
        int vendor_id FK
        int application_id FK "null for stop or restart"
        string action
        string decision
        text remarks
        datetime created_at
    }
    NOTIFICATIONS {
        int id PK
        int recipient_id FK
        string event_type
        string message
        boolean read
        datetime created_at
    }
    MENU_SECTION_PHOTOS {
        int id PK
        int vendor_id FK "unique with section and diet"
        string menu_section
        string dietary "vegetarian, non_vegetarian or any"
        string image_url "hotlinked Unsplash image"
        string photographer
        string photographer_url
        string photo_page_url
        string source
        string search_query
        datetime created_at
    }
    AUDIT_LOGS {
        int id PK
        int actor_id FK
        string event_type
        string entity_type "vendor, product or order"
        int entity_id "not a foreign key"
        text details
        datetime created_at
    }
```

## Design notes

- **One table for all roles.** `USERS.role` distinguishes students, vendors and admins. A vendor user owns exactly one `VENDORS` row; students own a cart and orders; admins write approval history. The diagram labels each relationship with the role it applies to.
- **One-vendor cart.** `CARTS.vendor_id` holds the vendor of the items currently in the cart, which is how the one-vendor rule (FR-07) is enforced. It is null when the cart is empty.
- **Order snapshots.** `ORDER_ITEMS` copies the product name, unit price, variant name and add-on names at checkout, so later menu or price changes never alter a past order (FR-08).
- **Deliberate denormalisation.** Three columns store small JSON lists instead of separate tables: `VENDORS.delivery_points_json`, `CART_ITEMS.addon_ids_json` and `ORDER_ITEMS.addons_json`. The add-on IDs in a cart line are therefore not enforced by a foreign key; the API re-validates them against `PRODUCT_ADDONS` on every cart read and at checkout.
- **Illustrative section photos.** `MENU_SECTION_PHOTOS` holds one stock photo per vendor menu section (two for sections that mix vegetarian and non-vegetarian items, so a vegetarian item never shows meat), matched to products by `menu_section` text rather than a foreign key. The API shows it only when the product has no `image_url` of its own, and returns it marked as illustrative with the photographer's credit.
- **Polymorphic audit log.** `AUDIT_LOGS.entity_type` plus `entity_id` can point at a vendor, product or order, so `entity_id` has no foreign-key constraint.
- **Database constraints** beyond keys: one cart per student; variant and add-on names unique within a product; variant prices at least 0; add-on prices null or at least 0; cart quantities greater than 0; one cart line per product, variant and add-on combination.
