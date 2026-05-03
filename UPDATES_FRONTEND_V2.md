# LabSynch Frontend — V2 Update Instructions

This document specifies all frontend changes required to match the current backend V2 state.
Read this file top-to-bottom before starting implementation.

---

## 1. Consumables — New Equipment Category

The backend now has an `is_consumable` flag on every equipment item.

### Changes required
- In the equipment catalog and browse views, display a **"Consumable"** badge on items where `is_consumable === true`.
- On booking item cards for consumables, replace the return-related copy with **"Single-use item — no return required"**.
- In the booking summary, group consumables separately from reusable equipment so the user can see what will and won't be returned.
- In the admin equipment list, add a filter for `is_consumable` (checkbox: show consumables only / reusables only).

---

## 2. Acquisition Cost — Equipment Detail (Admin only)

Each equipment item now has an `acquisition_cost` field (KES, nullable).

### Changes required
- On the admin equipment detail page, display **"Acquisition Cost: KES X,XXX"** in the info panel.
- Use this value in the damage report form to pre-fill the **estimated repair/replacement cost** as a reference.
- In the equipment list table (admin), add an optional column for acquisition cost (toggleable).

---

## 3. Overdue Penalty — Booking Detail

The `Booking` object now has an `overdue_penalty` field (Decimal, KES).

### What it means
When equipment is returned after the agreed `return_date`, the backend calculates a penalty charged at **150% of the daily rate** per overdue day, per item. This is stored on the booking at the time of return.

### Changes required
- On the booking detail page (school and admin), display the overdue penalty row when `overdue_penalty > 0`:
  ```
  Overdue Penalty:  KES 1,500.00
  ```
- Show a warning badge on `OVERDUE` bookings in the booking list: **"Equipment overdue — penalty accruing"**.
- In the booking summary footer, show:
  ```
  Equipment Total:   KES 12,000.00
  Transport Cost:    KES    500.00
  Overdue Penalty:   KES  1,500.00
  ─────────────────────────────────
  Total Payable:     KES 14,000.00
  ```
- Penalty is only shown after the booking transitions to `RETURNED` or `COMPLETED`.

---

## 4. Same-Day Booking Constraint

The backend now rejects any booking where `pickup_date <= today`.

### Changes required
- In the date picker for booking creation and cart, **disable today and all past dates** for `pickup_date`.
- Add helper text below the date picker: **"Bookings must be made at least 1 day in advance."**
- If the API returns a validation error on `pickup_date`, surface it as an inline field error (not a toast).

---

## 5. Delivery Status — Issuance Records

`EquipmentIssuance` now has a `delivery_status` field with four values:

| Value | Label |
|---|---|
| `PENDING` | Pending Delivery |
| `ON_TIME` | Delivered On Time |
| `LATE` | Delivered Late |
| `FAILED` | Delivery Failed |

There is also a `delivery_notes` free-text field.

### New API endpoint
```
PATCH /api/issuances/{id}/mark_delivery/
Body: { "delivery_status": "LATE", "delivery_notes": "Driver arrived 2 hours late." }
```

### Changes required — Admin issuance list/detail
- Display a **delivery status badge** on each issuance record (colour-coded: green = ON_TIME, amber = LATE, red = FAILED, grey = PENDING).
- Add a **"Mark Delivery"** action button on the issuance detail page (admin only).
- The action opens a modal with:
  - Dropdown: Delivery Status (`ON_TIME`, `LATE`, `FAILED`)
  - Text area: Delivery Notes (optional)
  - Submit calls `PATCH /api/issuances/{id}/mark_delivery/`
- If `delivery_status === "FAILED"`, show a prominent red alert on both the issuance detail and the related booking detail:
  **"Delivery failed — follow up required."**

### Changes required — School booking detail
- If the related issuance has `delivery_status === "FAILED"`, show: **"Your equipment was not delivered. Please contact LabSynch support."**
- If `delivery_status === "LATE"`, show: **"Your equipment was delivered late. We apologise for the inconvenience."**

---

## 6. Dashboard Metrics — Today's Activity

The admin dashboard API (`GET /api/reports/dashboard/`) now returns three additional fields:

```json
{
  "today_pickups": 3,
  "today_returns": 1,
  "today_pending_payment": 2
}
```

### Changes required
- Add three new KPI cards to the admin dashboard:
  - **Today's Pickups** — bookings with `pickup_date == today`
  - **Today's Returns** — bookings with `return_date == today`
  - **Awaiting Payment Today** — PENDING bookings whose pickup is today (they are about to be overdue if not paid)
- These cards should link to the bookings list filtered by today's date.

---

## 7. Booking Status — Removed APPROVED State

The `APPROVED` status no longer exists. The lifecycle is now:

```
PENDING → (payment) → RESERVED → DISPATCHED → IN_USE → RETURNED → COMPLETED
                                                        ↘ OVERDUE ↗
              ↘ CANCELLED (from PENDING, RESERVED)
```

### Changes required
- Remove any **"Approve"** button from admin booking list/detail.
- Remove any "Awaiting Approval" status messaging.
- Rename the status display:

| Old | New |
|---|---|
| Pending | Pending Payment |
| Approved | *(removed)* |
| Reserved | Reserved |

- For school users, after checkout show: **"Booking created — complete payment to reserve equipment."**
- The Pay Now / STK Push flow must be accessible directly from `PENDING` bookings (it was previously blocked until `APPROVED`).

---

## 8. School Profile — GPS Coordinates & Map

The `SchoolProfile` model has `gps_latitude` and `gps_longitude` (nullable Decimal fields).

### Changes required — School profile edit form
- Add a **map picker** component to the school profile update form.
  - Use [Leaflet.js](https://leafletjs.com/) or Google Maps JavaScript API.
  - Provide a **"Detect my location"** button that calls `navigator.geolocation.getCurrentPosition()` and drops a pin.
  - Allow the user to manually drag the pin to fine-tune position.
  - On confirm, write `gps_latitude` and `gps_longitude` into the form fields.
- Display a small read-only map preview on the profile page showing the stored location.

### Changes required — Admin school profile detail
- Show a read-only map with the school's pin when `gps_latitude` and `gps_longitude` are present.
- If not set, show a prompt: **"No location set — ask the school to update their profile."**

### API
Use `PATCH /api/users/me/school-profile/` with:
```json
{ "gps_latitude": "-1.031920", "gps_longitude": "37.069872" }
```

---

## 9. Analytics — Demand, Usage & School Reports

The backend exposes:
- `GET /api/reports/equipment/` — per-equipment utilisation (times booked, total quantity, total revenue)
- `GET /api/reports/clients/` — per-school activity (booking count, total spend, liability status)
- `GET /api/reports/bookings/?start_date=...&end_date=...` — booking counts by status + average duration

### Changes required — Admin Analytics page
Implement a dedicated **Analytics** section with three sub-pages:

#### 9a. Equipment Demand Report
- Bar chart: **Top 10 most booked equipment** by `times_booked`.
- Table with columns: Equipment Name | Code | Times Booked | Total Units Booked | Total Revenue (KES).
- Export to CSV button.

#### 9b. School Activity Report
- Table: School Name | County | Bookings | Total Spend | Liability Status.
- Colour-code liability status: green = CLEAR, red = HAS_OUTSTANDING.
- Click a school name to go to its admin profile.

#### 9c. Booking Trends
- Date range picker (start / end date) that calls `GET /api/reports/bookings/`.
- Pie chart: bookings by status.
- Single stat: average booking duration (days).

---

## 10. Personnel Scheduling (Document only — not yet implemented on backend)

This feature is planned for a future backend sprint. The frontend should prepare UI scaffolding.

### What is needed
When equipment with `requires_personnel === true` is included in a booking, LabSynch must assign a technician to accompany the equipment during use.

### Planned UI (build the shell now, wire up when API is ready)
- On the admin booking detail for `RESERVED` bookings containing personnel-required equipment, show a **"Assign Technician"** panel.
- The panel should list the required items with their `personnel_description`.
- A placeholder "Select Technician" dropdown (disabled until backend is ready).
- Show a banner: **"Technician assignment required before dispatch"** when personnel items are present and no technician is assigned.

---

## 11. Booking Filtering (Fixed)

The bookings API now fully supports:
- `?status=PENDING` — filter by status
- `?search=BK-2026` — search by booking reference or school name/email
- `?ordering=-created_at` — sort by any of: `created_at`, `pickup_date`, `return_date`, `status`, `total_amount`
- `?page=1&page_size=15` — pagination

### Changes required
- Ensure the admin booking list filter bar sends all active filters as query params.
- Persist filter state in URL query string so a page refresh retains the filters.
- The school booking list should always auto-apply `?ordering=-created_at`.

---

## 12. Booking Detail — Overdue & Penalty Messaging

### For OVERDUE bookings (school view)
Show a prominent banner:
```
⚠ Your equipment is overdue. A penalty of 150% of the daily rate is being
  charged for every day past your agreed return date of [return_date].
  Please return equipment immediately to stop the penalty clock.
```

### For RETURNED bookings with overdue_penalty > 0 (school view)
Show:
```
Your equipment was returned late. An overdue penalty of KES [amount] has
been added to your account.
```

---

## Summary of New / Changed API Surface

| Method | Endpoint | Change |
|---|---|---|
| GET | `/api/reports/dashboard/` | + `today_pickups`, `today_returns`, `today_pending_payment` |
| PATCH | `/api/issuances/{id}/mark_delivery/` | **New** — update delivery status |
| GET | `/api/issuances/` | + `delivery_status`, `delivery_notes` in response |
| GET | `/api/bookings/` | + filtering by `status`, `search`, `ordering` now works |
| GET | `/api/bookings/{id}/` | + `overdue_penalty` field in response |
| PATCH | `/api/school-profiles/{id}/` | + `transport_zone`, `gps_latitude`, `gps_longitude` now writable by admin |
| GET | `/api/equipment/` | + `is_consumable`, `overdue_penalty_rate`, `acquisition_cost` in response |

---

*Generated: 2026-04-17 — reflects backend V2 changes.*
