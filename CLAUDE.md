# CLAUDE.md

本檔是給 AI 輔助開發工具（Claude Code）的專案說明，開發時會自動載入作為上下文。

## 專案概要
新北市垃圾車即時位置 Open Data → SQLite → FastAPI RESTful API（CRUD）+ Swagger UI + Python Client。

## 常用指令
- 安裝：`python -m venv .venv` 後 `.venv\Scripts\pip install -r requirements.txt`
- 下載資料：`python fetch_data.py`
- 匯入 DB：`python import_db.py`
- 啟動：`uvicorn app.main:app --reload`（Swagger UI：http://127.0.0.1:8000/docs）
- 測試：`python -m pytest -q`
- Client 實測：`python client/api_client.py`（會重新產生 docs/api_examples.md）
- 匯出規格：`python scripts/export_openapi.py`（更新 docs/openapi.json）

## 架構約定
- 資料正規化為 4 個 Resource：District 1─N Route 1─N Truck 1─N Location。
- 所有 API 掛在 `/api/v1`，每個 router 位於 `app/routers/<resource>.py`。
- 共用錯誤處理在 `app/crud.py`：404 找不到、409 重複或仍有子資料、422 外鍵不存在或驗證失敗。
- Pydantic schema 每個 Resource 都有 Create / Update(PUT) / Patch / Out 四種。
- 下載與匯入邏輯集中在 `app/opendata.py`，CLI 與 `/admin/refresh` 共用。
- 修改 API 後要重新執行 `scripts/export_openapi.py` 與 client 示範，讓文件保持同步。
- 測試使用記憶體 SQLite，不要讓測試寫入 `data/garbage_trucks.db`。
