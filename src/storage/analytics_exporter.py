import sqlite3
import csv
import json
from pathlib import Path
import logging

LOGGER = logging.getLogger(__name__)

def export_db_to_csv(db_path: Path, output_dir: Path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Export images
        cursor.execute("SELECT * FROM images")
        img_rows = cursor.fetchall()
        
        if img_rows:
            csv_path = output_dir / "images_analytics.csv"
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=img_rows[0].keys())
                writer.writeheader()
                for row in img_rows:
                    writer.writerow(dict(row))
            LOGGER.info("Exported images to %s", csv_path)
            
        # Export videos
        cursor.execute("SELECT * FROM videos")
        vid_rows = cursor.fetchall()
        
        if vid_rows:
            csv_path = output_dir / "videos_analytics.csv"
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=vid_rows[0].keys())
                writer.writeheader()
                for row in vid_rows:
                    writer.writerow(dict(row))
            LOGGER.info("Exported videos to %s", csv_path)

def export_db_to_json(db_path: Path, output_dir: Path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM images")
        images = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM videos")
        videos = [dict(row) for row in cursor.fetchall()]
        
        json_path = output_dir / "analytics.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"images": images, "videos": videos}, f, indent=2)
        LOGGER.info("Exported JSON analytics to %s", json_path)

def export_analytics(subject_dir: Path, fmt: str):
    db_path = subject_dir / "database.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")
        
    if fmt == "csv":
        export_db_to_csv(db_path, subject_dir)
    elif fmt == "json":
        export_db_to_json(db_path, subject_dir)
    else:
        raise ValueError("Unsupported format. Use 'csv' or 'json'.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export database to CSV or JSON.")
    parser.add_argument("--input-dir", required=True, type=str, help="Target subject directory.")
    parser.add_argument("--format", choices=["csv", "json"], required=True, help="Export format.")
    args = parser.parse_args()
    
    try:
        export_analytics(Path(args.input_dir), args.format)
        print("Export successful.")
    except Exception as e:
        print(f"Export failed: {e}")
