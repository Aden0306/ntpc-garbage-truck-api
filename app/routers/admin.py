import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import opendata, schemas
from ..database import get_db

router = APIRouter(prefix="/admin", tags=["Admin 資料維護"])


@router.post(
    "/refresh",
    response_model=schemas.RefreshResult,
    summary="重新抓取 Open Data 並匯入",
    description="從新北市資料開放平台下載最新垃圾車位置，覆寫 data/garbage_trucks.json，並重建位置紀錄。",
)
def refresh(db: Session = Depends(get_db)):
    try:
        records = opendata.fetch_all()
    except requests.RequestException as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"failed to fetch open data: {exc}")
    opendata.save_json(records)
    return opendata.import_records(db, records)
