from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..crud import apply, ensure_absent, ensure_no_children, ensure_ref, get_or_404, paginate
from ..database import get_db

router = APIRouter(prefix="/trucks", tags=["Trucks 垃圾車"])
NAME = "truck"


@router.get("", response_model=schemas.TruckPage, summary="列出垃圾車")
def list_trucks(
    line_id: str | None = Query(None, description="依路線編號篩選"),
    city_id: str | None = Query(None, description="依行政區代碼篩選"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(models.Truck).order_by(models.Truck.car)
    if line_id:
        q = q.filter(models.Truck.line_id == line_id)
    if city_id:
        q = q.join(models.Route).filter(models.Route.city_id == city_id)
    return paginate(q, limit, offset)


@router.get("/{car}", response_model=schemas.TruckOut, summary="查詢單一垃圾車")
def get_truck(car: str, db: Session = Depends(get_db)):
    return get_or_404(db, models.Truck, car, NAME)


@router.get(
    "/{car}/locations", response_model=list[schemas.LocationOut], summary="列出垃圾車的位置紀錄"
)
def list_truck_locations(car: str, db: Session = Depends(get_db)):
    get_or_404(db, models.Truck, car, NAME)
    return (
        db.query(models.Location)
        .filter(models.Location.car == car)
        .order_by(models.Location.recorded_at.desc())
        .all()
    )


@router.get("/{car}/latest", response_model=schemas.LocationOut, summary="垃圾車最新位置")
def get_truck_latest(car: str, db: Session = Depends(get_db)):
    get_or_404(db, models.Truck, car, NAME)
    loc = (
        db.query(models.Location)
        .filter(models.Location.car == car)
        .order_by(models.Location.recorded_at.desc())
        .first()
    )
    if loc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"truck '{car}' has no locations")
    return loc


@router.post(
    "", response_model=schemas.TruckOut, status_code=status.HTTP_201_CREATED, summary="新增垃圾車"
)
def create_truck(body: schemas.TruckCreate, db: Session = Depends(get_db)):
    ensure_absent(db, models.Truck, body.car, NAME)
    ensure_ref(db, models.Route, body.line_id, "route")
    obj = models.Truck(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{car}", response_model=schemas.TruckOut, summary="更新垃圾車（整筆）")
def replace_truck(car: str, body: schemas.TruckUpdate, db: Session = Depends(get_db)):
    obj = get_or_404(db, models.Truck, car, NAME)
    ensure_ref(db, models.Route, body.line_id, "route")
    apply(obj, body.model_dump())
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{car}", response_model=schemas.TruckOut, summary="更新垃圾車（部分）")
def patch_truck(car: str, body: schemas.TruckPatch, db: Session = Depends(get_db)):
    obj = get_or_404(db, models.Truck, car, NAME)
    data = body.model_dump(exclude_unset=True, exclude_none=True)
    if "line_id" in data:
        ensure_ref(db, models.Route, data["line_id"], "route")
    apply(obj, data)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{car}", status_code=status.HTTP_204_NO_CONTENT, summary="刪除垃圾車")
def delete_truck(car: str, db: Session = Depends(get_db)):
    obj = get_or_404(db, models.Truck, car, NAME)
    ensure_no_children(obj.locations, NAME, "locations")
    db.delete(obj)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
