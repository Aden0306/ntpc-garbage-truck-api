from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from . import models, opendata
from .database import Base, SessionLocal, engine
from .routers import admin, districts, locations, routes, trucks

API_PREFIX = "/api/v1"

DESCRIPTION = """
新北市**垃圾清運車輛即時位置** Open Data 的 RESTful API。

資料來源：[新北市政府資料開放平台](https://data.ntpc.gov.tw/datasets/28ab4122-60e1-4065-98e5-abccb69aaca6)

原始資料被正規化為 4 種 Resource，各自提供完整 CRUD：

| Resource | 說明 | 主鍵 |
|---|---|---|
| `districts` | 行政區 | `city_id` |
| `routes` | 清運路線 | `line_id` |
| `trucks` | 垃圾車 | `car`（車牌） |
| `locations` | 位置紀錄 | `id` |

關聯：District 1─N Route 1─N Truck 1─N Location
"""


def init_db() -> None:
    """建立資料表；若資料庫是空的且有 JSON 檔，自動匯入。"""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(models.District).count() == 0 and opendata.DATA_FILE.exists():
            opendata.import_records(db, opendata.load_json())


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="新北市垃圾車即時位置 API",
    version="1.0.0",
    description=DESCRIPTION,
    lifespan=lifespan,
)

for r in (districts, routes, trucks, locations, admin):
    app.include_router(r.router, prefix=API_PREFIX)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")
