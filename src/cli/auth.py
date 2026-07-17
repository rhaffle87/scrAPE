import json
from pathlib import Path
from utils.logger import get_logger
from utils.session import SessionManager

logger = get_logger(__name__)

def perform_interactive_login(domain: str) -> None:
    """Launch a headful browser to let the user log in manually, then save cookies."""
    try:
        import undetected_chromedriver as uc
    except ImportError:
        logger.error("undetected-chromedriver is not installed. Cannot perform interactive login.")
        return

    logger.info("Launching headful browser for %s...", domain)
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        driver.get(f"https://{domain}")
        
        print("\n" + "="*80)
        print(f" INTERACTIVE LOGIN: {domain}")
        print(" 1. Please log in to the website in the opened browser window.")
        print(" 2. Complete any captchas or 2FA if required.")
        print(" 3. When you are fully logged in and see your dashboard/feed,")
        print("    return to this terminal and press ENTER.")
        print("="*80 + "\n")
        
        input("Press ENTER to save cookies and exit...")
        
        cookies = driver.get_cookies()
        cookies_dict = {c["name"]: c["value"] for c in cookies}
        
        if not cookies_dict:
            logger.warning("No cookies were captured! Session may not be authenticated.")
        else:
            manager = SessionManager()
            existing = manager.load_session(domain) or {}
            existing.update(cookies_dict)
            manager.save_session(domain, existing)
            logger.info("Successfully saved %d cookies for %s.", len(cookies_dict), domain)
        
    except Exception as e:
        logger.error("Failed during interactive login: %s", e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def import_cookies(domain: str, file_path: Path) -> None:
    """Import cookies from a JSON or Netscape format file."""
    if not file_path.exists():
        logger.error("Cookie file not found: %s", file_path)
        return
        
    cookies_dict = {}
    content = file_path.read_text(encoding="utf-8").strip()
    
    # Try parsing as JSON first
    if content.startswith("[") or content.startswith("{"):
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                # Simple name: value mapping
                cookies_dict = data
            elif isinstance(data, list):
                # List of cookie objects (e.g. from EditThisCookie)
                for c in data:
                    if "name" in c and "value" in c:
                        cookies_dict[c["name"]] = c["value"]
        except json.JSONDecodeError:
            pass
            
    # Try Netscape format if dictionary is still empty
    if not cookies_dict:
        for line in content.splitlines():
            line = line.strip()
            # Netscape cookies.txt files often have HTTPOnly comments, skip them
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            # Netscape format has 7 fields: domain, flag, path, secure, expiration, name, value
            if len(parts) >= 7:
                name = parts[5]
                value = parts[6]
                cookies_dict[name] = value

    if not cookies_dict:
        logger.error("Failed to parse cookies from %s. Unsupported format or empty file.", file_path)
        return
        
    manager = SessionManager()
    existing = manager.load_session(domain) or {}
    existing.update(cookies_dict)
    manager.save_session(domain, existing)
    
    logger.info("Successfully imported %d cookies for %s from %s.", len(cookies_dict), domain, file_path)
