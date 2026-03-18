# User Management Module - Structure Chart

## Module Overview
Handles user registration, authentication, profile management, and access control for both school users and administrators.

---

## Main Structure Chart

```mermaid
graph TB
    MAIN["User Management Module"]
    
    MAIN --> REG["Registration<br/>Controller"]
    MAIN --> AUTH["Authentication<br/>Controller"]
    MAIN --> PROFILE["Profile Management<br/>Controller"]
    MAIN --> ACCESS["Access Control<br/>Middleware"]
    
    REG --> VAL_REG["Validate Registration<br/>Data"]
    REG --> CHECK_EMAIL["Check Email<br/>Uniqueness"]
    REG --> SEND_VERIFY["Send Verification<br/>Email"]
    REG --> CREATE_USER["Create User<br/>Record"]
    
    AUTH --> VAL_LOGIN["Validate Login<br/>Credentials"]
    AUTH --> VERIFY_PASS["Verify Password<br/>(bcrypt)"]
    AUTH --> GEN_TOKEN["Generate JWT<br/>Token"]
    AUTH --> CREATE_SESSION["Create Session<br/>(Redis)"]
    AUTH --> LOGOUT["Logout &<br/>Destroy Session"]
    
    PROFILE --> GET_PROFILE["Get User<br/>Profile"]
    PROFILE --> UPDATE_PROFILE["Update Profile<br/>Data"]
    PROFILE --> CHANGE_PASS["Change Password"]
    PROFILE --> UPLOAD_AVATAR["Upload Profile<br/>Photo (S3)"]
    
    ACCESS --> VERIFY_TOKEN["Verify JWT<br/>Token"]
    ACCESS --> CHECK_ROLE["Check User<br/>Role"]
    ACCESS --> CHECK_PERM["Check<br/>Permissions"]
    
    VAL_REG --> DB_USER[("Users DB")]
    CHECK_EMAIL --> DB_USER
    CREATE_USER --> DB_USER
    SEND_VERIFY --> EMAIL_SVC["Email Service"]
    
    VAL_LOGIN --> DB_USER
    VERIFY_PASS --> DB_USER
    CREATE_SESSION --> REDIS[("Redis Cache")]
    GEN_TOKEN --> REDIS
    LOGOUT --> REDIS
    
    GET_PROFILE --> DB_USER
    GET_PROFILE --> DB_SCHOOL[("School Profile DB")]
    UPDATE_PROFILE --> DB_SCHOOL
    CHANGE_PASS --> DB_USER
    UPLOAD_AVATAR --> S3["S3 Storage"]
    
    VERIFY_TOKEN --> REDIS
    CHECK_ROLE --> DB_USER
    
    style MAIN fill:#e1f5ff
    style DB_USER fill:#336791,color:#fff
    style REDIS fill:#dc382d,color:#fff
    style S3 fill:#ff9900,color:#000
```

---

## Registration Process Flow

```mermaid
flowchart TD
    START([User Submits Registration])
    
    VALIDATE{Validate Input<br/>Schema}
    VALIDATE -->|Invalid| ERR_VAL[Return Validation<br/>Errors]
    VALIDATE -->|Valid| CHECK_EMAIL
    
    CHECK_EMAIL{Email Already<br/>Exists?}
    CHECK_EMAIL -->|Yes| ERR_DUP[Return Duplicate<br/>Email Error]
    CHECK_EMAIL -->|No| CHECK_KU
    
    CHECK_KU{Valid KU<br/>Email Domain?}
    CHECK_KU -->|No| ERR_DOMAIN[Return Invalid<br/>Domain Error]
    CHECK_KU -->|Yes| HASH_PASS
    
    HASH_PASS[Hash Password<br/>with bcrypt<br/>Cost: 12]
    
    HASH_PASS --> CREATE_USER[Create User Record<br/>is_verified = false]
    CREATE_USER --> CREATE_PROFILE[Create School Profile<br/>account_status = ACTIVE]
    
    CREATE_PROFILE --> GEN_TOKEN[Generate Verification<br/>Token<br/>Expires: 24 hours]
    GEN_TOKEN --> STORE_TOKEN[Store Token<br/>in Redis]
    
    STORE_TOKEN --> SEND_EMAIL[Send Verification Email<br/>with Link]
    SEND_EMAIL --> LOG_ACTION[Log Registration<br/>in Audit Trail]
    
    LOG_ACTION --> SUCCESS[Return Success<br/>+ User ID]
    
    ERR_VAL --> END([End])
    ERR_DUP --> END
    ERR_DOMAIN --> END
    SUCCESS --> END
    
    style START fill:#4caf50,color:#fff
    style SUCCESS fill:#4caf50,color:#fff
    style ERR_VAL fill:#f44336,color:#fff
    style ERR_DUP fill:#f44336,color:#fff
    style ERR_DOMAIN fill:#f44336,color:#fff
```

---

## Authentication Process Flow

```mermaid
flowchart TD
    START([User Submits Login])
    
    VALIDATE{Validate Email<br/>& Password}
    VALIDATE -->|Invalid| ERR_VAL[Return 400<br/>Validation Error]
    VALIDATE -->|Valid| FIND_USER
    
    FIND_USER[Query User<br/>by Email]
    FIND_USER --> USER_EXISTS{User<br/>Exists?}
    
    USER_EXISTS -->|No| ERR_CRED[Return 401<br/>Invalid Credentials]
    USER_EXISTS -->|Yes| CHECK_VERIFIED
    
    CHECK_VERIFIED{Email<br/>Verified?}
    CHECK_VERIFIED -->|No| ERR_VERIFY[Return 403<br/>Email Not Verified]
    CHECK_VERIFIED -->|Yes| CHECK_STATUS
    
    CHECK_STATUS{Account<br/>Status?}
    CHECK_STATUS -->|SUSPENDED/BLOCKED| ERR_STATUS[Return 403<br/>Account Suspended]
    CHECK_STATUS -->|ACTIVE| VERIFY_PASS
    
    VERIFY_PASS[Compare Password<br/>with bcrypt.compare]
    VERIFY_PASS --> PASS_MATCH{Password<br/>Match?}
    
    PASS_MATCH -->|No| ERR_CRED
    PASS_MATCH -->|Yes| GEN_JWT
    
    GEN_JWT[Generate JWT Token<br/>Payload: user_id, role<br/>Expires: 7 days]
    
    GEN_JWT --> CREATE_SESSION[Create Redis Session<br/>Key: session:user_id<br/>TTL: 7 days]
    
    CREATE_SESSION --> UPDATE_LOGIN[Update last_login<br/>Timestamp]
    UPDATE_LOGIN --> LOG_LOGIN[Log Login Event<br/>in Audit Trail]
    
    LOG_LOGIN --> RETURN_DATA[Return User Data +<br/>JWT Token +<br/>Profile Info]
    
    RETURN_DATA --> END([End])
    ERR_VAL --> END
    ERR_CRED --> END
    ERR_VERIFY --> END
    ERR_STATUS --> END
    
    style START fill:#4caf50,color:#fff
    style RETURN_DATA fill:#4caf50,color:#fff
    style ERR_VAL fill:#f44336,color:#fff
    style ERR_CRED fill:#f44336,color:#fff
    style ERR_VERIFY fill:#f44336,color:#fff
    style ERR_STATUS fill:#f44336,color:#fff
```

---

## Authorization Middleware Flow

```mermaid
flowchart TD
    START([API Request])
    
    EXTRACT[Extract JWT Token<br/>from Authorization Header]
    
    EXTRACT --> TOKEN_EXISTS{Token<br/>Exists?}
    TOKEN_EXISTS -->|No| ERR_AUTH[Return 401<br/>Unauthorized]
    TOKEN_EXISTS -->|Yes| VERIFY
    
    VERIFY[Verify JWT Signature<br/>with Secret Key]
    VERIFY --> VALID{Token<br/>Valid?}
    
    VALID -->|No| ERR_AUTH
    VALID -->|Yes| CHECK_SESSION
    
    CHECK_SESSION[Check Redis Session<br/>Key: session:user_id]
    CHECK_SESSION --> SESSION_EXISTS{Session<br/>Exists?}
    
    SESSION_EXISTS -->|No| ERR_SESSION[Return 401<br/>Session Expired]
    SESSION_EXISTS -->|Yes| DECODE
    
    DECODE[Decode JWT Payload<br/>Extract user_id, role]
    
    DECODE --> CHECK_ROLE{Required<br/>Role?}
    CHECK_ROLE -->|ADMIN Only| IS_ADMIN{User Role<br/>= ADMIN?}
    CHECK_ROLE -->|SCHOOL Only| IS_SCHOOL{User Role<br/>= SCHOOL?}
    CHECK_ROLE -->|Any Authenticated| ATTACH_USER
    
    IS_ADMIN -->|No| ERR_FORBIDDEN[Return 403<br/>Forbidden]
    IS_ADMIN -->|Yes| ATTACH_USER
    
    IS_SCHOOL -->|No| ERR_FORBIDDEN
    IS_SCHOOL -->|Yes| ATTACH_USER
    
    ATTACH_USER[Attach User Object<br/>to Request Context<br/>req.user = userData]
    
    ATTACH_USER --> NEXT[Call Next<br/>Middleware/Controller]
    
    NEXT --> END([Continue Request])
    ERR_AUTH --> END
    ERR_SESSION --> END
    ERR_FORBIDDEN --> END
    
    style START fill:#2196f3,color:#fff
    style NEXT fill:#4caf50,color:#fff
    style ERR_AUTH fill:#f44336,color:#fff
    style ERR_SESSION fill:#f44336,color:#fff
    style ERR_FORBIDDEN fill:#ff9800,color:#000
```

---

## Profile Update Process

```mermaid
flowchart TD
    START([User Submits Profile Update])
    
    AUTH[Verify User<br/>is Authenticated]
    AUTH --> VALIDATE
    
    VALIDATE{Validate Update<br/>Data Schema}
    VALIDATE -->|Invalid| ERR_VAL[Return 400<br/>Validation Error]
    VALIDATE -->|Valid| CHECK_PERMISSION
    
    CHECK_PERMISSION{User Updating<br/>Own Profile?}
    CHECK_PERMISSION -->|No & Not Admin| ERR_PERM[Return 403<br/>Forbidden]
    CHECK_PERMISSION -->|Yes or Admin| LOAD_CURRENT
    
    LOAD_CURRENT[Load Current<br/>Profile Data]
    
    LOAD_CURRENT --> PHOTO_UPDATE{Photo<br/>Update?}
    PHOTO_UPDATE -->|Yes| UPLOAD_S3[Upload to S3<br/>Bucket: user-avatars<br/>Generate Unique Key]
    PHOTO_UPDATE -->|No| MERGE_DATA
    
    UPLOAD_S3 --> DELETE_OLD[Delete Old Photo<br/>from S3 if exists]
    DELETE_OLD --> MERGE_DATA
    
    MERGE_DATA[Merge Updated Fields<br/>with Current Data]
    
    MERGE_DATA --> UPDATE_DB[Update User Record<br/>Update School Profile]
    UPDATE_DB --> LOG_UPDATE[Log Profile Update<br/>in Audit Trail]
    
    LOG_UPDATE --> CLEAR_CACHE[Clear User Cache<br/>in Redis]
    CLEAR_CACHE --> RETURN_UPDATED[Return Updated<br/>Profile Data]
    
    RETURN_UPDATED --> END([End])
    ERR_VAL --> END
    ERR_PERM --> END
    
    style START fill:#4caf50,color:#fff
    style RETURN_UPDATED fill:#4caf50,color:#fff
    style ERR_VAL fill:#f44336,color:#fff
    style ERR_PERM fill:#f44336,color:#fff
```

---

## Function Specifications

### 1. registerUser()
**Purpose**: Create new user account with email verification  
**Input**: 
- email (string, required)
- password (string, min 8 chars, required)
- full_name (string, required)
- phone_number (string, optional)
- school_name (string, required for SCHOOL type)
- registration_number (string, required for SCHOOL type)

**Output**: 
```json
{
  "success": true,
  "user_id": "uuid",
  "message": "Verification email sent"
}
```

**Algorithm**:
1. Validate input schema
2. Check email uniqueness
3. Verify KU email domain (@ku.ac.ke or @students.ku.ac.ke)
4. Hash password (bcrypt, cost 12)
5. Create USER record (is_verified = false)
6. Create SCHOOL_PROFILE record
7. Generate verification token (24h expiry)
8. Store token in Redis
9. Send verification email via SendGrid
10. Log action in AUDIT_LOG
11. Return success response

**Error Handling**:
- 400: Validation errors
- 409: Duplicate email
- 422: Invalid email domain
- 500: Database/service errors

---

### 2. loginUser()
**Purpose**: Authenticate user and create session  
**Input**:
- email (string, required)
- password (string, required)

**Output**:
```json
{
  "success": true,
  "token": "jwt_token_string",
  "user": {
    "user_id": "uuid",
    "email": "user@ku.ac.ke",
    "full_name": "John Doe",
    "user_type": "SCHOOL",
    "profile": {...}
  }
}
```

**Algorithm**:
1. Validate input
2. Find user by email
3. Check if user exists
4. Verify email is verified
5. Check account status (ACTIVE)
6. Compare password hash (bcrypt.compare)
7. Generate JWT token (7 day expiry)
8. Create Redis session (TTL 7 days)
9. Update last_login timestamp
10. Log login in AUDIT_LOG
11. Return token + user data

**Error Handling**:
- 400: Validation errors
- 401: Invalid credentials
- 403: Email not verified or account suspended
- 500: System errors

---

### 3. verifyToken()
**Purpose**: Middleware to verify JWT and attach user to request  
**Input**: JWT token from Authorization header  
**Output**: Populates `req.user` object or throws error

**Algorithm**:
1. Extract token from header
2. Verify JWT signature
3. Check Redis session exists
4. Decode payload
5. Check role if required
6. Attach user data to request
7. Call next()

**Error Handling**:
- 401: No token or invalid token
- 403: Insufficient permissions
- 500: Verification errors

---

### 4. updateProfile()
**Purpose**: Update user profile information  
**Input**:
- user_id (from JWT)
- Updates object (partial profile data)

**Output**: Updated user profile object

**Algorithm**:
1. Verify authentication
2. Check permission (own profile or admin)
3. Validate update data
4. Handle photo upload to S3 if present
5. Merge updates with current data
6. Update database records
7. Clear user cache
8. Log action
9. Return updated profile

**Error Handling**:
- 400: Validation errors
- 403: Permission denied
- 404: User not found
- 500: Update/upload errors

---

## Database Tables Used

| Table | Operations | Purpose |
|-------|-----------|---------|
| USER | CREATE, READ, UPDATE | Core user authentication data |
| SCHOOL_PROFILE | CREATE, READ, UPDATE | Extended school information |
| AUDIT_LOG | CREATE, READ | Track all user actions |

---

## External Dependencies

| Service | Usage | Configuration |
|---------|-------|---------------|
| bcrypt | Password hashing | Cost factor: 12 |
| jsonwebtoken | JWT generation/verification | Secret: env.JWT_SECRET, Expiry: 7d |
| Redis | Session storage | TTL: 7 days |
| SendGrid | Email verification | API Key: env.SENDGRID_API_KEY |
| AWS S3 | Profile photo storage | Bucket: labsych-user-avatars |
