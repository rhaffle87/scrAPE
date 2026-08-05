"""
cli_wizard.py — Interactive CLI Wizard Launcher & Re-export Shim.

Main entry point for interactive terminal wizard operations.
Re-exports standard wizard modes from cli_wizard_standard.py
and continuous watchdog mode from cli_wizard_watchdog.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to python path to resolve modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.cli_wizard_standard import (
    clear_screen,
    print_banner,
    get_input,
    get_bool_input,
    validate_not_empty,
    validate_number,
    load_subject_profiles,
    validate_seed_file,
    run_command,
    mode_general_scraping,
    mode_specified_scraping,
    mode_create_dataset,
    mode_rag_ingest,
    mode_domain_config,
    mode_proxy_auth,
    print_mission_statement,
    select_completed_run,
    sanitize_filename,
    val_float,
    CLR_HEADER,
    CLR_BLUE,
    CLR_CYAN,
    CLR_GREEN,
    CLR_WARNING,
    CLR_FAIL,
    CLR_END,
    CLR_BOLD,
    CLR_UNDERLINE,
)
from cli.cli_wizard_watchdog import mode_continuous_watchdog

__all__ = [
    "run_cli_wizard",
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
    "mode_continuous_watchdog",
    "mode_create_dataset",
    "mode_rag_ingest",
    "mode_domain_config",
    "mode_proxy_auth",
    "print_mission_statement",
    "select_completed_run",
    "sanitize_filename",
    "val_float",
]


def run_cli_wizard():
    """Interactive CLI Wizard loop."""
    while True:
        clear_screen()
        print_banner()
        print(f" {CLR_BOLD}Interactive Operation Modes:{CLR_END}\n")
        print(f"   1) {CLR_GREEN}{CLR_BOLD}General / Broad Scraping{CLR_END} (Search keyword, profile presets)")
        print(f"   2) {CLR_CYAN}{CLR_BOLD}Specified Seed Scraping{CLR_END} (Targeted seed files, high limits)")
        print(f"   3) {CLR_BLUE}{CLR_BOLD}Continuous Watchdog Agent{CLR_END} (Periodic background monitoring)")
        print(f"   4) {CLR_HEADER}{CLR_BOLD}AI Dataset Exporter{CLR_END} (LoRA / Kohya_ss ZIP dataset format)")
        print(f"   5) {CLR_WARNING}{CLR_BOLD}RAG Document Ingest{CLR_END} (Text & document chunk exporter)")
        print(f"   6) {CLR_CYAN}Domain Configuration{CLR_END} (Dynamic per-domain rate limits)")
        print(f"   7) {CLR_BLUE}Proxy & Auth Settings{CLR_END} (Save proxy configuration to .env)")
        print(f"   8) {CLR_FAIL}Exit{CLR_END}\n")

        choice = get_input("Select mode (1-8)", default="1")

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
            mode_domain_config()
        elif choice == "7":
            mode_proxy_auth()
        elif choice == "8":
            print(f"\n{CLR_GREEN}Exiting scrAPE Wizard. Goodbye!{CLR_END}")
            sys.exit(0)

        get_input("\nPress Enter to return to the main menu...")


def main():
    try:
        run_cli_wizard()
    except KeyboardInterrupt:
        print(f"\n{CLR_FAIL}Wizard session terminated by user.{CLR_END}")
        sys.exit(0)


if __name__ == "__main__":
    main()
