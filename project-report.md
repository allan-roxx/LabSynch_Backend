G:\kulogo.png 

Kenyatta University 

 

Department of Computing & Information Science 

 

SCO400: Problem Analysis 

 

Title: Labsynch: A Mobile Laboratory Equipment Booking And Management System 

 

 

 

Name: Allan Muange Kebaso 

Reg No: J17/0994/2022 

 

Project Supervisor: Mr. Alfred Karwega 

January 2026 

​​Table of Contents 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​ 

​​ 

 

 

 

 

 

 

 

 

 

LIST OF FIGURES 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

 

CHAPTER 4: PROBLEM ANALYSIS 

This chapter provides a detailed analysis of the proposed LabSynch system and represents its requirements. System analysis is a paradigm shift in the project, where the focus of the conceptual design is shifted towards the comprehensive understanding of the real problem of the system being designed to solve. As per the Object-Oriented Analysis and Design (OOAD) approach and the Unified Process described in Chapter Three, this chapter highlights the role of decomposition of the current system, collection of empirical data, formal model and strict specification of requirements. 

4.0 Justification of the Modelling Techniques Used 

The selection of the modeling techniques used in this chapter was guided by the object-oriented analysis and design paradigm and the Unified Process, which were adapted in Chapter 3. Analytical models were used to gain a better understanding of the problem domain before the beginning of the development phase. These models were chosen to support various activities during the problem analysis, such as systematic requirements elicitation, validation, and refinement. They capture how the current system works, as well as identifying its limitations, leading to the gradual definition of functional and non-functional requirements of the proposed system in a structured manner. 

4.1 Strategy and Approach of Analysis 

The discussion in this chapter follows a problem -decomposition approach, which has been supported by structured systems analysis and the OOAD practices. The concrete issue has been divided into the following scrutinizing dimensions: (i) organizational and operational background; (ii) existing procedures and workflows; (iii) data creation, storage, and usage; (iv) stakeholder interactions and obligations; and (v) systems vulnerabilities and limitations.  

Such an approach will ensure that the analysis covers not only the technical challenges but also the operational, organizational and human factors influencing the control of the laboratory equipment. 

4.2 Fact-Finding and Requirements Elicitation. 

The objectives of this project are to analyze the existing challenges of laboratory equipment access in educational institutions within Kiambu County in order to gather specific functional and non-functional requirements for a centralized rental platform. Another objective is to design and develop a data-driven web application, LabSynch, that will have inventory management, a booking engine, and automated payment processing algorithms. 

Furthermore, the project will validate the system by conducting functionality testing to ensure it handles equipment reservation, maintenance tracking, and administrative reporting accurately. 

One of the main goals of this chapter is to show that there is a real and true engagement with the real world in which LabSynch will be operating. In order to achieve this, a number of fact-finding methods were implemented to cross-check the results and reduce bias. 

4.2.1 Document Analysis 

Document analysis referred to a careful examination of documents and semi-official documents related to laboratory work in Kenyan secondary schools, such as the Kenyan Secondary School Science Curriculum, the laboratory safety standards provided by the Ministry of Education, as well as publicly available catalogues of laboratory equipment. 

According to the Ministry of Education (2019, p. 2), the previous 8-4-4 system faced a significant “resource gap manifested in poorly equipped workshops” at the secondary school level. This lack of equipment “impeded the implementation of practical aspects of the curriculum,” making it difficult for students to gain the intended self-reliance and vocational skills. 

The examination showed that the majority of schools must keep a standardised range of laboratory equipment to facilitate practical education. However, individual institutions are often hindered by the lack of funds to purchase or hold entire inventories. This subsequently becomes a need to have equipment-sharing or rental systems which are currently unregulated and unofficial. 

The definition of core requirements of equipment, safety requirements, and base assumptions that were used in the modelling of the proposed system were going to be based on the inferences made in the analysis of the document. 

4.2.2 Existing Practices and Systems Analysis. 

The evaluation of the existing practices was conducted through the examination of physical laboratory logbooks, spread sheets and informal records of communication used by laboratory technicians in the selected schools of Kiambu County. These systems were also observed to be disjointed, uneven and majorly dependent upon personal idiosyncrasy. 

Most of these cases were where the inventory registers were kept manually with much of the recordings being retroactive leading to a difference between the stocked and the actual equipment availability. There were no universal guidelines on how to record borrowing, returns and equipment conditions. Furthermore, the historical records were not easily accessible and hence analysis of trends or accountability was hardly possible. 

This discussion has shown that the existing system is not automated, standardised, and integrated, thus establishing the need to have a centralised digital solution. 

4.2.3 Questionnaires 

Questionnaires were physically administered to teachers and laboratory technicians in selected secondary schools within Kiambu County. A total of 8 questionnaires were distributed, out of which 7 were successfully completed and returned, representing an 87% response rate. The questionnaires covered the issues of everyday functioning problems, the reasons why equipment shortages might occur, the problems in planning the practical lessons, and the attitude to shared management of the resources. 

Most of the respondents indicated that they had to encounter delays regularly when carrying out practical lessons due to the availability of equipment or the problem of ineffective equipment. Some had to devise other ways of conducting laboratory experiments, such as the use of the 6kg gas cylinders from kitchenettes due to lack of Bunsen burners. Additionally, all schools had a challenge of purchasing laboratory equipment due to the high costs. 

Schools like Kimuchu Secondary School struggle with a large population of students and also had a hard time to cope with the introduction of the Competency Based Education (CBE) system which introduced a lot of activities that require the purchase of equipment to cater for the learning needs of students. 

It was also agreed that informal borrowing arrangements almost always led to misunderstanding and broken equipment or unreturned things. There were high opinions of the respondents on a centralised system that can offer transparency, advance booking and accountability. 

4.3 Description of Current System 

The current laboratory equipment management system works independently in each school. The physical records of inventory are kept at the local level usually maintained by the laboratory technicians in either physical log books or simple spread sheets. There is lack of centralised coordination or control amongst the institutions. 

Sharing of equipment when this is done is made possible by informal communication amongst teachers or technicians. The choices made about availability, condition and return schedules are based on trust as opposed to verifiable records. As a result, mistakes, conflicts, and lack of efficiency are highly prone in this environment. 

The current laboratory equipment management system works independently in each school. The physical records of inventory are kept at the local level usually maintained by the laboratory technicians in either physical logbooks or simple spread sheets. There is no centralised coordination or control amongst the institutions. 

4.3.2 Problems Identified in the Current System 

Analysis of the current system identified several critical weaknesses: 

i. Lack of real-time equipment availability information 
ii. High likelihood of booking conflicts 
iii. Absence of historical usage and accountability records 
iv. Equipment loss and damage due to poor tracking 
v. Increased administrative burden on laboratory staff 

These problems hinder effective laboratory instruction and resource utilization. 

4.3.3 Organisational Structure 

 

Figure 1: Organisational Structure 

4.3.4 Class Diagram 

 

Figure 2:Class Diagram of Current System 

4.3. Object Diagram 

 

Figure 3: Object Diagram of the current system 

 

4.3. Flowchart 

 

Figure 4: Flowchart of Booking Process 

 

Figure 5: Flowchart of Equipment Return 

4.3.6 Data Flow Diagram  

 

Figure 6: Data Flow Diagram 

4.3.7 Entity Relationship Diagram 

 

Figure 7: Entity Relationship Diagram 

4.3.8 Use case diagram 

 

Figure 8: Use Case Diagram 

4.3.9 Sequence diagram 

 

Figure 9: Sequence Diagram 

 

4.4 Requirement Specifications   

This section will state the needs of the proposed LabSynch system in different levels of abstraction. This systematic form of defining requirements is meant to make sure that the system to be designed and implemented directly responds to the organisational problem that was identified during the system analysis.   

4.4.1 Business Requirements   

The LabSynch system operates with a list of strategic business requirements based on the business problems that are experienced by the secondary school laboratories in Kiambu County. Optimisation of the use of laboratory equipment in institutions involved is the main business need. Some schools cannot afford to buy full laboratory inventories, due to budgetary constraints and therefore in some schools, there is under-utilisation of equipment and in others, there are acute shortages. The suggested system should then enable sharing of the resources with controlled, transparent and efficient ways.   

The other important business need is the minimization of unwarranted duplication in the purchases of equipment. Lack of visibility into the resources available within schools causes institutions to buy equipment that is available to be borrowed or rented. LabSynch will be beneficial towards equipping decision-making processes and enhancing the utilisation of finite budgets by ensuring that more informed procurement decisions are made and that the equipment availability is viewed centrally.   

The system should also contribute to the general educational requirement of improving applied science training. Access to science curriculum through laboratory equipment is essential to timely delivery. Failure to administer practical lessons because of lack of equipment compromises the results of learning and curriculum goals. LabSynch also needs to make sure that equipment accessibility is predictable, well coordinated and in line with academic schedules.   

Lastly, the system has to make the organisation accountable and traceable in the management of shared resources. Under the existing manual system, equipment loss, damage and misuse have been found to be major issues of concern. The suggested system will need to include the measures to track the responsibility, the history of use and equipment state, promoting the responsible use of the equipment and fostering the culture of institutional trust in the schools involved.   

4.4.2 User Requirements   

User requirements outline the needs and expectations of the individuals that will interface directly with the LabSynch system in the process of their daily tasks. These needs were based on questionnaires and observation on the current laboratory practices.   

One of the main groups of users is science teachers. Educators need the functionality to find laboratory equipment according to type, availability, condition and location. This is necessary in planning the lesson especially when practical sessions have to be planned at an earlier beforehand. Moreover, instructors need a system to book or order equipment to use at certain days and during definite periods of time with the definite feedback on whether it is approved. A possibility of tracking the status of reservations, confirmation, dispatch and return status is also a key requirement to minimize uncertainty and last-minute cancellations.   

The other important group of users is the laboratories technicians who are involved in the work of the laboratory even more. Technicians need equipment to enroll and revise inventory records, equipment descriptions, quantities, status and history of equipment condition and maintenance. They should also be in a position to check, accept or decline booking requests depending on availability and institutional policies. Also, functionality is needed by the technicians to track equipment returns, document condition on return and flag equipment in need of care or repair.   

There is a need to have higher-level oversight functionality by system administrators. They have the need to get detailed reports on equipment use, borrowing history and accident history. Administrators should be in a position to handle user accounts, distribute roles and permissions and make sure that there is conformity between the system use and organisational policies. These needs facilitate governance, auditing and long term planning.   

4.4.3 Functional Requirements   

Functional requirements are those behaviours and operations that should be undertaken by the LabSynch system to meet both business and user requirements. At a more basic level, the system should offer the functionality of equipment registration and classification, wherein the personnel at the laboratory should identify every item within the shared inventory with detailed information being logged. This incorporates properties like the type of equipment, its quantity, ownership, status of condition and availability.   

The system should facilitate an organized booking process that will allow the users to make equipment requests, send the requests to the approval process and change the availability status. Examples of business rules that this workflow should implement include conflict prevention, institutional borrowing policies, and maximum number of days which can be booked. The users should be notified of the approval decisions and due return deadlines through automated notifications.   

Return and condition tracking is another functional requirement that is critical. When the borrowed equipment is returned to the company, the system should be able to enable the technicians to take a condition test and to update the equipment status. This feature facilitates responsibility and offers information to the maintenance planning and dispute resolution.   

Moreover, the system should be able to generate reports on many dimensions, such as usages frequency, equipment usage trends, and historical incidences. The reports are used operationally and strategically, which allows making informed decisions at institutional and administrative levels.   

 4.4.4 Non-Functional Requirements   

Non-functional requirements determine the quality, and constraints within which the LabSynch system is supposed to be run. Security is one of the major issues as the system will contain institutional data and user information. This system should therefore adopt authentication and authorisation controls so that they can only access designated functions and data by authorised users.   

Reliability and availability are also necessary as the teachers and the technicians might rely on the system and rely on it to make time-sensitive plans. The system should be in a way that minimises the downtimes and the performance should be consistent at the time of peak uses, especially during the academic terms.   

Another non-functional requirement that is very critical is usability. The system should be user-friendly and easy to use with all users having different degrees of technical expertise. The navigation should be clear, feedback messages should be meaningful and interface should be consistent so as to promote adoption and minimize training needs.   

This should be scalable to cover possible expansion to other schools other than the first group. The system should have the capacity to handle the additional user numbers, institutions records and equipment without affecting the performance.   

Lastly, the system should be able to maintain data integrity and uniformity in all its activities. The records of transactions including bookings, approvals and returns should be properly done and synchronised to avoid conflict, loss or inconsistency of data that may weaken confidence in the system. 

4.5 Feasibility Analysis 

4.5.1 Technical Feasibility 

The proposed LabSynch system is technically feasible due to the availability and maturity of modern web-based technologies and development frameworks. The system will be developed using open-source tools and widely adopted programming languages that support scalability, security, and maintainability. The use of a web-based architecture ensures cross-platform accessibility, allowing users to access the system through standard web browsers without the need for specialized hardware or software installations. 

4.5.2 Economic Feasibility 

From an economic perspective, the LabSynch system is feasible as the development costs are intentionally kept low by leveraging free and open-source software tools. The primary expenses are limited to internet connectivity and minimal field data collection, making the project affordable within the scope of an academic environment. 

4.5.3 Operational Feasibility 

Operational feasibility was assessed by evaluating the readiness of users and institutions to adopt the proposed system. Most intended users, including teachers, laboratory technicians, and administrators, already possess basic computer literacy and are familiar with web-based applications such as online portals and email systems. This familiarity reduces resistance to change and shortens the learning curve. 

 

CHAPTER 5: SOLUTION DESIGN 

 

This chapter details the technical specifications and design of the LabSynch system. Building upon the requirements identified in the Problem Analysis phase, this section translates the logical requirements into physical system specifications. It covers the architectural design, data design, process design, and interface design, providing a blueprint for the construction and implementation of the centralized laboratory equipment management platform. 

The system will operate within a multi-institutional context involving: 

i. Participating schools 
ii. Laboratory technicians 
iii. Science teachers 
iv. LabSynch system administrators 

Each role interacts with the system according to clearly defined responsibilities and access privileges. 

5.1 Architectural Design 

5.1.1 System Architecture Overview 

The LabSynch system will adopt a Three-Tier Client-Server Architecture. This architectural pattern ensures separation of concerns, scalability, and maintainability. The three tiers are: 

Presentation Tier (Client Side): The user interface running in the web browser, accessible via desktops, tablets, and mobile devices. It handles user interactions and data presentation. 

Application Tier (Server Side): The core business logic, API endpoints, and authentication services. It processes requests from the client and interacts with the database. 

Data Tier (Database): The storage layer responsible for data persistence, integrity, and retrieval. 

 

Figure 10: Three-tier architecture 

5.1.2 Software Architecture & Technology Stack 

The choice of technology stack adheres to modern, open-source standards to ensure cost-effectiveness and broad community support. 

Component 

Technology 

Rationale 

Operating System 

Linux (Ubuntu Server) 

Robust, secure, and cost-effective for deployment on cloud VPS. 

Web Server 

Nginx 

High-performance reverse proxy and load balancer. 

Server-Side Scripting 

Django 

A high-level, open-source web framework written in Python that promotes rapid development and clean, pragmatic design. 

Client-Side Framework 

React.js 

Component-based, responsive UI development for dynamic user experiences. 

Database Management 

PostgreSQL 

Advanced open-source relational database ensuring data integrity and ACID compliance. 

Payment Integration 

M-Pesa Daraja API 

Standard mobile money gateway for the Kenyan market. 

5.1.3 Hardware Architecture and Cloud Infrastructure 

Since LabSynch is a cloud-hosted web application, the hardware requirements are divided into the Host Server (Cloud) and Client Devices (End Users). 

Host Server Specifications (Cloud VPS) 

The system will be hosted on a Virtual Private Server (e.g., DigitalOcean or local provider). 

CPU: 2 vCPU 

RAM: 4GB 

Storage: 25GB SSD (for application code and database) 

Client Device Requirements 

Users (Teachers, Technicians, Admins) require standard computing devices. 

Device Types: Desktop PC, Laptop, Tablet, or Smartphone. 

Network: Stable Internet connection (Minimum 3G/4G or Broadband). 

Software: Any modern web browser (Chrome, Firefox, Edge, Safari). 

5.2 Process Design 

5.2.1 Program Structure 

There is a modular structure of application logic. The API server is structured into business domain controllers and services. 

Module Breakdown: 

Auth Module: Manages Registration, JWT Token Generation, Password reset and Login. 

Inventory Module: CRUD Equation on Equipment, Stock Level Management, Image Upload. 

Booking Module: Availability Checking, Date Range Checking, Reservation Processing, Status Process (Approve/Reject). 

Payment Module: M-Pesa STK Push trigger, Callback Processing, Payment Verification. 

Admin Module: Reporting, User Management, System Administration. 

 

Figure 11: Program Structure 

5.2.2 State Transition Diagram 

Below is a state transition diagram that shows how objects within the proposed Labsynch system change in response to events that will occur within the system.  

 

Figure 12: State Transition Diagram 

5.2.2 Create Booking Process 

 

Figure 13: Create Booking Process 

5.2.3 Calculate Booking Price 

 

Figure 14: Calculate Booking Price 

5.3.4 Cancel Booking Process 

 

Figure 15: Cancel Booking process 

5.2.4 Data Flow Diagram Level 0 

 

Figure 16: DFD Level 0 

5.2.5 Data Flow Diagram Level 1 

 

Figure 17: DFD Level 1 

5.3 Data Design 

5.3.1 Physical Data Model 

The logical entities identified in the analysis phase are transformed into physical database tables in PostgreSQL. The schema is normalized to Third Normal Form (3NF) to reduce redundancy. 

Table Specifications: 

users Table 

Columns: user_id (UUID, PK), email (VARCHAR), password_hash (VARCHAR), role (ENUM: 'ADMIN', 'SCHOOL_ADMIN', 'TEACHER'), created_at (TIMESTAMP). 

Index: idx_email (Unique). 

schools Table 

Columns: school_id (UUID, PK), user_id (FK), school_name (VARCHAR), registration_number (VARCHAR), location (TEXT). 

equipment Table 

Columns: equipment_id (UUID, PK), name (VARCHAR), category (VARCHAR), stock_quantity (INT), unit_price (DECIMAL), image_url (VARCHAR). 

Index: idx_category. 

bookings Table 

Columns: booking_id (UUID, PK), school_id (FK), status (ENUM: 'PENDING', 'APPROVED', 'ISSUED', 'RETURNED'), start_date (DATE), end_date (DATE), total_cost (DECIMAL). 

payments Table 

Columns: payment_id (UUID, PK), booking_id (FK), mpesa_receipt (VARCHAR), amount (DECIMAL), status (ENUM: 'SUCCESS', 'FAILED'). 

 

5.3.2 Database Design 

Below is an entity relationship diagram that shows the primary keys, foreign keys and relationships between various data models within the proposed system. 

 

Figure 18: Entity Relationship Diagram 

5.3.3 Data Storage Strategy 

Relational data including users data, bookings, accounting, etc will be stored within the PostgreSQL database on the primary database server. 

Backup Strategy: This will be set to take automated database snapshots every day and will keep 7 days of the snapshots. 

5.4 User Interface Design 

The design is usability-oriented. Its design is based on a dashboard-centric layout. 

5.4.1 Input Design 

Forms: Client side validation will be used on all input forms (Registration, Booking) to provide feedback (e.g., "Field required" and invalid email format). 

Booking Date Picker: This is an interactive calendar that does not allow the user to book dates that are already past, or that have invalid dates. 

 

Authentication Pages 

[Text Wrapping Break] 

Figure 19: Login page 

 

Figure 20: Registration Page 

Equipment Booking and Return Page 

 

Figure 21: Booking page 

 

Figure 22: Equipment return page 

5.4.2 Output Design 

Dashboards: Role based dashboards. 

 

Figure 23: School Dashboard 

 

Figure 24: Labsynch Admin Dashboard 

Booking Details Page 

 

Figure 25: Booking details page 

5.5 Test Design 

The testing plan is used to test the reliability of the system before roll out. 

Unit Testing: Unit testing involves testing separate functions through testing tools such as Jest. 

Integration Testing: Checking communication between the PostgreSQL database and Django REST API. 

System Testing: System: Testing of complete workflows (e.g., A user finding an item, booking it and paying through M-Pesa). 

5.6 Implementation Plan 

The implementation of the system will be done in stages: 

Environment Setup: VPS provisioning, dependencies (Django, Postgres, Nginx) installation. 

Database Migration: It takes advantage of Django Object Relational Mapping (ORM) migrations to build schemas on the database. 

Backend Deployment: Deploying the API services and setting up environment variables (API Keys). 

Frontend Build: The React app is compiled and the Nginx server is used to serve the statical assets. 

Data Population: Importing the preliminary inventory data of the analysis phase in the spreadsheet. 

5.7 Conclusion 

This solution design gives detailed technical road map of the LabSynch system. The design solves the fundamental issues of efficiency and accountability that were determined during the analysis stage by relying on a scalable client-server architecture, an effective database schema, and an accountable network setup. The second step is the real construction and coding of such designed components. 

 

REFERENCES 

Buede, D. M., & Miller, W. D. (2024). The engineering design of systems: models and methods. John Wiley & Sons. 

GeeksforGeeks. (2025, July 23). Three-tier client-server architecture in distributed system. Retrieved January 27, 2026, from https://www.geeksforgeeks.org/three-tier-client-server-architecture-in-distributed-system  

Ministry of Education, Republic of Kenya. (2019). National curriculum policy. Ministry of Education. https://www.education.go.ke 

Riddle, W. E. (1979). An approach to software system modelling and analysis. Computer Languages, 4(1), 49-66. 

 