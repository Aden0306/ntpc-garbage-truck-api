from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..crud import apply, ensure_absent, ensure_no_children, ensure_ref, get_or_404, paginate
from ..database import get_db

router = APIRouter(prefix="/routes", tags=["Routes 清運路線"])
NAME = "route"


@router.get("", response_model=schemas.RoutePage, summary="列出清運路線")
def list_routes(
    city_id: str | None = Query(None, description="依行政區代碼篩選"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(models.Route).order_by(models.Route.line_id)
    if city_id:
        q = q.filter(models.Route.city_id == city_id)
    return paginate(q, limit, offset)


@router.get("/{line_id}", response_model=schemas.RouteOut, summary="查詢單一路線")
def get_route(line_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, models.Route, line_id, NAME)


@router.get("/{line_id}/trucks", response_model=list[schemas.TruckOut], summary="列出路線上的垃圾車")
def list_route_trucks(line_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, models.Route, line_id, NAME).trucks


@router.post(
    "", response_model=schemas.RouteOut, status_code=status.HTTP_201_CREATED, summary="新增路線"
)
def create_route(body: schemas.RouteCreate, db: Session = Depends(get_db)):
    ensure_absent(db, models.Route, body.line_id, NAME)
    ensure_ref(db, models.District, body.city_id, "district")
    obj = models.Route(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{line_id}", response_model=schemas.RouteOut, summary="更新路線（整筆）")
def replace_route(line_id: str, body: schemas.RouteUpdate, db: Session = Depends(get_db)):
    obj = get_or_404(db, models.Route, line_id, NAME)
    ensure_ref(db, models.District, body.city_id, "district")
    apply(obj, body.model_dump())
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{line_id}", response_model=schemas.RouteOut, summary="更新路線（部分）")
def patch_route(line_id: str, body: schemas.RoutePatch, db: Session = Depends(get_db)):
    obj = get_or_404(db, models.Route, line_id, NAME)
    data = body.model_dump(exclude_unset=True, exclude_none=True)
    if "city_id" in data:
        ensure_ref(db, models.District, data["city_id"], "district")
    apply(obj, data)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{line_id}", status_code=status.HTTP_204_NO_CONTENT, summary="刪除路線")
def delete_route(line_id: str, db: Session = Depends(get_db)):
    obj = get_or_404(db, models.Route, line_id, NAME)
    ensure_no_children(obj.trucks, NAME, "trucks")
    db.delete(obj)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
