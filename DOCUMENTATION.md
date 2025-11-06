# DOCUMENTATION

# Plant API - Endpoints Usage Guide

Base URL: `http://<your-server>/plants`

This guide explains how to **use the Plant API** to manage Hydroponics plants.

---

## 1. GET /plants/

**Description:** Retrieve all plants.

**Request:**

```http
GET /plants/
```

**Response:**

* Returns a list of plants in JSON format.

```json
[
  {
    "plant_name": "Lettuce",
    "type": "Leafy Green",
    "ph_range": "5.5–6.5",
    "ec_range": "1.0–1.5",
    "light_hours": "12–16",
    "growth_cycle_days": "30–45",
    "notes": "Fast-growing, ideal for beginners."
  }
]
```

---

## 2. GET /plants/{plant_name}

**Description:** Retrieve a single plant by name.

**Request:**

```http
GET /plants/Lettuce
```

**Response:**

```json
{
  "plant_name": "Lettuce",
  "type": "Leafy Green",
  "ph_range": "5.5–6.5",
  "ec_range": "1.0–1.5",
  "light_hours": "12–16",
  "growth_cycle_days": "30–45",
  "notes": "Fast-growing, ideal for beginners."
}
```

**Errors:**

* `404 Not Found` if the plant does not exist.

---

## 3. POST /plants/

**Description:** Add a single new plant.

**Request:**

```http
POST /plants/
Content-Type: application/json

{
  "plant_name": "Basil",
  "type": "Herb",
  "ph_range": "5.5–6.5",
  "ec_range": "1.2–1.8",
  "light_hours": "10–14",
  "growth_cycle_days": "40–50",
  "notes": "Good companion plant for tomatoes."
}
```

**Response:**

```json
{
  "plant_name": "Basil",
  "type": "Herb",
  "ph_range": "5.5–6.5",
  "ec_range": "1.2–1.8",
  "light_hours": "10–14",
  "growth_cycle_days": "40–50",
  "notes": "Good companion plant for tomatoes."
}
```

**Errors:**

* `400 Bad Request` if a plant with the same name already exists.

---

## 4. POST /plants/all

**Description:** Add multiple plants in bulk.

**Request:**

```http
POST /plants/all
Content-Type: application/json

[
  {
    "plant_name": "Lettuce",
    "type": "Leafy Green",
    "ph_range": "5.5–6.5",
    "ec_range": "1.0–1.5",
    "light_hours": "12–16",
    "growth_cycle_days": "30–45",
    "notes": "Fast-growing, ideal for beginners."
  },
  {
    "plant_name": "Tomato",
    "type": "Fruit",
    "ph_range": "6.0–6.8",
    "ec_range": "2.0–3.0",
    "light_hours": "14–18",
    "growth_cycle_days": "60–80",
    "notes": "Requires support and pruning."
  }
]
```

**Response:**

```json
{
  "inserted": ["Tomato"],
  "skipped": ["Lettuce"],
  "total": 2
}
```

* **inserted:** Plants successfully added.
* **skipped:** Plants already existed and were not added.
* **total:** Total plants submitted.

---

**Note:** All responses are returned as JSON. Redis caching is used internally to speed up retrieval.


# User Module Documentation

This module provides models and API endpoints for user authentication and management, including email/password signup and login, as well as OAuth login via external providers.

---

## Enums

### Provider

Authentication providers:

* `EMAIL`: Email/password authentication
* `GOOGLE`: Google OAuth
* `FACEBOOK`: Facebook OAuth
* `GITHUB`: GitHub OAuth

### Role

User roles:

* `growlab:superadmin`: Company super administrator
* `growlab:employee`: Company employee
* `farm:admin`: Farm administrator
* `farm:employee`: Farm employee
* `user`: Normal user

---

## Models

### OAuthUser

Represents OAuth provider user details.

**Fields**

* `provider`: OAuth provider (Provider enum)
* `provider_user_id`: Unique ID from the OAuth provider
* `email`: Optional user email from provider
* `name`: Optional full name
* `avatar_url`: Optional avatar URL
* `access_token`: OAuth access token
* `refresh_token`: Optional OAuth refresh token

**Example**

```json
{
  "provider": "google",
  "provider_user_id": "12345",
  "email": "user@example.com",
  "name": "John Doe",
  "avatar_url": "http://avatar.url",
  "access_token": "ya29.a0AfH6SMB...",
  "refresh_token": "1//0gR..."
}
```

---

### User

Represents a system user.

**Fields**

* `email`: User email (required if provider is EMAIL)
* `password`: User password (required if provider is EMAIL)
* `provider`: Authentication provider
* `oauth`: OAuth details (required if provider is not EMAIL)
* `created_at`: Account creation timestamp (defaults to UTC now)
* `role`: User role (default `user`)
* `domain_ids`: Mapping of domain IDs to roles

**Validators**

* `validate_email_password`: Ensures email and password are provided if provider is EMAIL
* `validate_oauth`: Ensures OAuth details are provided if provider is not EMAIL

**Example (Email User)**

```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "provider": "EMAIL",
  "role": "user",
  "domain_ids": {
    "farm123": "farm:admin"
  }
}
```

**Example (OAuth User)**

```json
{
  "provider": "google",
  "oauth": {
    "provider": "google",
    "provider_user_id": "12345",
    "email": "user@example.com",
    "name": "John Doe",
    "avatar_url": "http://avatar.url",
    "access_token": "ya29.a0AfH6SMB..."
  },
  "role": "user",
  "domain_ids": {}
}
```

---

### EmailSignup

Model for email signup request.

**Example**

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

---

### Email Login

Model for email login request.

**Example**

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

---

### OAuthLogin

Model for OAuth login request.

**Example**

```json
{
  "provider": "google",
  "provider_user_id": "12345",
  "access_token": "ya29.a0AfH6SMB...",
  "email": "user@example.com",
  "name": "John Doe",
  "avatar_url": "http://avatar.url"
}
```

---

### Token

Represents access and refresh tokens.

**Fields**

* `access_token`: Access token string
* `refresh_token`: Refresh token string
* `token_type`: Token type, default "bearer"

**Example**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## API Endpoints

### POST /refresh

Refresh an access token using a refresh token.

**Request**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Errors**

* 401 Unauthorized: Invalid refresh token

---

### POST /signup

Register a new user using email/password.

**Request**

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Errors**

* 400 Bad Request: Email already registered or missing fields
* 500 Internal Server Error: Database error

---

### POST /login

Authenticate an existing user using email/password.

**Request**

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Errors**

* 401 Unauthorized: Invalid credentials

---

### POST /oauth-login

Authenticate or register a user using OAuth.

**Request**

```json
{
  "provider": "google",
  "provider_user_id": "12345",
  "access_token": "ya29.a0AfH6SMB...",
  "email": "user@example.com",
  "name": "John Doe",
  "avatar_url": "http://avatar.url"
}
```

**Response**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Notes**

* Creates a new user if not already registered
* Uses provider + provider_user_id for authentication


## Actuator WebSocket Usage Guide

This guide explains how to use the WebSocket endpoint to monitor actuator states in real-time.

---

## Endpoint

`ws://<server_address>/actuators/{farm_name}/{actuator_name}`

**Path Parameters:**
- `farm_name` – Name of the farm.
- `actuator_name` – Name of the actuator.

**Example URL:**

`ws://localhost:8000/actuators/farm1/pump1`

---

## Connecting

1. Open a WebSocket connection to the endpoint with the correct `farm_name` and `actuator_name`.
2. The server registers the connection and sends the last known actuator status.

---

## Initial Data

Upon connecting, the server sends the last known actuator status:

```json
{
  "type": "init",
  "status": "<current_status>"
}
```

# Sensor API Documentation

## This API allows developers to **collect, retrieve, and stream sensor data** from farms. It supports REST endpoints for historical data and WebSocket for real-time updates.


## Base URL

All endpoints are prefixed with the API router, e.g. `/sensors-history`.

---

## Models

### Sensor

```json
{
  "sensor_name": "temperature",
  "farm_id": "farm1",
  "value": 25.5,
  "unit": "C",
  "sensor_type": "analog",
  "created": "2025-11-05T16:08:24.233474+00:00"
}
```

* `sensor_name` (string): Name of the sensor.
* `farm_id` (string): Farm identifier.
* `value` (float): Sensor reading.
* `unit` (string, optional): Unit of measurement.
* `sensor_type` (string, optional): Type of sensor.
* `created` (datetime, optional): Timestamp of the reading. Defaults to current UTC time.

---

## REST API Endpoints

### 1. Add a Single Sensor Reading

**POST** `/sensors-history/collect`
**Request Body:** `Sensor` JSON
**Response:** Saved `Sensor` object

**Behavior:** Saves the sensor reading and broadcasts to connected WebSocket clients.

---

### 2. Add Multiple Sensor Readings (Batch)

**POST** `/sensors-history/collect/batch`
**Request Body:** List of `Sensor` objects
**Response:** List of saved sensors

**Behavior:** Saves multiple readings. WebSocket broadcast not included by default.

---

### 3. Get All Sensor Readings

**GET** `/sensors-history/`
**Response:** List of `Sensor` objects

---

### 4. Get Sensors by Farm

**GET** `/sensors-history/farm/{farm_id}`
**Path Parameter:** `farm_id`
**Response:** List of `Sensor` objects for the specified farm.

---

### 5. Get Sensors by Date Range

**GET** `/sensors-history/range/`
**Query Parameters:** `start` (ISO datetime), `end` (ISO datetime)
**Response:** List of `Sensor` objects within the date range.

---

### 6. Get Sensors by Farm and Date Range

**GET** `/sensors-history/farm/{farm_id}/range/`
**Path Parameter:** `farm_id`
**Query Parameters:** `start`, `end` (ISO datetime)
**Response:** List of `Sensor` objects filtered by farm and date range.

---

### 7. Get Sensors by Farm and Sensor Name

**GET** `/sensors-history/farm/{farm_id}/sensor/{sensor_name}`
**Path Parameters:**

* `farm_id`
* `sensor_name`

**Response:** List of `Sensor` objects for the specific sensor on the specified farm.

---

## WebSocket Endpoint

### Live Updates

**WS** `/sensors-history/live/{farm_id}/{sensor_name}`

**Behavior:**

* Client subscribes to a specific sensor on a farm.
* Sends new sensor readings in real-time as they are inserted.
* Optional: fetch last reading on connect.

**Message format:**

```json
{
  "type": "update",
  "data": {
    "sensor_name": "temperature",
    "farm_id": "farm1",
    "value": 26.1,
    "unit": "C",
    "sensor_type": "analog",
    "created": "2025-11-05T16:08:24.233474+00:00"
  }
}
```


# Sensors API Documentation


## Base URL

```
/sensors
```

---

## Models

### `SensorType` (Enum)

| Value   | Description    |
| ------- | -------------- |
| ANALOG  | Analog sensor  |
| DIGITAL | Digital sensor |

---

### `RegisterSensor` (Request Model)

| Field       | Type                | Required    | Description                                            |
| ----------- | ------------------- | ----------- | ------------------------------------------------------ |
| sensor_name | string              | Yes         | Name of the sensor                                     |
| farm_id     | string              | Yes         | ID of the farm this sensor belongs to                  |
| unit        | string              | Yes         | Measurement unit of the sensor                         |
| sensor_type | SensorType          | Yes         | Type of sensor: ANALOG or DIGITAL                      |
| range       | Tuple[float, float] | Conditional | Required if sensor_type is ANALOG; ignored for DIGITAL |
| created     | datetime            | Optional    | Timestamp of creation (defaults to current UTC time)   |

> **Validation:**
>
> * Analog sensors must define a valid `(min, max)` range where `min < max`.
> * Digital sensors ignore the `range` field.

---

### `ResponseSensor` (Response Model)

| Field       | Type                | Description                                |
| ----------- | ------------------- | ------------------------------------------ |
| id          | string              | Sensor ID (MongoDB ObjectId as string)     |
| sensor_name | string              | Name of the sensor                         |
| farm_id     | string              | ID of the farm                             |
| unit        | string              | Measurement unit                           |
| sensor_type | SensorType          | Type of sensor                             |
| range       | Tuple[float, float] | Range for analog sensors; null for digital |
| created     | datetime            | Sensor creation timestamp                  |

---

## Endpoints

### 1. Create Sensor

**POST** `/sensors/`

* **Request Body:** `RegisterSensor`
* **Response:** `ResponseSensor`
* **Status Codes:**

  * `201 CREATED` – Sensor created successfully
  * `500 INTERNAL SERVER ERROR` – Unexpected server error

**Behavior:**

* Inserts the sensor only if it does not already exist with the same `farm_id` and **case-insensitive** `sensor_name`.
* Returns the existing sensor if found.

**Example Request:**

```json
{
  "sensor_name": "Temperature",
  "farm_id": "farm123",
  "unit": "°C",
  "sensor_type": "ANALOG",
  "range": [0, 100]
}
```

**Example Response:**

```json
{
  "id": "650c1e2d5a0f1b2c3d4e5f6a",
  "sensor_name": "Temperature",
  "farm_id": "farm123",
  "unit": "°C",
  "sensor_type": "ANALOG",
  "range": [0, 100],
  "created": "2025-11-06T21:00:00Z"
}
```

---

### 2. List Sensors with Pagination

**GET** `/sensors/`

* **Query Parameters:**

  * `page` (int, default=1) – Page number (starting from 1)
  * `limit` (int, default=10) – Number of sensors per page

* **Response:** List of `ResponseSensor`

**Example Request:**

```
GET /sensors/?page=2&limit=5
```

**Example Response:**

```json
[
  {
    "id": "650c1e2d5a0f1b2c3d4e5f6b",
    "sensor_name": "Humidity",
    "farm_id": "farm123",
    "unit": "%",
    "sensor_type": "ANALOG",
    "range": [0, 100],
    "created": "2025-11-06T21:05:00Z"
  }
]
```

---

### 3. Get Sensor by ID

**GET** `/sensors/{sensor_id}`

* **Path Parameter:** `sensor_id` – MongoDB ObjectId as string
* **Response:** `ResponseSensor`
* **Status Codes:**

  * `200 OK` – Sensor found
  * `400 BAD REQUEST` – Invalid ID format
  * `404 NOT FOUND` – Sensor not found

---

### 4. Get Sensors by Farm

**GET** `/sensors/farm/{farm_id}`

* **Path Parameter:** `farm_id` – Farm ID
* **Response:** List of `RegisterSensor`
* **Status Codes:**

  * `200 OK` – Returns all sensors for the given farm

---

### 5. Update Sensor

**PUT** `/sensors/{sensor_id}`

* **Path Parameter:** `sensor_id` – MongoDB ObjectId
* **Request Body:** Partial dictionary of updated fields
* **Response:** `ResponseSensor`
* **Status Codes:**

  * `200 OK` – Sensor updated
  * `400 BAD REQUEST` – Invalid ID
  * `404 NOT FOUND` – Sensor not found or no changes made

---

### 6. Delete Sensor

**DELETE** `/sensors/{sensor_id}`

* **Path Parameter:** `sensor_id` – MongoDB ObjectId
* **Response:** JSON message
* **Status Codes:**

  * `204 NO CONTENT` – Sensor deleted successfully
  * `400 BAD REQUEST` – Invalid ID
  * `404 NOT FOUND` – Sensor not found

**Example Response:**

```json
{
  "message": "Sensor and its history deleted successfully"
}
```



