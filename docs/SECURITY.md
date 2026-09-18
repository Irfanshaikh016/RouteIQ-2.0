# RouteIQ 2.0 — Security & Multi-Tenant Isolation Architecture

## 1. Multi-Tenant Data Isolation Principle

The primary security mandate in RouteIQ 2.0 is:
> **A user from Organization A must NEVER be able to view, query, modify, delete, or reference assets belonging to Organization B.**

### Defense-in-Depth Implementation:
1. **Token Cryptographic Scoping**: Every JWT includes the claim `org_id`. This claim cannot be tampered with without invalidating the cryptographic signature.
2. **Controller-Level Enforcement**: The dependency `get_current_org_id` extracts `org_id` directly from validated credentials. API handlers strictly pass `org_id` to repository operations.
3. **Repository-Level Filtering**: All retrieval queries (`get_vehicle`, `list_vehicles`, etc.) filter explicitly by `organization_id`. Requests attempting to access entities belonging to another organization return `HTTP 404 Not Found` (rather than disclosing existence).
4. **Relational Constraints**: Attempting to create a delivery where the pickup or destination location belongs to a different organization is actively rejected with `HTTP 400 Bad Request`.
5. **Database Multi-Tenant Unique Constraints**:
   - `UNIQUE (organization_id, registration_number)`
   - `UNIQUE (organization_id, reference_number)`
   These constraints ensure that even across concurrent requests, tenant namespace collisions are strictly prevented.

---

## 2. Credential Security & Zero-Trust Secrets

1. **Password Hashing**: Bcrypt with salted rounds. Plaintext passwords never touch persistence.
2. **Response Sanitization**: All outbound user schemas inherit from `BaseModel` without exposing `password_hash`.
3. **No Hardcoded Secrets**: `SECRET_KEY`, `DATABASE_URL`, and Supabase keys must be provided via `.env` environment variables.
4. **Version Control Safety**: `.gitignore` strictly rejects `.env`, `.env*.local`, `.pem`, `.key`, and certificate bundles.

---

## 3. Automated Security Tests

The automated test suite in `backend/tests/test_security_isolation.py` explicitly tests and validates cross-tenant barriers:
- Proves User B receives `HTTP 404` when attempting to `GET`, `PATCH`, or `DELETE` User A's vehicles.
- Proves User B receives `HTTP 404` when attempting to `GET`, `PATCH`, or `DELETE` User A's locations.
- Proves User B receives `HTTP 404` when attempting to `GET`, `PATCH`, or `DELETE` User A's deliveries.
- Proves User B is blocked (`HTTP 400`) from creating a delivery referencing User A's locations.
