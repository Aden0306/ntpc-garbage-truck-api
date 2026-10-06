from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..crud import apply, ensure_absent, ensure_no_children, get_or_404, paginate
from ..database import get_db

router = APIRouter(prefix="/districts", tags=["Districts 行政區"])
NAME = "district"


@router.get("", response_model=schemas.DistrictPage, summary="列出行政區")
def list_districts(
    name: str | None = Query(None, description="行政區名稱（模糊比對）"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(models.District).order_by(models.District.city_id)
    if name:
        q = q.filter(models.District.city_name.contains(name))
    return paginate(q, limit, offset)


@router.get("/{city_id}", response_model=schemas.DistrictOut, summary="查詢單一行政區")
def get_district(city_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, models.District, city_id, NAME)


@router.get(
    "/{city_id}/routes", response_model=list[schemas.RouteOut], summary="列出行政區內的清運路線"
)
def list_district_routes(city_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, models.District, city_id, NAME).routes


@router.post(
    "", response_model=schemas.DistrictOut, status_code=status.HTTP_201_CREATED, summary="新增行政區"
)
def create_district(body: schemas.DistrictCreate, db: Session = Depends(get_db)):
    ensure_absent(db, models.District, body.city_id, NAME)
    obj = models.District(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{city_id}", response_model=schemas.DistrictOut, summary="更新行政區（整筆）")
def replace_district(city_id: str, body: schemas.DistrictUpdate, db: Session = Depends(get_db)):
    obj = get_or_404(db, models.District, city_id, NAME)
    apply(obj, body.model_dump())
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{city_id}", response_model=schemas.DistrictOut, summary="更新行政區（部分）")
def patch_district(city_id: str, body: schemas.DistrictPatch, db: Session = Depends(get_db)):
    obj = get_or_404(db, models.District, city_id, NAME)
    apply(obj, body.model_dump(exclude_unset=True, exclude_none=True))
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{city_id}", status_code=status.HTTP_204_NO_CONTENT, summary="刪除行政區")
def delete_district(city_id: str, db: Session = Depends(get_db)):
    obj = get_or_404(db, models.District, city_id, NAME)
    ensure_no_children(obj.routes, NAME, "routes")
    db.delete(obj)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
