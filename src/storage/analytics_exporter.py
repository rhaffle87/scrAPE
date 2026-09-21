import sqlite3
import csv
import json
from pathlib import Path
import logging

LOGGER = logging.getLogger(__name__)

def _get_table_rows(cursor: sqlite3.Cursor, table_name: str) -> list[dict]:
    cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        return []
    cursor.execute(f"SELECT * FROM {table_name}")
    return [dict(row) for row in cursor.fetchall()]


def export_db_to_csv(db_path: Path, output_dir: Path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        img_rows = _get_table_rows(cursor, "images")
        if img_rows:
            csv_path = output_dir / "images_analytics.csv"
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(img_rows[0].keys()))
                writer.writeheader()
                for row in img_rows:
                    writer.writerow(row)
            LOGGER.info("Exported images to %s", csv_path)

        vid_rows = _get_table_rows(cursor, "videos")
        if vid_rows:
            csv_path = output_dir / "videos_analytics.csv"
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(vid_rows[0].keys()))
                writer.writeheader()
                for row in vid_rows:
                    writer.writerow(row)
            LOGGER.info("Exported videos to %s", csv_path)


def export_db_to_json(db_path: Path, output_dir: Path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        images = _get_table_rows(cursor, "images")
        videos = _get_table_rows(cursor, "videos")

        json_path = output_dir / "analytics.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"images": images, "videos": videos}, f, indent=2)
        LOGGER.info("Exported JSON analytics to %s", json_path)


def export_db_to_parquet(db_path: Path, output_dir: Path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        img_rows = _get_table_rows(cursor, "images")
        vid_rows = _get_table_rows(cursor, "videos")

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        if img_rows:
            img_table = pa.Table.from_pylist(img_rows)
            pq_img_path = output_dir / "images.parquet"
            pq.write_table(img_table, pq_img_path, compression="snappy")
            LOGGER.info("Exported images to %s", pq_img_path)

        if vid_rows:
            vid_table = pa.Table.from_pylist(vid_rows)
            pq_vid_path = output_dir / "videos.parquet"
            pq.write_table(vid_table, pq_vid_path, compression="snappy")
            LOGGER.info("Exported videos to %s", pq_vid_path)
    except ImportError:
        LOGGER.warning("pyarrow not installed; falling back to JSON export.")
        export_db_to_json(db_path, output_dir)



def export_analytics(subject_dir: Path, fmt: str):
    db_path = subject_dir / "database.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")

    fmt_lower = fmt.lower().strip()
    if fmt_lower == "csv":
        export_db_to_csv(db_path, subject_dir)
    elif fmt_lower == "json":
        export_db_to_json(db_path, subject_dir)
    elif fmt_lower == "parquet":
        export_db_to_parquet(db_path, subject_dir)
    else:
        raise ValueError("Unsupported format. Use 'csv', 'json', or 'parquet'.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export database to CSV, JSON, or Parquet.")
    parser.add_argument("--input-dir", required=True, type=str, help="Target subject directory.")
    parser.add_argument("--format", choices=["csv", "json", "parquet"], required=True, help="Export format.")
    args = parser.parse_args()

    try:
        export_analytics(Path(args.input_dir), args.format)
        print("Export successful.")
    except Exception as e:
        print(f"Export failed: {e}")

