"""
cli_wizard_standard.py — Interactive Configuration & Mode Routines.

Contains interactive configuration prompts, banner renderers, input validators,
and mode execution handlers for general scraping, specified seed scraping,
dataset formatting, RAG ingestion, domain config tuning, and proxy authentication.
"""

from __future__ import annotations

import sys
import subprocess
import re
from pathlib import Path

from src.config.version import VERSION

# Ensure UTF-8 output encoding for block characters on Windows
if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "reconfigure"):
        getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        getattr(sys.stderr, "reconfigure")(encoding="utf-8")

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
CLR_DIM = "\033[2m"
CLR_REVERSE = "\033[7m"
CLR_ORANGE = "\033[38;5;208m"  # Acquisition Orange (#ff5500)

__all__ = [
    "clear_screen",
    "print_banner",
    "get_input",
    "get_bool_input",
    "validate_not_empty",
    "validate_number",
    "load_subject_profiles",
    "validate_seed_file",
    "run_command",
    "mode_general_scraping",
    "mode_specified_scraping",
    "mode_create_dataset",
    "mode_rag_ingest",
    "mode_domain_config",
    "mode_proxy_auth",
    "print_mission_statement",
    "select_completed_run",
    "sanitize_filename",
    "val_float",
    "prompt_core_systems_options",
    "mode_core_systems_setup",
    "CLR_ORANGE",
]


def clear_screen():
    print("\033[H\033[2J", end="", flush=True)


def print_banner():
    ver_str = f"v{VERSION}"
    banner = f"""{CLR_ORANGE}{CLR_BOLD}
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗            ┃
┃ ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝            ┃
┃ ███████╗██║     ██████╔╝███████║██████╔╝█████╗              ┃
┃ ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝              ┃
┃ ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗            ┃
┃ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝            ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ [SYSTEM] DATA & MEDIA AUTONOMOUS AGENT{ver_str:>16}      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
{CLR_END}"""
    print(banner)


def get_input(prompt: str, default: str = "", val_fn=None) -> str:
    while True:
        default_str = f" [{CLR_DIM}{default}{CLR_END}]" if default else ""
        sys.stdout.write(f"{CLR_ORANGE}[USER]{CLR_END} ▶ {prompt}{default_str}: ")
        sys.stdout.flush()
        try:
            val = sys.stdin.readline().strip()
        except KeyboardInterrupt:
            print(f"\n\n{CLR_FAIL}[SYSTEM] Process interrupted by user.{CLR_END}")
            sys.exit(0)

        if not val and default:
            val = default
        if val_fn:
            valid, msg = val_fn(val)
            if not valid:
                print(f"{CLR_FAIL}[SYSTEM] ✗ Error: {msg}{CLR_END}")
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


def load_subject_profiles(profile_path: str = "data/subject_profiles.json") -> dict:
    """Load subject profile presets from JSON configuration file."""
    import json
    try:
        path = Path(profile_path)
        if not path.is_absolute() and not path.exists():
            _project_root = Path(__file__).resolve().parent.parent.parent
            path = _project_root / profile_path
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


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
    print(f"\n{CLR_DIM}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{CLR_END}")
    print(f"{CLR_DIM}┃{CLR_END} {CLR_CYAN}[AGENT]{CLR_END} ⚒ Running external command...")
    print(f"{CLR_DIM}┃{CLR_END} {CLR_DIM}{' '.join(cmd)}{CLR_END}")
    print(f"{CLR_DIM}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{CLR_END}\n")
    process = None
    try:
        process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, text=True)  # nosec B603
        process.wait()
    except KeyboardInterrupt:
        print(f"\n{CLR_WARNING}Execution interrupted by user.{CLR_END}")
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def mode_general_scraping():
    print(f"\n{CLR_BOLD}{CLR_REVERSE} [SYSTEM] █ MODE: GENERAL SCRAPING {CLR_END}\n")
    keyword = get_input("Enter search keyword", val_fn=validate_not_empty)

    print("\nChoose a scraping profile:")
    print(
        f"  1) {CLR_GREEN}{CLR_BOLD}Quick Scan{CLR_END}   (Fast, respects robots.txt, 50 media limit)"
    )
    print(
        f"  2) {CLR_BLUE}{CLR_BOLD}Deep Scrape{CLR_END}  (Power users, deeper pages, 500 media limit)"
    )
    print(
        f"  3) {CLR_CYAN}{CLR_BOLD}Custom Scrape{CLR_END}(Manual configuration of all parameters)"
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

    enable_gov = get_bool_input("Enable Dynamic CPU/RAM Load Governor?", default=True)

    cmd = [
        sys.executable,
        str(Path(__file__).parent / "main.py"),
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
    if enable_gov:
        cmd.append("--enable-governor")

    core_flags = prompt_core_systems_options()
    cmd.extend(core_flags)

    run_command(cmd)

    print(f"\n{CLR_GREEN}Scraping complete.{CLR_END}")


def mode_specified_scraping():
    print(f"\n{CLR_BOLD}{CLR_REVERSE} [SYSTEM] █ MODE: TARGETED SEED SCRAPING {CLR_END}\n")
    keyword = get_input(
        "Enter keyword identifier (e.g. 'apple')", val_fn=validate_not_empty
    )

    seed_files = sorted(Path("seeds").glob("*.txt"))
    seed_file = ""
    if seed_files:
        print("\nAvailable Seed Manifest Files in seeds/:")
        for idx, sfile in enumerate(seed_files, start=1):
            print(f"  {idx}) {CLR_GREEN}{sfile.name}{CLR_END}")
        print(f"  {len(seed_files)+1}) Enter custom path manually")

        choice = get_input("Select seed file option", default="1")
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(seed_files):
                seed_file = str(seed_files[choice_num - 1])
        except (ValueError, TypeError):
            pass

    if not seed_file:
        seed_file = get_input("Enter Seed File Path", val_fn=validate_seed_file)

    max_results = get_input(
        "Max results per media type (0 for unlimited)", default="200", val_fn=validate_number
    )
    page_limit = get_input(
        "Max page fetches (0 for unlimited)", default="300", val_fn=validate_number
    )

    cmd = [
        sys.executable,
        str(Path(__file__).parent / "main.py"),
        "--keyword",
        keyword,
        "--seed-file",
        seed_file,
        "--max-results",
        max_results,
        "--page-limit",
        page_limit,
        "--download-media",
        "--output",
        "both",
    ]

    core_flags = prompt_core_systems_options()
    cmd.extend(core_flags)

    run_command(cmd)


def print_mission_statement():
    print(f"\n{CLR_BOLD}{CLR_REVERSE} [SYSTEM] █ MODE: AI DATASET GENERATOR & TRAINING PIPELINE {CLR_END}\n")
    print(f"{CLR_DIM}┃{CLR_END} This tool formats raw scraped images into high-quality datasets for AI model")
    print(f"{CLR_DIM}┃{CLR_END} training (LoRA, SDXL, Flux, ControlNet) using taggers and Kohya_ss exports.\n")


def select_completed_run() -> Path | None:
    output_dir = Path("output")
    if not output_dir.exists():
        print(f"{CLR_FAIL}No output directory found.{CLR_END}")
        return None

    subjects = [d for d in output_dir.iterdir() if d.is_dir() and d.name != "cache"]
    if not subjects:
        print(f"{CLR_FAIL}No completed subject runs found in output/.{CLR_END}")
        return None

    print("\nSelect Subject Dataset to Export:")
    for idx, subj in enumerate(subjects, start=1):
        print(f"  {idx}) {CLR_GREEN}{subj.name}{CLR_END}")

    choice = get_input("Select subject option", default="1")
    try:
        idx_num = int(choice)
        if 1 <= idx_num <= len(subjects):
            return subjects[idx_num - 1]
    except (ValueError, TypeError):
        pass
    return None


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^\w\-]", "_", name)


def mode_create_dataset():
    print_mission_statement()
    target_dir = select_completed_run()
    if not target_dir:
        return

    print(f"\nProcessing dataset for: {CLR_BOLD}{target_dir.name}{CLR_END}")
    zip_name = sanitize_filename(target_dir.name) + "_dataset.zip"
    dest_path = Path("output") / zip_name
    
    min_score = get_input("Minimum Aesthetic Score (0.0 to disable)", default="5.5", val_fn=val_float)
    enable_tagging = get_bool_input("Enable WD14 Vision Tagging?", default=True)
    enable_crop = get_bool_input("Enable Smart Face Crop?", default=False)

    cmd = [
        sys.executable,
        "-m",
        "src.ml.dataset_exporter",
        "--input-dir",
        str(target_dir),
        "--output-zip",
        str(dest_path),
        "--min-aesthetic-score",
        min_score,
    ]
    
    if enable_tagging:
        cmd.append("--ml-tag")
    if enable_crop:
        cmd.append("--ml-crop")

    run_command(cmd)


def mode_rag_ingest():
    print(f"\n{CLR_BOLD}{CLR_REVERSE} [SYSTEM] █ MODE: RAG TEXT / DOCUMENT INGEST {CLR_END}\n")
    target_dir = select_completed_run()
    if not target_dir:
        return

    cmd = [
        sys.executable,
        "-m",
        "src.ml.rag_exporter",
        "--input-dir",
        str(target_dir),
    ]
    run_command(cmd)


def val_float(v):
    try:
        f = float(v)
        if f >= 0:
            return True, ""
        return False, "Must be >= 0"
    except (ValueError, TypeError):
        return False, "Must be a valid number"


def mode_domain_config():
    print(f"\n{CLR_BOLD}{CLR_REVERSE} [SYSTEM] █ MODE: DYNAMIC DOMAIN CONFIGURATION {CLR_END}\n")
    domain = get_input("Enter target domain (e.g. 'example.com')", val_fn=validate_not_empty)
    rps = get_input("Requests per second limit (0 for unthrottled)", default="1.0", val_fn=val_float)

    config_path = Path("data/domain_config.json")
    import json
    cfg = {}
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}

    rate_limits = cfg.setdefault("rate_limits", {})
    rate_limits[domain.lower()] = float(rps)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"\n{CLR_GREEN}Updated rate limit for {domain} to {rps} RPS in data/domain_config.json{CLR_END}")


def mode_proxy_auth():
    print(f"\n{CLR_BOLD}{CLR_REVERSE} [SYSTEM] █ MODE: PROXY & AUTH SETTINGS {CLR_END}\n")
    proxy_url = get_input("Enter Proxy URL (e.g. http://user:pass@host:port, or blank to disable)", default="")
    env_path = Path(".env")

    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    new_lines = []
    found = False
    for line in lines:
        if line.startswith("SCRAPER_PROXY="):
            new_lines.append(f"SCRAPER_PROXY={proxy_url}")
            found = True
        else:
            new_lines.append(line)

    if not found and proxy_url:
        new_lines.append(f"SCRAPER_PROXY={proxy_url}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"\n{CLR_GREEN}Proxy settings saved to .env file.{CLR_END}")


def mode_scraper_auth():
    print(f"\n{CLR_BOLD}{CLR_REVERSE} [SYSTEM] █ MODE: CONFIGURE SCRAPER AUTHENTICATION {CLR_END}\n")
    domain = get_input("Enter target platform domain (e.g. instagram.com, x.com, tiktok.com)", val_fn=validate_not_empty)
    cookie_name = get_input("Enter cookie name (e.g. sessionid, auth_token)", val_fn=validate_not_empty)
    cookie_value = get_input(f"Enter cookie value for {cookie_name}", val_fn=validate_not_empty)

    try:
        from network.session import SessionManager
        manager = SessionManager()
        existing = manager.load_session(domain) or {}
        if isinstance(existing, list):
            existing_dict = {c["name"]: c["value"] for c in existing if isinstance(c, dict)}
        else:
            existing_dict = existing
            
        existing_dict[cookie_name] = cookie_value
        manager.save_session(domain, existing_dict)
        print(f"\n{CLR_GREEN}Successfully saved authentication cookie for {domain}{CLR_END}")
    except Exception as e:
        print(f"\n{CLR_FAIL}Failed to save authentication: {e}{CLR_END}")

def mode_export_database():
    print(f"\n{CLR_BOLD}{CLR_REVERSE} [SYSTEM] █ MODE: EXPORT LOCAL DATABASE {CLR_END}\n")
    target_dir = select_completed_run()
    if not target_dir:
        return

    fmt = get_input("Export format (csv or json)", default="csv").lower()
    if fmt not in ("csv", "json"):
        print(f"{CLR_FAIL}Invalid format. Using csv.{CLR_END}")
        fmt = "csv"

    cmd = [
        sys.executable,
        "-m",
        "src.storage.analytics_exporter",
        "--input-dir",
        str(target_dir),
        "--format",
        fmt
    ]
    run_command(cmd)


def prompt_core_systems_options() -> list[str]:
    """Interactive prompt sequence for ML pipelines, storage sinks, self-healing DOM, and worker processes."""
    flags: list[str] = []
    print(f"\n{CLR_CYAN}--- NEXT-GEN CORE SYSTEMS ARCHITECTURE CONFIGURATION ---{CLR_END}")
    enable_core = get_bool_input("Configure ML, Cloud Storage, or Self-Healing options?", default=False)
    if not enable_core:
        return flags

    # ML Pipeline
    enable_ml = get_bool_input("Enable Inline ML Pipeline (Aesthetic scoring, tagging, cropping)?", default=False)
    if enable_ml:
        min_score = get_input("Min Aesthetic Score threshold (0.0 to disable, e.g. 5.5)", default="0.0", val_fn=val_float)
        if float(min_score) > 0:
            flags.extend(["--aesthetic-score", min_score])
        if get_bool_input("Enable smart face/object crop?", default=False):
            flags.append("--auto-crop")
        if get_bool_input("Enable WD14 vision dataset tagging?", default=False):
            flags.append("--tag-dataset")
        if get_bool_input("Export RAG knowledge base?", default=False):
            flags.append("--export-rag")
        if get_bool_input("Auto-export database to CSV?", default=False):
            flags.append("--auto-export-db")

    # Storage Backend
    enable_s3 = get_bool_input("Use Cloud Storage Sink (S3/MinIO) instead of Local?", default=False)
    if enable_s3:
        flags.extend(["--storage-backend", "s3"])
        bucket = get_input("Enter S3 bucket name", default="scrape-media")
        flags.extend(["--s3-bucket", bucket])
        prefix = get_input("Enter S3 key prefix", default="runs/")
        flags.extend(["--s3-prefix", prefix])

    # Autonomous Self-Healing DOM Parser
    if get_bool_input("Enable Autonomous Self-Healing DOM Parser fallback?", default=False):
        flags.append("--enable-self-healing")
        if get_bool_input("Enable Tier 4 Multi-Modal Vision-Language (VLM) DOM healing?", default=False):
            flags.append("--enable-vlm-healing")
            vlm_prov = get_input("VLM Provider (ollama/gemini/openai)", default="ollama")
            flags.extend(["--vlm-provider", vlm_prov.lower()])
            if vlm_prov.lower() in ("gemini", "openai"):
                if get_bool_input("Grant explicit consent to send screenshots to hosted API?", default=False):
                    flags.append("--vlm-provider-consent")

    # Global Content-Addressable Storage (CAS)
    if get_bool_input("Enable Global Content-Addressable Storage (CAS) deduplication?", default=False):
        flags.append("--enable-cas")

    # Columnar Apache Parquet Export
    if get_bool_input("Export crawl results to Snappy Apache Parquet dataset?", default=False):
        flags.append("--export-parquet")

    # Worker Processes Pool
    w_proc = get_input("Isolated Worker Processes (0 for CPU core auto-detection)", default="0", val_fn=validate_number)
    if int(w_proc) > 0:
        flags.extend(["--worker-processes", w_proc])

    return flags


def mode_core_systems_setup():
    """Configure default CAPTCHA solver provider and storage credentials."""
    print(f"\n{CLR_BOLD}{CLR_REVERSE} [SYSTEM] █ MODE: CORE SYSTEMS & CAPTCHA CONFIGURATION {CLR_END}\n")
    print("Select primary CAPTCHA solver provider:")
    print("  1) FreeAudioProvider (Zero-Cost Local Whisper / SpeechRecognition)")
    print("  2) CapSolver (Commercial API)")
    print("  3) 2Captcha (Commercial API)")
    print("  4) AntiCaptcha (Commercial API)")
    choice = get_input("Select provider (1-4)", default="1")
    prov_map = {"1": "free_audio", "2": "capsolver", "3": "2captcha", "4": "anticaptcha"}
    provider = prov_map.get(choice, "free_audio")

    env_path = Path(".env")
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    new_lines = [line for line in lines if not line.startswith("CAPTCHA_PRIMARY_PROVIDER=")]
    new_lines.append(f"CAPTCHA_PRIMARY_PROVIDER={provider}")
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"\n{CLR_GREEN}Primary CAPTCHA provider set to: {provider} in .env{CLR_END}")

