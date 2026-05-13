# LabSynch Platform — Terms and Conditions

**Effective Date:** 1 January 2026
**Platform Operator:** LabSynch Limited
**Contact:** support@labsynch.co.ke

By creating an account and checking the "I agree to the Terms and Conditions" box during registration, your institution agrees to be fully bound by every clause in this document. If you do not agree, you may not create an account or use the platform.

---

## 1. Definitions

| Term | Meaning |
|---|---|
| **Platform** | The LabSynch web application and API at labsynch.co.ke |
| **Operator** | LabSynch Limited, the company that owns and operates the Platform |
| **School / Client** | An accredited educational institution registered on the Platform |
| **Administrator / Admin** | An Operator employee with elevated platform access |
| **Equipment** | Laboratory instruments, apparatus, and consumables listed for rental |
| **Booking** | A confirmed request by a School to rent specified Equipment for a defined period |
| **Booking Reference** | A unique human-readable identifier (e.g. BK-2026-0042) assigned to each Booking |
| **Pickup Date** | The date on which the School agrees to collect or receive the Equipment |
| **Return Date** | The agreed date by which the Equipment must be physically returned |
| **Penalty Period** | Any period between the Return Date and the actual date of physical return |
| **Consumable** | Equipment designated as single-use; consumables are not returned after use |
| **Daily Rate** | The per-item, per-day rental price listed on the Platform for each Equipment item |

---

## 2. Account Registration & Eligibility

### 2.1 Who May Register

Only accredited schools and educational institutions in Kenya may register a School account. Individuals may not register on behalf of an institution without written authorisation from that institution's principal or director.

### 2.2 Registration Requirements

To register, you must:

- Provide a valid institutional email address.
- Provide the school's official name and registration number (Ministry of Education registration or equivalent).
- Provide accurate contact person details (name and designation).
- Read and explicitly accept these Terms and Conditions by checking the acceptance checkbox during registration.

### 2.3 Email Verification

After registration, a verification link will be sent to the provided email address. The account will be restricted until email verification is completed. Bookings cannot be created on an unverified account.

### 2.4 Accuracy of Information

You are responsible for ensuring all profile information — school name, address, GPS coordinates, county, contact person, phone number — is accurate and kept up to date. The Operator is not liable for failed deliveries, miscommunications, or disputes arising from inaccurate profile data.

### 2.5 Account Security

You are responsible for maintaining the confidentiality of your login credentials. Any activity conducted under your account is your institution's responsibility. Report suspected unauthorised access to support@labsynch.co.ke immediately.

---

## 3. Booking Policy

### 3.1 Advance Booking Requirement

All bookings must be made **at least one (1) full calendar day in advance**. Same-day bookings are not permitted. The Platform will reject any booking where the Pickup Date is today or in the past.

### 3.2 Minimum Rental Period

The minimum booking duration is **one (1) day** (Pickup Date to Return Date must differ by at least one day).

### 3.3 Availability & Confirmation

Equipment availability is checked at the time of booking. Availability is displayed in real time and is subject to change. A booking is only confirmed after **successful payment** is received. Unpaid bookings (status: PENDING) do not reserve equipment and may be superseded.

### 3.4 Booking Status Lifecycle

Your booking will progress through the following statuses:

| Status | Meaning |
|---|---|
| **PENDING** | Booking created; awaiting payment. Equipment is NOT yet reserved. |
| **RESERVED** | Payment confirmed; equipment is reserved for your dates. |
| **DISPATCHED** | Equipment has been dispatched and is in transit to your school. |
| **IN_USE** | Equipment has been received and is in active use at your school. |
| **OVERDUE** | Equipment has not been returned by the agreed Return Date. |
| **RETURNED** | Equipment has been physically returned and checked in. |
| **COMPLETED** | Booking fully closed; all obligations met. |
| **CANCELLED** | Booking cancelled before dispatch. |

### 3.5 Cancellation Policy

- Bookings in **PENDING** or **RESERVED** status may be cancelled.
- Once a booking is **DISPATCHED**, cancellation is not permitted.
- Cancellations must be requested via the Platform before the Pickup Date.
- The Operator reserves the right to cancel any booking that cannot be fulfilled due to equipment damage, maintenance, or force majeure, with full refund of amounts paid.

### 3.6 Equipment Quantities

The Platform enforces a **one-day grace buffer** between consecutive bookings for the same equipment. If your requested dates immediately follow another booking's return date, availability may show zero — this is intentional to account for transit and inspection time.

---

## 4. Payment Terms

### 4.1 Payment Method

All payments are processed via **M-Pesa (Lipa Na M-Pesa / STK Push)** through Safaricom's Daraja API. You will receive an STK Push prompt on the registered M-Pesa phone number when initiating payment.

### 4.2 Payment Timing

Payment must be completed to move a booking from PENDING to RESERVED. Equipment will not be prepared for dispatch until payment is confirmed on the Platform.

### 4.3 Total Amount

The total amount payable for a booking includes:

- **Equipment rental fee**: Daily Rate × Quantity × Number of rental days, per item.
- **Personnel costs** (if applicable): For equipment requiring a qualified technician, a personnel cost per day applies. This is displayed on the equipment detail page before booking.
- **Transport costs** (if applicable): Delivery/collection charges based on your registered transport zone.

All amounts are in **Kenya Shillings (KES)** inclusive of applicable taxes.

### 4.4 Receipts

A payment receipt will be issued electronically upon confirmation. M-Pesa transaction receipts serve as proof of payment. The Platform generates a reference number for every completed payment.

### 4.5 Disputed Payments

If you believe a payment was deducted but not reflected on the Platform, contact support@labsynch.co.ke within **48 hours** with the M-Pesa confirmation message. The Operator will investigate and resolve within 5 business days.

### 4.6 Refund Policy

- Bookings cancelled **before dispatch**: full refund processed within 7 business days.
- Bookings cancelled **after dispatch**: no refund.
- Overdue penalties are non-refundable once incurred.
- Damage repair costs are non-refundable.

---

## 5. Overdue & Penalty Policy

### 5.1 Definition of Overdue

A booking becomes **OVERDUE** when the physical equipment has not been returned to the Operator's premises by the close of business (17:00 EAT) on the agreed Return Date.

### 5.2 Overdue Penalty Rate

An overdue penalty is charged at **150% (one and a half times) of the standard Daily Rate** per item, per overdue day.

> **Example:** If you rent 3 Bunsen Burners at KES 500/day each and return them 2 days late:
> Penalty = 3 items × KES 500 × 1.5 × 2 days = **KES 4,500**

The penalty is calculated automatically by the Platform and recorded on the booking.

### 5.3 Penalty Accrual

The penalty clock starts at 00:01 EAT on the day after the Return Date and runs until the equipment is physically received and checked in by an Operator staff member. The School and relevant Administrators will receive a notification when a booking transitions to OVERDUE status.

### 5.4 Penalty Notification

The Platform will send daily notifications to the School for every active OVERDUE booking. Administrators will be notified of all OVERDUE bookings. Failure to receive a notification does not waive penalty obligations.

### 5.5 At-Risk Notifications

When an upcoming RESERVED booking may be affected by another School's OVERDUE equipment, both the affected School and Administrators will receive an **"At Risk"** notification at least 3 days before the pickup date. This is advisory only and does not guarantee availability.

### 5.6 Penalty Settlement

Outstanding overdue penalties must be settled before a School can create new bookings. The Operator may suspend booking privileges for accounts with uncleared penalties.

### 5.7 Liability Status

Each School account carries a **Liability Status**:
- **CLEAR**: No outstanding obligations.
- **HAS_OUTSTANDING**: Unpaid penalties, damage costs, or unresolved obligations exist.

An account in `HAS_OUTSTANDING` status may be restricted from making new bookings until the balance is resolved.

---

## 6. Equipment Handling & Care

### 6.1 Responsibility Upon Receipt

The School becomes fully responsible for the Equipment from the moment it is received (signed for) until the moment it is physically returned and accepted by the Operator.

### 6.2 Proper Use

Equipment must be used only for its intended educational or laboratory purpose by qualified personnel or under appropriate supervision. Use for commercial purposes, resale, or subletting is strictly prohibited.

### 6.3 Care Obligations

The School must:

- Handle all Equipment with reasonable care.
- Store Equipment in appropriate conditions (avoiding extreme temperatures, moisture, and physical shock).
- Not attempt to repair, modify, disassemble, or reconfigure any Equipment.
- Report any malfunction or damage immediately to the Operator.

### 6.4 Consumables

Items marked as **Consumable** are for single use and are not expected to be returned. Charges for consumables are non-refundable once the booking is dispatched.

### 6.5 Personnel-Required Equipment

Some Equipment requires a qualified LabSynch technician to accompany its use. This will be clearly marked on the Equipment listing (`requires_personnel: true`). A daily personnel cost applies and is included in the booking total. The School must ensure the technician has access to appropriate facilities.

---

## 7. Damage Policy

### 7.1 Reporting Damage

Any damage to Equipment must be reported to the Operator immediately and in any event no later than **24 hours** after discovery. Damage reports are filed through the Platform or by contacting support@labsynch.co.ke.

### 7.2 Assessment & Cost

The Operator will assess damage severity (MINOR, MODERATE, SEVERE, or TOTAL_LOSS) and calculate a repair or replacement cost. The School will be notified of the assessed cost through the Platform.

### 7.3 School Liability

The School is liable for the full assessed repair or replacement cost for any damage occurring while Equipment is in the School's custody. The Operator's assessment is final unless disputed in writing within **5 business days** of notification.

### 7.4 Damage Settlement

Damage costs must be settled before the affected booking can be marked COMPLETED. Unresolved damage costs contribute to a `HAS_OUTSTANDING` liability status.

### 7.5 Fair Wear and Tear

Normal, expected wear and tear from appropriate use is not chargeable. The Operator will clearly communicate the basis for any damage charge.

---

## 8. Equipment Return

### 8.1 Return Process

Equipment must be returned to the Operator's designated facility by the Return Date. The School must ensure equipment is packed appropriately and all components are included.

### 8.2 Return Verification

Upon return, Operator staff will inspect and verify the Equipment. The booking status will be updated to RETURNED on the Platform once accepted. Any discrepancy (missing components, damaged items) will be logged as a damage report at this point.

### 8.3 Proof of Return

The Platform record of `RETURNED` status, timestamped by an Administrator, constitutes proof of return. The School should retain the Platform notification confirming return acceptance.

---

## 9. Privacy & Data

### 9.1 Data Collected

The Platform collects: institutional name, contact details, GPS location (if provided), booking history, payment records, and communication logs.

### 9.2 Use of Data

Data is used solely to operate the Platform, process bookings and payments, and communicate with you about your account. Data is not sold to third parties.

### 9.3 Data Retention

Booking, payment, and damage records are retained for a minimum of **7 years** for audit and legal compliance purposes.

### 9.4 GPS Location

GPS coordinates submitted through the profile are used only to assist with logistics planning and delivery. This data is optional.

---

## 10. Operator's Rights & Obligations

### 10.1 Operator Rights

The Operator reserves the right to:

- Suspend or terminate any account that violates these Terms.
- Modify equipment pricing, availability, and policies with reasonable notice.
- Refuse a booking for any equipment that is under maintenance or has been decommissioned.
- Recover overdue penalties and damage costs through legal means if necessary.

### 10.2 Operator Obligations

The Operator will:

- Provide equipment in good working condition as described.
- Confirm or reject bookings within the Platform's automated workflow.
- Process verified refunds within the stated timeframes.
- Maintain the confidentiality of your institutional data.

---

## 11. Limitation of Liability

The Operator is not liable for:

- Loss or damage arising from the School's misuse of Equipment.
- Any injury, accident, or harm resulting from use of Equipment at the School's premises.
- Loss of experimental data, research outcomes, or any consequential or indirect loss.
- Delays in delivery caused by third-party logistics providers, road conditions, or force majeure events.

The Operator's maximum liability in any dispute is limited to the total amount paid by the School for the specific booking in question.

---

## 12. Amendments

The Operator may update these Terms at any time. Registered users will be notified by email at least **14 days** before changes take effect. Continued use of the Platform after the effective date of amendments constitutes acceptance of the revised Terms.

---

## 13. Governing Law

These Terms are governed by the laws of the **Republic of Kenya**. Any dispute arising from the use of the Platform shall be subject to the exclusive jurisdiction of the courts of Kenya.

---

## 14. Contact

For any questions regarding these Terms, contact:

- **Email:** support@labsynch.co.ke
- **Phone:** +254 700 000 000
- **Address:** LabSynch Limited, Nairobi, Kenya

---

*By checking "I agree to the Terms and Conditions" during account registration, you confirm that you have read, understood, and agree to be bound by these Terms on behalf of your institution.*

*Version 1.0 — Effective 1 January 2026*
