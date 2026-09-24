import os
import sqlite3
import csv
import json
from pathlib import Path
import logging

from contextlib import contextmanager
from common.security import validate_safe_path

LOGGER = logging.getLogger(__name__)

@contextmanager
def _open_db(db_path: Path):
    """Context manager ensuring SQLite connection is strictly closed upon exit."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def _get_table_rows(cursor: sqlite3.Cursor, table_name: str) -> list[dict]:
    cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        return []
    cursor.execute(f"SELECT * FROM {table_name}")
    return [dict(row) for row in cursor.fetchall()]


def export_db_to_csv(db_path: Path, output_dir: Path):
    safe_out = Path(os.path.abspath(os.path.normpath(str(output_dir)))).resolve()
    with _open_db(db_path) as conn:
        cursor = conn.cursor()

        img_rows = _get_table_rows(cursor, "images")
        if img_rows:
            csv_path = validate_safe_path(safe_out, safe_out / "images_analytics.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(img_rows[0].keys()))
                writer.writeheader()
                for row in img_rows:
                    writer.writerow(row)
            LOGGER.info("Exported images to %s", csv_path)

        vid_rows = _get_table_rows(cursor, "videos")
        if vid_rows:
            csv_path = validate_safe_path(safe_out, safe_out / "videos_analytics.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(vid_rows[0].keys()))
                writer.writeheader()
                for row in vid_rows:
                    writer.writerow(row)
            LOGGER.info("Exported videos to %s", csv_path)


def export_db_to_json(db_path: Path, output_dir: Path):
    safe_out = Path(os.path.abspath(os.path.normpath(str(output_dir)))).resolve()
    with _open_db(db_path) as conn:
        cursor = conn.cursor()

        images = _get_table_rows(cursor, "images")
        videos = _get_table_rows(cursor, "videos")

        json_path = validate_safe_path(safe_out, safe_out / "analytics.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"images": images, "videos": videos}, f, indent=2)
        LOGGER.info("Exported JSON analytics to %s", json_path)


def export_db_to_parquet(db_path: Path, output_dir: Path):
    safe_out = Path(os.path.abspath(os.path.normpath(str(output_dir)))).resolve()
    with _open_db(db_path) as conn:
        cursor = conn.cursor()

        img_rows = _get_table_rows(cursor, "images")
        vid_rows = _get_table_rows(cursor, "videos")

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        if img_rows:
            img_table = pa.Table.from_pylist(img_rows)
            pq_img_path = validate_safe_path(safe_out, safe_out / "images.parquet")
            pq.write_table(img_table, str(pq_img_path), compression="snappy")
            LOGGER.info("Exported images to %s", pq_img_path)

        if vid_rows:
            vid_table = pa.Table.from_pylist(vid_rows)
            pq_vid_path = validate_safe_path(safe_out, safe_out / "videos.parquet")
            pq.write_table(vid_table, str(pq_vid_path), compression="snappy")
            LOGGER.info("Exported videos to %s", pq_vid_path)
    except ImportError:
        LOGGER.warning("pyarrow not installed; falling back to JSON export.")
        export_db_to_json(db_path, safe_out)



def export_analytics(subject_dir: Path, fmt: str):
    import tempfile
    resolved_subject = Path(subject_dir).resolve()

    allowed_roots = [Path(".").resolve(), Path(tempfile.gettempdir()).resolve()]
    try:
        import config
        if hasattr(config, "OUTPUT_DIR"):
            allowed_roots.append(Path(config.OUTPUT_DIR).resolve())
    except Exception:
        pass

    safe_dir: Path | None = None
    for root in allowed_roots:
        try:
            safe_dir = validate_safe_path(root, resolved_subject)
            break
        except (ValueError, Exception):
            continue

    if safe_dir is None:
        raise ValueError(f"Target directory escapes allowed workspace boundaries: {subject_dir}")

    db_path = validate_safe_path(safe_dir, safe_dir / "database.db")
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")

    fmt_lower = fmt.lower().strip()
    if fmt_lower == "csv":
        export_db_to_csv(db_path, safe_dir)
    elif fmt_lower == "json":
        export_db_to_json(db_path, safe_dir)
    elif fmt_lower == "parquet":
        export_db_to_parquet(db_path, safe_dir)
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

