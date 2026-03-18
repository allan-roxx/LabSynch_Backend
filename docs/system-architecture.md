# System Architecture - Program Structure Chart

## High-Level System Structure

```mermaid
graph TB
    MAIN["LABSYCH MAIN SYSTEM"]
    
    subgraph "Presentation Layer"
        WEB["Web Application<br/>(Next.js)"]
        UI["UI Components<br/>(React + Tailwind)"]
    end
    
    subgraph "Application Layer"
        API["REST API Server<br/>(Express.js)"]
        AUTH["Authentication<br/>Middleware"]
        VALID["Validation<br/>Layer"]
    end
    
    subgraph "Business Logic Layer"
        M1["User Management<br/>Module"]
        M2["Equipment Management<br/>Module"]
        M3["Booking Processing<br/>Module"]
        M4["Payment Processing<br/>Module"]
        M5["Lifecycle Management<br/>Module"]
        M6["Reporting Module"]
    end
    
    subgraph "Data Access Layer"
        ORM["Prisma ORM"]
        CACHE["Redis Cache"]
    end
    
    subgraph "External Services"
        MPESA["M-Pesa API"]
        EMAIL["SendGrid Email"]
        SMS["Africa's Talking SMS"]
        S3["AWS S3 Storage"]
    end
    
    subgraph "Data Storage"
        DB[("PostgreSQL<br/>Database")]
        FILES[("File Storage<br/>S3 Buckets")]
    end
    
    %% Flow connections
    MAIN --> WEB
    WEB --> UI
    UI --> API
    
    API --> AUTH
    AUTH --> VALID
    VALID --> M1
    VALID --> M2
    VALID --> M3
    VALID --> M4
    VALID --> M5
    VALID --> M6
    
    M1 --> ORM
    M2 --> ORM
    M3 --> ORM
    M4 --> ORM
    M5 --> ORM
    M6 --> ORM
    
    ORM --> CACHE
    ORM --> DB
    
    M4 --> MPESA
    M3 --> EMAIL
    M3 --> SMS
    M5 --> S3
    M2 --> S3
    
    S3 --> FILES
    
    style MAIN fill:#e1f5ff
    style API fill:#fff4e1
    style DB fill:#e8f5e9
    style FILES fill:#e8f5e9
```

---

## Three-Tier Architecture

```mermaid
graph LR
    subgraph "TIER 1: Client"
        BROWSER["Web Browser"]
        MOBILE["Mobile Browser"]
    end
    
    subgraph "TIER 2: Application Server"
        NEXTJS["Next.js<br/>SSR/SSG"]
        EXPRESS["Express API<br/>Business Logic"]
        WORKER["Background Workers<br/>(Bull Queue)"]
    end
    
    subgraph "TIER 3: Data Server"
        POSTGRES["PostgreSQL<br/>Primary Database"]
        REDIS_DB["Redis<br/>Session + Cache"]
        S3_STORAGE["AWS S3<br/>File Storage"]
    end
    
    BROWSER -->|HTTPS| NEXTJS
    MOBILE -->|HTTPS| NEXTJS
    
    NEXTJS -->|API Calls| EXPRESS
    EXPRESS -->|Queue Jobs| WORKER
    
    EXPRESS -->|SQL Queries| POSTGRES
    EXPRESS -->|Cache R/W| REDIS_DB
    WORKER -->|Upload Files| S3_STORAGE
    
    style NEXTJS fill:#61dafb,color:#000
    style EXPRESS fill:#90c53f,color:#000
    style POSTGRES fill:#336791,color:#fff
```

---

## Module Hierarchy

```mermaid
graph TB
    ROOT["Labsych System"]
    
    ROOT --> FRONTEND["Frontend Module"]
    ROOT --> BACKEND["Backend Module"]
    ROOT --> SERVICES["External Services"]
    
    FRONTEND --> PAGES["Page Components"]
    FRONTEND --> COMPONENTS["Shared Components"]
    FRONTEND --> HOOKS["Custom Hooks"]
    FRONTEND --> UTILS["Utility Functions"]
    
    PAGES --> P1["Landing Page"]
    PAGES --> P2["Authentication Pages"]
    PAGES --> P3["School Dashboard"]
    PAGES --> P4["Admin Dashboard"]
    PAGES --> P5["Equipment Catalog"]
    PAGES --> P6["Booking Pages"]
    PAGES --> P7["Payment Pages"]
    
    BACKEND --> ROUTES["API Routes"]
    BACKEND --> CONTROLLERS["Controllers"]
    BACKEND --> MIDDLEWARES["Middlewares"]
    BACKEND --> MODELS["Data Models"]
    
    ROUTES --> R1["User Routes"]
    ROUTES --> R2["Equipment Routes"]
    ROUTES --> R3["Booking Routes"]
    ROUTES --> R4["Payment Routes"]
    ROUTES --> R5["Admin Routes"]
    
    SERVICES --> EXT1["M-Pesa Integration"]
    SERVICES --> EXT2["Email Service"]
    SERVICES --> EXT3["SMS Service"]
    SERVICES --> EXT4["S3 Storage"]
    
    style ROOT fill:#e1f5ff
    style FRONTEND fill:#fff4e1
    style BACKEND fill:#ffe4e1
    style SERVICES fill:#e8f5e9
```

---

## Component Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant NextJS as Next.js Frontend
    participant API as Express API
    participant Auth as Auth Middleware
    participant BL as Business Logic
    participant DB as PostgreSQL
    participant Cache as Redis
    participant Ext as External Service
    
    User->>NextJS: HTTP Request
    NextJS->>API: API Call (REST)
    API->>Auth: Validate Token
    Auth->>Cache: Check Session
    Cache-->>Auth: Session Valid
    Auth->>BL: Execute Business Logic
    BL->>DB: Query/Update Data
    DB-->>BL: Data Response
    BL->>Cache: Update Cache
    BL->>Ext: External API Call (if needed)
    Ext-->>BL: External Response
    BL-->>API: Business Logic Result
    API-->>NextJS: JSON Response
    NextJS-->>User: Rendered Page
```

---

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        L1["Layer 1: Network Security<br/>HTTPS/TLS, Firewall"]
        L2["Layer 2: Authentication<br/>JWT Tokens, Session Management"]
        L3["Layer 3: Authorization<br/>Role-Based Access Control"]
        L4["Layer 4: Input Validation<br/>Schema Validation, Sanitization"]
        L5["Layer 5: Data Security<br/>Encryption at Rest, Password Hashing"]
        L6["Layer 6: Audit Logging<br/>Activity Tracking, GDPR Compliance"]
    end
    
    USER["User Request"] --> L1
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> L5
    L5 --> L6
    L6 --> APP["Application Core"]
    
    style L1 fill:#ffebee
    style L2 fill:#fff3e0
    style L3 fill:#e8f5e9
    style L4 fill:#e3f2fd
    style L5 fill:#f3e5f5
    style L6 fill:#fce4ec
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        LB["Load Balancer<br/>(Nginx)"]
        
        subgraph "Application Servers"
            APP1["App Server 1<br/>Next.js + Express"]
            APP2["App Server 2<br/>Next.js + Express"]
        end
        
        subgraph "Database Cluster"
            DB_MASTER["PostgreSQL<br/>Master"]
            DB_REPLICA["PostgreSQL<br/>Replica"]
        end
        
        subgraph "Cache Layer"
            REDIS_1["Redis Node 1"]
            REDIS_2["Redis Node 2"]
        end
        
        subgraph "Background Jobs"
            WORKER_1["Worker 1<br/>(Notifications)"]
            WORKER_2["Worker 2<br/>(Reports)"]
        end
    end
    
    INTERNET["Internet"] -->|HTTPS| LB
    LB --> APP1
    LB --> APP2
    
    APP1 --> DB_MASTER
    APP2 --> DB_MASTER
    DB_MASTER -.->|Replication| DB_REPLICA
    
    APP1 --> REDIS_1
    APP2 --> REDIS_2
    
    APP1 -->|Queue Jobs| WORKER_1
    APP2 -->|Queue Jobs| WORKER_2
    
    WORKER_1 --> DB_MASTER
    WORKER_2 --> DB_MASTER
    
    style LB fill:#e1f5ff
    style DB_MASTER fill:#336791,color:#fff
    style INTERNET fill:#ff9800,color:#fff
```

---

## Module Communication Pattern

| Source Module | Target Module | Communication Method | Data Format |
|---------------|---------------|---------------------|-------------|
| Frontend | Backend API | REST API (HTTPS) | JSON |
| API | Database | Prisma ORM | SQL |
| API | Redis | ioredis Client | Key-Value |
| Backend | M-Pesa | HTTPS POST | JSON |
| Backend | SendGrid | HTTPS POST | JSON |
| Backend | S3 | AWS SDK | Binary/Multipart |
| Workers | Database | Prisma ORM | SQL |
| Workers | Email/SMS | HTTPS POST | JSON |

---

## Error Handling Strategy

```mermaid
graph LR
    ERROR["Error Occurs"]
    
    ERROR --> LOG["Log Error<br/>(Winston Logger)"]
    LOG --> CLASSIFY["Classify Error"]
    
    CLASSIFY --> VAL["Validation Error<br/>(400)"]
    CLASSIFY --> AUTH_ERR["Auth Error<br/>(401/403)"]
    CLASSIFY --> NOTFOUND["Not Found<br/>(404)"]
    CLASSIFY --> BUSINESS["Business Logic Error<br/>(422)"]
    CLASSIFY --> SYSTEM["System Error<br/>(500)"]
    
    VAL --> RESPOND["Return Structured<br/>Error Response"]
    AUTH_ERR --> RESPOND
    NOTFOUND --> RESPOND
    BUSINESS --> RESPOND
    SYSTEM --> ALERT["Alert Admin +<br/>Generic Error Message"]
    
    ALERT --> RESPOND
    RESPOND --> CLIENT["Client Receives<br/>Error Details"]
    
    style ERROR fill:#f44336,color:#fff
    style ALERT fill:#ff9800,color:#fff
    style RESPOND fill:#4caf50,color:#fff
```
