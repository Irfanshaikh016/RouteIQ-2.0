# RouteIQ 2.0 — Authentication & Authorization Architecture

## 1. Authentication Overview

RouteIQ 2.0 uses stateless, cryptographically-signed **JSON Web Tokens (JWT)** based on the industry-standard OAuth2 Bearer token pattern.

All authentication flows avoid storing passwords in plaintext or transmitting sensitive cryptographic hashes.

---

## 2. Password Security & Hashing

- **Algorithm**: Salted `bcrypt` using `passlib.context.CryptContext`.
- **Rounds**: Automatically managed work factor preventing brute-force and rainbow table attacks.
- **Verification**: Constant-time comparison preventing timing attacks.
- **Leak Prevention**: `password_hash` is strictly excluded from all Pydantic response models (`UserResponse`, `TokenResponse`).

---

## 3. Token Architecture

### Token Specification
- **Algorithm**: `HS256` (HMAC with SHA-256).
- **Secret Key**: Configurable via `SECRET_KEY` environment variable.
- **Expiration**: Defaults to 24 hours (`ACCESS_TOKEN_EXPIRE_MINUTES = 1440`).

### Token Payload Structure
```json
{
  "sub": "b2f671c4-1249-410d-83b5-78e2023bf8aa",
  "org_id": "90e38634-8c08-4171-aa31-e40fc15dc3d9",
  "role": "admin",
  "iat": 1789728000,
  "exp": 1789814400
}
```

- `sub`: User's unique UUID.
- `org_id`: User's primary Organization UUID. Used to enforce multi-tenant isolation on all downstream data requests.
- `role`: Role string (`admin`, `manager`, `operator`).
- `iat`: Timestamp of issuance.
- `exp`: Timestamp of token expiration.

---

## 4. Role-Based Access Control (RBAC)

RouteIQ 2.0 supports three user roles:

| Role | Permitted Actions |
|---|---|
| **`admin`** | Full organization administrative access. Can register assets, update organization profile, manage user roles, and perform all operations. |
| **`manager`** | Fleet and delivery operations manager. Can create, edit, and delete vehicles, locations, and delivery consignments. |
| **`operator`** | Operations staff / dispatch operator. Can create deliveries and locations, and view fleet assets without administrative mutation rights. |

---

## 5. Security Best Practices Implemented

1. **Email Enumeration Mitigation**: Failed logins return generic HTTP 401 `Invalid email or password credentials` regardless of whether the email exists in the database.
2. **Account Invalidation**: Tokens belonging to inactive users (`is_active = False`) are rejected on every request.
3. **Stateless Logout**: Client clears the token from `localStorage`; the backend endpoint `/api/v1/auth/logout` explicitly confirms session termination.
