import math
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..crud import apply, ensure_ref, get_or_404, paginate
from ..database import get_db

router = APIRouter(prefix="/locations", tags=["Locations 位置紀錄"])
NAME = "location"
EARTH_RADIUS_M = 6_371_000


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


@router.get("", response_model=schemas.LocationPage, summary="列出位置紀錄")
def list_locations(
    car: str | None = Query(None, description="依車牌篩選"),
    city_id: str | None = Query(None, description="依行政區代碼篩選"),
    since: datetime | None = Query(None, description="起始時間（含）"),
    until: datetime | None = Query(None, description="結束時間（含）"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(models.Location).order_by(models.Location.id)
    if car:
        q = q.filter(models.Location.car == car)
    if city_id:
        q = q.join(models.Truck).join(models.Route).filter(models.Route.city_id == city_id)
    if since:
        q = q.filter(models.Location.recorded_at >= since)
    if until:
        q = q.filter(models.Location.recorded_at <= until)
    return paginate(q, limit, offset)


@router.get(
    "/nearby",
    response_model=list[schemas.NearbyLocationOut],
    summary="查詢附近的垃圾車",
    description="回傳距離指定座標 `radius_m` 公尺內的位置紀錄，由近到遠排序。",
)
def nearby_locations(
    lat: float = Query(..., ge=-90, le=90, examples=[25.0120]),
    lon: float = Query(..., ge=-180, le=180, examples=[121.4627]),
    radius_m: float = Query(1000, gt=0, le=50_000),
    limit: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
):
    # 先用經緯度方框粗篩，再以 Haversine 精算距離
    dlat = radius_m / 111_320
    dlon = radius_m / (111_320 * max(math.cos(math.radians(lat)), 1e-6))
    candidates = (
        db.query(models.Location)
        .filter(models.Location.latitude.between(lat - dlat, lat + dlat))
        .filter(models.Location.longitude.between(lon - dlon, lon + dlon))
        .all()
    )
    results = []
    for loc in candidates:
        d = haversine_m(lat, lon, loc.latitude, loc.longitude)
        if d <= radius_m:
            item = schemas.LocationOut.model_validate(loc).model_dump()
            results.append({**item, "distance_m": round(d, 1)})
    results.sort(key=lambda r: r["distance_m"])
    return results[:limit]


@router.get("/{location_id}", response_model=schemas.LocationOut, summary="查詢單筆位置紀錄")
def get_location(location_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, models.Location, location_id, NAME)


@router.post(
    "",
    response_model=schemas.LocationOut,
    status_code=status.HTTP_201_CREATED,
    summary="新增位置紀錄",
)
def create_location(body: schemas.LocationCreate, db: Session = Depends(get_db)):
    ensure_ref(db, models.Truck, body.car, "truck")
    obj = models.Location(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{location_id}", response_model=schemas.LocationOut, summary="更新位置紀錄（整筆）")
def replace_location(
    location_id: int, body: schemas.LocationUpdate, db: Session = Depends(get_db)
):
    obj = get_or_404(db, models.Location, location_id, NAME)
    ensure_ref(db, models.Truck, body.car, "truck")
    apply(obj, body.model_dump())
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{location_id}", response_model=schemas.LocationOut, summary="更新位置紀錄（部分）")
def patch_location(location_id: int, body: schemas.LocationPatch, db: Session = Depends(get_db)):
    obj = get_or_404(db, models.Location, location_id, NAME)
    data = body.model_dump(exclude_unset=True, exclude_none=True)
    if "car" in data:
        ensure_ref(db, models.Truck, data["car"], "truck")
    apply(obj, data)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT, summary="刪除位置紀錄")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    obj = get_or_404(db, models.Location, location_id, NAME)
    db.delete(obj)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
