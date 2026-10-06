# API 實測範例

由 `client/api_client.py` 對 `http://127.0.0.1:8000` 實際執行產生。

## 1. GET /api/v1/districts?limit=5

**Request**

```http
GET /api/v1/districts?limit=5
```

**Response** — Status Code: `200`

```json
{
  "total": 11,
  "limit": 5,
  "offset": 0,
  "items": [
    {
      "city_name": "板橋區",
      "city_id": "6500100"
    },
    {
      "city_name": "三重區",
      "city_id": "6500200"
    },
    {
      "city_name": "中和區",
      "city_id": "6500300"
    },
    "... (2 more)"
  ]
}
```

## 2. GET /api/v1/districts/6500100

**Request**

```http
GET /api/v1/districts/6500100
```

**Response** — Status Code: `200`

```json
{
  "city_name": "板橋區",
  "city_id": "6500100"
}
```

## 3. GET /api/v1/districts/6500100/routes

**Request**

```http
GET /api/v1/districts/6500100/routes
```

**Response** — Status Code: `200`

```json
[
  {
    "city_id": "6500100",
    "line_id": "220068"
  }
]
```

## 4. GET /api/v1/routes/220068/trucks

**Request**

```http
GET /api/v1/routes/220068/trucks
```

**Response** — Status Code: `200`

```json
[
  {
    "line_id": "220068",
    "car": "KEJ-6387"
  }
]
```

## 5. GET /api/v1/trucks/KEJ-6387/latest

**Request**

```http
GET /api/v1/trucks/KEJ-6387/latest
```

**Response** — Status Code: `200`

```json
{
  "car": "KEJ-6387",
  "recorded_at": "2026-10-06T21:08:07",
  "address": "新北市板橋區民生路二段161巷5號",
  "longitude": 121.470191666667,
  "latitude": 25.0196316666667,
  "id": 42
}
```

## 6. GET /api/v1/trucks?limit=3

**Request**

```http
GET /api/v1/trucks?limit=3
```

**Response** — Status Code: `200`

```json
{
  "total": 73,
  "limit": 3,
  "offset": 0,
  "items": [
    {
      "line_id": "247006",
      "car": "001-UY"
    },
    {
      "line_id": "241029",
      "car": "022-UY"
    },
    {
      "line_id": "241031",
      "car": "062-VK"
    }
  ]
}
```

## 7. GET /api/v1/locations?limit=3

**Request**

```http
GET /api/v1/locations?limit=3
```

**Response** — Status Code: `200`

```json
{
  "total": 73,
  "limit": 3,
  "offset": 0,
  "items": [
    {
      "car": "KEJ-6635",
      "recorded_at": "2026-10-06T21:08:17",
      "address": "新北市新店區薏仁坑路2-1號",
      "longitude": 121.50069,
      "latitude": 24.9579583333333,
      "id": 1
    },
    {
      "car": "969-R7",
      "recorded_at": "2026-10-06T21:08:10",
      "address": "新北市永和區福和路1號",
      "longitude": 121.526345,
      "latitude": 25.00979,
      "id": 2
    },
    {
      "car": "KEV-0009",
      "recorded_at": "2026-10-06T21:08:14",
      "address": "新北市泰山區黎明路25號",
      "longitude": 121.421965,
      "latitude": 25.0608366666667,
      "id": 3
    }
  ]
}
```

## 8. GET /api/v1/locations/nearby?lat=25.012&lon=121.4627&radius_m=3000&limit=5

**Request**

```http
GET /api/v1/locations/nearby?lat=25.012&lon=121.4627&radius_m=3000&limit=5
```

**Response** — Status Code: `200`

```json
[
  {
    "car": "KEJ-6387",
    "recorded_at": "2026-10-06T21:08:07",
    "address": "新北市板橋區民生路二段161巷5號",
    "longitude": 121.470191666667,
    "latitude": 25.0196316666667,
    "id": 42,
    "distance_m": 1135.8
  }
]
```

## 9. POST /api/v1/districts

**Request**

```http
POST /api/v1/districts
```

```json
{
  "city_id": "DEMO001",
  "city_name": "示範區"
}
```

**Response** — Status Code: `201`

```json
{
  "city_name": "示範區",
  "city_id": "DEMO001"
}
```

## 10. POST /api/v1/districts

**Request**

```http
POST /api/v1/districts
```

```json
{
  "city_id": "DEMO001",
  "city_name": "示範區"
}
```

**Response** — Status Code: `409`

```json
{
  "detail": "district 'DEMO001' already exists"
}
```

## 11. PUT /api/v1/districts/DEMO001

**Request**

```http
PUT /api/v1/districts/DEMO001
```

```json
{
  "city_name": "示範區（改）"
}
```

**Response** — Status Code: `200`

```json
{
  "city_name": "示範區（改）",
  "city_id": "DEMO001"
}
```

## 12. PATCH /api/v1/districts/DEMO001

**Request**

```http
PATCH /api/v1/districts/DEMO001
```

```json
{
  "city_name": "示範區2"
}
```

**Response** — Status Code: `200`

```json
{
  "city_name": "示範區2",
  "city_id": "DEMO001"
}
```

## 13. POST /api/v1/routes

**Request**

```http
POST /api/v1/routes
```

```json
{
  "line_id": "DEMO-L1",
  "city_id": "DEMO001"
}
```

**Response** — Status Code: `201`

```json
{
  "city_id": "DEMO001",
  "line_id": "DEMO-L1"
}
```

## 14. POST /api/v1/routes

**Request**

```http
POST /api/v1/routes
```

```json
{
  "line_id": "X",
  "city_id": "NOPE"
}
```

**Response** — Status Code: `422`

```json
{
  "detail": "referenced district 'NOPE' does not exist"
}
```

## 15. GET /api/v1/routes/DEMO-L1

**Request**

```http
GET /api/v1/routes/DEMO-L1
```

**Response** — Status Code: `200`

```json
{
  "city_id": "DEMO001",
  "line_id": "DEMO-L1"
}
```

## 16. PUT /api/v1/routes/DEMO-L1

**Request**

```http
PUT /api/v1/routes/DEMO-L1
```

```json
{
  "city_id": "DEMO001"
}
```

**Response** — Status Code: `200`

```json
{
  "city_id": "DEMO001",
  "line_id": "DEMO-L1"
}
```

## 17. POST /api/v1/trucks

**Request**

```http
POST /api/v1/trucks
```

```json
{
  "car": "DEMO-001",
  "line_id": "DEMO-L1"
}
```

**Response** — Status Code: `201`

```json
{
  "line_id": "DEMO-L1",
  "car": "DEMO-001"
}
```

## 18. PATCH /api/v1/trucks/DEMO-001

**Request**

```http
PATCH /api/v1/trucks/DEMO-001
```

```json
{
  "line_id": "DEMO-L1"
}
```

**Response** — Status Code: `200`

```json
{
  "line_id": "DEMO-L1",
  "car": "DEMO-001"
}
```

## 19. POST /api/v1/locations

**Request**

```http
POST /api/v1/locations
```

```json
{
  "car": "DEMO-001",
  "recorded_at": "2026-10-06T20:00:00",
  "address": "新北市板橋區中山路一段161號",
  "longitude": 121.4627,
  "latitude": 25.012
}
```

**Response** — Status Code: `201`

```json
{
  "car": "DEMO-001",
  "recorded_at": "2026-10-06T20:00:00",
  "address": "新北市板橋區中山路一段161號",
  "longitude": 121.4627,
  "latitude": 25.012,
  "id": 74
}
```

## 20. GET /api/v1/locations/74

**Request**

```http
GET /api/v1/locations/74
```

**Response** — Status Code: `200`

```json
{
  "car": "DEMO-001",
  "recorded_at": "2026-10-06T20:00:00",
  "address": "新北市板橋區中山路一段161號",
  "longitude": 121.4627,
  "latitude": 25.012,
  "id": 74
}
```

## 21. PUT /api/v1/locations/74

**Request**

```http
PUT /api/v1/locations/74
```

```json
{
  "car": "DEMO-001",
  "recorded_at": "2026-10-06T20:05:00",
  "address": "新北市板橋區縣民大道二段7號",
  "longitude": 121.4635,
  "latitude": 25.0137
}
```

**Response** — Status Code: `200`

```json
{
  "car": "DEMO-001",
  "recorded_at": "2026-10-06T20:05:00",
  "address": "新北市板橋區縣民大道二段7號",
  "longitude": 121.4635,
  "latitude": 25.0137,
  "id": 74
}
```

## 22. PATCH /api/v1/locations/74

**Request**

```http
PATCH /api/v1/locations/74
```

```json
{
  "address": "新北市板橋區（PATCH）"
}
```

**Response** — Status Code: `200`

```json
{
  "car": "DEMO-001",
  "recorded_at": "2026-10-06T20:05:00",
  "address": "新北市板橋區（PATCH）",
  "longitude": 121.4635,
  "latitude": 25.0137,
  "id": 74
}
```

## 23. GET /api/v1/trucks/DEMO-001/latest

**Request**

```http
GET /api/v1/trucks/DEMO-001/latest
```

**Response** — Status Code: `200`

```json
{
  "car": "DEMO-001",
  "recorded_at": "2026-10-06T20:05:00",
  "address": "新北市板橋區（PATCH）",
  "longitude": 121.4635,
  "latitude": 25.0137,
  "id": 74
}
```

## 24. DELETE /api/v1/trucks/DEMO-001

**Request**

```http
DELETE /api/v1/trucks/DEMO-001
```

**Response** — Status Code: `409`

```json
{
  "detail": "truck still has 1 locations; delete them first"
}
```

## 25. DELETE /api/v1/locations/74

**Request**

```http
DELETE /api/v1/locations/74
```

**Response** — Status Code: `204`

_(no content)_

## 26. DELETE /api/v1/trucks/DEMO-001

**Request**

```http
DELETE /api/v1/trucks/DEMO-001
```

**Response** — Status Code: `204`

_(no content)_

## 27. DELETE /api/v1/routes/DEMO-L1

**Request**

```http
DELETE /api/v1/routes/DEMO-L1
```

**Response** — Status Code: `204`

_(no content)_

## 28. DELETE /api/v1/districts/DEMO001

**Request**

```http
DELETE /api/v1/districts/DEMO001
```

**Response** — Status Code: `204`

_(no content)_

## 29. GET /api/v1/districts/DEMO001

**Request**

```http
GET /api/v1/districts/DEMO001
```

**Response** — Status Code: `404`

```json
{
  "detail": "district 'DEMO001' not found"
}
```
