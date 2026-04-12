# Frontend Requirements — LabSynch Next.js Application

This document describes the frontend work needed to support the seven new backend feature areas. The frontend is a Next.js application consuming the LabSynch Django REST API.

---

## 1. Transport and Location-Based Pricing

### New UI Elements

- **School Profile Settings page** — add fields for `town`, `gps_latitude`, `gps_longitude`, and a `transport_zone` dropdown (fetched from `GET /api/transport-zones/`).
- **Registration form** — optionally collect `town` during sign-up.
- **Cart / Checkout** — add a "Request Delivery" toggle (`requires_transport`). When enabled, show the estimated transport fee (from the school's assigned `transport_zone.base_transport_fee`). When disabled, show "Self-Pickup" label.
- **Booking detail page** — show `requires_transport` flag and `transport_cost` breakdown in the cost summary.

### Admin Panel

- **Transport Zone CRUD** — new admin page (list, create, edit, delete) backed by `GET/POST/PATCH/DELETE /api/transport-zones/`.
- **School Profile edit (admin)** — expose `transport_zone` selector so admins can assign zones to schools.

### API Endpoints Used

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/transport-zones/` | List all zones |
| POST | `/api/transport-zones/` | Create zone (admin) |
| PATCH | `/api/transport-zones/{id}/` | Update zone (admin) |
| DELETE | `/api/transport-zones/{id}/` | Delete zone (admin) |
| PATCH | `/api/cart/` | Send `requires_transport` with cart dates |

---

## 2. Booking Status Refinement (State Machine)

### Status Flow

```
PENDING → APPROVED → RESERVED → DISPATCHED → IN_USE → RETURNED → COMPLETED
                                    ↗ (pickup)
                        RESERVED ──────────→ IN_USE
```

Additionally: `IN_USE → OVERDUE` (system-driven), `PENDING/APPROVED/RESERVED → CANCELLED`.

### UI Changes

- **Booking list** — update status badges with new color-coded states:
  - `PENDING` (grey), `APPROVED` (blue), `RESERVED` (purple), `DISPATCHED` (orange), `IN_USE` (green), `RETURNED` (teal), `COMPLETED` (dark green), `OVERDUE` (red), `CANCELLED` (muted).
- **Booking detail (school user)** — show a visual status stepper/timeline reflecting the current position in the flow.
- **Booking detail (admin)** — action buttons appear contextually:
  - PENDING → "Approve" button (`POST /api/bookings/{id}/approve/`)
  - RETURNED → "Complete" button (`POST /api/bookings/{id}/complete/`)
  - PENDING / APPROVED / RESERVED → "Cancel" button (`POST /api/bookings/{id}/cancel/`)
- **Cancel button (school user)** — allow school users to cancel their own bookings while in `PENDING`, `APPROVED`, or `RESERVED` state.
- Remove any references to old `CONFIRMED`, `PAID`, or `ISSUED` statuses.

---

## 3. Trust, Liability, and Enforcement Logic

### School-Side

- **Dashboard banner** — if the logged-in school's `liability_status` is `HAS_OUTSTANDING`, show a prominent warning: _"You have unresolved damage liabilities. New bookings are blocked until resolved."_
- **Create Booking / Checkout** — if the API returns a 400 with a liability error, surface a clear message and link to the school's damage history.

### Admin-Side

- **School profile list** — show `liability_status` column. Filter by `HAS_OUTSTANDING`.
- **Damage report resolution** — after resolving (marking `PAID` / `WAIVED`), the backend auto-recalculates the school's liability. The admin UI refreshes the status badge.

### API Usage

- `liability_status` is returned in `GET /api/school-profiles/` and in the JWT login response `school_profile` object.
- `amount_paid` and `amount_outstanding` fields on `GET /api/damage-reports/{id}/`.

---

## 4. Receipts and Contracts (PDF Downloads)

### New Buttons

- **Payment receipt** — on any completed payment row, add a "Download Receipt" button/icon that hits `GET /api/payments/{id}/receipt/`. The response is `application/pdf`; trigger a browser download.
- **Equipment usage agreement** — on each booking detail page, add a "Download Contract" button that hits `GET /api/bookings/{id}/contract/`. Available once the booking exists (any status).

### Implementation Notes

- Use `fetch()` with `response.blob()` → `URL.createObjectURL()` → programmatic `<a>` click, or use `window.open()`.
- Receipt button should only be visible when `payment_status === "SUCCESS"`.

---

## 5. Inventory System Enhancement

### Equipment Detail (Admin)

- Add fields to the equipment create/edit form:
  - `acquisition_cost` (currency input, optional)
  - `acquisition_date` (date picker, optional)
- Display both on the equipment detail page (admin view).

### Equipment Catalog (School User)

- No change — these fields are informational for admin only.

---

## 6. Advanced Reporting System (Admin Dashboard)

All report endpoints require `ADMIN` role.

### Pages / Tabs

1. **Dashboard Overview** — `GET /api/reports/dashboard/`
   - Cards: Total Bookings, Active Bookings, Overdue Bookings, Total Revenue, Revenue This Month, Total Schools, Total Equipment, Pending Damage Reports.

2. **Booking Analytics** — `GET /api/reports/bookings/?start_date=&end_date=`
   - Date range picker (start/end).
   - Summary: total, average rental duration.
   - Bar/pie chart: bookings by status.

3. **Financial Report** — `GET /api/reports/financial/?start_date=&end_date=`
   - Total revenue, payment count, outstanding damage cost.
   - Line chart for revenue trend (monthly — can compute client-side from raw data or backend can be extended).

4. **Equipment Utilisation** — `GET /api/reports/equipment/`
   - Table: equipment name, code, times booked, total quantity booked, total revenue.
   - Sort by most-booked or highest-revenue.

5. **Client Activity** — `GET /api/reports/clients/`
   - Table: school name, county, liability status, booking count, total spend.
   - Filter by liability status.

### Charting Library

Recommend [Recharts](https://recharts.org/) or [Chart.js](https://www.chartjs.org/) with their React wrappers.

---

## 7. Specialized Equipment Handling

### Equipment Catalog

- If `requires_personnel === true`, show a badge/tag: _"Technician Required"_ and display `personnel_description` and `personnel_cost_per_day`.
- In the cart summary, show a per-item "Personnel Cost" line for items that require a technician.

### Booking Detail

- `BookingItem` now includes `personnel_cost`. Show it as a line item in the booking cost breakdown alongside rental subtotal and transport cost.

### Equipment Create/Edit (Admin)

- Add fields:
  - `requires_personnel` (checkbox)
  - `personnel_cost_per_day` (currency input, shown when checkbox is on)
  - `personnel_description` (text input)

---

## Summary of New/Changed API Endpoints

| Endpoint | Method | Change Type |
|----------|--------|-------------|
| `/api/transport-zones/` | CRUD | **New** |
| `/api/bookings/{id}/approve/` | POST | **New** |
| `/api/bookings/{id}/complete/` | POST | **New** |
| `/api/bookings/{id}/contract/` | GET | **New** (returns PDF) |
| `/api/payments/{id}/receipt/` | GET | **New** (returns PDF) |
| `/api/reports/dashboard/` | GET | **New** |
| `/api/reports/bookings/` | GET | **New** |
| `/api/reports/financial/` | GET | **New** |
| `/api/reports/equipment/` | GET | **New** |
| `/api/reports/clients/` | GET | **New** |
| `/api/cart/` | PATCH | **Updated** — accepts `requires_transport` |
| `/api/bookings/` | POST | **Updated** — accepts `requires_transport` |
| `/api/damage-reports/{id}/resolve/` | POST | **Updated** — accepts `amount_paid` |
| `/api/school-profiles/{id}/` | GET/PATCH | **Updated** — new location & liability fields |
| `/api/equipment/{id}/` | GET/POST/PATCH | **Updated** — new inventory & personnel fields |

---

## Data Model Changes to Reflect in Frontend Types

```typescript
// Updated enums
type BookingStatus =
  | "PENDING"
  | "APPROVED"
  | "RESERVED"
  | "DISPATCHED"
  | "IN_USE"
  | "RETURNED"
  | "COMPLETED"
  | "OVERDUE"
  | "CANCELLED";

type LiabilityStatus = "CLEAR" | "HAS_OUTSTANDING";

// New type
interface TransportZone {
  id: string;
  zone_name: string;
  description: string;
  base_transport_fee: string; // decimal as string
  is_active: boolean;
}

// Updated interfaces (add these fields)
interface SchoolProfile {
  // ...existing fields...
  town: string;
  gps_latitude: string | null;
  gps_longitude: string | null;
  transport_zone: string | null; // UUID
  transport_zone_name: string | null;
  liability_status: LiabilityStatus;
}

interface Booking {
  // ...existing fields...
  requires_transport: boolean;
  transport_cost: string; // decimal
}

interface BookingItem {
  // ...existing fields...
  personnel_cost: string; // decimal
}

interface Equipment {
  // ...existing fields...
  acquisition_cost: string | null;
  acquisition_date: string | null;
  requires_personnel: boolean;
  personnel_cost_per_day: string;
  personnel_description: string;
}

interface DamageReport {
  // ...existing fields...
  amount_paid: string; // decimal
  amount_outstanding: string; // decimal (computed)
}
```
