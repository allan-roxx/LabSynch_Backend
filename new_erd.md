# LabSynch ERD

```mermaid
erDiagram
    USER {
        uuid id PK
        string email
        string full_name
        string user_type
        boolean is_verified
    }

    SCHOOL_PROFILE {
        uuid id PK
        uuid user_id FK
        string school_name
        string registration_number
        string account_status
        string liability_status
    }

    TRANSPORT_ZONE {
        uuid id PK
        string zone_name
        decimal base_transport_fee
        boolean is_active
    }

    EQUIPMENT_CATEGORY {
        uuid id PK
        string category_name
        string description
        int display_order
    }

    EQUIPMENT {
        uuid id PK
        uuid category_id FK
        string equipment_name
        string equipment_code
        int total_quantity
        int available_quantity
        decimal unit_price_per_day
        string condition
        boolean is_active
        boolean is_consumable
        decimal overdue_penalty_rate
        uuid transport_zone_id FK
    }

    EQUIPMENT_IMAGE {
        uuid id PK
        uuid equipment_id FK
        string image_url
        int display_order
        boolean is_primary
    }

    PRICING_RULE {
        uuid id PK
        uuid category_id FK
        int min_days
        int max_days
        decimal discount_percentage
        date effective_from
        date effective_to
        boolean is_active
    }

    CART {
        uuid id PK
        uuid user_id FK
        date pickup_date
        date return_date
        string special_instructions
        boolean requires_transport
    }

    CART_ITEM {
        uuid id PK
        uuid cart_id FK
        uuid equipment_id FK
        int quantity
    }

    BOOKING {
        uuid id PK
        string booking_reference
        uuid school_profile_id FK
        date pickup_date
        date return_date
        string status
        decimal total_amount
        boolean requires_transport
        decimal transport_cost
        decimal overdue_penalty
        boolean penalty_cleared
        decimal penalty_carried_forward
    }

    BOOKING_ITEM {
        uuid id PK
        uuid booking_id FK
        uuid equipment_id FK
        int quantity
        decimal unit_price
        decimal subtotal
        decimal personnel_cost
    }

    PAYMENT {
        uuid id PK
        string transaction_ref
        uuid booking_id FK
        decimal amount_paid
        string payment_method
        string payment_status
        string mpesa_transaction_id
        string mpesa_phone_number
        string mpesa_checkout_request_id
    }

    EQUIPMENT_ISSUANCE {
        uuid id PK
        uuid booking_id FK
        uuid issued_by_id FK
        uuid received_by_id FK
        string delivery_status
        string issue_notes
    }

    EQUIPMENT_RETURN {
        uuid id PK
        uuid booking_id FK
        uuid received_by_id FK
        uuid returned_by_id FK
        boolean has_damage
        string return_notes
    }

    DAMAGE_REPORT {
        uuid id PK
        uuid equipment_return_id FK
        uuid booking_item_id FK
        uuid reported_by_id FK
        int quantity_damaged
        string severity
        decimal repair_cost
        decimal amount_paid
        string resolution_status
    }

    MAINTENANCE_SCHEDULE {
        uuid id PK
        uuid equipment_id FK
        string maintenance_type
        string status
        date scheduled_date
        date completed_date
        decimal cost
    }

    NOTIFICATION {
        uuid id PK
        uuid user_id FK
        string notification_type
        string title
        string body
        boolean is_read
        uuid booking_id
        uuid payment_id
        uuid issuance_id
    }

    USER ||--o| SCHOOL_PROFILE : has
    TRANSPORT_ZONE ||--o{ SCHOOL_PROFILE : serves
    EQUIPMENT_CATEGORY ||--o{ EQUIPMENT : groups
    TRANSPORT_ZONE ||--o{ EQUIPMENT : prices_delivery_for
    EQUIPMENT ||--o{ EQUIPMENT_IMAGE : has
    EQUIPMENT_CATEGORY ||--o{ PRICING_RULE : has
    USER ||--o| CART : owns
    CART ||--o{ CART_ITEM : contains
    EQUIPMENT ||--o{ CART_ITEM : referenced_by
    SCHOOL_PROFILE ||--o{ BOOKING : places
    BOOKING ||--o{ BOOKING_ITEM : contains
    EQUIPMENT ||--o{ BOOKING_ITEM : reserved_as
    BOOKING ||--o{ PAYMENT : paid_by
    BOOKING ||--o| EQUIPMENT_ISSUANCE : issued_for
    USER ||--o{ EQUIPMENT_ISSUANCE : issues
    USER ||--o{ EQUIPMENT_ISSUANCE : receives
    BOOKING ||--o| EQUIPMENT_RETURN : returned_as
    USER ||--o{ EQUIPMENT_RETURN : receives
    USER ||--o{ EQUIPMENT_RETURN : returns
    EQUIPMENT_RETURN ||--o{ DAMAGE_REPORT : may_create
    BOOKING_ITEM ||--o{ DAMAGE_REPORT : damaged_line_item
    USER ||--o{ DAMAGE_REPORT : reports
    EQUIPMENT ||--o{ MAINTENANCE_SCHEDULE : maintained_by
    USER ||--o{ NOTIFICATION : receives
}
```

## Notes

- `SchoolProfile.registration_number` is optional and nullable.
- `Notification.booking_id`, `payment_id`, and `issuance_id` are loose UUID references used for frontend linking.
- `BaseModel` fields such as `id`, `created_at`, and `updated_at` are not repeated on every entity for readability.
