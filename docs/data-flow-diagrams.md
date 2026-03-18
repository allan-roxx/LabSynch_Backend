# Data Flow Diagrams (DFD) - Proposed Labsych System

## Description
These diagrams show how data flows through the proposed Labsych digital platform, from user input to system processing to outputs.

---

## Organizational Structure

### 4.5.1 Organizational Structure

The proposed Labsych system will operate within a multi-institutional context involving the following stakeholders:

```mermaid
graph TB
    subgraph "LABSYCH ORGANIZATION"
        MGT["Labsych Management<br/>(Business Owner)"]
        SYSADMIN["System Administrators<br/>• Manage platform<br/>• Configure settings<br/>• Monitor operations"]
        LABTECH["Laboratory Technicians<br/>• Handle equipment<br/>• Conduct inspections<br/>• Manage handovers"]
        SUPPORT["Support Staff<br/>• Customer service<br/>• Maintenance coordination"]
    end
    
    subgraph "PARTICIPATING SCHOOLS"
        SCHOOL1["Secondary School A"]
        SCHOOL2["Secondary School B"]
        SCHOOL3["Secondary School C"]
        SCHOOLN["...More Schools"]
    end
    
    subgraph "SCHOOL STAFF"
        PRINCIPAL["School Principal<br/>(Approving Authority)"]
        SCIENCEHOD["Head of Science Dept<br/>(Coordinator)"]
        TEACHERS["Science Teachers<br/>• Request equipment<br/>• Plan practicals<br/>• Supervise students"]
        SCHOOLTECH["School Lab Technician<br/>(Optional)"]
    end
    
    subgraph "EXTERNAL SERVICES"
        MPESA["M-Pesa<br/>Payment Gateway"]
        EMAIL["Email/SMS<br/>Notification Service"]
    end
    
    %% Hierarchical relationships
    MGT --> SYSADMIN
    MGT --> LABTECH
    MGT --> SUPPORT
    
    PRINCIPAL --> SCIENCEHOD
    SCIENCEHOD --> TEACHERS
    SCIENCEHOD --> SCHOOLTECH
    
    %% Operational relationships
    SCHOOL1 -.-> SCIENCEHOD
    SCHOOL2 -.-> SCIENCEHOD
    SCHOOL3 -.-> SCIENCEHOD
    SCHOOLN -.-> SCIENCEHOD
    
    TEACHERS -->|"Equipment<br/>requests"| SYSADMIN
    SYSADMIN -->|"Booking<br/>confirmation"| TEACHERS
    
    LABTECH -->|"Equipment<br/>handover"| SCHOOLTECH
    SCHOOLTECH -->|"Equipment<br/>return"| LABTECH
    
    TEACHERS -->|"Payment<br/>initiation"| MPESA
    MPESA -->|"Payment<br/>confirmation"| SYSADMIN
    
    SYSADMIN -->|"Notifications"| EMAIL
    EMAIL -->|"Delivery to"| TEACHERS
    
    style MGT fill:#e1f5ff
    style SYSADMIN fill:#fff4e1
    style LABTECH fill:#fff4e1
    style SCIENCEHOD fill:#e8f5e9
    style TEACHERS fill:#e8f5e9
```

### Roles and Responsibilities

| Stakeholder | Role | System Interaction | Responsibilities |
|-------------|------|-------------------|------------------|
| **Labsych Management** | Business Owner | Strategic oversight | - Define business policies<br/>- Set pricing strategies<br/>- Approve major decisions |
| **System Administrators** | Platform Manager | Full system access | - Configure equipment catalog<br/>- Manage user accounts<br/>- Generate reports<br/>- Handle system settings |
| **Laboratory Technicians** | Operations Staff | Equipment management | - Physical equipment handling<br/>- Conduct handover/return inspections<br/>- Report damages<br/>- Coordinate maintenance |
| **Participating Schools** | Client Organization | Institutional entity | - Register with Labsych<br/>- Maintain account standing<br/>- Ensure equipment safety |
| **School Principal** | Approving Authority | Budget approval | - Authorize equipment bookings<br/>- Approve expenditure<br/>- Oversee science department |
| **Head of Science** | Department Coordinator | Primary user account | - Coordinate equipment needs<br/>- Manage booking calendar<br/>- Liaise with Labsych |
| **Science Teachers** | End Users | Equipment requestors | - Request specific equipment<br/>- Plan practical sessions<br/>- Supervise equipment use<br/>- Report issues |
| **School Lab Technician** | School-side Handler | Optional role | - Collect equipment from Labsych<br/>- Prepare for lessons<br/>- Return equipment<br/>- Assist with inspections |

### Communication Hierarchy

```mermaid
flowchart LR
    subgraph "Request Flow"
        T1[Science Teacher] -->|1. Equipment need| HOD[Head of Science]
        HOD -->|2. Create booking| SYS[Labsych System]
        SYS -->|3. Confirmation| HOD
        HOD -->|4. Schedule| T1
    end
    
    subgraph "Approval Flow"
        HOD2[Head of Science] -->|Budget request| PRIN[Principal]
        PRIN -->|Approved| HOD2
        HOD2 -->|Proceed payment| SYS2[Labsych System]
    end
    
    subgraph "Operational Flow"
        SYS3[Labsych System] -->|Pickup notification| TECH[School Lab Tech]
        TECH -->|Collect equipment| LABTECH[Labsych Technician]
        LABTECH -->|Handover + inspection| TECH
        TECH -->|Deliver to| TEACH[Science Teacher]
    end
```

---

## Level 0 DFD (Context Diagram)

```mermaid
flowchart TB
    subgraph EXTERNAL["External Entities"]
        SCHOOL["School<br/>(Teacher/Administrator)"]
        ADMIN["Labsych<br/>Administrator"]
        MPESA["M-Pesa<br/>Payment Gateway"]
        EMAIL["Email/SMS<br/>Service"]
    end
    
    subgraph SYSTEM["LABSYCH SYSTEM<br/>(Web-Based Platform)"]
        CORE(("0<br/>Labsych<br/>Equipment<br/>Rental<br/>Platform"))
    end
    
    %% School interactions
    SCHOOL -->|"Login credentials<br/>Equipment search<br/>Booking request<br/>Payment instruction"| CORE
    CORE -->|"Equipment catalog<br/>Booking confirmation<br/>Invoice<br/>Equipment handover schedule"| SCHOOL
    
    %% Admin interactions
    ADMIN -->|"Equipment data<br/>Pricing rules<br/>Maintenance records<br/>Damage assessments"| CORE
    CORE -->|"System reports<br/>Booking analytics<br/>Revenue reports<br/>Equipment status"| ADMIN
    
    %% M-Pesa integration
    CORE -->|"Payment request<br/>(Amount, phone)"| MPESA
    MPESA -->|"Payment confirmation<br/>Transaction ID"| CORE
    
    %% Email/SMS notifications
    CORE -->|"Booking confirmation<br/>Reminders<br/>Receipts"| EMAIL
    EMAIL -->|"Delivery status"| CORE
```

---

## Level 1 DFD (Major Processes)

```mermaid
flowchart TB
    %% External Entities
    SCHOOL["School"]
    ADMIN["Admin"]
    MPESA["M-Pesa"]
    EMAIL["Email/SMS"]
    
    %% Major Processes
    P1(("1.0<br/>User<br/>Management"))
    P2(("2.0<br/>Equipment<br/>Management"))
    P3(("3.0<br/>Booking<br/>Processing"))
    P4(("4.0<br/>Payment<br/>Processing"))
    P5(("5.0<br/>Equipment<br/>Lifecycle<br/>Management"))
    P6(("6.0<br/>Reporting &<br/>Analytics"))
    
    %% Data Stores
    D1[("D1: Users<br/>Database")]
    D2[("D2: Equipment<br/>Inventory")]
    D3[("D3: Bookings<br/>Database")]
    D4[("D4: Transactions<br/>Database")]
    D5[("D5: Maintenance<br/>Log")]
    D6[("D6: Audit<br/>Trail")]
    
    %% School flows
    SCHOOL -->|"Registration data<br/>Login credentials"| P1
    P1 -->|"Authentication<br/>token"| SCHOOL
    
    SCHOOL -->|"Search query"| P2
    P2 -->|"Available<br/>equipment list"| SCHOOL
    
    SCHOOL -->|"Booking request<br/>(items, dates, qty)"| P3
    P3 -->|"Booking<br/>confirmation"| SCHOOL
    
    SCHOOL -->|"Payment<br/>initiation"| P4
    P4 -->|"Receipt &<br/>status"| SCHOOL
    
    %% Admin flows
    ADMIN -->|"Equipment data<br/>Pricing updates"| P2
    ADMIN -->|"Maintenance<br/>schedule"| P5
    ADMIN -->|"Report<br/>request"| P6
    P6 -->|"Analytics<br/>dashboard"| ADMIN
    
    %% M-Pesa integration
    P4 <-->|"Payment<br/>request/response"| MPESA
    
    %% Email/SMS
    P3 -->|"Notification<br/>request"| EMAIL
    P4 -->|"Receipt<br/>email"| EMAIL
    
    %% Data store interactions
    P1 <-->|"User data"| D1
    P2 <-->|"Equipment data"| D2
    P3 <-->|"Booking data"| D3
    P3 -->|"Update<br/>availability"| D2
    P4 <-->|"Transaction data"| D4
    P4 -->|"Update booking<br/>status"| D3
    P5 <-->|"Equipment status"| D2
    P5 <-->|"Maintenance<br/>records"| D5
    P6 -->|"Query all<br/>data"| D1
    P6 -->|"Query all<br/>data"| D2
    P6 -->|"Query all<br/>data"| D3
    P6 -->|"Query all<br/>data"| D4
    P1 -->|"Log actions"| D6
    P3 -->|"Log actions"| D6
    P4 -->|"Log actions"| D6
```

---

## Level 2 DFD - Process 3.0 (Booking Processing) Decomposition

```mermaid
flowchart TB
    SCHOOL["School"]
    EMAIL["Email/SMS"]
    
    %% Sub-processes
    P31(("3.1<br/>Validate<br/>Booking<br/>Request"))
    P32(("3.2<br/>Check<br/>Availability"))
    P33(("3.3<br/>Calculate<br/>Pricing"))
    P34(("3.4<br/>Create<br/>Booking<br/>Record"))
    P35(("3.5<br/>Update<br/>Inventory"))
    P36(("3.6<br/>Generate<br/>Confirmation"))
    
    %% Data Stores
    D2[("D2: Equipment<br/>Inventory")]
    D3[("D3: Bookings<br/>Database")]
    D7[("D7: Pricing<br/>Rules")]
    
    %% Flow
    SCHOOL -->|"Booking request<br/>(equipment IDs,<br/>quantities, dates)"| P31
    
    P31 -->|"Validated<br/>request"| P32
    P31 -->|"Invalid<br/>request"| SCHOOL
    
    P32 <-->|"Check stock &<br/>schedule"| D2
    P32 -->|"Unavailable"| SCHOOL
    P32 -->|"Available<br/>items list"| P33
    
    P33 <-->|"Get pricing<br/>rules"| D7
    P33 -->|"Total cost<br/>calculation"| P34
    
    P34 -->|"Booking record"| D3
    P34 -->|"Booking ID"| P35
    
    P35 -->|"Reserve<br/>quantity"| D2
    D2 -->|"Updated<br/>availability"| P35
    
    P35 -->|"Success"| P36
    
    P36 -->|"Booking details"| D3
    P36 -->|"Confirmation<br/>notification"| EMAIL
    P36 -->|"Booking<br/>confirmation"| SCHOOL
```

---

## Level 2 DFD - Process 4.0 (Payment Processing) Decomposition

```mermaid
flowchart TB
    SCHOOL["School"]
    MPESA["M-Pesa API"]
    EMAIL["Email/SMS"]
    
    %% Sub-processes
    P41(("4.1<br/>Initiate<br/>Payment<br/>Request"))
    P42(("4.2<br/>Send<br/>M-Pesa<br/>STK Push"))
    P43(("4.3<br/>Process<br/>Callback"))
    P44(("4.4<br/>Update<br/>Transaction<br/>Record"))
    P45(("4.5<br/>Update<br/>Booking<br/>Status"))
    P46(("4.6<br/>Generate<br/>Receipt"))
    
    %% Data Stores
    D3[("D3: Bookings")]
    D4[("D4: Transactions")]
    
    %% Flow
    SCHOOL -->|"Payment initiation<br/>(Booking ID,<br/>M-Pesa number)"| P41
    
    P41 <-->|"Get amount<br/>due"| D3
    P41 -->|"Payment request<br/>details"| P42
    P41 -->|"Create pending<br/>transaction"| D4
    
    P42 -->|"STK Push<br/>request"| MPESA
    MPESA -->|"Checkout<br/>Request ID"| P42
    P42 -->|"Update with<br/>Checkout ID"| D4
    P42 -->|"Awaiting<br/>payment"| SCHOOL
    
    MPESA -->|"Payment callback<br/>(Success/Fail)"| P43
    
    P43 -->|"Payment<br/>result"| P44
    
    P44 <-->|"Update<br/>transaction"| D4
    
    P44 -->|"Success"| P45
    P44 -->|"Failed"| SCHOOL
    
    P45 <-->|"Update status<br/>to 'PAID'"| D3
    P45 -->|"Payment<br/>confirmed"| P46
    
    P46 -->|"Receipt data"| D4
    P46 -->|"Receipt<br/>email"| EMAIL
    P46 -->|"Receipt &<br/>confirmation"| SCHOOL
```

---

## Level 2 DFD - Process 5.0 (Equipment Lifecycle) Decomposition

```mermaid
flowchart TB
    ADMIN["Admin"]
    SCHOOL["School"]
    
    %% Sub-processes
    P51(("5.1<br/>Schedule<br/>Maintenance"))
    P52(("5.2<br/>Record<br/>Equipment<br/>Issue/Return"))
    P53(("5.3<br/>Inspect<br/>Condition"))
    P54(("5.4<br/>Process<br/>Damage<br/>Report"))
    P55(("5.5<br/>Update<br/>Equipment<br/>Status"))
    
    %% Data Stores
    D2[("D2: Equipment<br/>Inventory")]
    D3[("D3: Bookings")]
    D5[("D5: Maintenance<br/>Log")]
    D8[("D8: Damage<br/>Records")]
    
    %% Maintenance flow
    ADMIN -->|"Maintenance<br/>schedule"| P51
    P51 <-->|"Equipment<br/>list"| D2
    P51 -->|"Schedule<br/>entry"| D5
    P51 -->|"Mark as<br/>unavailable"| D2
    
    %% Issue/Return flow
    SCHOOL -->|"Equipment<br/>return"| P52
    P52 <-->|"Booking<br/>details"| D3
    P52 -->|"Handover<br/>record"| P53
    
    %% Inspection
    P53 -->|"Condition<br/>report"| P54
    
    %% Damage processing
    P54 -->|"No damage"| P55
    P54 -->|"Damage<br/>found"| D8
    D8 -->|"Damage<br/>charge"| SCHOOL
    D8 -->|"Update<br/>status"| P55
    
    %% Status update
    P55 -->|"Update<br/>availability"| D2
    P55 -->|"Mark booking<br/>complete"| D3
    P55 -->|"Needs<br/>maintenance"| D5
```

---

## Data Store Descriptions

| ID | Name | Description | Access Pattern |
|----|------|-------------|----------------|
| **D1** | Users Database | Stores school and admin user accounts, credentials, profiles | Read/Write by P1 |
| **D2** | Equipment Inventory | Tracks all equipment items, quantities, availability, status | Read/Write by P2, P3, P5 |
| **D3** | Bookings Database | Records all booking transactions, status, dates | Read/Write by P3, P4, P5 |
| **D4** | Transactions Database | Financial transaction records, M-Pesa references, receipts | Read/Write by P4 |
| **D5** | Maintenance Log | Maintenance schedules, repair records, equipment history | Read/Write by P5 |
| **D6** | Audit Trail | System activity logs for security and debugging | Write-only by all processes |
| **D7** | Pricing Rules | Dynamic pricing algorithm parameters | Read by P3.3 |
| **D8** | Damage Records | Equipment damage reports, photos, charges | Read/Write by P5.4 |

---

## Process Descriptions

### Process 1.0: User Management
Handles school registration, authentication, profile management. Uses KU email verification for schools.

### Process 2.0: Equipment Management
Manages equipment catalog, categorization, pricing, and availability display. Admin can add/edit equipment.

### Process 3.0: Booking Processing
Core booking engine that validates requests, checks availability, calculates pricing, and creates reservations.

### Process 4.0: Payment Processing
Integrates with M-Pesa for payment collection, handles callbacks, generates receipts.

### Process 5.0: Equipment Lifecycle Management
Tracks equipment from issue to return, manages maintenance, handles damage reports.

### Process 6.0: Reporting & Analytics
Generates reports on utilization, revenue, popular items, school activity, system health.

---

## Key Improvements Over Current System

### Real-Time Data Flow
- **Current**: Sequential manual lookups
- **Proposed**: Parallel database queries with instant results

### Automated Notifications
- **Current**: Verbal confirmations only
- **Proposed**: Email/SMS at every stage (booking, payment, reminder, completion)

### Data Integrity
- **Current**: No referential integrity, manual reconciliation
- **Proposed**: Database constraints, automatic consistency checks

### Scalability
- **Current**: Limited by staff availability
- **Proposed**: Handles 100+ concurrent bookings automatically

### Traceability
- **Current**: No audit trail
- **Proposed**: Complete audit log of all transactions (D6)
