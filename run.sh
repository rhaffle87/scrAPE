#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT"

# If arguments were passed, forward directly to CLI main.py
if [ "$#" -gt 0 ]; then
    python3 -m src.cli.main "$@"
    exit $?
fi

while true; do
    clear
    echo "========================================================================"
    echo "                  scrAPE — UNIFIED MASTER LAUNCHER                      "
    echo "========================================================================"
    echo ""
    echo "  [1] Launch WebUI Dashboard & Cockpit (FastAPI + HTMX)"
    echo "  [2] Launch Interactive CLI Scrape Wizard"
    echo "  [3] Interactive Domain Login (--login)"
    echo "  [4] Install Package & Register Global 'scrape' Command"
    echo "  [5] Launch Continuous Watchdog Agent (monitor_agent.py)"
    echo "  [6] Launch Automated Release Wizard (release.py)"
    echo "  [0] Exit"
    echo ""
    echo "========================================================================"
    read -p "Select option [0-6]: " CHOICE

    case "$CHOICE" in
        1)
            echo ""
            echo "Starting WebUI Dashboard on http://localhost:10001 ..."
            python3 -m frontend.app
            read -p "Press Enter to return to menu..."
            ;;
        2)
            echo ""
            echo "Starting Interactive CLI Wizard..."
            python3 -m src.cli.cli_wizard
            read -p "Press Enter to return to menu..."
            ;;
        3)
            echo ""
            read -p "Enter domain to login (e.g. example.com): " LOGIN_DOMAIN
            if [ -n "$LOGIN_DOMAIN" ]; then
                python3 -m src.cli.main --login "$LOGIN_DOMAIN"
            fi
            read -p "Press Enter to return to menu..."
            ;;
        4)
            echo ""
            echo "Installing package in editable mode..."
            pip install -e .
            read -p "Press Enter to return to menu..."
            ;;
        5)
            echo ""
            read -p "Enter keyword to monitor: " WATCHDOG_KW
            read -p "Enter seed file path (optional, press Enter to skip): " WATCHDOG_SEED
            read -p "Enter check interval in seconds [default: 60]: " WATCHDOG_INT
            if [ -z "$WATCHDOG_INT" ]; then WATCHDOG_INT=60; fi

            if [ -n "$WATCHDOG_KW" ]; then
                if [ -n "$WATCHDOG_SEED" ]; then
                    python3 -m src.cli.monitor_agent --keyword "$WATCHDOG_KW" --seed-file "$WATCHDOG_SEED" --interval "$WATCHDOG_INT" --use-state-cache
                else
                    python3 -m src.cli.monitor_agent --keyword "$WATCHDOG_KW" --interval "$WATCHDOG_INT" --use-state-cache
                fi
            else
                echo "Keyword is required to launch Watchdog Agent."
            fi
            read -p "Press Enter to return to menu..."
            ;;
        6)
            echo ""
            python3 -m src.cli.release
            read -p "Press Enter to return to menu..."
            ;;
        0)
            exit 0
            ;;
        *)
            ;;
    esac
done
