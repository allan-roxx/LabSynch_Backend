# CHAPTER 6: SYSTEM IMPLEMENTATION

This chapter describes the practical construction of the LabSynch system as designed in Chapter Five. It details the tools and technologies used during coding and testing, the testing strategy and data used to validate the system, and the proposed changeover plan for migrating participating institutions from manual processes to the new platform.

## 6.1 Tools Used for Coding and Testing

The implementation of LabSynch was guided by the Object-Oriented Analysis and Design (OOAD) paradigm and the Unified Process introduced in Chapter Three. Each tool was deliberately selected to enforce separation of concerns, support iterative development, and align with the modular architecture specified in the solution design.

### 6.1.1 Backend Framework: Django and Django REST Framework

The server-side application was built using **Django 5.2**, a high-level Python web framework that follows the Model-View-Template (MVT) pattern and encourages rapid development through its built-in ORM, migration engine, and administration interface (Django Software Foundation, 2025). Django was extended with **Django REST Framework (DRF) 3.15**, a toolkit that provides serializers, viewsets, routers, and authentication classes for building RESTful APIs. The combination allows each business domain — authentication, equipment, bookings, payments, notifications — to be encapsulated in an independent Django application (`apps/`) following a consistent structure of `models.py`, `serializers.py`, `views.py`, `services.py`, and `urls.py`.

All business logic was isolated in `services.py` files, keeping views thin and making the service layer independently testable. This strict layering mirrors the object-oriented principle of encapsulation and the Unified Process discipline of separating analysis artefacts from implementation artefacts.

### 6.1.2 Authentication: djangorestframework-simplejwt

Authentication was implemented using **djangorestframework-simplejwt 5.3**, which issues short-lived JSON Web Tokens (JWT). Access tokens expire after 60 minutes and refresh tokens after 7 days. This stateless token mechanism removes the need for server-side sessions and is well suited to the planned React.js front end where tokens are stored client-side. Two custom permission classes — `IsAdminUser` and `IsSchoolUser` — enforce role-based access at the viewset level.

### 6.1.3 Asynchronous Task Queue: Celery and Redis

**Celery 5.4** with **Redis 5** as the message broker handles all time-deferred and background workloads: sending booking confirmation emails, payment receipt emails, equipment issued and returned notifications, overdue alerts dispatched on a periodic schedule, and penalty-cleared notifications. Decoupling these operations from the HTTP request-response cycle ensures that API endpoints remain responsive under load. Each task is idempotent and carries a `max_retries=3` policy, consistent with the reliability requirements stated in Chapter Four.

### 6.1.4 Payment Integration: M-Pesa Daraja API

Mobile money payment processing was implemented against the **Safaricom Daraja API 3.0** STK Push endpoint (Safaricom PLC, 2025). When a school confirms a booking, the system initiates an STK Push to the school's registered phone number. Safaricom calls the system's registered callback URL upon settlement. The callback handler verifies the transaction, updates the booking status to `RESERVED`, and — where applicable — clears any outstanding overdue penalties that were rolled into the booking total. During development, **ngrok** was used to expose the local callback endpoint to the public internet so that Safaricom's servers could reach it.

### 6.1.5 API Documentation: drf-spectacular

**drf-spectacular 0.27** was used to auto-generate an OpenAPI 3 schema from the DRF viewsets and serializers. This produced an interactive Swagger UI endpoint (`/api/schema/swagger-ui/`) that served as the primary interface for manual exploratory testing throughout the development phase, enabling the developer to submit requests and inspect responses without an external tool.

### 6.1.6 Database: PostgreSQL and Django ORM

**PostgreSQL** is the target production database. All models inherit from a shared `BaseModel` that provides a UUID primary key and `created_at`/`updated_at` timestamps. The Django ORM manages schema evolution through automatically generated migrations. During development, SQLite was used locally via a `DATABASE_URL` environment variable, keeping the environment lightweight while maintaining ORM compatibility with PostgreSQL.

### 6.1.7 Additional Libraries

| Library | Purpose |
|---|---|
| `django-environ` | Secure loading of secrets and environment variables from a `.env` file |
| `django-cors-headers` | Cross-Origin Resource Sharing headers for browser-based front-end clients |
| `django-filter` | Declarative queryset filtering on list endpoints |
| `Pillow` | Server-side image processing for equipment photo uploads |
| `reportlab` | Server-side PDF generation for downloadable booking and financial reports |
| `django-storages` + `boto3` | S3-compatible object storage for equipment images in production |

### 6.1.8 Testing Tools

**pytest 8** and **pytest-django 4.8** form the testing backbone. pytest's fixture system and parametrize decorator make it straightforward to compose test scenarios without inheritance-heavy test class hierarchies. **factory_boy 3.3** provides declarative model factories (`UserFactory`, `SchoolProfileFactory`, `EquipmentFactory`, `BookingFactory`) that construct valid, database-backed objects in a single line of test code, avoiding scattered `Model.objects.create()` calls. Code quality was maintained throughout the development cycle using **flake8** for linting, **black** for formatting, and **isort** for import ordering.

---

## 6.2 Testing

### 6.2.1 Testing Approach

Testing was structured across three complementary levels, following the layered architecture of the application.

**Unit Testing** targeted individual service functions in isolation. Because all business logic resides in `services.py`, each critical operation — creating a booking, computing outstanding overdue penalties, processing an M-Pesa callback, issuing and returning equipment — could be exercised without invoking HTTP. M-Pesa's external HTTP call was mocked using `unittest.mock.patch` so that payment tests ran deterministically without network dependency.

**Integration Testing** verified that multiple layers — serializer validation, service invocation, ORM writes, and HTTP response format — behaved correctly end-to-end. These tests used DRF's `APIClient` to submit HTTP requests against the full Django URL routing stack with a real (SQLite) database. The test in `tests/bookings/test_bookings.py` illustrates this pattern: it logs in as a school user, submits a booking payload, and asserts both the HTTP 201 response and the downstream effect on `Equipment.available_quantity`, confirming that availability reservation works atomically.

**Manual / Exploratory Testing** was conducted through the Swagger UI at each development milestone. Representative workflows — registering a school, browsing the equipment catalogue, adding items to a cart, confirming a booking, simulating an STK Push callback, issuing and returning equipment, and generating a PDF report — were executed in full to verify end-to-end correctness and to catch edge cases not covered by automated tests.

### 6.2.2 Test Data

Test data was constructed using factory_boy factories rather than fixed database fixtures, making test sets independent and reproducible. Key test scenarios and the data involved are summarised below:

| Scenario | Test Data Used |
|---|---|
| Booking creation reserves availability | `SchoolProfileFactory`, `EquipmentFactory(available_quantity=5)`, booking for quantity 2 |
| Overbooking prevention | Same equipment, booking attempted for quantity 6 (exceeds stock) |
| Duplicate booking conflict | Two overlapping bookings for same equipment and date range |
| Penalty roll-forward on new booking | School with an existing `RETURNED` booking where `penalty_cleared=False`; new booking total must include outstanding penalty |
| M-Pesa callback success | Mocked Safaricom callback payload with `ResultCode: 0`; assert booking status changes to `RESERVED` |
| M-Pesa callback failure | Mocked callback with `ResultCode: 1032` (cancelled by user); assert booking remains `PENDING` |
| Equipment return — overdue penalty | Booking whose `return_date` is in the past; assert `overdue_penalty > 0` after return |
| Admin clear penalty | `admin_clear_booking_penalty()` service; assert `penalty_cleared=True` and downstream `PENDING` bookings recalculated |

Boundary conditions tested included: `return_date == pickup_date` (must be rejected), `available_quantity = 0` (must be rejected), and payments with amounts below the booking total (must be rejected by the service layer).

---

## 6.3 Proposed Changeover Techniques

Changeover is the process of transitioning an organisation from an existing system to a new one (Sommerville, 2016). Two complementary changeover strategies are proposed for LabSynch.

### 6.3.1 Pilot Conversion

In the first phase, LabSynch will be deployed to a single pilot school within Kiambu County. All equipment inventory data for that institution will be captured and loaded into the system before go-live. Laboratory technicians and teachers at the pilot school will use LabSynch exclusively for booking management. The pilot phase allows the development team to identify operational issues, user training gaps, and unforeseen edge cases in a controlled environment before wider rollout. Feedback gathered during the pilot will be used to refine the system.

### 6.3.2 Phased Parallel Running

After the pilot is validated, each subsequent school will be onboarded in a phased manner over successive academic terms. During each school's onboarding window, the institution will run its existing manual log-book process **in parallel** with LabSynch for a period of four to six weeks. Both systems will capture the same transactions, allowing staff to compare records and build confidence in the digital system before the manual process is retired. Parallel running increases the workload on staff temporarily but significantly reduces the risk of data loss or operational disruption (Sommerville, 2016).

Data migration for each new school will follow this sequence:

1. Export the school's existing inventory from spreadsheets or logbooks.
2. Import equipment records using the Django management command data population script.
3. Create user accounts for the school administrator, science teachers, and laboratory technicians.
4. Conduct a half-day orientation session covering equipment browsing, booking, and return workflows.
5. Activate the school's account on the production server and begin the parallel running window.
6. After the parallel window, formally retire the manual process.

---

# CHAPTER 7: LIMITATIONS, RECOMMENDATIONS AND CONCLUSIONS

## 7.1 Limitations

### 7.1.1 Time Constraints

The development cycle of LabSynch was carried out alongside a full academic workload, which compressed the time available for implementation, testing, and documentation. Certain planned features — including the React.js front-end, a dedicated mobile application, and advanced predictive analytics on equipment demand — could not be completed within the project timeline. As a result, the delivered system constitutes the API back-end and administrative interface only; the consumer-facing front end remains as future work.

### 7.1.2 Financial Constraints

The project was self-funded within the limits of a student budget. Cloud hosting costs were minimised by using the SQLite database in development and deferring production PostgreSQL and Redis deployment to the final testing phase. The M-Pesa Daraja sandbox environment was used throughout development because obtaining a live Daraja production account requires a registered business entity, which is beyond the scope of an academic project. Consequently, end-to-end live payment testing was not possible.

### 7.1.3 Anti-Cooperative Responses During Data Collection

During the questionnaire distribution phase, several laboratory technicians and teachers were reluctant to participate, citing time pressures associated with ongoing examinations and term-end administrative duties. Of the 8 questionnaires distributed, one was not returned, reducing the intended sample. Additionally, some respondents were guarded about revealing the exact nature of their informal equipment-sharing arrangements, likely due to concerns about institutional accountability. This limited the depth of information gathered on current inter-school equipment exchange practices.

---

## 7.2 Conclusion

The LabSynch project was motivated by a documented gap between the laboratory equipment requirements of secondary schools in Kiambu County and the resources available to individual institutions. The analysis in Chapter Four confirmed that existing manual, school-level inventory systems are fragmented, non-transparent, and ill-suited to facilitating safe inter-school equipment sharing.

The system designed and implemented in Chapters Five and Six addresses these gaps through a centralised, role-based web API built on Django and Django REST Framework. The booking state machine — spanning `PENDING`, `RESERVED`, `DISPATCHED`, `IN_USE`, `OVERDUE`, `RETURNED`, and `COMPLETED` — provides a structured accountability trail from reservation through return. The overdue penalty subsystem ties financial accountability to each booking, incentivising timely returns. The M-Pesa integration aligns the payment mechanism with the dominant mobile money infrastructure in Kenya, reducing friction for school administrators.

From a theoretical perspective, the system validates the applicability of OOAD and the Unified Process to a resource-constrained academic development context: iterative elaboration of use cases and domain models in Chapter Four and Five fed directly into the service-layer design, confirming that upfront analysis reduces rework during implementation. From a policy standpoint, LabSynch demonstrates that a centralised equipment rental model is technically viable for Kenyan secondary schools and could meaningfully contribute to the equitable delivery of the Competency Based Curriculum (CBC) practical requirements identified by the Ministry of Education (2019).

---

## 7.3 Recommendations

The following recommendations are made for the further development and eventual deployment of LabSynch:

1. **Front-End Development**: A React.js or React Native client should be developed against the existing REST API to provide school users and administrators with a polished, mobile-accessible interface. The API is already fully documented via OpenAPI/Swagger and ready for front-end integration.

2. **Live M-Pesa Production Integration**: The system should be registered under a valid business entity to obtain production Daraja API credentials, enabling real-money STK Push testing and eventual live deployment.

3. **Expansion to Other Counties**: After a successful pilot in Kiambu County, the platform should be extended to other counties in Kenya, potentially partnering with county governments or the Ministry of Education to fund hosting and incentivise institutional participation.

4. **Predictive Availability Analytics**: Usage data accumulated over academic terms should be used to build a demand forecasting model that alerts administrators before shortages are likely to occur, enabling proactive procurement decisions.

5. **Equipment Condition Scoring**: The damage reporting module should be extended with a structured condition score (e.g., 1–5 scale) that is updated at every return. Aggregated scores would provide an objective basis for scheduling preventive maintenance and retiring equipment.

6. **Offline Mode**: Given the variable internet connectivity in some school settings, a progressive web application (PWA) with offline caching should be considered so that essential read operations — browsing the catalogue and viewing booking status — remain functional during connectivity outages.

---

## References

Django Software Foundation. (2025). *Django documentation* (Version 5.2). https://docs.djangoproject.com/en/5.2/

Ministry of Education, Republic of Kenya. (2019). *National curriculum policy*. Ministry of Education. https://www.education.go.ke

Safaricom PLC. (2025). *Daraja API developer guide* (Version 3.0). https://developer.safaricom.co.ke

Sommerville, I. (2016). *Software engineering* (10th ed.). Pearson Education Limited.
