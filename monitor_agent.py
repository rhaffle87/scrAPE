import sys
import time
import subprocess
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Configuration — edit these two values before running
# ---------------------------------------------------------------------------
KEYWORD = "example_subject"           # The keyword / subject name to scrape
SEED_FILE = "seeds/example_subject.txt"  # Path to the matching seed manifest file
# ---------------------------------------------------------------------------

def run_scraper():
    print(f"[{datetime.now().isoformat()}] Starting full scrAPE run...")
    cmd = [
        sys.executable,
        "main.py",
        "--keyword", KEYWORD,
        "--seed-file", SEED_FILE,
        "--download-media"
    ]
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        start_time = time.time()
        timeout = 1800  # 30 minutes
        
        while True:
            if time.time() - start_time > timeout:
                print(f"[{datetime.now().isoformat()}] ERROR: scrAPE timed out after {timeout} seconds. Terminating process...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                process.wait()
                break
                
            line = process.stdout.readline()
            if not line:
                break
            sys.stdout.write(line)
            sys.stdout.flush()
            
        return_code = process.wait()
        if return_code == 0:
            print(f"[{datetime.now().isoformat()}] scrAPE run finished successfully.")
        else:
            print(f"[{datetime.now().isoformat()}] scrAPE run failed with exit code {return_code}.")
            
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Unexpected error during run: {e}")

def main():
    interval_seconds = 60  # 60 seconds check interval
    print(f"[{datetime.now().isoformat()}] Sleep Monitoring Agent (scrAPE) initialized with check interval of 60 seconds.")
    
    try:
        # Initial immediate run
        run_scraper()
        
        while True:
            next_run = datetime.now() + timedelta(seconds=interval_seconds)
            print(f"[{datetime.now().isoformat()}] Next run scheduled at {next_run.isoformat()}. Sleeping...")
            
            # Sleep in small increments to allow responsive Ctrl+C
            sleep_elapsed = 0
            while sleep_elapsed < interval_seconds:
                time.sleep(5)
                sleep_elapsed += 5
                
            run_scraper()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().isoformat()}] Sleep Monitoring Agent stopped by user request.")

if __name__ == "__main__":
    main()
