"""新北市垃圾車即時位置 API 的 Python Client。

用法：
    python client/api_client.py                       # 對 http://127.0.0.1:8000 執行示範流程
    python client/api_client.py --base-url https://... # 指定伺服器
    python client/api_client.py --output docs/api_examples.md

示範流程會依序測試每個 Resource 的 CRUD，並把每一次 Request / Response
寫成 Markdown 實測範例。
"""
import argparse
import json
import sys
from pathlib import Path

import requests


class GarbageTruckClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.prefix = "/api/v1"
        self.timeout = timeout
        self.session = requests.Session()
        self.log: list[dict] = []

    def request(self, method: str, path: str, *, json_body=None, params=None) -> requests.Response:
        url = f"{self.base_url}{self.prefix}{path}"
        resp = self.session.request(method, url, json=json_body, params=params, timeout=self.timeout)
        try:
            output = resp.json()
        except ValueError:
            output = resp.text or None
        self.log.append(
            {
                "method": method,
                "path": self.prefix + path,
                "params": params,
                "body": json_body,
                "status": resp.status_code,
                "output": output,
            }
        )
        return resp

    # ---- 通用 CRUD ----
    def list(self, resource: str, **params):
        return self.request("GET", f"/{resource}", params=params or None)

    def get(self, resource: str, key):
        return self.request("GET", f"/{resource}/{key}")

    def create(self, resource: str, data: dict):
        return self.request("POST", f"/{resource}", json_body=data)

    def replace(self, resource: str, key, data: dict):
        return self.request("PUT", f"/{resource}/{key}", json_body=data)

    def patch(self, resource: str, key, data: dict):
        return self.request("PATCH", f"/{resource}/{key}", json_body=data)

    def delete(self, resource: str, key):
        return self.request("DELETE", f"/{resource}/{key}")

    # ---- 特殊查詢 ----
    def district_routes(self, city_id: str):
        return self.request("GET", f"/districts/{city_id}/routes")

    def route_trucks(self, line_id: str):
        return self.request("GET", f"/routes/{line_id}/trucks")

    def truck_locations(self, car: str):
        return self.request("GET", f"/trucks/{car}/locations")

    def truck_latest(self, car: str):
        return self.request("GET", f"/trucks/{car}/latest")

    def nearby(self, lat: float, lon: float, radius_m: float = 1000, limit: int = 5):
        return self.request(
            "GET", "/locations/nearby", params={"lat": lat, "lon": lon, "radius_m": radius_m, "limit": limit}
        )

    def refresh(self):
        return self.request("POST", "/admin/refresh")


def _truncate(output, max_items: int = 3):
    """範例文件中列表只保留前幾筆，避免太長。"""
    if isinstance(output, list) and len(output) > max_items:
        return output[:max_items] + [f"... ({len(output) - max_items} more)"]
    if isinstance(output, dict) and isinstance(output.get("items"), list):
        return {**output, "items": _truncate(output["items"], max_items)}
    return output


def write_markdown(log: list[dict], path: Path, base_url: str) -> None:
    lines = [
        "# API 實測範例",
        "",
        f"由 `client/api_client.py` 對 `{base_url}` 實際執行產生。",
        "",
    ]
    for i, e in enumerate(log, 1):
        query = ""
        if e["params"]:
            query = "?" + "&".join(f"{k}={v}" for k, v in e["params"].items())
        lines += [f"## {i}. {e['method']} {e['path']}{query}", ""]
        lines += ["**Request**", "", "```http", f"{e['method']} {e['path']}{query}", "```", ""]
        if e["body"] is not None:
            lines += ["```json", json.dumps(e["body"], ensure_ascii=False, indent=2), "```", ""]
        lines += [f"**Response** — Status Code: `{e['status']}`", ""]
        if e["output"] is not None:
            lines += ["```json", json.dumps(_truncate(e["output"]), ensure_ascii=False, indent=2), "```", ""]
        else:
            lines += ["_(no content)_", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_demo(client: GarbageTruckClient) -> list[str]:
    """執行完整示範流程；回傳不符合預期的步驟清單。"""
    failures: list[str] = []

    def check(resp: requests.Response, expected: int, label: str):
        mark = "OK " if resp.status_code == expected else "FAIL"
        print(f"[{mark}] {resp.request.method:6} {resp.request.path_url:60} -> {resp.status_code} ({label})")
        if resp.status_code != expected:
            failures.append(f"{label}: expected {expected}, got {resp.status_code}")
        return resp

    # --- 讀取真實資料 ---
    districts = check(client.list("districts", limit=5), 200, "列出行政區").json()["items"]
    if districts:
        cid = districts[0]["city_id"]
        check(client.get("districts", cid), 200, "查詢單一行政區")
        routes = check(client.district_routes(cid), 200, "行政區內路線").json()
        if routes:
            trucks = check(client.route_trucks(routes[0]["line_id"]), 200, "路線上的垃圾車").json()
            if trucks:
                check(client.truck_latest(trucks[0]["car"]), 200, "垃圾車最新位置")
    check(client.list("trucks", limit=3), 200, "列出垃圾車")
    check(client.list("locations", limit=3), 200, "列出位置紀錄")
    check(client.nearby(25.0120, 121.4627, radius_m=3000), 200, "板橋車站附近 3 公里的垃圾車")

    # --- CRUD 示範（使用測試用代碼，最後全部刪除）---
    cid, lid, car = "DEMO001", "DEMO-L1", "DEMO-001"
    check(client.create("districts", {"city_id": cid, "city_name": "示範區"}), 201, "新增行政區")
    check(client.create("districts", {"city_id": cid, "city_name": "示範區"}), 409, "重複新增 → 409")
    check(client.replace("districts", cid, {"city_name": "示範區（改）"}), 200, "PUT 行政區")
    check(client.patch("districts", cid, {"city_name": "示範區2"}), 200, "PATCH 行政區")

    check(client.create("routes", {"line_id": lid, "city_id": cid}), 201, "新增路線")
    check(client.create("routes", {"line_id": "X", "city_id": "NOPE"}), 422, "參照不存在的行政區 → 422")
    check(client.get("routes", lid), 200, "查詢路線")
    check(client.replace("routes", lid, {"city_id": cid}), 200, "PUT 路線")

    check(client.create("trucks", {"car": car, "line_id": lid}), 201, "新增垃圾車")
    check(client.patch("trucks", car, {"line_id": lid}), 200, "PATCH 垃圾車")

    loc = check(
        client.create(
            "locations",
            {
                "car": car,
                "recorded_at": "2026-10-06T20:00:00",
                "address": "新北市板橋區中山路一段161號",
                "longitude": 121.4627,
                "latitude": 25.0120,
            },
        ),
        201,
        "新增位置紀錄",
    ).json()
    loc_id = loc["id"]
    check(client.get("locations", loc_id), 200, "查詢位置紀錄")
    check(
        client.replace(
            "locations",
            loc_id,
            {
                "car": car,
                "recorded_at": "2026-10-06T20:05:00",
                "address": "新北市板橋區縣民大道二段7號",
                "longitude": 121.4635,
                "latitude": 25.0137,
            },
        ),
        200,
        "PUT 位置紀錄",
    )
    check(client.patch("locations", loc_id, {"address": "新北市板橋區（PATCH）"}), 200, "PATCH 位置紀錄")
    check(client.truck_latest(car), 200, "示範車最新位置")
    check(client.delete("trucks", car), 409, "仍有位置紀錄時刪除車輛 → 409")

    # --- 清理 ---
    check(client.delete("locations", loc_id), 204, "刪除位置紀錄")
    check(client.delete("trucks", car), 204, "刪除垃圾車")
    check(client.delete("routes", lid), 204, "刪除路線")
    check(client.delete("districts", cid), 204, "刪除行政區")
    check(client.get("districts", cid), 404, "刪除後查詢 → 404")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parent.parent / "docs" / "api_examples.md"))
    args = parser.parse_args()

    client = GarbageTruckClient(args.base_url)
    failures = run_demo(client)
    write_markdown(client.log, Path(args.output), args.base_url)
    print(f"\n{len(client.log)} requests, {len(failures)} failures. Examples written to {args.output}")
    for f in failures:
        print("  -", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
