import sys
import os
import time
import threading
import subprocess
import webbrowser
from pathlib import Path

import uvicorn
import pystray
import questionary
from PIL import Image, ImageDraw

# Ensure the parent directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Fix for pythonw.exe on Windows where sys.stdout and sys.stderr are None
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')


def create_icon_image():
    """Create a simple generated icon for the system tray."""
    image = Image.new('RGB', (64, 64), color=(11, 13, 12))
    draw = ImageDraw.Draw(image)
    draw.rectangle([16, 16, 48, 48], fill=(255, 85, 0))
    return image


def start_server():
    """Run the uvicorn server in this thread."""
    uvicorn.run("frontend.app:app", host="localhost", port=10001, reload=False, log_level="warning")


def check_and_install_dependencies():
    """Verify and automatically install system dependencies (npm, playwright)."""
    # Only run dependency checks if we are running in an interactive terminal
    if hasattr(sys.stdout, "isatty") and not sys.stdout.isatty():
        return
    if hasattr(sys.stdout, "name") and sys.stdout.name == os.devnull:
        return

    # 1. Check Node.js dependencies for crawlee_bridge
    bridge_dir = ROOT_DIR / "crawlee_bridge"
    node_modules = bridge_dir / "node_modules"
    if bridge_dir.exists() and not node_modules.exists():
        print("📦 Node.js dependencies for crawlee_bridge not found. Installing...")
        try:
            # Check if npm is available
            subprocess.run(["npm", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
            # Run npm install
            print("🚀 Running npm install in crawlee_bridge...")
            subprocess.run(["npm", "install"], cwd=str(bridge_dir), check=True, shell=True)
            print("✅ Node.js dependencies installed successfully!\n")
        except Exception as e:
            print(f"⚠️ Failed to install Node.js dependencies: {e}. Please ensure Node.js and npm are installed and in your PATH.\n")
            time.sleep(2)

    # 2. Check Playwright browser dependencies
    try:
        from playwright.sync_api import sync_playwright
        # Try to launch chromium headlessly to see if binaries are present
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
            except Exception:
                print("🎭 Playwright browser binaries not found. Installing...")
                try:
                    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                    print("✅ Playwright browser binaries installed successfully!\n")
                except Exception as e:
                    print(f"⚠️ Failed to install Playwright browser binaries: {e}\n")
                    time.sleep(2)
    except ImportError:
        pass


def on_open_dashboard(icon, item):
    """Open the web dashboard in the default browser."""
    webbrowser.open("http://localhost:10001/")


def on_quit(icon, item):
    """Stop the system tray and forcefully exit the application."""
    icon.stop()
    sys.exit(0)


def run_tray():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    icon_image = create_icon_image()
    menu = pystray.Menu(
        pystray.MenuItem("Open Dashboard", on_open_dashboard, default=True),
        pystray.MenuItem("Quit", on_quit)
    )
    
    icon = pystray.Icon("scrAPE", icon_image, "scrAPE Watchdog", menu)
    icon.run()


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def main():
    # If running silently via pythonw, skip the menu and go straight to tray.
    # We can detect this by checking if sys.stdout is devnull or an invalid handle,
    # but since we overrode it above, we can check if it's pointing to devnull.
    if hasattr(sys.stdout, "name") and sys.stdout.name == os.devnull:
        run_tray()
        return

    check_and_install_dependencies()

    VERSION = "v0.17.0"
    
    clear_screen()
    print("========================================")
    print(f"  Choose Interface ({VERSION})")
    print("  🚀 Server: http://localhost:10001")
    print("========================================\n")
    
    choice = questionary.select(
        "",
        choices=[
            f"Update to {VERSION} (current: {VERSION})",
            "Web UI (Open in Browser)",
            "Terminal UI (Interactive CLI)",
            "Hide to Tray (Background)",
            "Exit"
        ],
        qmark=">"
    ).ask()

    if not choice or choice == "Exit":
        sys.exit(0)
        
    elif choice.startswith("Update"):
        print("\n[INFO] Update feature coming in a future release.")
        time.sleep(2)
        main()
        
    elif choice == "Web UI (Open in Browser)":
        print("\n[INFO] Starting background server...")
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Give server a moment to bind
        time.sleep(1)
        print("[INFO] Opening browser...")
        webbrowser.open("http://localhost:10001/")
        print("[INFO] Server is running. Press CTRL+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down server...")
            sys.exit(0)
            
    elif choice == "Terminal UI (Interactive CLI)":
        # Launch cli_wizard.py
        subprocess.call([sys.executable, "-m", "src.cli.cli_wizard"])
        
    elif choice == "Hide to Tray (Background)":
        print("\n⌛ Starting background process... (tray icon will appear in ~3s)")
        DETACHED_PROCESS = 0x00000008
        proc = subprocess.Popen(
            [sys.executable.replace("python.exe", "pythonw.exe"), "-m", "src.cli.launcher"],
            creationflags=DETACHED_PROCESS
        )
        print(f"🔔 scrAPE is now running in background (PID: {proc.pid})")
        print("Server: http://localhost:10001\n")
        print("💡 You can close this terminal. Right-click tray icon to quit.")
        time.sleep(2)
        sys.exit(0)

if __name__ == "__main__":
    main()
