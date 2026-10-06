"""把 data/garbage_trucks.json 匯入 SQLite（data/garbage_trucks.db）。"""
from app import opendata
from app.database import Base, SessionLocal, engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        stats = opendata.import_records(db, opendata.load_json())
    for table, count in stats.items():
        print(f"{table:>10}: {count}")


if __name__ == "__main__":
    main()
