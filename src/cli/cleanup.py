import argparse
import sys
import shutil
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT_DIR / "output"

def get_dir_size(path: Path) -> int:
    """Calculate total size of a directory recursively."""
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())

def format_size(size: int) -> str:
    """Format bytes into a human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def main():
    parser = argparse.ArgumentParser(
        description="Clean up old scrape runs to enforce Data Retention Policies (GDPR Compliance)"
    )
    parser.add_argument(
        "--days", 
        type=int, 
        required=True, 
        help="Delete all runs older than this many days"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Print what would be deleted without actually deleting anything"
    )
    
    args = parser.parse_args()
    
    if args.days < 0:
        print("Error: --days must be greater than or equal to 0", file=sys.stderr)
        sys.exit(1)
        
    now = time.time()
    cutoff_time = now - (args.days * 86400)
    
    deleted_runs = 0
    reclaimed_bytes = 0
    
    if not OUTPUT_DIR.exists():
        print(f"Output directory {OUTPUT_DIR} does not exist.")
        sys.exit(0)
    
    print(f"Scanning for runs older than {args.days} days...")
    
    for domain_dir in OUTPUT_DIR.glob("*"):
        if not domain_dir.is_dir():
            continue
            
        runs_dir = domain_dir / "runs"
        if not runs_dir.exists():
            continue
            
        for run_dir in runs_dir.glob("*"):
            if not run_dir.is_dir():
                continue
                
            # Check modification time of results.json if it exists, otherwise the dir itself
            mtime = run_dir.stat().st_mtime
            results_file = run_dir / "results.json"
            if results_file.exists():
                mtime = results_file.stat().st_mtime
                
            if mtime < cutoff_time:
                run_size = get_dir_size(run_dir)
                age_days = (now - mtime) / 86400
                
                if args.dry_run:
                    print(f"[DRY-RUN] Would delete {run_dir.relative_to(ROOT_DIR)} "
                          f"(Size: {format_size(run_size)}, Age: {age_days:.1f} days)")
                else:
                    try:
                        shutil.rmtree(run_dir)
                        print(f"Deleted {run_dir.relative_to(ROOT_DIR)} "
                              f"(Reclaimed: {format_size(run_size)})")
                        reclaimed_bytes += run_size
                        deleted_runs += 1
                    except Exception as e:
                        print(f"Error deleting {run_dir}: {e}", file=sys.stderr)
                        
        # Clean up empty domain directories
        try:
            if not any(runs_dir.iterdir()):
                if args.dry_run:
                    print(f"[DRY-RUN] Would delete empty directory {domain_dir.relative_to(ROOT_DIR)}")
                else:
                    shutil.rmtree(domain_dir)
        except Exception:
            pass # Ignore if not empty or locked
    
    if args.dry_run:
        print("\nDry run completed. No files were modified.")
    else:
        print("\nCleanup complete.")
        print(f"Deleted {deleted_runs} runs.")
        print(f"Reclaimed {format_size(reclaimed_bytes)} of disk space.")

if __name__ == "__main__":
    main()
