# State Transition Diagrams - Proposed Labsych System

## Description
State machines showing the lifecycle and valid state transitions for key entities in the Labsych system.

---

## 1. Booking State Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> PENDING: School creates booking
    
    PENDING --> CONFIRMED: School reviews and confirms
    PENDING --> CANCELLED: School cancels before payment
    
    CONFIRMED --> PAID: Payment successful (UC-16)
    CONFIRMED --> CANCELLED: Payment timeout/School cancels
    
    PAID --> ISSUED: Equipment handed over (UC-19)
    PAID --> CANCELLED: Admin cancels (exceptional)
    
    ISSUED --> COMPLETED: Equipment returned & inspected (UC-20/21)
    ISSUED --> OVERDUE: Return date passed
    
    OVERDUE --> COMPLETED: Finally returned & inspected
    
    COMPLETED --> [*]
    CANCELLED --> [*]
    
    note right of PENDING
        - Created via UC-09
        - Equipment reserved
        - Awaiting school confirmation
    end note
    
    note right of CONFIRMED
        - School approved booking
        - Awaiting payment
        - 24hr payment deadline
    end note
    
    note right of PAID
        - Payment successful
        - Awaiting pickup date
        - Cannot be cancelled by school
    end note
    
    note right of ISSUED
        - Equipment physically with school
        - Return date tracked
        - Reminder sent 1 day before
    end note
    
    note right of OVERDUE
        - Past return date
        - Late fees may apply
        - Daily notifications sent
    end note
    
    note right of COMPLETED
        - Equipment returned
        - Final state
        - Damages processed (if any)
    end note
    
    note right of CANCELLED
        - Booking terminated
        - Equipment unreserved
        - Refund if already paid
    end note
```

### Booking State Descriptions

| State | Description | Entry Condition | Exit Condition | Timeout |
|-------|-------------|-----------------|----------------|---------|
| **PENDING** | Initial draft state after creation | UC-09 executed | School confirms or cancels | 24 hours |
| **CONFIRMED** | School approved, awaiting payment | School clicks "Confirm" | Payment received or cancelled | 24 hours |
| **PAID** | Payment successful | M-Pesa callback success (UC-16) | Equipment issued or admin cancel | Until pickup_date |
| **ISSUED** | Equipment in school's possession | UC-19 completed | Equipment returned | Until return_date |
| **OVERDUE** | Past return date, not yet returned | return_date + 1 day | Equipment returned | No limit |
| **COMPLETED** | Successfully closed | UC-20/21 completed, no damage or damage resolved | Terminal state | - |
| **CANCELLED** | Booking terminated | Cancellation triggered | Terminal state | - |

### State Transition Rules

```javascript
// Allowed state transitions (enforced at application layer)
const BOOKING_TRANSITIONS = {
  PENDING: ['CONFIRMED', 'CANCELLED'],
  CONFIRMED: ['PAID', 'CANCELLED'],
  PAID: ['ISSUED', 'CANCELLED'], // CANCELLED only by admin
  ISSUED: ['COMPLETED', 'OVERDUE'],
  OVERDUE: ['COMPLETED'],
  COMPLETED: [], // Terminal
  CANCELLED: []  // Terminal
};

// Validation function
function canTransition(currentState, newState) {
  return BOOKING_TRANSITIONS[currentState].includes(newState);
}
```

---

## 2. Payment State Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> PENDING: User initiates payment (UC-15)
    
    PENDING --> SUCCESS: M-Pesa callback: ResultCode=0
    PENDING --> FAILED: M-Pesa callback: ResultCode≠0
    PENDING --> TIMEOUT: No callback within 2 min
    
    TIMEOUT --> PENDING: User retries payment
    FAILED --> PENDING: User retries payment
    
    SUCCESS --> REFUNDED: Admin issues refund
    
    SUCCESS --> [*]
    FAILED --> [*]
    REFUNDED --> [*]
    
    note right of PENDING
        - STK Push sent to phone
        - CheckoutRequestID recorded
        - Awaiting user to enter PIN
        - Max wait: 2 minutes
    end note
    
    note right of SUCCESS
        - Payment confirmed
        - TransactionID recorded
        - Booking updated to PAID
        - Receipt sent
    end note
    
    note right of FAILED
        - Payment declined/cancelled
        - Reason stored
        - User can retry
    end note
    
    note right of TIMEOUT
        - User didn't respond
        - Can retry payment
    end note
    
    note right of REFUNDED
        - Manual refund processed
        - Booking cancelled
        - Refund reference recorded
    end note
```

### Payment State Business Rules

| State | M-Pesa Action | Booking Impact | Retryable |
|-------|---------------|----------------|-----------|
| **PENDING** | STK Push sent | No change | - |
| **SUCCESS** | Payment confirmed | Status → PAID | No |
| **FAILED** | Payment rejected | Status unchanged | Yes (new payment) |
| **TIMEOUT** | No response | Status unchanged | Yes (same payment can retry) |
| **REFUNDED** | Manual M-Pesa reversal | Status → CANCELLED | No |

---

## 3. Equipment Status State Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> AVAILABLE: Equipment added (UC-23)
    
    AVAILABLE --> RESERVED: Booking created
    AVAILABLE --> NEEDS_MAINTENANCE: Maintenance scheduled (UC-28)
    
    RESERVED --> ISSUED: Equipment handed over
    RESERVED --> AVAILABLE: Booking cancelled
    
    ISSUED --> RETURNED: Equipment returned (UC-20)
    
    RETURNED --> AVAILABLE: Inspection OK (UC-21)
    RETURNED --> DAMAGED: Damage detected (UC-21→UC-22)
    
    DAMAGED --> UNDER_REPAIR: Repair scheduled
    DAMAGED --> RETIRED: Beyond economic repair
    
    UNDER_REPAIR --> AVAILABLE: Repair completed (UC-29)
    UNDER_REPAIR --> RETIRED: Unrepairable
    
    NEEDS_MAINTENANCE --> UNDER_MAINTENANCE: Maintenance started
    
    UNDER_MAINTENANCE --> AVAILABLE: Maintenance completed (UC-29)
    UNDER_MAINTENANCE --> NEEDS_MAINTENANCE: Deferred
    
    AVAILABLE --> RETIRED: Admin retires equipment
    NEEDS_MAINTENANCE --> RETIRED: Admin decision
    
    RETIRED --> [*]
    
    note right of AVAILABLE
        - In warehouse/storage
        - Can be booked
        - available_quantity > 0
    end note
    
    note right of RESERVED
        - In active booking
        - Not available for other bookings
        - Awaiting pickup
    end note
    
    note right of ISSUED
        - Physically with school
        - Not in warehouse
        - Return date tracked
    end note
    
    note right of NEEDS_MAINTENANCE
        - Routine service due
        - Temporarily unavailable
        - Scheduled maintenance
    end note
    
    note right of DAMAGED
        - Returned with damage
        - Damage report filed
        - Awaiting repair decision
    end note
    
    note right of RETIRED
        - Permanently removed
        - No longer bookable
        - is_active = FALSE
    end note
```

### Equipment Availability Logic

```javascript
// How available_quantity is calculated
function updateEquipmentAvailability(equipmentId) {
  const equipment = getEquipment(equipmentId);
  
  // Count units in active bookings (RESERVED or ISSUED)
  const reservedUnits = countUnitsInBookings(equipmentId, 
    ['RESERVED', 'ISSUED']
  );
  
  // Count units under maintenance/repair
  const maintenanceUnits = countUnitsInMaintenance(equipmentId);
  
  // Available = Total - Reserved - Under Maintenance
  const availableQuantity = equipment.total_quantity 
                          - reservedUnits 
                          - maintenanceUnits;
  
  updateDatabase(equipmentId, { available_quantity: availableQuantity });
  
  return availableQuantity;
}
```

---

## 4. User Account State Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> UNVERIFIED: User registers (UC-01)
    
    UNVERIFIED --> ACTIVE: Email verified (UC-02)
    UNVERIFIED --> EXPIRED: 24hrs no verification
    
    EXPIRED --> UNVERIFIED: Resend verification email
    
    ACTIVE --> SUSPENDED: Admin suspends (policy violation)
    ACTIVE --> BLOCKED: Multiple failed payments/fraud
    
    SUSPENDED --> ACTIVE: Admin reactivates
    SUSPENDED --> BLOCKED: Repeated violations
    
    BLOCKED --> ACTIVE: Admin unblocks (exceptional)
    
    ACTIVE --> DELETED: User requests deletion
    SUSPENDED --> DELETED: Admin deletes
    BLOCKED --> DELETED: Admin deletes
    
    DELETED --> [*]
    
    note right of UNVERIFIED
        - Registration complete
        - Email not verified
        - Cannot create bookings
        - 24hr verification window
    end note
    
    note right of ACTIVE
        - Normal operational state
        - Can browse and book
        - Full system access
    end note
    
    note right of SUSPENDED
        - Temporary restriction
        - Cannot create new bookings
        - Can view existing bookings
        - Reason displayed to user
    end note
    
    note right of BLOCKED
        - Severe restriction
        - No new bookings
        - Login allowed (view only)
        - Requires admin intervention
    end note
    
    note right of DELETED
        - Account terminated
        - Data anonymized (GDPR)
        - Booking history retained
    end note
```

### User Account Triggers

| Trigger Event | From State | To State | Actor |
|--------------|------------|----------|-------|
| Registration complete | - | UNVERIFIED | System |
| Email verification link clicked | UNVERIFIED | ACTIVE | User |
| 24hrs elapsed, no verification | UNVERIFIED | EXPIRED | System (cron job) |
| Admin suspends (manual) | ACTIVE | SUSPENDED | Admin |
| Payment failed 3 times | ACTIVE | BLOCKED | System |
| Damage not paid for 30 days | ACTIVE | BLOCKED | System |
| Admin reactivates | SUSPENDED | ACTIVE | Admin |
| User/admin deletes account | ANY | DELETED | User/Admin |

---

## 5. Maintenance Ticket State Diagram

```mermaid
stateDiagram-v2
    [*] --> SCHEDULED: Admin schedules (UC-28)
    
    SCHEDULED --> IN_PROGRESS: Technician starts work
    SCHEDULED --> CANCELLED: No longer needed
    
    IN_PROGRESS --> COMPLETED: Work finished (UC-29)
    IN_PROGRESS --> PENDING_PARTS: Awaiting spare parts
    
    PENDING_PARTS --> IN_PROGRESS: Parts arrived
    PENDING_PARTS --> CANCELLED: Too expensive/obsolete
    
    COMPLETED --> [*]
    CANCELLED --> [*]
    
    note right of SCHEDULED
        - Maintenance planned
        - Date set
        - Equipment marked unavailable
        - Technician assigned
    end note
    
    note right of IN_PROGRESS
        - Work underway
        - Equipment in workshop
        - Progress tracked
    end note
    
    note right of PENDING_PARTS
        - Work paused
        - Spare parts ordered
        - Extended downtime
    end note
    
    note right of COMPLETED
        - Work finished
        - Cost recorded
        - Equipment returned to AVAILABLE
        - Next maintenance scheduled
    end note
```

---

## 6. Damage Report State Diagram

```mermaid
stateDiagram-v2
    [*] --> PENDING: Damage detected (UC-22)
    
    PENDING --> ASSESSED: Admin reviews damage
    
    ASSESSED --> CHARGED: Charge amount set
    ASSESSED --> WAIVED: Minor damage, waived
    
    CHARGED --> PAID: School pays damage fee
    CHARGED --> DISPUTED: School disputes charge
    
    DISPUTED --> CHARGED: Dispute rejected
    DISPUTED --> WAIVED: Dispute accepted
    
    PAID --> REPAIRED: Repair work scheduled
    WAIVED --> REPAIRED: Minor damage, repair anyway
    WAIVED --> CLOSED: No repair needed
    
    REPAIRED --> CLOSED: Equipment back in service
    
    CLOSED --> [*]
    
    note right of PENDING
        - Damage documented
        - Photos uploaded
        - Awaiting assessment
    end note
    
    note right of ASSESSED
        - Admin assessed damage
        - Repair cost estimated
        - Charge amount calculated
    end note
    
    note right of CHARGED
        - School invoiced
        - Payment awaited
        - Equipment not available
    end note
    
    note right of WAIVED
        - No charge to school
        - Reason documented
        - Goodwill gesture
    end note
    
    note right of REPAIRED
        - Repair completed
        - Equipment functional
        - Cost recorded
    end note
```

---

## State Machine Implementation Notes

### Database Storage
Each state is stored as an ENUM field in the respective table:
- `BOOKING.status`
- `PAYMENT.payment_status`
- `EQUIPMENT.condition` (proxy for status)
- `USER.account_status`
- `MAINTENANCE_SCHEDULE.status`
- `DAMAGE_REPORT.resolution_status`

### State Change Logging
Every state transition is logged in `AUDIT_LOG`:

```javascript
function transitionState(entity, entityId, fromState, toState, reason, userId) {
  // Validate transition is allowed
  if (!isValidTransition(entity, fromState, toState)) {
    throw new Error(`Invalid transition: ${fromState} → ${toState}`);
  }
  
  // Update entity state
  updateEntityState(entity, entityId, toState);
  
  // Log transition
  createAuditLog({
    user_id: userId,
    action_type: 'UPDATE',
    entity_type: entity,
    entity_id: entityId,
    description: `State changed: ${fromState} → ${toState}. Reason: ${reason}`
  });
  
  // Trigger side effects (notifications, updates)
  handleStateTransitionSideEffects(entity, entityId, toState);
}
```

### Automated State Transitions
Some transitions are triggered by system cron jobs:

```javascript
// Daily cron job (runs at midnight)
async function checkOverdueBookings() {
  const overdueBookings = await db.query(`
    SELECT booking_id FROM BOOKING 
    WHERE status = 'ISSUED' 
    AND return_date < CURRENT_DATE
  `);
  
  for (const booking of overdueBookings) {
    transitionState('BOOKING', booking.booking_id, 
      'ISSUED', 'OVERDUE', 
      'Automatic: return date passed', 
      SYSTEM_USER_ID
    );
    
    // Send overdue notification
    sendNotification(booking.school_id, 'OVERDUE_NOTICE');
  }
}

// Hourly cron job
async function checkPendingBookingExpiry() {
  const expiredBookings = await db.query(`
    SELECT booking_id FROM BOOKING 
    WHERE status = 'PENDING' 
    AND created_at < NOW() - INTERVAL '24 hours'
  `);
  
  for (const booking of expiredBookings) {
    transitionState('BOOKING', booking.booking_id, 
      'PENDING', 'CANCELLED', 
      'Automatic: 24hr confirmation timeout', 
      SYSTEM_USER_ID
    );
  }
}
```

---

## Key Insights from State Diagrams

### 1. No Backwards Movement
- States generally progress forward (PENDING → CONFIRMED → PAID → ISSUED → COMPLETED)
- Exceptions: TIMEOUT → PENDING (payment retry), SUSPENDED → ACTIVE (reactivation)

### 2. Terminal States
- **COMPLETED**, **CANCELLED** (bookings)
- **SUCCESS**, **FAILED**, **REFUNDED** (payments)
- **RETIRED**, **DELETED** (equipment, users)

### 3. Automated Transitions
- ISSUED → OVERDUE (date-based)
- PENDING → EXPIRED (timeout)
- Payment PENDING → TIMEOUT (no callback)

### 4. Admin Intervention Points
- Any state → CANCELLED (bookings)
- ACTIVE → SUSPENDED (users)
- CHARGED → WAIVED (damages)

These state diagrams ensure data integrity and provide clear business rules for the Labsych platform.
