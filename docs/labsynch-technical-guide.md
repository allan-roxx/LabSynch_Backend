
**LabSynch Technical Description for Django + React Team**

LabSynch is a centralized, web-based multi-school laboratory equipment rental and management platform. It replaces manual logbooks and phone-based coordination with a transactional system that supports inventory visibility, booking lifecycle control, digital payments (M-Pesa), issuance/returns, damage accountability, maintenance planning, notifications, and reporting.

This description is aligned with your analysis and design docs, especially entity-relationship-diagram.md, booking-module.md, and user-management-module.md.

## 1. Product Shape (What You Are Building)

- Multi-tenant by institution context (schools as customers), but inventory is centrally managed by LabSynch admins.
- Two primary actor types:
- `SCHOOL` users who browse, book, pay, and track returns.
- `ADMIN` users who manage inventory, approve/issue/receive equipment, process damages, maintenance, reporting, and system settings.
- Core outcomes:
- Real-time equipment availability.
- Conflict-free bookings with date/quantity validation.
- Traceable handover and return workflows.
- End-to-end auditability.

## 2. Recommended Architecture (Django + React)

- Frontend:
- React app (Vite or Next.js frontend mode), role-based dashboards.
- React Router, React Query, form validation (React Hook Form + Zod/Yup), state for auth/session.
- Backend:
- Django + Django REST Framework as API layer.
- Django ORM over PostgreSQL.
- JWT auth (or session auth if same-domain deployment), RBAC permissions by user type.
- Async/background:
- Celery + Redis for notification jobs, payment callback post-processing, scheduled reminders.
- Storage/integrations:
- S3-compatible object storage for equipment and proof photos.
- M-Pesa Daraja API for payments.
- Email/SMS provider for notifications.
- Infrastructure:
- Nginx reverse proxy, HTTPS-only, Linux server.

## 3. Core Modules

- Authentication and User Management:
- Registration, KU email verification, login, password reset, profile updates.
- `USER` + `SCHOOL_PROFILE` 1:1 relationship.
- Inventory Management:
- Equipment categories, equipment records, images, active/inactive status, quantities, pricing baseline.
- Booking Engine:
- Search/filter equipment, availability checks by overlapping date ranges.
- Booking creation, line items, subtotal/tax/total calculation, status transitions.
- Payment Module:
- Initiate payment, store transaction refs, process callback, update booking/payment states atomically.
- Issuance and Return Lifecycle:
- Physical handover records (`EQUIPMENT_ISSUANCE`), return records (`EQUIPMENT_RETURN`), return condition capture.
- Damage and Maintenance:
- Damage reports with severity and charge logic.
- Maintenance schedule tracking and impact on availability.
- Notifications and Audit:
- Outbound notification tracking.
- Full activity logs for key actions.
- Reporting and Settings:
- Operational dashboards, exports, configurable business settings (VAT, limits, reminders).

## 4. Data Model Summary (From ERD)

Primary entities and critical relationships:

- `USER` -> `SCHOOL_PROFILE` (1:1)
- `SCHOOL_PROFILE` -> `BOOKING` (1:N)
- `BOOKING` -> `BOOKING_ITEM` (1:N)
- `BOOKING` -> `PAYMENT` (0..1 or 1..N depending policy; ERD currently models near 1:1)
- `BOOKING` -> `EQUIPMENT_ISSUANCE` (0..1)
- `BOOKING` -> `EQUIPMENT_RETURN` (0..1)
- `EQUIPMENT_CATEGORY` -> `EQUIPMENT` (1:N)
- `EQUIPMENT` -> `EQUIPMENT_IMAGE` (1:N)
- `EQUIPMENT` -> `MAINTENANCE_SCHEDULE` (1:N)
- `EQUIPMENT_RETURN` + `BOOKING_ITEM` + `EQUIPMENT` -> `DAMAGE_REPORT`
- `USER` -> `AUDIT_LOG`, `NOTIFICATION`, admin action tables

Important constraints to enforce in DB + service layer:

- `available_quantity <= total_quantity`
- booking `return_date > pickup_date`
- positive quantities and payment amounts
- unique booking/payment references
- transactional updates for booking creation/cancellation/payment callbacks

## 5. Business Workflows to Implement First

- Booking creation:
- Validate auth, dates, quantities, equipment active state.
- Check overlapping bookings.
- Compute pricing using `PRICING_RULE` + tax from `SYSTEM_SETTING`.
- Create booking + booking items + reserve availability in one DB transaction.
- Payment flow:
- Create pending payment record.
- Trigger M-Pesa request.
- On callback, verify and update payment + booking status atomically.
- Issuance/return flow:
- Admin issues equipment to school user.
- Admin receives return, captures condition.
- If damage exists, create damage reports and charges.
- Cancellation flow:
- Allow only valid states/roles.
- Restore availability and log actions transactionally.

## 6. API Surface (High-Level)

- `/api/auth/*`
- `/api/users/*`, `/api/schools/*`
- `/api/equipment-categories/*`, `/api/equipment/*`, `/api/equipment-images/*`
- `/api/bookings/*`, `/api/booking-items/*`
- `/api/payments/*`, `/api/payments/mpesa/callback`
- `/api/issuances/*`, `/api/returns/*`, `/api/damages/*`
- `/api/maintenance/*`
- `/api/notifications/*`
- `/api/reports/*`
- `/api/settings/*`
- `/api/audit-logs/*` (admin only)

## 7. Frontend App Shape

- Public pages:
- Landing, catalog, equipment detail.
- School portal:
- Dashboard, booking cart/create flow, booking history/status timeline, payment history, profile.
- Admin portal:
- Inventory CRUD, booking operations, issuance/returns desk, damage/maintenance management, reports, settings.
- Shared UX requirements:
- Role-aware navigation.
- Real-time status badges.
- Strong form validation and clear state/error feedback.
- Mobile-responsive layout.

## 8. Implementation Notes for Team Alignment

- Keep statuses as explicit enums and enforce transition guards in service layer.
- Use UUID PKs consistently.
- Use DB transactions around any operation that touches booking/payment/inventory together.
- Add optimistic locking or row-level locking for high-contention inventory updates.
- Generate references (`BK-YYYY-NNNN`, `TXN-YYYY-NNNN`) in backend service, not frontend.
- Maintain full audit logs for admin and critical school actions.
- Prefer soft deactivation (`is_active`) over hard deletes for core business entities.

One important alignment check: your state diagram includes `OVERDUE`, while the ERD booking status list currently omits it. Confirm whether `OVERDUE` should be added to booking status enum before implementation starts.

If you want, I can convert this into a ready-to-share `technical-handoff-django-react.md` file in your workspace with an API contract template and sprint-by-sprint build plan.