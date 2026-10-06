"""新北市垃圾車即時位置 Open Data：下載與匯入 SQLite 的共用邏輯。"""
import json
import time
from datetime import datetime
from pathlib import Path

import requests
from sqlalchemy.orm import Session

from . import models

DATASET_URL = (
    "https://data.ntpc.gov.tw/api/datasets/"
    "28AB4122-60E1-4065-98E5-ABCCB69AACA6/json"
)
PAGE_SIZE = 1000
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "garbage_trucks.json"


def fetch_all(retries: int = 3, timeout: int = 30) -> list[dict]:
    """逐頁抓取全部資料，直到回傳空頁為止。"""
    records: list[dict] = []
    page = 0
    while True:
        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(
                    DATASET_URL,
                    params={"page": page, "size": PAGE_SIZE},
                    timeout=timeout,
                )
                resp.raise_for_status()
                rows = resp.json()
                break
            except (requests.RequestException, ValueError):
                if attempt == retries:
                    raise
                time.sleep(2 * attempt)
        if not rows:
            return records
        records.extend(rows)
        if len(rows) < PAGE_SIZE:
            return records
        page += 1


def save_json(records: list[dict], path: Path = DATA_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path = DATA_FILE) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y/%m/%d %H:%M:%S")


def import_records(db: Session, records: list[dict]) -> dict:
    """把原始資料正規化寫入 4 張表。位置紀錄會先清空再重建，可重複執行。"""
    db.query(models.Location).delete()

    districts = {d.city_id: d for d in db.query(models.District)}
    routes = {r.line_id: r for r in db.query(models.Route)}
    trucks = {t.car: t for t in db.query(models.Truck)}

    for row in records:
        city_id, line_id, car = row["cityid"], row["lineid"], row["car"]

        if city_id not in districts:
            districts[city_id] = models.District(city_id=city_id, city_name=row["cityname"])
            db.add(districts[city_id])
        else:
            districts[city_id].city_name = row["cityname"]

        if line_id not in routes:
            routes[line_id] = models.Route(line_id=line_id, city_id=city_id)
            db.add(routes[line_id])
        else:
            routes[line_id].city_id = city_id

        if car not in trucks:
            trucks[car] = models.Truck(car=car, line_id=line_id)
            db.add(trucks[car])
        else:
            trucks[car].line_id = line_id

        db.add(
            models.Location(
                car=car,
                recorded_at=_parse_time(row["time"]),
                address=row["location"],
                longitude=float(row["longitude"]),
                latitude=float(row["latitude"]),
            )
        )

    db.commit()
    return {
        "records": len(records),
        "districts": db.query(models.District).count(),
        "routes": db.query(models.Route).count(),
        "trucks": db.query(models.Truck).count(),
        "locations": db.query(models.Location).count(),
    }
