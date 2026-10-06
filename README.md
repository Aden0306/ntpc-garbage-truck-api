# 新北市垃圾車即時位置 RESTful API

抓取新北市政府「垃圾車即時位置」Open Data，匯入 SQLite，並以 **Python + FastAPI** 提供完整 CRUD 的 RESTful API，附 Swagger UI 線上文件與 Python API Client。

- 資料來源：[新北市政府資料開放平台 — 垃圾車即時位置](https://data.ntpc.gov.tw/datasets/28ab4122-60e1-4065-98e5-abccb69aaca6)
- 線上 API 文件（Swagger UI，GitHub Pages）：https://aden0306.github.io/ntpc-garbage-truck-api/
- 本機 Swagger UI：啟動後開 http://127.0.0.1:8000/docs（ReDoc：`/redoc`）
- API 實測範例：[docs/api_examples.md](docs/api_examples.md)

## 專案結構

```
├─ data/
│  ├─ garbage_trucks.json   # Open Data 原始資料（單一 JSON 檔）
│  └─ garbage_trucks.db     # 匯入後的 SQLite 資料庫
├─ fetch_data.py            # 下載 Open Data → data/garbage_trucks.json
├─ import_db.py             # JSON → SQLite
├─ app/                     # FastAPI API Server
│  ├─ main.py               # 進入點、Swagger 設定
│  ├─ database.py           # SQLAlchemy / SQLite 連線
│  ├─ models.py             # ORM 資料表
│  ├─ schemas.py            # Pydantic 請求／回應格式
│  ├─ crud.py               # 共用錯誤處理與分頁
│  ├─ opendata.py           # Open Data 下載與匯入邏輯
│  └─ routers/              # districts / routes / trucks / locations / admin
├─ client/api_client.py     # Python API Client（含完整 CRUD 示範流程）
├─ tests/test_api.py        # pytest 自動化測試
├─ scripts/export_openapi.py
├─ docs/
│  ├─ openapi.json          # API 規格（OpenAPI 3）
│  ├─ index.html            # 靜態 Swagger UI（GitHub Pages）
│  └─ api_examples.md       # 實測範例（Request / Response）
├─ CLAUDE.md                # AI 輔助開發（Claude Code）專案設定檔
└─ requirements.txt
```

## 環境建置

需求：Python 3.10 以上（開發時使用 3.11）

```bash
git clone https://github.com/Aden0306/ntpc-garbage-truck-api.git
cd ntpc-garbage-truck-api
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
```

## 執行方式

```bash
# 1.（可選）重新下載最新 Open Data；repo 中已附一份
python fetch_data.py

# 2.（可選）匯入 SQLite；repo 中已附一份 .db，啟動時若 DB 是空的也會自動匯入
python import_db.py

# 3. 啟動 API Server
uvicorn app.main:app --reload
#   → Swagger UI: http://127.0.0.1:8000/docs

# 4. 另開終端機，執行 API Client 實測（會產生 docs/api_examples.md）
python client/api_client.py
#   指定其他伺服器：python client/api_client.py --base-url http://host:port

# 5. 自動化測試
python -m pytest -q

# 6. 重新匯出 OpenAPI 規格
python scripts/export_openapi.py
```

## 資料模型

原始資料欄位：`lineid, car, time, location, longitude, latitude, cityid, cityname`，正規化為 4 個 Resource：

```
District (行政區) 1─N Route (清運路線) 1─N Truck (垃圾車) 1─N Location (位置紀錄)
```

| Resource | 主鍵 | 欄位 |
|---|---|---|
| districts | `city_id` | `city_name` |
| routes | `line_id` | `city_id` → districts |
| trucks | `car`（車牌） | `line_id` → routes |
| locations | `id`（自動編號） | `car` → trucks, `recorded_at`, `address`, `longitude`, `latitude` |

## API 一覽（前綴 `/api/v1`）

| Method | Path | 說明 |
|---|---|---|
| GET | `/districts?name=&limit=&offset=` | 列出行政區 |
| GET | `/districts/{city_id}` | 查詢行政區 |
| GET | `/districts/{city_id}/routes` | 行政區內的路線 |
| POST | `/districts` | 新增行政區 |
| PUT | `/districts/{city_id}` | 更新行政區（整筆） |
| PATCH | `/districts/{city_id}` | 更新行政區（部分） |
| DELETE | `/districts/{city_id}` | 刪除行政區 |
| GET | `/routes?city_id=&limit=&offset=` | 列出路線 |
| GET | `/routes/{line_id}` | 查詢路線 |
| GET | `/routes/{line_id}/trucks` | 路線上的垃圾車 |
| POST / PUT / PATCH / DELETE | `/routes`、`/routes/{line_id}` | 路線 CRUD |
| GET | `/trucks?line_id=&city_id=&limit=&offset=` | 列出垃圾車 |
| GET | `/trucks/{car}` | 查詢垃圾車 |
| GET | `/trucks/{car}/locations` | 垃圾車的所有位置紀錄 |
| GET | `/trucks/{car}/latest` | 垃圾車最新位置 |
| POST / PUT / PATCH / DELETE | `/trucks`、`/trucks/{car}` | 垃圾車 CRUD |
| GET | `/locations?car=&city_id=&since=&until=&limit=&offset=` | 列出位置紀錄 |
| GET | `/locations/nearby?lat=&lon=&radius_m=&limit=` | 查詢附近的垃圾車（依距離排序） |
| GET | `/locations/{id}` | 查詢位置紀錄 |
| POST / PUT / PATCH / DELETE | `/locations`、`/locations/{id}` | 位置紀錄 CRUD |
| POST | `/admin/refresh` | 重新抓取 Open Data 並匯入 |

### 狀態碼

| Code | 意義 |
|---|---|
| 200 | 成功 |
| 201 | 新增成功 |
| 204 | 刪除成功（無內容） |
| 404 | 資料不存在 |
| 409 | 主鍵重複，或仍有子資料無法刪除 |
| 422 | 欄位驗證失敗，或參照的上層資料不存在 |
| 502 | `/admin/refresh` 無法連線到 Open Data 來源 |

### 範例

```http
POST /api/v1/districts
Content-Type: application/json

{"city_id": "DEMO001", "city_name": "示範區"}
```

```
201 Created
{"city_name": "示範區", "city_id": "DEMO001"}
```

更多完整範例請見 [docs/api_examples.md](docs/api_examples.md)。

## AI 輔助開發

本專案使用 **Claude Code** 協助設計與開發，專案設定檔為 [CLAUDE.md](CLAUDE.md)，其中記錄了常用指令與架構約定，供 AI 工具在開發時載入。
