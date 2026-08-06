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

from src.config.version import VERSION_TAG as VERSION  # noqa: E402
from src.config import WEBUI_HOST, WEBUI_PORT  # noqa: E402


# Fix for pythonw.exe on Windows where sys.stdout and sys.stderr are None
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# ── Autostart (Windows Registry HKCU — no admin rights required) ─────────────
_AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_AUTOSTART_NAME = "scrAPE"


def _get_autostart_command() -> str:
    """Return the pythonw.exe command used to register autostart."""
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    return f'"{pythonw}" -m src.cli.launcher'


def is_autostart_enabled() -> bool:
    """Return True if the scrAPE autostart entry exists in the registry."""
    if os.name != "nt":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_KEY) as key:
            winreg.QueryValueEx(key, _AUTOSTART_NAME)
            return True
    except (FileNotFoundError, OSError):
        return False


def enable_autostart() -> None:
    """Write the autostart registry entry under HKCU."""
    if os.name != "nt":
        return
    import winreg
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, _AUTOSTART_NAME, 0, winreg.REG_SZ, _get_autostart_command())


def disable_autostart() -> None:
    """Remove the autostart registry entry under HKCU."""
    if os.name != "nt":
        return
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, _AUTOSTART_NAME)
    except (FileNotFoundError, OSError):
        pass  # Already absent, nothing to do


def toggle_autostart(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    """Toggle autostart on/off and refresh the tray menu."""
    if is_autostart_enabled():
        disable_autostart()
    else:
        enable_autostart()
    # Rebuild the menu in-place so the checkmark updates immediately
    icon.menu = _build_menu()
    icon.update_menu()

# ─────────────────────────────────────────────────────────────────────────────


def create_icon_image():
    """Create a bold, high-contrast scrAPE tray icon optimized for small display sizes.

    PIL-drawn icons are preferred over loading the .ico file because the .ico
    frames at 256x256 lose all legibility when Windows scales them down to
    the 16-24px tray display size. This hand-drawn version is tuned so that
    the orange / dark / white contrast reads clearly at every tray size.
    """
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Solid orange background — immediately recognizable even at 16px
    draw.rectangle([0, 0, size - 1, size - 1], fill=(255, 85, 0, 255))

    # Dark inner card face — inset 6px on each side
    m = 6
    draw.rectangle([m, m, size - m - 1, size - m - 1], fill=(22, 25, 23, 255))

    # Brow ridge — white thick bar across the upper face
    draw.rectangle([m + 4, m + 8, size - m - 5, m + 17], fill=(244, 244, 240, 255))

    # Left eye socket
    draw.rectangle([m + 4, m + 19, m + 14, m + 28], fill=(0, 0, 0, 255))
    # Right eye socket
    draw.rectangle([size - m - 15, m + 19, size - m - 5, m + 28], fill=(0, 0, 0, 255))

    # Orange pupils (acquisition nodes)
    draw.rectangle([m + 7, m + 22, m + 11, m + 25], fill=(255, 85, 0, 255))
    draw.rectangle([size - m - 12, m + 22, size - m - 8, m + 25], fill=(255, 85, 0, 255))

    # Jaw / muzzle block — orange, lower third
    draw.rectangle([m + 4, m + 30, size - m - 5, m + 42], fill=(255, 85, 0, 255))

    # Nostril slits — small dark rectangles in jaw
    draw.rectangle([m + 10, m + 32, m + 13, m + 38], fill=(22, 25, 23, 255))
    draw.rectangle([size - m - 14, m + 32, size - m - 11, m + 38], fill=(22, 25, 23, 255))

    return image


def start_server():
    """Run the uvicorn server in this thread."""
    uvicorn.run("frontend.app:app", host=WEBUI_HOST, port=WEBUI_PORT, reload=False, log_level="warning")



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
            npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
            subprocess.run([npm_cmd, "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec B603 B607
            # Run npm install
            print("🚀 Running npm install in crawlee_bridge...")
            subprocess.run([npm_cmd, "install"], cwd=str(bridge_dir), check=True)  # nosec B603 B607
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
                print("Playwright browser binaries not found. Installing...")
                try:
                    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)  # nosec B603 B607
                    print("Playwright browser binaries installed successfully!\n")
                except Exception as e:
                    print(f"Failed to install Playwright browser binaries: {e}\n")
                    time.sleep(2)
    except ImportError:
        pass


def on_open_dashboard(icon, item):
    """Open the web dashboard in the default browser."""
    webbrowser.open(f"http://localhost:{WEBUI_PORT}/")



def on_quit(icon, item):
    """Stop the system tray and forcefully exit the application."""
    icon.stop()
    sys.exit(0)


def _build_menu() -> pystray.Menu:
    """Build the tray context menu, reflecting current autostart state."""
    autostart_label = (
        "✓ Auto-start Enabled" if is_autostart_enabled() else "Auto-start Disabled"
    )
    return pystray.Menu(
        pystray.MenuItem(f"scrAPE  (Port {WEBUI_PORT})", None, enabled=False),

        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Dashboard", on_open_dashboard, default=True),
        pystray.MenuItem(autostart_label, toggle_autostart),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit),
    )


def run_tray():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    icon_image = create_icon_image()
    icon = pystray.Icon("scrAPE", icon_image, f"scrAPE - Port {WEBUI_PORT}", _build_menu())
    icon.run()



def clear_screen():
    print("\033[H\033[2J", end="", flush=True)


def main():
    # If running silently via pythonw, skip the menu and go straight to tray.
    # We can detect this by checking if sys.stdout is devnull or an invalid handle,
    # but since we overrode it above, we can check if it's pointing to devnull.
    if hasattr(sys.stdout, "name") and sys.stdout.name == os.devnull:
        run_tray()
        return

    check_and_install_dependencies()
    
    clear_screen()
    print("========================================")
    print(f"  Choose Interface ({VERSION})")
    print(f"  🚀 Server: http://localhost:{WEBUI_PORT}")
    print("========================================\n")

    
    autostart_status = "Enabled ✓" if is_autostart_enabled() else "Disabled"
    choice = questionary.select(
        "",
        choices=[
            f"Update to {VERSION} (current: {VERSION})",
            "Web UI (Open in Browser)",
            "Terminal UI (Interactive CLI)",
            "Release Automation Wizard",
            "Hide to Tray (Background)",
            f"Auto-start on Boot  [{autostart_status}]",
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

    elif choice == "Release Automation Wizard":
        subprocess.call([sys.executable, "-m", "src.cli.release"])  # nosec B603 B607
        main()
        
    elif choice == "Web UI (Open in Browser)":
        print("\n[INFO] Starting background server...")
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Give server a moment to bind
        time.sleep(1)
        print("[INFO] Opening browser...")
        webbrowser.open(f"http://localhost:{WEBUI_PORT}/")
        print("[INFO] Server is running. Press CTRL+C to exit.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down server...")
            sys.exit(0)
            
    elif choice == "Terminal UI (Interactive CLI)":
        # Launch cli_wizard.py
        subprocess.call([sys.executable, "-m", "src.cli.cli_wizard"])  # nosec B603 B607

    elif choice.startswith("Auto-start on Boot"):
        if is_autostart_enabled():
            disable_autostart()
            print("\n✅ Auto-start disabled. scrAPE will NOT run on next boot.")
        else:
            enable_autostart()
            print("\n✅ Auto-start enabled. scrAPE will launch silently on next boot.")
        time.sleep(1.5)
        main()
        
    elif choice == "Hide to Tray (Background)":
        print("\n⌛ Starting background process... (tray icon will appear in ~3s)")
        DETACHED_PROCESS = 0x00000008
        proc = subprocess.Popen(  # nosec B603 B607
            [sys.executable.replace("python.exe", "pythonw.exe"), "-m", "src.cli.launcher"],
            creationflags=DETACHED_PROCESS
        )
        print(f"🔔 scrAPE is now running in background (PID: {proc.pid})")
        print(f"Server: http://localhost:{WEBUI_PORT}\n")

        print("💡 You can close this terminal. Right-click tray icon to quit.")
        time.sleep(2)
        sys.exit(0)

if __name__ == "__main__":
    main()
