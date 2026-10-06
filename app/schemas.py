from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- District 行政區 ----------
class DistrictBase(BaseModel):
    city_name: str = Field(..., max_length=32, examples=["板橋區"])


class DistrictCreate(DistrictBase):
    city_id: str = Field(..., max_length=16, examples=["6500100"])


class DistrictUpdate(DistrictBase):
    pass


class DistrictPatch(BaseModel):
    city_name: str | None = Field(None, max_length=32)


class DistrictOut(DistrictCreate, ORMModel):
    pass


# ---------- Route 清運路線 ----------
class RouteBase(BaseModel):
    city_id: str = Field(..., max_length=16, examples=["6500100"])


class RouteCreate(RouteBase):
    line_id: str = Field(..., max_length=16, examples=["210001"])


class RouteUpdate(RouteBase):
    pass


class RoutePatch(BaseModel):
    city_id: str | None = Field(None, max_length=16)


class RouteOut(RouteCreate, ORMModel):
    pass


# ---------- Truck 垃圾車 ----------
class TruckBase(BaseModel):
    line_id: str = Field(..., max_length=16, examples=["210001"])


class TruckCreate(TruckBase):
    car: str = Field(..., max_length=16, examples=["KEA-0001"], description="車牌號碼")


class TruckUpdate(TruckBase):
    pass


class TruckPatch(BaseModel):
    line_id: str | None = Field(None, max_length=16)


class TruckOut(TruckCreate, ORMModel):
    pass


# ---------- Location 位置紀錄 ----------
class LocationBase(BaseModel):
    car: str = Field(..., max_length=16, examples=["KEA-0001"])
    recorded_at: datetime = Field(..., examples=["2026-10-06T20:42:37"])
    address: str = Field(..., max_length=128, examples=["新北市板橋區中山路一段161號"])
    longitude: float = Field(..., ge=-180, le=180, examples=[121.4627])
    latitude: float = Field(..., ge=-90, le=90, examples=[25.0120])


class LocationCreate(LocationBase):
    pass


class LocationUpdate(LocationBase):
    pass


class LocationPatch(BaseModel):
    car: str | None = Field(None, max_length=16)
    recorded_at: datetime | None = None
    address: str | None = Field(None, max_length=128)
    longitude: float | None = Field(None, ge=-180, le=180)
    latitude: float | None = Field(None, ge=-90, le=90)


class LocationOut(LocationBase, ORMModel):
    id: int


class NearbyLocationOut(LocationOut):
    distance_m: float = Field(..., description="與查詢點的距離（公尺）")


# ---------- 共用 ----------
class Page(BaseModel):
    total: int
    limit: int
    offset: int


class DistrictPage(Page):
    items: list[DistrictOut]


class RoutePage(Page):
    items: list[RouteOut]


class TruckPage(Page):
    items: list[TruckOut]


class LocationPage(Page):
    items: list[LocationOut]


class RefreshResult(BaseModel):
    records: int
    districts: int
    routes: int
    trucks: int
    locations: int
