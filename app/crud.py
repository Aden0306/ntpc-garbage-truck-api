"""各 router 共用的小工具。"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Query, Session


def get_or_404(db: Session, model, key, name: str):
    obj = db.get(model, key)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} '{key}' not found")
    return obj


def ensure_absent(db: Session, model, key, name: str) -> None:
    if db.get(model, key) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{name} '{key}' already exists")


def ensure_ref(db: Session, model, key, name: str) -> None:
    """檢查外鍵所參照的資料是否存在。"""
    if db.get(model, key) is None:
        raise HTTPException(
            422, f"referenced {name} '{key}' does not exist"
        )


def ensure_no_children(children: list, name: str, child_name: str) -> None:
    if children:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{name} still has {len(children)} {child_name}; delete them first",
        )


def apply(obj, data: dict) -> None:
    for field, value in data.items():
        setattr(obj, field, value)


def paginate(query: Query, limit: int, offset: int) -> dict:
    return {
        "total": query.count(),
        "limit": limit,
        "offset": offset,
        "items": query.limit(limit).offset(offset).all(),
    }
