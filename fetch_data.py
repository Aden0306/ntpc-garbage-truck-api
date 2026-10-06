"""下載新北市垃圾車即時位置 Open Data，存成 data/garbage_trucks.json。"""
from app import opendata


def main() -> None:
    print(f"Fetching {opendata.DATASET_URL} ...")
    records = opendata.fetch_all()
    opendata.save_json(records)
    print(f"Saved {len(records)} records to {opendata.DATA_FILE}")


if __name__ == "__main__":
    main()
