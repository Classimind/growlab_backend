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
