# LabSynch: Work Breakdown Structure & Gantt Chart

## 1. Work Breakdown Structure (WBS)

### Phase 1: Backend API Development (✅ Completed)
- **1.1 Setup & Auth**: Django project, DRF configuration, JWT auth, Role models (`ADMIN`, `SCHOOL`).
- **1.2 Equipment Management**: Models (`Equipment`, `PricingRule`), CRUD services, constraints.
- **1.3 Booking Engine**: Cart creation, complex availability checks, SQL transaction locking.
- **1.4 Payments**: M-Pesa Safaricom STK Push, asynchronous webhook processing.
- **1.5 Inventory Lifecycle**: Issuances, Returns, Damage Reports, and Maintenance pooling.
- **1.6 QA Verification**: Comprehensive Pytest coverage verifying the entire logic scope.

### Phase 2: Frontend Client Development (🚧 Pending)
- **2.1 Initialization**: Next.js/React layout setup, routing structures, styling foundations.
- **2.2 Auth Integration**: Login pages, JWT lifecycle client configuration, Register form.
- **2.3 School Perspective Interface**: Catalog UI, Cart UI, M-Pesa checkout wizard, personal dashboard.
- **2.4 Admin Perspective Interface**: Datatables for global orders, forms for executing Return handovers, Damage charge assignments, and Maintenance trackers.

### Phase 3: Post-Production & Handoff (⏳ Future)
- **3.1 Global QA / UAT**: Integration tests running both the front and backend cohesively.
- **3.2 Server Provisioning**: Setup cloud database, caching (Redis), web server, static proxies.
- **3.3 Go-Live Deployment**.

---

## 2. Project Gantt Chart

```mermaid
gantt
    title LabSynch Project Timeline
    dateFormat  YYYY-MM-DD
    section Backend (Done)
    System Architecture & Auth     :done, b1, 2026-03-01, 3d
    Equipment & Booking Engine     :done, b2, after b1, 4d
    M-Pesa Payments Lifecycle      :done, b3, after b2, 2d
    Issuances, Returns, Damages    :done, b4, after b3, 3d
    Pytest Verification            :done, b5, after b4, 1d

    section Frontend
    Project Scaffold & Auth UI     :active, f1, 2026-03-31, 3d
    School Tenant UX (Catalog/Cart):        f2, after f1, 5d
    Admin Dashboard (Orders/Logs)  :        f3, after f2, 5d
    M-Pesa Visual Payment Flow     :        f4, after f3, 2d

    section QA & Deploy
    End-to-End Testing (UAT)       :        q1, after f4, 4d
    Server Config & Go-Live        :        q2, after q1, 2d
```
