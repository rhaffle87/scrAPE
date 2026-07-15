import os
import sys
import subprocess
import re
import time
from pathlib import Path

# ANSI colors for premium terminal styling
CLR_HEADER = "\033[95m"
CLR_BLUE = "\033[94m"
CLR_CYAN = "\033[96m"
CLR_GREEN = "\033[92m"
CLR_WARNING = "\033[93m"
CLR_FAIL = "\033[91m"
CLR_END = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_UNDERLINE = "\033[4m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    banner = f"""{CLR_CYAN}{CLR_BOLD}
      ██████  ▄████▄   ██▀███   ▄▄▄       ██▓███  ▓█████ 
    ▒██    ▒ ▒██▀ ▀█  ▓██ ▒ ██▒▒████▄    ▓██░  ██▒▓█   ▀ 
    ░ ▓██▄   ▒▓█    ▄ ▓██ ░▄█ ▒▒██  ▀█▄  ▓██░ ██▓▒▒███   
      ▒   ██▒▒▓▓▄ ▄██▒▒██▀▀█▄  ░██▄▄▄▄██ ▒██▄█▓▒ ▒▒▓█  ▄ 
    ▒██████▒▒▒ ▓███▀ ░░██▓ ▒██▒ ▓█   ▓██▒▒██▒ ░  ░░▒████▒
    ▒ ▒▓▒ ▒ ░░ ░▒ ▒  ░░ ▒▓ ░▒▓░ ▒▒   ▓▒█░▒▓▒░ ░  ░░░ ▒░ ░
    ░ ░▒  ░ ░  ░  ▒     ░▒ ░ ▒░  ▒   ▒▒ ░░▒ ░      ░ ░  ░
    ░  ░  ░  ░          ░░   ░   ░   ▒   ░░          ░   
          ░  ░ ░         ░           ░  ░            ░  ░
             ░                                           {CLR_END}"""
    print(banner)


def get_input(prompt: str, default: str = "", val_fn=None) -> str:
    while True:
        default_str = f" [{CLR_GREEN}{default}{CLR_END}]" if default else ""
        sys.stdout.write(f" {prompt}{default_str}: ")
        sys.stdout.flush()
        try:
            val = sys.stdin.readline().strip()
        except KeyboardInterrupt:
            print(f"\n\n{CLR_FAIL}Process interrupted by user.{CLR_END}")
            sys.exit(0)

        if not val and default:
            val = default
        if val_fn:
            valid, msg = val_fn(val)
            if not valid:
                print(f" {CLR_FAIL}Error: {msg}{CLR_END}")
                continue
        return val


def get_bool_input(prompt: str, default: bool = True) -> bool:
    default_str = "Y/n" if default else "y/N"
    val = get_input(f"{prompt} ({default_str})", default="y" if default else "n")
    return val.lower() in ("y", "yes", "true", "1")


def validate_not_empty(val: str):
    if not val.strip():
        return False, "Input cannot be empty."
    return True, ""


def validate_number(val: str):
    if not val.isdigit():
        return False, "Must be a non-negative integer."
    return True, ""


def validate_seed_file(val: str):
    if not val.strip():
        return True, ""
    path = Path(val)
    if not path.exists():
        return False, f"File '{val}' does not exist."
    if not path.is_file():
        return False, f"'{val}' is not a file."
    return True, ""


def run_command(cmd: list[str]):
    print(
        f"\n{CLR_BLUE}{CLR_BOLD}═════════════════════ EXECUTION ═════════════════════{CLR_END}"
    )
    print(f"Executing: {CLR_GREEN}{' '.join(cmd)}{CLR_END}\n")
    try:
        process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, text=True)
        process.wait()
    except KeyboardInterrupt:
        print(f"\n{CLR_WARNING}Execution interrupted by user.{CLR_END}")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def mode_general_scraping():
    print(f"{CLR_BOLD}{CLR_CYAN}─── Mode: General / Broad Scraping ───{CLR_END}\n")
    keyword = get_input("Enter search keyword", val_fn=validate_not_empty)

    print("\nChoose a scraping profile:")
    print(
        f"  1) {CLR_GREEN}{CLR_BOLD}Quick Scan{CLR_END} (Recommended for common users — fast, respects robots.txt, 50 media limit)"
    )
    print(
        f"  2) {CLR_BLUE}{CLR_BOLD}Deep Scrape{CLR_END} (Recommended for power users — slower, checks deeper pages, 500 media limit)"
    )
    print(
        f"  3) {CLR_CYAN}{CLR_BOLD}Custom Scrape{CLR_END} (Manual configuration of all parameters)"
    )

    profile = get_input("Select profile (1-3)", default="1")

    if profile == "1":
        max_results = "50"
        page_limit = "25"
        crawl_depth = "2"
        ignore_robots = False
        download_media = True
    elif profile == "2":
        max_results = "500"
        page_limit = "150"
        crawl_depth = "3"
        ignore_robots = True
        download_media = True
    else:
        download_media = get_bool_input("Download media files to disk?", default=True)
        max_results = get_input(
            "Max results per type (0 for unlimited)",
            default="0",
            val_fn=validate_number,
        )
        page_limit = get_input(
            "Max page fetch limit (0 for unlimited)",
            default="0",
            val_fn=validate_number,
        )
        crawl_depth = get_input(
            "Max crawl depth (0 for unlimited)", default="0", val_fn=validate_number
        )
        ignore_robots = get_bool_input("Ignore robots.txt check?", default=False)

    cmd = [
        sys.executable,
        "main.py",
        "--keyword",
        keyword,
        "--max-results",
        max_results,
        "--page-limit",
        page_limit,
        "--crawl-depth",
        crawl_depth,
        "--output",
        "both",
    ]
    if download_media:
        cmd.append("--download-media")
    if ignore_robots:
        cmd.append("--ignore-robots")

    run_command(cmd)


def mode_specified_scraping():
    print(
        f"{CLR_BOLD}{CLR_CYAN}─── Mode: Specified / Targeted Seed Scraping ───{CLR_END}\n"
    )
    keyword = get_input(
        "Enter keyword identifier (e.g. 'apple')", val_fn=validate_not_empty
    )

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", keyword.lower()).strip("_")
    default_seed = f"seeds/{slug}.txt"
    if not Path(default_seed).exists():
        default_seed = ""

    seed_file = get_input(
        "Enter path to seed manifest file",
        default=default_seed,
        val_fn=validate_seed_file,
    )

    print("\nChoose a scraping profile:")
    print(
        f"  1) {CLR_GREEN}{CLR_BOLD}Focused Archive{CLR_END} (Recommended — downloads media only from seed domains, ignores robots)"
    )
    print(
        f"  2) {CLR_BLUE}{CLR_BOLD}Augmented Search{CLR_END} (Downloads from seeds AND runs DuckDuckGo to augment missing items)"
    )
    print(
        f"  3) {CLR_CYAN}{CLR_BOLD}Custom Scrape{CLR_END} (Manual configuration of all parameters)"
    )

    profile = get_input("Select profile (1-3)", default="1")

    if profile == "1":
        download_media = True
        ignore_robots = True
        force_search = False
    elif profile == "2":
        download_media = True
        ignore_robots = True
        force_search = True
    else:
        download_media = get_bool_input("Download media files to disk?", default=True)
        ignore_robots = get_bool_input("Ignore robots.txt check?", default=True)
        force_search = get_bool_input(
            "Force DuckDuckGo search alongside seed file?", default=False
        )

    cmd = [sys.executable, "main.py", "--keyword", keyword, "--output", "both"]
    if seed_file:
        cmd.extend(["--seed-file", seed_file])
    if download_media:
        cmd.append("--download-media")
    if ignore_robots:
        cmd.append("--ignore-robots")
    if force_search:
        cmd.append("--force-search")
    else:
        cmd.append("--skip-search")

    run_command(cmd)


def mode_continuous_watchdog():
    print(
        f"{CLR_BOLD}{CLR_CYAN}─── Mode: Continuous Monitoring Watchdog ───{CLR_END}\n"
    )
    keyword = get_input("Enter keyword query", val_fn=validate_not_empty)

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", keyword.lower()).strip("_")
    default_seed = f"seeds/{slug}.txt"
    if not Path(default_seed).exists():
        default_seed = ""

    seed_file = get_input(
        "Enter seed manifest path (optional)",
        default=default_seed,
        val_fn=validate_seed_file,
    )

    print("\nChoose a scheduler profile:")
    print(
        f"  1) {CLR_GREEN}{CLR_BOLD}Standard Updates{CLR_END} (Runs check every 10 minutes, respects rate-limits)"
    )
    print(
        f"  2) {CLR_BLUE}{CLR_BOLD}Aggressive Polling{CLR_END} (Runs check every 1 minute for fast updates/testing)"
    )
    print(
        f"  3) {CLR_CYAN}{CLR_BOLD}Custom Scheduler{CLR_END} (Manual configuration of all parameters)"
    )

    profile = get_input("Select profile (1-3)", default="1")

    if profile == "1":
        interval = "600"
        timeout = "1800"
        download_media = True
        ignore_robots = True
    elif profile == "2":
        interval = "60"
        timeout = "300"
        download_media = True
        ignore_robots = True
    else:
        download_media = get_bool_input("Download media files to disk?", default=True)
        interval = get_input(
            "Interval between runs in seconds", default="60", val_fn=validate_number
        )
        timeout = get_input(
            "Max runtime per run in seconds", default="1800", val_fn=validate_number
        )
        ignore_robots = get_bool_input("Ignore robots.txt check?", default=True)

    cmd = [
        sys.executable,
        "monitor_agent.py",
        "--keyword",
        keyword,
        "--interval",
        interval,
        "--timeout",
        timeout,
    ]
    if seed_file:
        cmd.extend(["--seed-file", seed_file])
    if download_media:
        cmd.append("--download-media")
    if ignore_robots:
        cmd.append("--ignore-robots")

    run_command(cmd)


def print_mission_statement():
    print(f" {CLR_BOLD}{CLR_CYAN}═══════════════════ HIGH-EFFICIENCY FUEL PUMP FOR AI ═══════════════════{CLR_END}")
    print(f"  scrAPE is essentially a {CLR_BOLD}high-efficiency fuel pump for AI{CLR_END}.")
    print(f"  By using a systematic layer-by-layer crawler (BFS) equipped with an")
    print(f"  AI-friendly scraper (Crawl4AI), it maps entire websites and converts")
    print(f"  messy internet pages into clean, structured text that AI models and LLMs")
    print(f"  can immediately understand.")
    print(f"  ")
    print(f"  Because scrAPE has built-in smart asset deduplication, concurrent")
    print(f"  downloading, and strict boundary controls, it solves the biggest")
    print(f"  headaches in data engineering:")
    print(f"  • Stops the crawler from getting lost on external sites")
    print(f"  • Cuts down massive storage costs by stripping out duplicate files")
    print(f"  • Gathers deep data at lightning speed")
    print(f"  ")
    print(f"  It is exactly what companies want for building custom AI knowledge bases,")
    print(f"  feeding vector databases for RAG applications, and running cost-effective")
    print(f"  AI data pipeline operations.")
    print(f" {CLR_BOLD}{CLR_CYAN}════════════════════════════════════════════════════════════════════════{CLR_END}\n")


def select_completed_run():
    # Scan output/ directory
    output_dir = Path("output")
    if not output_dir.exists():
        print(f" {CLR_FAIL}No output directory found. Please run a scrape first.{CLR_END}")
        return None, None
    
    subjects = [d for d in output_dir.iterdir() if d.is_dir() and d.name != "cache"]
    if not subjects:
        print(f" {CLR_FAIL}No completed runs found under output/.{CLR_END}")
        return None, None
    
    print("\nSelect scraped subject:")
    for idx, sub in enumerate(subjects, 1):
        print(f"  {idx}) {CLR_GREEN}{sub.name}{CLR_END}")
    
    sub_choice = get_input(f"Select subject (1-{len(subjects)})", val_fn=validate_number)
    sub_idx = int(sub_choice) - 1
    if sub_idx < 0 or sub_idx >= len(subjects):
        print(f" {CLR_FAIL}Invalid selection.{CLR_END}")
        return None, None
    
    subject_dir = subjects[sub_idx]
    runs_dir = subject_dir / "runs"
    if not runs_dir.exists():
        # Fallback if no runs subfolder structure exists
        runs = [subject_dir]
    else:
        runs = [d for d in runs_dir.iterdir() if d.is_dir()]
        
    if not runs:
        print(f" {CLR_FAIL}No runs found for {subject_dir.name}.{CLR_END}")
        return None, None
        
    print("\nSelect specific run ID:")
    for idx, r in enumerate(runs, 1):
        print(f"  {idx}) {CLR_BLUE}{r.name}{CLR_END}")
        
    r_choice = get_input(f"Select run (1-{len(runs)})", val_fn=validate_number)
    r_idx = int(r_choice) - 1
    if r_idx < 0 or r_idx >= len(runs):
        print(f" {CLR_FAIL}Invalid selection.{CLR_END}")
        return None, None
        
    return subject_dir.name, runs[r_idx]


def mode_create_dataset():
    import shutil
    from urllib.parse import urlparse
    print(f"{CLR_BOLD}{CLR_CYAN}─── Mode: Create Structured AI Dataset ───{CLR_END}\n")
    print("This utility groups and exports scraped files from a completed run into a single")
    print("structured folder with clean filenames and custom organization styles.\n")
    
    subject_name, run_dir = select_completed_run()
    if not run_dir:
        return
        
    # Check if there are images or videos to copy
    image_src = run_dir / "images"
    video_src = run_dir / "videos"
    
    has_images = image_src.exists() and any(image_src.iterdir())
    has_videos = video_src.exists() and any(video_src.iterdir())
    
    if not has_images and not has_videos:
        print(f"\n {CLR_WARNING}Warning: No downloaded media files found in this run.{CLR_END}")
        print(" (Make sure you ran the scraper with the --download-media flag.)")
        return
        
    print("\nChoose grouping / layout style for the dataset:")
    print(f"  1) {CLR_GREEN}{CLR_BOLD}Consolidated Flat{CLR_END} (All files in one folder, prefixed to prevent collisions)")
    print(f"  2) {CLR_BLUE}{CLR_BOLD}Domain-Grouped{CLR_END} (Subfolders created for each source domain)")
    print(f"  3) {CLR_CYAN}{CLR_BOLD}Media-Type Grouped{CLR_END} (Subfolders for 'images' and 'videos')")
    
    style = get_input("Select layout (1-3)", default="1")
    
    target_root = Path("datasets") / f"{subject_name}_{run_dir.name}_dataset"
    target_root.mkdir(parents=True, exist_ok=True)
    
    print(f"\nExporting to: {CLR_GREEN}{target_root.resolve()}{CLR_END}...")
    copied_count = 0
    
    def sanitize_filename(name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", name)

    # We can load results.json if we want to know source domain or alt text details
    results_path = run_dir / "results.json"
    url_to_domain = {}
    if results_path.exists():
        import json
        try:
            with open(results_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for img in data.get("images", []):
                url_to_domain[img.get("file_path")] = img.get("source_domain") or urlparse(img.get("url")).netloc
            for vid in data.get("videos", []):
                url_to_domain[vid.get("file_path")] = vid.get("source_domain") or urlparse(vid.get("url")).netloc
        except Exception:
            pass

    for src_dir, kind in [(image_src, "images"), (video_src, "videos")]:
        if not src_dir.exists():
            continue
        for file_path in src_dir.rglob("*"):
            if not file_path.is_file():
                continue
                
            # Determine domain folder if needed
            rel_path_in_run = file_path.relative_to(run_dir).as_posix()
            domain = url_to_domain.get(rel_path_in_run) or file_path.parent.name
            domain_clean = sanitize_filename(domain)
            
            if style == "1":
                # Consolidated flat
                new_name = f"{domain_clean}_{file_path.name}"
                dest = target_root / new_name
            elif style == "2":
                # Domain grouped
                domain_dir = target_root / domain_clean
                domain_dir.mkdir(exist_ok=True)
                dest = domain_dir / file_path.name
            else:
                # Media type grouped
                kind_dir = target_root / kind
                kind_dir.mkdir(exist_ok=True)
                dest = kind_dir / file_path.name
                
            shutil.copy2(file_path, dest)
            copied_count += 1
            
    print(f"\n {CLR_GREEN}Success!{CLR_END} Copied {copied_count} files to: {target_root.name}")


def mode_rag_ingest():
    from urllib.parse import urlparse
    print(f"{CLR_BOLD}{CLR_CYAN}─── Mode: Enterprise LLM RAG Ingestion Helper ───{CLR_END}\n")
    print("This utility processes crawled pages, text tokens, alt descriptions, and scores")
    print("into highly structured formats optimized for ingestion into Vector DBs/RAG pipelines.\n")
    
    subject_name, run_dir = select_completed_run()
    if not run_dir:
        return
        
    results_path = run_dir / "results.json"
    if not results_path.exists():
        print(f" {CLR_FAIL}Error: results.json not found in the run folder.{CLR_END}")
        return
        
    import json
    try:
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f" {CLR_FAIL}Error reading results.json: {e}{CLR_END}")
        return
        
    print("\nChoose ingestion output format:")
    print(f"  1) {CLR_GREEN}{CLR_BOLD}Consolidated Markdown Document{CLR_END} (A single well-structured .md document of all findings)")
    print(f"  2) {CLR_BLUE}{CLR_BOLD}Chunked Page-Level Documents{CLR_END} (Individual markdown files for each scraped page)")
    print(f"  3) {CLR_CYAN}{CLR_BOLD}JSON-Lines (JSONL) format{CLR_END} (One JSON record per document, perfect for automated embedding pipelines)")
    
    format_choice = get_input("Select format (1-3)", default="1")
    
    dest_dir = Path("rag_ingest") / f"{subject_name}_{run_dir.name}_rag"
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    images = data.get("images", [])
    videos = data.get("videos", [])
    reports = data.get("page_reports", [])
    metadata = data.get("run_metadata", {})
    
    print(f"\nGenerating RAG documents in: {CLR_GREEN}{dest_dir.resolve()}{CLR_END}...")
    
    if format_choice == "1":
        # Consolidated markdown
        md_file = dest_dir / "consolidated_knowledge.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# Knowledge Base: Scrape Results for '{data.get('keyword')}'\n\n")
            f.write(f"- **Run ID:** {data.get('run_id')}\n")
            f.write(f"- **Scanned Pages Count:** {data.get('page_count')}\n")
            f.write(f"- **Discovered Images:** {len(images)}\n")
            f.write(f"- **Discovered Videos:** {len(videos)}\n\n")
            
            f.write("## Scanned Source Pages\n\n")
            for idx, r in enumerate(reports, 1):
                f.write(f"{idx}. [{r.get('url')}]({r.get('url')}) — Status: {r.get('status')} (Depth: {r.get('depth')})\n")
                
            f.write("\n## Extracted Structured Media & Alt Text Metadata\n\n")
            f.write("Below is the cleaned alt text, titles, and source URLs representing extracted knowledge.\n\n")
            
            for idx, img in enumerate(images, 1):
                f.write(f"### Image Asset #{idx}\n")
                f.write(f"- **Source Page:** {img.get('source_page')}\n")
                f.write(f"- **File Path:** {img.get('file_path')}\n")
                f.write(f"- **Alt Description:** \"{img.get('alt_text') or 'N/A'}\"\n")
                f.write(f"- **Context Title:** \"{img.get('page_title') or 'N/A'}\"\n")
                f.write(f"- **Relevance Score:** {img.get('score')}\n")
                f.write(f"- **URL:** {img.get('url')}\n\n")
                
            for idx, vid in enumerate(videos, 1):
                f.write(f"### Video Asset #{idx}\n")
                f.write(f"- **Source Page:** {vid.get('source_page')}\n")
                f.write(f"- **File Path:** {vid.get('file_path')}\n")
                f.write(f"- **Context Title/Label:** \"{vid.get('page_title') or vid.get('type') or 'N/A'}\"\n")
                f.write(f"- **Relevance Score:** {vid.get('score')}\n")
                f.write(f"- **URL:** {vid.get('url')}\n\n")
                
        print(f"Created: {md_file.name}")
        
    elif format_choice == "2":
        # Chunked Page-Level Documents
        # Group assets by page URL
        pages_dict = {}
        for r in reports:
            pages_dict[r.get("url")] = {"report": r, "images": [], "videos": []}
        for img in images:
            sp = img.get("source_page")
            if sp not in pages_dict:
                pages_dict[sp] = {"report": None, "images": [], "videos": []}
            pages_dict[sp]["images"].append(img)
        for vid in videos:
            sp = vid.get("source_page")
            if sp not in pages_dict:
                pages_dict[sp] = {"report": None, "images": [], "videos": []}
            pages_dict[sp]["videos"].append(vid)
            
        file_count = 0
        for page_url, pdata in pages_dict.items():
            parsed = urlparse(page_url)
            filename = re.sub(r"[^a-zA-Z0-9]+", "_", parsed.netloc + parsed.path).strip("_") or "root"
            p_file = dest_dir / f"{filename}.md"
            
            with open(p_file, "w", encoding="utf-8") as f:
                f.write(f"# Document: {pdata['report'].get('url') if pdata['report'] else page_url}\n\n")
                if pdata['report']:
                    f.write(f"- **Crawl Depth:** {pdata['report'].get('depth')}\n")
                    f.write(f"- **Crawl Status:** {pdata['report'].get('status')}\n\n")
                
                f.write("## Extracted Media Contents & Descriptions\n\n")
                for idx, img in enumerate(pdata["images"], 1):
                    f.write(f"### Image #{idx} (Score: {img.get('score')})\n")
                    f.write(f"- **Description:** {img.get('alt_text') or 'No alt description available.'}\n")
                    f.write(f"- **Title:** {img.get('page_title') or 'N/A'}\n")
                    f.write(f"- **Asset Path:** {img.get('file_path')}\n")
                    f.write(f"- **Direct Link:** {img.get('url')}\n\n")
                    
                for idx, vid in enumerate(pdata["videos"], 1):
                    f.write(f"### Video #{idx} (Score: {vid.get('score')})\n")
                    f.write(f"- **Title:** {vid.get('page_title') or 'N/A'}\n")
                    f.write(f"- **Asset Path:** {vid.get('file_path')}\n")
                    f.write(f"- **Direct Link:** {vid.get('url')}\n\n")
                    
            file_count += 1
        print(f"Created {file_count} chunked page document markdown files.")
        
    else:
        # JSONL format
        jsonl_file = dest_dir / "documents.jsonl"
        with open(jsonl_file, "w", encoding="utf-8") as f:
            for idx, img in enumerate(images, 1):
                doc = {
                    "id": f"img_{idx}",
                    "url": img.get("url"),
                    "source_page": img.get("source_page"),
                    "text": f"Image showing {img.get('alt_text')}. Context: {img.get('page_title')}.",
                    "metadata": {
                        "type": "image",
                        "score": img.get("score"),
                        "file_path": img.get("file_path"),
                        "mime_type": img.get("mime_type")
                    }
                }
                f.write(json.dumps(doc) + "\n")
            for idx, vid in enumerate(videos, 1):
                doc = {
                    "id": f"vid_{idx}",
                    "url": vid.get("url"),
                    "source_page": vid.get("source_page"),
                    "text": f"Video media titled {vid.get('page_title') or vid.get('type')}.",
                    "metadata": {
                        "type": "video",
                        "score": vid.get("score"),
                        "file_path": vid.get("file_path")
                    }
                }
                f.write(json.dumps(doc) + "\n")
        print(f"Created: {jsonl_file.name}")
        
    print(f"\n {CLR_GREEN}Success!{CLR_END} Ingestion assets generated in: {dest_dir.name}")


def main():
    while True:
        clear_screen()
        print_banner()
        print_mission_statement()
        print(f" {CLR_BOLD}Please select a scraping operation flow:{CLR_END}\n")
        print(
            f"   {CLR_GREEN}{CLR_BOLD}1.{CLR_END} General/Broad Search Scraping  (Uses DuckDuckGo search + recursive crawl)"
        )
        print(
            f"   {CLR_GREEN}{CLR_BOLD}2.{CLR_END} Specified/Targeted Scraping     (Uses a strict seed manifest file)"
        )
        print(
            f"   {CLR_GREEN}{CLR_BOLD}3.{CLR_END} Continuous Watchdog Agent      (Runs scheduled scrapes at interval)"
        )
        print(
            f"   {CLR_GREEN}{CLR_BOLD}4.{CLR_END} Create Structured AI Dataset   (Format and group findings in one folder)"
        )
        print(
            f"   {CLR_GREEN}{CLR_BOLD}5.{CLR_END} Enterprise LLM RAG Ingestion   (Extract clean markdown texts for vector DBs)"
        )
        print(f"   {CLR_FAIL}{CLR_BOLD}6.{CLR_END} Exit\n")

        choice = get_input("Enter selection (1-6)", default="1")

        clear_screen()
        print_banner()

        if choice == "1":
            mode_general_scraping()
        elif choice == "2":
            mode_specified_scraping()
        elif choice == "3":
            mode_continuous_watchdog()
        elif choice == "4":
            mode_create_dataset()
        elif choice == "5":
            mode_rag_ingest()
        elif choice == "6":
            print(f"\n {CLR_GREEN}Goodbye!{CLR_END}\n")
            break
        else:
            print(f" {CLR_FAIL}Invalid option '{choice}'. Please select 1-6.{CLR_END}")
            time.sleep(2)
            continue

        print(f"\n{CLR_CYAN}Press Enter to return to main menu...{CLR_END}")
        sys.stdin.readline()


if __name__ == "__main__":
    main()
