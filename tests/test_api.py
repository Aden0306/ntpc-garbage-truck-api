"""API 自動化測試：使用暫存 SQLite，不會動到 data/garbage_trucks.db。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import opendata
from app.database import Base, get_db
from app.main import app

SAMPLE = [
    {"lineid": "234064", "car": "KEJ-6635", "time": "2026/10/06 20:42:37",
     "location": "新北市新店區安康路二段320巷6號", "longitude": "121.505106666667",
     "latitude": "24.9599933333333", "cityid": "6500400", "cityname": "永和區"},
    {"lineid": "234026", "car": "BWM-8152", "time": "2026/10/06 20:42:51",
     "location": "新北市永和區福和路1號", "longitude": "121.526028333333",
     "latitude": "25.0096516666667", "cityid": "6500400", "cityname": "永和區"},
    {"lineid": "249004", "car": "303-UY", "time": "2026/10/06 20:42:36",
     "location": "新北市八里區中山路一段219號", "longitude": "121.411363333333",
     "latitude": "25.1577833333333", "cityid": "6502300", "cityname": "八里區"},
]
P = "/api/v1"


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    event.listen(engine, "connect", lambda c, _: c.execute("PRAGMA foreign_keys=ON"))
    Session = sessionmaker(bind=engine, autoflush=False)
    Base.metadata.create_all(engine)
    with Session() as db:
        opendata.import_records(db, SAMPLE)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    # 不使用 with 區塊，避免 lifespan 去碰正式資料庫
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_import_normalizes(client):
    assert client.get(f"{P}/districts").json()["total"] == 2
    assert client.get(f"{P}/routes").json()["total"] == 3
    assert client.get(f"{P}/trucks").json()["total"] == 3
    assert client.get(f"{P}/locations").json()["total"] == 3


def test_district_crud(client):
    r = client.post(f"{P}/districts", json={"city_id": "T1", "city_name": "測試區"})
    assert r.status_code == 201
    assert client.post(f"{P}/districts", json={"city_id": "T1", "city_name": "x"}).status_code == 409
    assert client.get(f"{P}/districts/T1").json()["city_name"] == "測試區"
    assert client.put(f"{P}/districts/T1", json={"city_name": "A"}).json()["city_name"] == "A"
    assert client.patch(f"{P}/districts/T1", json={"city_name": "B"}).json()["city_name"] == "B"
    assert client.delete(f"{P}/districts/T1").status_code == 204
    assert client.get(f"{P}/districts/T1").status_code == 404


def test_district_delete_with_children_conflicts(client):
    assert client.delete(f"{P}/districts/6500400").status_code == 409


def test_route_crud_and_fk(client):
    assert client.post(f"{P}/routes", json={"line_id": "R1", "city_id": "NOPE"}).status_code == 422
    assert client.post(f"{P}/routes", json={"line_id": "R1", "city_id": "6502300"}).status_code == 201
    assert client.put(f"{P}/routes/R1", json={"city_id": "6500400"}).json()["city_id"] == "6500400"
    assert client.patch(f"{P}/routes/R1", json={"city_id": "NOPE"}).status_code == 422
    assert len(client.get(f"{P}/districts/6500400/routes").json()) == 3
    assert client.delete(f"{P}/routes/R1").status_code == 204


def test_truck_crud(client):
    assert client.post(f"{P}/trucks", json={"car": "T-1", "line_id": "249004"}).status_code == 201
    assert client.patch(f"{P}/trucks/T-1", json={"line_id": "234026"}).json()["line_id"] == "234026"
    assert len(client.get(f"{P}/trucks", params={"city_id": "6500400"}).json()["items"]) == 3
    assert client.get(f"{P}/trucks/T-1/latest").status_code == 404
    assert client.delete(f"{P}/trucks/T-1").status_code == 204


def test_location_crud_and_latest(client):
    body = {"car": "303-UY", "recorded_at": "2026-10-06T21:00:00", "address": "八里",
            "longitude": 121.41, "latitude": 25.15}
    r = client.post(f"{P}/locations", json=body)
    assert r.status_code == 201
    loc_id = r.json()["id"]
    assert client.get(f"{P}/trucks/303-UY/latest").json()["id"] == loc_id
    assert client.put(f"{P}/locations/{loc_id}", json={**body, "address": "X"}).json()["address"] == "X"
    assert client.patch(f"{P}/locations/{loc_id}", json={"latitude": 25.16}).json()["latitude"] == 25.16
    assert client.patch(f"{P}/locations/{loc_id}", json={"latitude": 999}).status_code == 422
    assert client.delete(f"{P}/trucks/303-UY").status_code == 409
    assert client.delete(f"{P}/locations/{loc_id}").status_code == 204
    assert client.get(f"{P}/locations/{loc_id}").status_code == 404


def test_location_filters(client):
    assert client.get(f"{P}/locations", params={"city_id": "6502300"}).json()["total"] == 1
    assert client.get(f"{P}/locations", params={"car": "KEJ-6635"}).json()["total"] == 1
    r = client.get(f"{P}/locations", params={"since": "2026-10-06T20:42:40"})
    assert r.json()["total"] == 1


def test_nearby(client):
    r = client.get(f"{P}/locations/nearby", params={"lat": 25.0096, "lon": 121.5260, "radius_m": 500})
    assert r.status_code == 200
    data = r.json()
    assert [d["car"] for d in data] == ["BWM-8152"]
    assert data[0]["distance_m"] < 100
