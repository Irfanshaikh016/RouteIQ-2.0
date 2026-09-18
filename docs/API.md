# RouteIQ 2.0 — REST API Reference (Phase 2)

Base URL: `http://localhost:8000/api/v1`

---

## 1. Authentication Endpoints

### `POST /auth/register`
Creates a new tenant Organization and administrator User account.
- **Access**: Public
- **Status**: `201 Created`
- **Request Body**:
  ```json
  {
    "email": "dispatcher@logistics-ner.in",
    "password": "MinLength8Characters!",
    "full_name": "Tenzing Norbu",
    "organization_name": "Himalayan Express Logistics",
    "role": "admin"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in_seconds": 86400,
    "user_id": "b2f671c4-1249-410d-83b5-78e2023bf8aa",
    "organization_id": "90e38634-8c08-4171-aa31-e40fc15dc3d9",
    "role": "admin",
    "email": "dispatcher@logistics-ner.in",
    "full_name": "Tenzing Norbu"
  }
  ```

### `POST /auth/login`
Authenticates a user and returns a signed JWT.
- **Access**: Public
- **Status**: `200 OK`
- **Request Body**:
  ```json
  {
    "email": "dispatcher@logistics-ner.in",
    "password": "MinLength8Characters!"
  }
  ```

### `POST /auth/logout`
Stateless logout acknowledgement.
- **Access**: Authenticated

### `GET /auth/me`
Retrieves the profile of the currently authenticated user.
- **Access**: Authenticated

---

## 2. Vehicles Endpoints

All vehicle endpoints require an authenticated Bearer token and are strictly scoped to the user's `organization_id`.

| Method | Endpoint | Description | Permitted Roles |
|---|---|---|---|
| `POST` | `/vehicles` | Create new vehicle asset | `admin`, `manager` |
| `GET` | `/vehicles` | List all organization vehicles | `admin`, `manager`, `operator` |
| `GET` | `/vehicles/{id}` | Get single vehicle by ID | `admin`, `manager`, `operator` |
| `PATCH` | `/vehicles/{id}` | Update vehicle parameters | `admin`, `manager` |
| `DELETE` | `/vehicles/{id}` | Delete vehicle asset | `admin`, `manager` |

---

## 3. Locations Endpoints

Depots, hubs, and address stops. Coordinates must satisfy `latitude: [-90, 90]` and `longitude: [-180, 180]`.

| Method | Endpoint | Description | Permitted Roles |
|---|---|---|---|
| `POST` | `/locations` | Register new facility stop | `admin`, `manager`, `operator` |
| `GET` | `/locations` | List organization facilities | `admin`, `manager`, `operator` |
| `GET` | `/locations/{id}` | Get location details | `admin`, `manager`, `operator` |
| `PATCH` | `/locations/{id}` | Update facility details | `admin`, `manager` |
| `DELETE` | `/locations/{id}` | Delete facility (blocked if active orders exist) | `admin`, `manager` |

---

## 4. Deliveries Endpoints

Delivery orders linking pickup and delivery locations within the same organization.

| Method | Endpoint | Description | Permitted Roles |
|---|---|---|---|
| `POST` | `/deliveries` | Create delivery consignment | `admin`, `manager`, `operator` |
| `GET` | `/deliveries` | List organization deliveries | `admin`, `manager`, `operator` |
| `GET` | `/deliveries/{id}` | Get delivery by ID | `admin`, `manager`, `operator` |
| `PATCH` | `/deliveries/{id}` | Update delivery status/params | `admin`, `manager`, `operator` |
| `DELETE` | `/deliveries/{id}` | Delete/cancel delivery | `admin`, `manager` |

---

## 5. Error Response Format

Errors return consistent, client-safe JSON payloads without internal stack traces:
```json
{
  "detail": "Descriptive client-safe error message"
}
```
Standard status codes:
- `400 Bad Request`: Validation failure or semantic constraint error.
- `401 Unauthorized`: Missing or invalid Bearer credentials.
- `403 Forbidden`: Insufficient role permissions or inactive account.
- `404 Not Found`: Entity does not exist or belongs to another tenant.
- `422 Unprocessable Entity`: Input schema validation failed.
