# Use Case Models - Proposed Labsych System

## Description
Complete use case diagrams and descriptions for all actors and their interactions with the Labsych platform.

---

## Use Case Diagram - Complete System

```mermaid
flowchart TB
    subgraph "Actors"
        SCHOOL["🏫 School<br/>Administrator"]
        ADMIN["👤 Labsych<br/>System Admin"]
        SYSTEM["⚙️ System<br/>(Automated)"]
    end
    
    subgraph "Labsych Platform Use Cases"
        subgraph "Authentication & User Management"
            UC1["UC-01<br/>Register School"]
            UC2["UC-02<br/>Verify Email"]
            UC3["UC-03<br/>Login to System"]
            UC4["UC-04<br/>Manage Profile"]
        end
        
        subgraph "Equipment Browsing & Discovery"
            UC5["UC-05<br/>Browse Equipment<br/>Catalog"]
            UC6["UC-06<br/>Search Equipment"]
            UC7["UC-07<br/>View Equipment<br/>Details"]
            UC8["UC-08<br/>Check Availability"]
        end
        
        subgraph "Booking Management (School)"
            UC9["UC-09<br/>Create Booking"]
            UC10["UC-10<br/>Add Items to<br/>Booking"]
            UC11["UC-11<br/>Calculate Price"]
            UC12["UC-12<br/>Submit Booking"]
            UC13["UC-13<br/>View My Bookings"]
            UC14["UC-14<br/>Cancel Booking"]
        end
        
        subgraph "Payment Processing"
            UC15["UC-15<br/>Initiate M-Pesa<br/>Payment"]
            UC16["UC-16<br/>Process Payment<br/>Callback"]
            UC17["UC-17<br/>View Receipt"]
            UC18["UC-18<br/>Download Invoice"]
        end
        
        subgraph "Equipment Handover & Return"
            UC19["UC-19<br/>Record Equipment<br/>Issue"]
            UC20["UC-20<br/>Record Equipment<br/>Return"]
            UC21["UC-21<br/>Inspect Equipment<br/>Condition"]
            UC22["UC-22<br/>Document Damage"]
        end
        
        subgraph "Inventory Management (Admin)"
            UC23["UC-23<br/>Add New<br/>Equipment"]
            UC24["UC-24<br/>Update Equipment<br/>Details"]
            UC25["UC-25<br/>Manage Categories"]
            UC26["UC-26<br/>Set Pricing Rules"]
            UC27["UC-27<br/>Update Stock<br/>Levels"]
        end
        
        subgraph "Maintenance Management"
            UC28["UC-28<br/>Schedule<br/>Maintenance"]
            UC29["UC-29<br/>Record<br/>Maintenance<br/>Completion"]
            UC30["UC-30<br/>View Maintenance<br/>History"]
        end
        
        subgraph "Reporting & Analytics"
            UC31["UC-31<br/>Generate<br/>Utilization Report"]
            UC32["UC-32<br/>Generate<br/>Revenue Report"]
            UC33["UC-33<br/>View Booking<br/>Analytics"]
            UC34["UC-34<br/>Export Data"]
        end
        
        subgraph "Notifications"
            UC35["UC-35<br/>Send Booking<br/>Confirmation"]
            UC36["UC-36<br/>Send Payment<br/>Receipt"]
            UC37["UC-37<br/>Send Pickup<br/>Reminder"]
            UC38["UC-38<br/>Send Return<br/>Reminder"]
        end
    end
    
    %% School Actor Relationships
    SCHOOL --> UC1
    SCHOOL --> UC3
    SCHOOL --> UC4
    SCHOOL --> UC5
    SCHOOL --> UC6
    SCHOOL --> UC7
    SCHOOL --> UC8
    SCHOOL --> UC9
    SCHOOL --> UC10
    SCHOOL --> UC13
    SCHOOL --> UC14
    SCHOOL --> UC15
    SCHOOL --> UC17
    SCHOOL --> UC18
    
    %% Admin Actor Relationships
    ADMIN --> UC3
    ADMIN --> UC4
    ADMIN --> UC19
    ADMIN --> UC20
    ADMIN --> UC21
    ADMIN --> UC22
    ADMIN --> UC23
    ADMIN --> UC24
    ADMIN --> UC25
    ADMIN --> UC26
    ADMIN --> UC27
    ADMIN --> UC28
    ADMIN --> UC29
    ADMIN --> UC30
    ADMIN --> UC31
    ADMIN --> UC32
    ADMIN --> UC33
    ADMIN --> UC34
    
    %% System Actor Relationships
    SYSTEM --> UC2
    SYSTEM --> UC11
    SYSTEM --> UC12
    SYSTEM --> UC16
    SYSTEM --> UC35
    SYSTEM --> UC36
    SYSTEM --> UC37
    SYSTEM --> UC38
    
    %% Include Relationships
    UC1 -.->|includes| UC2
    UC9 -.->|includes| UC8
    UC9 -.->|includes| UC10
    UC10 -.->|includes| UC11
    UC12 -.->|includes| UC35
    UC15 -.->|includes| UC16
    UC16 -.->|includes| UC36
    UC19 -.->|includes| UC37
    UC20 -.->|includes| UC21
    UC21 -.->|extends| UC22
```

---

## Detailed Use Case Descriptions

### UC-01: Register School

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-01 |
| **Name** | Register School |
| **Actor** | School Administrator (Primary) |
| **Precondition** | - User has KU email address<br/>- School not already registered |
| **Postcondition** | - User account created<br/>- Verification email sent<br/>- Account status: UNVERIFIED |
| **Main Flow** | 1. School admin accesses registration page<br/>2. System displays registration form<br/>3. Admin enters: email (@ku.ac.ke), password, school name, contact info<br/>4. Admin submits form<br/>5. System validates input (email format, password strength)<br/>6. System creates USER record with is_verified=FALSE<br/>7. System creates SCHOOL_PROFILE record<br/>8. System generates verification token<br/>9. System sends verification email via UC-02<br/>10. System displays "Check your email" message |
| **Alternative Flows** | **A1**: Email already exists<br/>- System shows "Email already registered"<br/>- Return to step 3<br/><br/>**A2**: Invalid email domain (not @ku.ac.ke)<br/>- System shows "Must use KU email"<br/>- Return to step 3 |
| **Business Rules** | - Only @ku.ac.ke emails allowed<br/>- Password must be 8+ characters<br/>- School name must be unique |

---

### UC-05: Browse Equipment Catalog

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-05 |
| **Name** | Browse Equipment Catalog |
| **Actor** | School Administrator |
| **Precondition** | - User is logged in<br/>- At least one active equipment exists |
| **Postcondition** | - Equipment list displayed<br/>- User can select equipment for details |
| **Main Flow** | 1. User clicks "Browse Equipment"<br/>2. System displays all categories<br/>3. User selects category (optional)<br/>4. System queries EQUIPMENT table WHERE is_active=TRUE<br/>5. For each equipment, system displays:<br/>   - Primary image<br/>   - Equipment name<br/>   - Category<br/>   - Price per day<br/>   - Available quantity<br/>6. User can click on item for UC-07 |
| **Alternative Flows** | **A1**: No equipment in selected category<br/>- System shows "No items available in this category"<br/><br/>**A2**: User applies filters (price range, availability)<br/>- System refines query<br/>- Return to step 5 |
| **UI Requirements** | - Responsive grid layout<br/>- Pagination (20 items per page)<br/>- Filter sidebar<br/>- Sort by: name, price, availability |

---

### UC-09: Create Booking

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-09 |
| **Name** | Create Booking |
| **Actor** | School Administrator (Primary), System (Supporting) |
| **Precondition** | - User logged in<br/>- User has verified school profile<br/>- At least one equipment available |
| **Postcondition** | - Booking record created with status=PENDING<br/>- Equipment reserved (available_quantity reduced)<br/>- Booking confirmation sent |
| **Main Flow** | 1. User clicks "Create New Booking"<br/>2. System displays booking form<br/>3. User selects pickup date and return date<br/>4. System validates dates (return > pickup, not in past)<br/>5. User searches and selects equipment (includes UC-08)<br/>6. For each equipment, user specifies quantity<br/>7. System checks availability via UC-08<br/>8. User adds equipment to booking (includes UC-10)<br/>9. System calculates total via UC-11<br/>10. User reviews booking summary<br/>11. User adds special instructions (optional)<br/>12. User clicks "Submit Booking"<br/>13. System validates entire booking<br/>14. System creates BOOKING record<br/>15. System creates BOOKING_ITEM records<br/>16. System updates EQUIPMENT.available_quantity (reserve)<br/>17. System generates booking reference (BK-2026-0001)<br/>18. System triggers UC-35 (confirmation email)<br/>19. System displays booking confirmation with payment link |
| **Alternative Flows** | **A1**: Insufficient quantity available<br/>- System shows "Only X units available"<br/>- User adjusts quantity or removes item<br/>- Return to step 8<br/><br/>**A2**: Date validation fails<br/>- System shows error message<br/>- Return to step 3<br/><br/>**A3**: User cancels before submission<br/>- System discards draft<br/>- No database changes |
| **Business Rules** | - Minimum booking: 1 day<br/>- Maximum advance booking: 90 days<br/>- Maximum return date: 30 days from pickup<br/>- Quantity must be ≤ available_quantity |
| **Exception Handling** | **E1**: Database error during creation<br/>- System rolls back transaction<br/>- System shows "Booking failed, please try again"<br/>- System logs error to AUDIT_LOG |

---

### UC-15: Initiate M-Pesa Payment

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-15 |
| **Name** | Initiate M-Pesa Payment |
| **Actor** | School Administrator (Primary), M-Pesa API (Secondary), System |
| **Precondition** | - Booking exists with status=CONFIRMED<br/>- Total amount > 0<br/>- User has M-Pesa registered phone |
| **Postcondition** | - PAYMENT record created with status=PENDING<br/>- STK Push sent to user's phone<br/>- User awaiting payment prompt |
| **Main Flow** | 1. User views booking details<br/>2. User clicks "Pay with M-Pesa"<br/>3. System displays payment summary (amount, breakdown)<br/>4. User enters M-Pesa phone number<br/>5. System validates phone number format (07XX or 01XX)<br/>6. User confirms payment<br/>7. System creates PAYMENT record with status=PENDING<br/>8. System generates transaction reference (TXN-2026-0001)<br/>9. System calls M-Pesa STK Push API:<br/>   - Amount: booking.total_amount<br/>   - Phone: user input<br/>   - Reference: booking_reference<br/>   - Callback URL: /api/payments/callback<br/>10. M-Pesa API returns CheckoutRequestID<br/>11. System updates PAYMENT.mpesa_checkout_request_id<br/>12. System displays "Check your phone for M-Pesa prompt"<br/>13. System starts polling for callback (includes UC-16) |
| **Alternative Flows** | **A1**: Invalid phone number<br/>- System shows "Invalid phone format"<br/>- Return to step 4<br/><br/>**A2**: M-Pesa API timeout/error<br/>- System shows "Payment service unavailable"<br/>- System marks payment as FAILED<br/>- User can retry |
| **Timeout Handling** | - User has 2 minutes to complete payment<br/>- After timeout, payment marked as FAILED<br/>- User can initiate new payment |

---

### UC-16: Process Payment Callback

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-16 |
| **Name** | Process Payment Callback |
| **Actor** | System (Primary), M-Pesa API (Trigger) |
| **Precondition** | - PAYMENT record exists with CheckoutRequestID<br/>- M-Pesa sends callback |
| **Postcondition** | - PAYMENT status updated (SUCCESS or FAILED)<br/>- If success: BOOKING status → PAID<br/>- Receipt sent to user |
| **Main Flow** | 1. M-Pesa API POST to /api/payments/callback<br/>2. System receives callback JSON<br/>3. System validates callback signature/authenticity<br/>4. System extracts:<br/>   - CheckoutRequestID<br/>   - ResultCode (0 = success)<br/>   - TransactionID<br/>   - Amount<br/>5. System finds PAYMENT by CheckoutRequestID<br/>6. **IF** ResultCode = 0 (Success):<br/>   7. System updates PAYMENT:<br/>      - status = SUCCESS<br/>      - mpesa_transaction_id = TransactionID<br/>      - completed_at = NOW<br/>      - callback_response = full JSON<br/>   8. System updates BOOKING.status = PAID<br/>   9. System triggers UC-36 (send receipt)<br/>   10. System returns HTTP 200 to M-Pesa<br/>**ELSE** (Payment failed):<br/>   11. System updates PAYMENT.status = FAILED<br/>   12. System stores failure reason<br/>   13. System notifies user of failure<br/>   14. System returns HTTP 200 to M-Pesa |
| **Alternative Flows** | **A1**: Duplicate callback<br/>- System detects payment already processed<br/>- System ignores, returns HTTP 200<br/><br/>**A2**: Amount mismatch<br/>- System logs discrepancy<br/>- Admin review required |
| **Security** | - Validate M-Pesa IP whitelist<br/>- Verify callback signature<br/>- Use HTTPS only |

---

### UC-19: Record Equipment Issue

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-19 |
| **Name** | Record Equipment Issue (Handover) |
| **Actor** | Labsych Admin (Primary), School Representative |
| **Precondition** | - Booking status = PAID<br/>- Current date = pickup_date<br/>- School rep present at pickup location |
| **Postcondition** | - EQUIPMENT_ISSUANCE record created<br/>- BOOKING status → ISSUED<br/>- Photo evidence uploaded |
| **Main Flow** | 1. Admin searches for booking by reference or school<br/>2. System displays booking details and items<br/>3. Admin retrieves physical equipment from storage<br/>4. Admin and school rep count and verify items together<br/>5. Admin takes photo of equipment batch<br/>6. System uploads photo to cloud storage<br/>7. Admin enters any condition notes<br/>8. School rep acknowledges receipt (digital signature or code)<br/>9. System creates EQUIPMENT_ISSUANCE record:<br/>   - booking_id<br/>   - issued_by = admin_user_id<br/>   - received_by = school_user_id<br/>   - issued_at = NOW<br/>   - issue_photo_url<br/>   - issue_notes<br/>10. System updates BOOKING.status = ISSUED<br/>11. System triggers UC-37 (return reminder email)<br/>12. System prints/emails handover receipt |
| **Alternative Flows** | **A1**: Items not ready (under maintenance)<br/>- Admin delays handover<br/>- System sends notification to school<br/><br/>**A2**: School rep doesn't show up<br/>- Admin marks as "no-show"<br/>- System sends follow-up notification |
| **Business Rules** | - Photo is mandatory<br/>- Handover only on/after pickup_date<br/>- All booking items must be issued together |

---

### UC-21: Inspect Equipment Condition

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-21 |
| **Name** | Inspect Equipment Condition (On Return) |
| **Actor** | Labsych Admin (Primary) |
| **Precondition** | - School returning equipment<br/>- EQUIPMENT_ISSUANCE record exists |
| **Postcondition** | - EQUIPMENT_RETURN record created<br/>- Condition documented<br/>- If damage: extends to UC-22 |
| **Main Flow** | 1. School rep brings equipment back<br/>2. Admin searches for booking<br/>3. System displays issued items list<br/>4. For each item:<br/>   5. Admin counts returned quantity<br/>   6. Admin visually inspects condition<br/>   7. Admin compares with issue photo<br/>   8. Admin marks item as: OK / DAMAGED<br/>9. Admin takes photo of returned equipment<br/>10. System creates EQUIPMENT_RETURN record<br/>11. **IF** all items OK:<br/>   12. System sets has_damage = FALSE<br/>   13. System updates EQUIPMENT.available_quantity (+returned)<br/>   14. System updates BOOKING.status = COMPLETED<br/>   15. Go to step 18<br/>**ELSE** (damage detected):<br/>   16. System sets has_damage = TRUE<br/>   17. System extends to UC-22 (Document Damage)<br/>18. System sends completion notification to school |
| **Alternative Flows** | **A1**: Missing items (qty returned < qty issued)<br/>- Admin marks missing items<br/>- System generates damage report for missing items<br/>- Missing items treated as severe damage |
| **UI Requirements** | - Side-by-side comparison: issue photo vs current<br/>- Checklist for each item<br/>- Quick damage marking |

---

### UC-23: Add New Equipment

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-23 |
| **Name** | Add New Equipment to Inventory |
| **Actor** | Labsych System Admin |
| **Precondition** | - User logged in as ADMIN<br/>- Equipment category exists |
| **Postcondition** | - New EQUIPMENT record created<br/>- Equipment visible in catalog<br/>- Equipment images uploaded |
| **Main Flow** | 1. Admin navigates to "Inventory Management"<br/>2. Admin clicks "Add New Equipment"<br/>3. System displays equipment form<br/>4. Admin enters:<br/>   - Equipment name<br/>   - Category (dropdown)<br/>   - Description<br/>   - Total quantity<br/>   - Unit price per day<br/>   - Storage location<br/>   - Condition (default: NEW)<br/>5. System auto-generates equipment_code (EQP-XXX)<br/>6. Admin uploads 1-5 images<br/>7. Admin marks one image as primary<br/>8. System validates all fields<br/>9. System creates EQUIPMENT record with:<br/>   - available_quantity = total_quantity<br/>   - is_active = TRUE<br/>10. System creates EQUIPMENT_IMAGE records<br/>11. System logs action in AUDIT_LOG<br/>12. System displays success message<br/>13. Equipment now appears in catalog |
| **Validation Rules** | - Equipment name: 3-100 characters<br/>- Total quantity: > 0<br/>- Unit price: > 0<br/>- At least 1 image required<br/>- Description: 20-500 characters |
| **Alternative Flows** | **A1**: Duplicate equipment name<br/>- System warns "Similar item exists"<br/>- Admin can confirm or modify |

---

### UC-31: Generate Utilization Report

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-31 |
| **Name** | Generate Equipment Utilization Report |
| **Actor** | Labsych System Admin |
| **Precondition** | - User logged in as ADMIN<br/>- Historical booking data exists |
| **Postcondition** | - Report generated and displayed<br/>- Option to export as PDF/Excel |
| **Main Flow** | 1. Admin navigates to "Reports & Analytics"<br/>2. Admin selects "Utilization Report"<br/>3. Admin specifies:<br/>   - Date range (from, to)<br/>   - Equipment category (optional)<br/>   - Report format (Summary/Detailed)<br/>4. Admin clicks "Generate"<br/>5. System queries:<br/>   - Total bookings per equipment<br/>   - Total days rented per equipment<br/>   - Revenue per equipment<br/>   - Utilization rate: (days rented / days available) × 100<br/>   - Most popular items<br/>   - Underutilized items<br/>6. System calculates metrics<br/>7. System generates visual charts:<br/>   - Bar chart: bookings per category<br/>   - Pie chart: revenue distribution<br/>   - Line chart: utilization over time<br/>8. System displays report on screen<br/>9. Admin can export to PDF or Excel |
| **Report Metrics** | - **Utilization Rate**: % of time equipment was rented<br/>- **Revenue per Item**: Total income per equipment<br/>- **Turnover Rate**: Bookings per month<br/>- **Idle Equipment**: Items not booked in X days |
| **Business Value** | - Identify equipment to purchase more of<br/>- Identify equipment to retire<br/>- Optimize inventory investment |

---

## Use Case Priority Matrix

| Priority | Use Cases | Rationale |
|----------|-----------|-----------|
| **Critical (MVP)** | UC-01, UC-03, UC-05, UC-07, UC-09, UC-11, UC-15, UC-16, UC-23 | Core booking and payment flow |
| **High** | UC-08, UC-13, UC-19, UC-20, UC-21, UC-24, UC-26, UC-35, UC-36 | Essential operations |
| **Medium** | UC-02, UC-04, UC-14, UC-17, UC-22, UC-27, UC-28, UC-37, UC-38 | Enhances usability |
| **Low** | UC-06, UC-18, UC-25, UC-29, UC-30, UC-31, UC-32, UC-33, UC-34 | Nice-to-have features |

---

## Actor Descriptions

### School Administrator
- **Role**: Represents a secondary school using Labsych
- **Goals**: Find equipment, book easily, pay securely, receive equipment on time
- **Technical Skill**: Medium (comfortable with web forms, M-Pesa)
- **Frequency**: Multiple times per term

### Labsych System Admin
- **Role**: Labsych staff managing operations
- **Goals**: Efficient inventory management, accurate record-keeping, maximize utilization
- **Technical Skill**: High
- **Frequency**: Daily

### System (Automated)
- **Role**: Background processes and integrations
- **Responsibilities**: Email verification, payment callbacks, automated notifications, calculations
- **Trigger**: Events (booking created, payment received, etc.)
