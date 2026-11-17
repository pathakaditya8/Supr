# Sequence diagrams

These UML sequence diagrams trace the main Supr interactions as implemented in `backend/app/main.py`, `backend/app/security.py` and `frontend/src/App.tsx` (state on 2026-11-17). Messages name the real API routes; error replies show the HTTP status the API returns.

Participants used throughout:

- **Browser UI**: the React single-page app (`App.tsx`).
- **API**: the FastAPI application (`main.py`), including the `current_user` / `allow(role)` dependencies.
- **Security**: token and password helpers (`security.py`).
- **Database**: SQLAlchemy models over SQLite (PostgreSQL via `DATABASE_URL`).

## 1. Sign-in and role-checked request

Covers FR-01 and NFR-01. Every protected route repeats the token and role check shown in the second half.

```mermaid
sequenceDiagram
    autonumber
    actor U as Student, vendor or admin
    participant UI as Browser UI
    participant API as API
    participant SEC as Security
    participant DB as Database

    U->>UI: Enter email and password
    UI->>API: POST /api/auth/login
    API->>DB: Find user by lower-cased email
    DB-->>API: User record or none
    API->>SEC: verify_password(password, Argon2 hash)
    SEC-->>API: true or false
    alt Unknown email or wrong password
        API-->>UI: 401 Email or password is incorrect
        UI-->>U: Show the same generic error
    else Credentials valid
        API->>SEC: issue_token(user id, role)
        SEC-->>API: HMAC-signed token with expiry
        API-->>UI: 200 access token and user profile
        UI->>UI: Save token and user in localStorage
        UI-->>U: Open the role workspace
    end

    Note over U,DB: Any later protected request
    U->>UI: Open a protected screen
    UI->>API: Request with Authorization Bearer token
    API->>SEC: read_token(token)
    SEC-->>API: Payload, or none if tampered or expired
    alt Token missing, invalid or expired
        API-->>UI: 401 Please sign in to continue
    else Token valid
        API->>DB: Load user by id
        DB-->>API: User
        alt Account disabled or deleted
            API-->>UI: 401 Account unavailable
        else Role not allowed for this route
            API-->>UI: 403 This account cannot access that area
        else Role allowed
            API-->>UI: 200 requested data
        end
    end
```

## 2. Student places an order

Covers FR-07, FR-08 and NFR-02. Prices are always recalculated on the server, and the cart is limited to one vendor.

```mermaid
sequenceDiagram
    autonumber
    actor S as Student
    participant UI as Browser UI
    participant API as API
    participant DB as Database

    S->>UI: Choose an item, size or variant and add-ons
    UI->>API: POST /api/cart/items with product, variant, add-ons, quantity
    API->>DB: Load product and its vendor
    DB-->>API: Product and vendor
    alt Item unpublished, unavailable or not enough stock
        API-->>UI: 409 This listing is unavailable or has insufficient stock
    else Vendor not approved
        API-->>UI: 409 This vendor is not active
    else Cart already holds another vendor's items
        API-->>UI: 409 Your cart can contain items from one vendor only
        UI-->>S: Ask the student to clear the cart first
    else Item can be added
        API->>DB: Recalculate price from variant and add-on records
        alt Variant missing or add-on unknown or unpriced
            API-->>UI: 422 Invalid variant or add-on selection
        else Selection valid
            API->>DB: Create or update the cart line
            API-->>UI: 201 cart with server-calculated subtotal
            UI-->>S: Show updated bag
        end
    end

    S->>UI: Checkout and pick a delivery point if offered
    UI->>API: POST /api/orders with delivery location
    API->>DB: Load cart and vendor
    alt Delivery point not one the vendor supports
        API-->>UI: 422 Choose one of this vendor's supported delivery locations
    else Order can be placed
        loop Each cart line
            API->>DB: Re-check availability and recalculate price
        end
        API->>DB: Insert order with status pending
        loop Each cart line
            API->>DB: Insert order item snapshot of name, price, variant, add-ons
            API->>DB: Conditional update that lowers stock only if enough remains
            alt Another order took the last stock first
                API-->>UI: 409 A cart item just sold out
                Note over API,DB: Transaction is not committed, nothing is saved
            end
        end
        API->>DB: Empty cart, notify vendor, write audit log, commit
        API-->>UI: 201 order id, status pending, subtotal
        UI-->>S: Show order confirmation
    end
```

## 3. Vendor fulfils an order

Covers FR-09 and FR-11. The API only allows the transitions listed in `update_order_status`.

```mermaid
sequenceDiagram
    autonumber
    actor V as Vendor
    participant UI as Browser UI
    participant API as API
    participant DB as Database
    actor S as Student

    V->>UI: Open Orders tab
    UI->>API: GET /api/orders
    API->>DB: Orders where vendor is this vendor
    DB-->>API: Only this vendor's orders
    API-->>UI: Order list
    V->>UI: Accept, reject, or move to the next stage
    UI->>API: PATCH /api/orders/{id}/status with new status
    API->>DB: Load vendor profile and order
    alt Vendor not approved
        API-->>UI: 403 Only approved vendors can manage listings and orders
    else Order belongs to another vendor
        API-->>UI: 404 Order not found
    else Transition not allowed, for example pending to ready
        API-->>UI: 409 That order status change is not allowed
    else Rejected or cancelled
        API->>DB: Return each item's quantity to stock
        API->>DB: Save status, notify student, write audit log
        API-->>UI: 200 new status
    else Accepted, preparing, ready, out for delivery (campus delivery only) or completed
        API->>DB: Save status, notify student, write audit log
        API-->>UI: 200 new status
    end
    S->>UI: Open notifications or Your orders
    UI->>API: GET /api/notifications and GET /api/orders
    API-->>UI: Order is now accepted, preparing, ready or completed
```

## 4. Vendor application, admin approval and participation control

Covers FR-04, FR-05, FR-10, FR-13 and NFR-05. A vendor's menu is visible to students only while the vendor's status is approved.

```mermaid
sequenceDiagram
    autonumber
    actor V as Vendor
    participant UI as Browser UI
    participant API as API
    participant DB as Database
    actor A as University Admin

    V->>UI: Fill in business details
    UI->>API: POST /api/vendor/applications
    alt Vendor already approved or stopped
        API-->>UI: 409 This vendor is already participating
    else Application already pending
        API-->>UI: 409 An application is already awaiting review
    else New or resubmitted application
        API->>DB: Save application with status pending
        API->>DB: Notify vendor that review is pending
        API-->>UI: 201 application pending
    end
    V->>UI: Attach supporting document
    UI->>API: POST /api/vendor/application/documents
    API->>DB: Store file privately and record the document

    A->>UI: Open Applications
    UI->>API: GET /api/admin/applications
    API-->>UI: Pending applications with document links
    A->>UI: Review documents
    UI->>API: GET /api/admin/documents/{id}
    API-->>UI: File, admin only
    A->>UI: Approve or reject, record agreement validity and remarks
    UI->>API: POST /api/admin/applications/{id}/decision
    alt Approving without recording agreement validity
        API-->>UI: 400 Record agreement validity before approval
    else Decision recorded
        API->>DB: Set application and vendor status
        API->>DB: Write approval history and audit log
        API->>DB: Notify vendor of the decision
        API-->>UI: 200 decision saved
        Note over API,DB: Approved vendor's published menu now appears to students
    end

    opt Later, admin stops or restarts the vendor
        A->>UI: Stop participation or Restart participation
        UI->>API: POST /api/admin/vendors/{id}/participation
        API->>DB: Set vendor status to stopped or approved
        API->>DB: Write approval history and audit log, notify vendor
        API-->>UI: 200 new status
        Note over API,DB: Stopped vendor's menu is hidden and checkout is refused
    end
```
