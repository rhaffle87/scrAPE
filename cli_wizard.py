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


def main():
    while True:
        clear_screen()
        print_banner()
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
        print(f"   {CLR_FAIL}{CLR_BOLD}4.{CLR_END} Exit\n")

        choice = get_input("Enter selection (1-4)", default="1")

        clear_screen()
        print_banner()

        if choice == "1":
            mode_general_scraping()
        elif choice == "2":
            mode_specified_scraping()
        elif choice == "3":
            mode_continuous_watchdog()
        elif choice == "4":
            print(f"\n {CLR_GREEN}Goodbye!{CLR_END}\n")
            break
        else:
            print(f" {CLR_FAIL}Invalid option '{choice}'. Please select 1-4.{CLR_END}")
            time.sleep(2)
            continue

        print(f"\n{CLR_CYAN}Press Enter to return to main menu...{CLR_END}")
        sys.stdin.readline()


if __name__ == "__main__":
    main()
