"""
browser_client.py — Browser Automation Fallback Mixin for HttpClient.

Provides browser automation fallback execution methods for WAF bypass and stealth scraping:
  - Crawlee (Cheerio & Puppeteer)
  - DrissionPage
  - Helium (Chrome & Firefox)
  - undetected-chromedriver (UC)
  - Camoufox
  - Nodriver
  - FlareSolverr
  - Crawl4AI
"""

from __future__ import annotations

import sys
import time
import re
import typing
from pathlib import Path
from urllib.parse import urlparse

from config import (
    STEALTH_HEADFUL,
    FORCE_HEADLESS,
    FLARESOLVERR_URL,
)

import threading
from typing import ClassVar

__all__ = ["BrowserClientMixin"]


class BrowserClientMixin:
    """Mixin class providing browser automation fallback methods to HttpClient."""

    _flaresolverr_lock: ClassVar[threading.Lock] = threading.Lock()
    _flaresolverr_online: ClassVar[bool | None] = None

    captcha_provider: str | typing.Any = None
    captcha_key: str | None = None
    max_captcha_spend: float = 0.0
    session_manager: typing.Any = None

    def get_proxy(self) -> str | None:
        return None

    def _hostname(self, url: str) -> str:
        return urlparse(url).netloc.lower()

    def _get_browser_profile_path(self, host: str) -> str | None:
        return None

    def _is_cloudflare_challenge(self, html: str) -> bool:
        return False

    def _is_blocked_page(self, html: str, url: str = "") -> bool:
        return False

    def _fallback_lock_for(self, host: str) -> typing.Any:
        return threading.Lock()

    def _get_with_crawlee_cheerio(self, url: str) -> tuple[str, list[dict]]:
        """Fetch URL using Crawlee Cheerio (fast parser)"""
        from network.crawlee_client import CrawleeClient
        client = CrawleeClient()
        html = client.get_with_cheerio(url, proxy=self.get_proxy())
        return html, []

    def _get_with_crawlee_puppeteer(self, url: str) -> tuple[str, list[dict]]:
        """Fetch URL using Crawlee Puppeteer (stealth browser)"""
        from network.crawlee_client import CrawleeClient
        client = CrawleeClient()
        host = self._hostname(url)
        profile_path = self._get_browser_profile_path(host)
        html, cookies = client.get_with_puppeteer(url, proxy=self.get_proxy(), user_data_dir=profile_path)
        return html, cookies

    def _get_with_drissionpage(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using DrissionPage to bypass Turnstile/WAF locally."""
        from monitoring.logger import get_logger

        logger = get_logger(__name__)

        try:
            from network.browser_pool import BrowserPoolManager
        except ImportError as e:
            logger.error("BrowserPoolManager not found: %s", e)
            raise e

        proxy = self.get_proxy()
        host = self._hostname(url)

        # Determine GUI platform
        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos
        headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))

        logger.info("Requesting pooled DrissionPage for %s (headless=%s)", url, headless_mode)

        try:
            with BrowserPoolManager.get_drission_page(proxy, headless_mode) as page:
                # Fetch URL and wait for redirection/challenge solving with fast-fail timeout
                page.get(url, timeout=20.0)

                # Fast-fail wait for Turnstile challenge to be solved
                solve_timeout = 30.0
                start_time = time.time()
                clicked = False
                while time.time() - start_time < solve_timeout:
                    html = page.html
                    if not self._is_cloudflare_challenge(html):
                        break

                    # Active Turnstile clicker
                    try:
                        import random
                        # Inject human-like mouse jitter
                        page.actions.move(random.randint(50, 200), random.randint(50, 200))

                        if not clicked:
                            cf_iframe = page.ele('xpath://iframe', timeout=1) or page.ele('#jvye6', timeout=1)
                            if cf_iframe:
                                logger.info("Found Cloudflare Turnstile widget/iframe, simulating human hover and click.")
                                page.actions.move_to(cf_iframe).click()
                                clicked = True
                    except Exception as e:
                        logger.debug("Turnstile auto-clicker exception: %s", repr(e))

                    time.sleep(0.5)

                html = page.html
                if self._is_cloudflare_challenge(html):
                    raise TimeoutError("DrissionPage hit Cloudflare challenge timeout.")

                # Trigger lazy-loaded images by scrolling
                logger.info("Scrolling down to trigger lazy loading for %s...", url)
                try:
                    last_height = 0
                    for _ in range(8):  # Max 8 scrolls
                        page.scroll.to_bottom()
                        time.sleep(1.0)
                        new_height = page.run_js("return document.body.scrollHeight")
                        if new_height == last_height:
                            break
                        last_height = new_height
                except Exception as e:
                    logger.debug("DrissionPage scroll failed: %s", e)

                html = page.html

                # Extract cookies
                cookies = page.cookies(all_info=True)
                cookies_list = []
                for c in cookies:
                    cookies_list.append(
                        {
                            "name": c.get("name"),
                            "value": c.get("value"),
                            "domain": c.get("domain") or host,
                            "path": c.get("path") or "/",
                        }
                    )

                return html, cookies_list

        except Exception as e:
            logger.error("DrissionPage request failed: %s", repr(e))
            raise e

        raise RuntimeError("Unreachable code path in _get_with_drissionpage")

    def _get_with_helium(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using Helium as a browser fallback (supports Firefox if Chrome is missing)."""
        from monitoring.logger import get_logger

        logger = get_logger(__name__)

        try:
            import helium
        except ImportError as e:
            logger.error("Helium not installed: %s", e)
            raise e

        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos
        headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))

        logger.info("Launching Helium for %s (headless=%s)", url, headless_mode)

        started = False
        try:
            logger.info("Helium: Trying Chrome browser...")

            from selenium.webdriver.chrome.options import Options as ChromeOptions
            chrome_options = ChromeOptions()

            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            proxy = self.get_proxy()
            if proxy:
                chrome_options.add_argument(f"--proxy-server={proxy}")

            helium.start_chrome(url, headless=headless_mode, options=chrome_options)
            started = True
        except Exception as chrome_err:
            logger.warning(
                "Helium: Chrome browser launch failed: %s. Falling back to Firefox...",
                chrome_err,
            )
            try:
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                firefox_options = FirefoxOptions()
                proxy = self.get_proxy()
                if proxy:
                    firefox_options.add_argument(f"--proxy-server={proxy}")

                helium.start_firefox(url, headless=headless_mode, options=firefox_options)
                started = True
            except Exception as firefox_err:
                logger.error("Helium: Firefox browser launch failed: %s", firefox_err)
                raise RuntimeError(
                    f"Helium failed to start either Chrome or Firefox: {firefox_err}"
                ) from chrome_err

        try:
            driver = helium.get_driver()
            solve_timeout = 30.0
            start_time = time.time()
            while time.time() - start_time < solve_timeout:
                html = driver.page_source
                if not self._is_cloudflare_challenge(html):
                    break
                time.sleep(1.0)

            html = driver.page_source
            if self._is_cloudflare_challenge(html):
                raise TimeoutError("Helium hit Cloudflare challenge timeout.")

            logger.info("Scrolling down to trigger lazy loading for %s...", url)
            try:
                last_height = 0
                for _ in range(8):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.0)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
            except Exception as e:
                logger.debug("Helium scroll failed: %s", e)

            html = driver.page_source

            cookies = driver.get_cookies()
            cookies_list = []
            host = self._hostname(url)
            for c in cookies:
                cookies_list.append(
                    {
                        "name": c.get("name"),
                        "value": c.get("value"),
                        "domain": c.get("domain") or host,
                        "path": c.get("path") or "/",
                    }
                )

            return html, cookies_list

        except Exception as e:
            logger.error("Helium request failed: %s", repr(e))
            raise e
        finally:
            if started:
                try:
                    helium.kill_browser()
                except Exception:
                    pass

    def _get_with_uc(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using undetected-chromedriver as the deepest fallback tier."""
        from monitoring.logger import get_logger

        logger = get_logger(__name__)

        try:
            import undetected_chromedriver as uc

            if not getattr(uc.Chrome, "_patched_quit", False):
                original_quit = uc.Chrome.quit
                def patched_quit(self):
                    try:
                        original_quit(self)
                    except OSError:
                        pass
                uc.Chrome.quit = patched_quit
                uc.Chrome._patched_quit = True

        except ImportError as e:
            logger.error("undetected-chromedriver not installed: %s", e)
            raise e

        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos
        headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))

        logger.info(
            "Launching undetected-chromedriver for %s (headless=%s)", url, headless_mode
        )
        driver = None
        for attempt in range(2):
            try:
                options = uc.ChromeOptions()
                if headless_mode:
                    options.add_argument("--headless")
                options.add_argument("--disable-gpu")

                proxy = self.get_proxy()
                if proxy:
                    options.add_argument(f"--proxy-server={proxy}")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

                driver = uc.Chrome(options=options, use_subprocess=True, version_main=150)
                break
            except Exception as driver_err:
                if "session not created" in str(driver_err).lower() and attempt == 0:
                    logger.warning("uc.Chrome session creation failed. Retrying initialization...")
                    time.sleep(2)
                    continue
                raise driver_err

        if driver is None:
            raise RuntimeError("Failed to initialize undetected-chromedriver driver instance.")

        try:
            driver.set_page_load_timeout(30)
            driver.get(url)

            solve_timeout = 25.0
            start_time = time.time()
            capsolver_attempted = False
            while time.time() - start_time < solve_timeout:
                html = driver.page_source
                if not self._is_cloudflare_challenge(html):
                    break
                if self.captcha_provider and self.captcha_key and not capsolver_attempted:
                    success = self._solve_cloudflare_captcha_uc(driver, url)
                    capsolver_attempted = True
                    if success:
                        solve_timeout += 10.0
                time.sleep(1.0)

            html = driver.page_source
            if self._is_cloudflare_challenge(html):
                raise TimeoutError(
                    "undetected-chromedriver hit Cloudflare challenge timeout."
                )

            logger.info("Scrolling down to trigger lazy loading for %s...", url)
            try:
                last_height = 0
                for _ in range(8):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.0)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
            except Exception as e:
                logger.debug("UC scroll failed: %s", e)

            html = driver.page_source

            cookies = driver.get_cookies()
            cookies_list = []
            host = self._hostname(url)
            for c in cookies:
                cookies_list.append(
                    {
                        "name": c.get("name"),
                        "value": c.get("value"),
                        "domain": c.get("domain") or host,
                        "path": c.get("path") or "/",
                    }
                )

            return html, cookies_list

        except Exception as e:
            logger.error("undetected-chromedriver request failed: %s", e)
            raise e
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    def _solve_cloudflare_captcha_uc(self, driver, url: str) -> bool:
        if not self.captcha_provider or not self.captcha_key:
            return False
        from monitoring.logger import get_logger
        logger = get_logger(__name__)

        provider_str = self.captcha_provider if isinstance(self.captcha_provider, str) else getattr(self.captcha_provider, "name", "")
        provider_name = (provider_str or "").lower()
        api_key_str = self.captcha_key or ""
        spend_limit = float(getattr(self, "max_captcha_spend", 0.0) or 0.0)
        provider = None
        if provider_name == "capsolver":
            from captcha.captcha_solvers.capsolver_provider import CapSolverProvider
            provider = CapSolverProvider(api_key=api_key_str, max_spend_per_run=spend_limit)
        elif provider_name == "2captcha":
            from captcha.captcha_solvers.twocaptcha_provider import TwoCaptchaProvider
            provider = TwoCaptchaProvider(api_key=api_key_str, max_spend=spend_limit)
        elif provider_name == "anticaptcha":
            from captcha.captcha_solvers.anticaptcha_provider import AntiCaptchaProvider
            provider = AntiCaptchaProvider(api_key=api_key_str, max_spend=spend_limit)
        else:
            logger.warning(f"Unknown captcha provider: {provider_name}")
            return False

        html = driver.page_source
        sitekey = None

        match = re.search(r'data-sitekey=["\']([^"\']+)["\']', html)
        if match:
            sitekey = match.group(1)
        if not sitekey:
            match = re.search(r'sitekey:\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if match:
                sitekey = match.group(1)

        if not sitekey:
            logger.warning(f"{provider_name}: Cloudflare Turnstile detected, but sitekey not found in HTML.")
            return False

        logger.info(f"{provider_name}: Solving Turnstile for sitekey {sitekey}...")
        try:
            token = provider.solve_turnstile(website_url=url, website_key=sitekey, timeout=60)
            if not token:
                logger.warning(f"{provider_name}: No token returned in solution.")
                return False

            logger.info(f"{provider_name}: Injecting token...")
            script = f"""
            let input = document.querySelector('[name="cf-turnstile-response"]');
            if (input) {{
                input.value = "{token}";
                let form = input.closest('form');
                if (form) {{
                    form.submit();
                    return true;
                }}
            }}

            if (window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients) {{
                for (let c in window.___grecaptcha_cfg.clients) {{
                    let client = window.___grecaptcha_cfg.clients[c];
                    for (let k in client) {{
                        if (client[k] && client[k].callback) {{
                            client[k].callback("{token}");
                            return true;
                        }}
                    }}
                }}
            }}

            if (window.turnstile && typeof window.turnstile.getResponse === 'function') {{
                let t_input = document.querySelector('input[name="cf-turnstile-response"]');
                if (t_input) {{
                    t_input.value = "{token}";
                }}
            }}
            return false;
            """
            success = driver.execute_script(script)
            if success:
                logger.info(f"{provider_name}: Token injected and form submitted.")
                return True
            else:
                logger.warning(f"{provider_name}: Failed to locate cf-turnstile-response input or form to submit.")
                return False
        except Exception as e:
            logger.error(f"{provider_name} API failed: {repr(e)}")
            return False

    def _get_with_camoufox(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using Camoufox stealth browser with fingerprint & headful escalation tuning."""
        from monitoring.logger import get_logger
        logger = get_logger(__name__)

        try:
            from camoufox.sync_api import Camoufox
        except ImportError:
            logger.warning("Camoufox library is not installed.")
            raise Exception("Camoufox library is not installed")

        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos
        headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))

        camou_os = "win" if is_windows else ("mac" if is_macos else "lin")

        def _fetch_camou(is_headless: bool) -> tuple[str, list[dict]]:
            logger.info("Launching Camoufox for %s (headless=%s, os=%s)", url, is_headless, camou_os)
            host = self._hostname(url)
            profile_path = self._get_browser_profile_path(host)
            kwargs = {
                "headless": is_headless,
                "os": camou_os,
                "humanize": True,
                "window_size": (1920, 1080),
                "user_data_dir": profile_path,
            }
            with Camoufox(**kwargs) as browser:
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=30000)

                if is_headless and self._is_cloudflare_challenge(page.content()):
                    raise TimeoutError("Camoufox headless hit Cloudflare Turnstile challenge.")

                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                except Exception:
                    pass

                html = page.content()
                cookies = page.context.cookies()

                cookie_list = []
                host = self._hostname(url)
                for c in cookies:
                    cookie_list.append(
                        {
                            "name": c.get("name"),
                            "value": c.get("value"),
                            "domain": c.get("domain") or host,
                            "path": c.get("path") or "/",
                        }
                    )
                return html, cookie_list

        try:
            return _fetch_camou(headless_mode)
        except Exception as exc:
            if headless_mode and is_local_gui and not FORCE_HEADLESS:
                logger.warning(
                    "\n"
                    "========================================================================\n"
                    "CAMOUFOX HEADLESS WAF CHALLENGE ON: %s\n"
                    "Escalating Camoufox to HEADFUL (visible) mode for 20 seconds.\n"
                    "Please solve/click the Turnstile checkbox if prompted in the window.\n"
                    "========================================================================",
                    url,
                )
                try:
                    return _fetch_camou(False)
                except Exception as headful_exc:
                    logger.error("Camoufox headful escalation failed for %s: %s", url, repr(headful_exc))
                    raise headful_exc
            logger.error("Camoufox request failed: %s", repr(exc))
            raise exc

    def _get_with_nodriver(self, url: str, force_headful: bool = False) -> tuple[str, list[dict]]:
        """Fetch *url* using Nodriver stealth browser for Turnstile bypass.
        Auto-escalates to headful mode if headless challenge fails.
        """
        from monitoring.logger import get_logger
        logger = get_logger(__name__)

        try:
            import nodriver as uc  # type: ignore
        except ImportError:
            logger.warning("Nodriver library is not installed.")
            raise Exception("Nodriver library is not installed")

        import asyncio

        async def _fetch():
            is_windows = sys.platform.startswith("win")
            is_macos = sys.platform == "darwin"
            is_local_gui = is_windows or is_macos
            headless_mode = False if (STEALTH_HEADFUL or force_headful) else (True if FORCE_HEADLESS else (not is_local_gui))

            logger.info("Launching Nodriver for %s (headless=%s, force_headful=%s)", url, headless_mode, force_headful)

            browser = await uc.start(headless=headless_mode)
            try:
                page = await browser.get(url)

                await asyncio.sleep(4.0)

                content = await page.get_content()
                if self._is_cloudflare_challenge(content):
                    logger.info("Cloudflare challenge detected in Nodriver. Attempting interaction...")

                    try:
                        await page.evaluate("window.scrollTo(0, Math.floor(Math.random() * 500));")
                        await asyncio.sleep(1.0)

                        widget = await page.select("iframe[src*='turnstile'], .cf-turnstile")
                        if widget:
                            logger.info("Found Turnstile widget. Simulating click...")
                            await widget.click()
                            await asyncio.sleep(4.0)
                    except Exception as interact_err:
                        logger.debug("Nodriver interaction failed: %s", interact_err)

                content = await page.get_content()
                if self._is_cloudflare_challenge(content):
                    if headless_mode and is_local_gui and not FORCE_HEADLESS:
                        logger.warning("Nodriver failed Cloudflare challenge in headless mode. Escalating to headful mode.")
                        raise TimeoutError("Nodriver hit Cloudflare challenge (headless mode).")
                    elif not headless_mode:
                        logger.warning("Nodriver failed Cloudflare challenge even in headful mode.")
                        raise TimeoutError("Nodriver hit Cloudflare challenge (headful mode).")
                    else:
                        raise TimeoutError("Nodriver hit Cloudflare challenge (non-GUI environment).")

                cookies_str = str(await page.evaluate("document.cookie"))
                cookies = []
                host = self._hostname(url)
                if cookies_str:
                    for c_pair in cookies_str.split(";"):
                        c_pair = c_pair.strip()
                        if "=" in c_pair:
                            name, val = c_pair.split("=", 1)
                            cookies.append({"name": name, "value": val, "domain": host, "path": "/"})

                return content, cookies
            finally:
                browser.stop()

        try:
            return asyncio.run(_fetch())
        except TimeoutError as exc:
            if not force_headful and "headless mode" in str(exc):
                return self._get_with_nodriver(url, force_headful=True)
            logger.error("Nodriver request failed: %s", repr(exc))
            raise exc
        except Exception as exc:
            logger.error("Nodriver request failed: %s", repr(exc))
            raise exc

    def _get_with_flaresolverr(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using FlareSolverr proxy service with session reuse & proxy forwarding."""
        import httpx
        from monitoring.logger import get_logger
        logger = get_logger(__name__)

        fs_url = FLARESOLVERR_URL or "http://127.0.0.1:8191/v1"

        with self.__class__._flaresolverr_lock:
            if self.__class__._flaresolverr_online is False:
                logger.warning("FlareSolverr service is offline (previous ping failed). Skipping FlareSolverr fallback.")
                raise Exception("FlareSolverr service is offline")

        host = self._hostname(url)
        domain_slug = re.sub(r"[^\w\-]", "_", host)
        session_id = f"session_{domain_slug}"

        proxy = self.get_proxy()
        payload: dict[str, typing.Any] = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
            "session": session_id,
        }
        if proxy:
            payload["proxy"] = {"url": proxy}

        logger.info("Sending request to FlareSolverr at %s for %s (session=%s)", fs_url, url, session_id)

        try:
            with httpx.Client(timeout=65.0) as client:
                if self.__class__._flaresolverr_online is None:
                    ping_urls = [fs_url, "http://localhost:8191/v1", "http://127.0.0.1:8191/v1"]
                    ping_success = False
                    active_url = fs_url
                    for p_url in dict.fromkeys(ping_urls):
                        try:
                            base_url = p_url.rsplit("/v1", 1)[0]
                            ping_res = client.get(base_url or p_url, timeout=3.0)
                            ping_res.raise_for_status()
                            ping_success = True
                            active_url = p_url
                            break
                        except Exception:
                            continue

                    if not ping_success:
                        try:
                            import subprocess
                            logger.info("FlareSolverr unreachable. Attempting background docker start flaresolverr...")
                            subprocess.Popen(  # nosec B603 B607
                                ["docker", "start", "flaresolverr"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                            time.sleep(3.5)
                            for p_url in dict.fromkeys(ping_urls):
                                try:
                                    base_url = p_url.rsplit("/v1", 1)[0]
                                    ping_res = client.get(base_url or p_url, timeout=3.0)
                                    ping_res.raise_for_status()
                                    ping_success = True
                                    active_url = p_url
                                    break
                                except Exception:
                                    continue
                        except Exception as docker_err:
                            logger.debug("Auto-starting FlareSolverr container failed: %s", docker_err)

                    if ping_success:
                        fs_url = active_url
                        with self.__class__._flaresolverr_lock:
                            self.__class__._flaresolverr_online = True
                    else:
                        with self.__class__._flaresolverr_lock:
                            self.__class__._flaresolverr_online = False
                        logger.warning("FlareSolverr health-check failed at %s. Disabling FlareSolverr.", fs_url)
                        raise Exception("FlareSolverr health-check failed")

                res = client.post(fs_url, json=payload)
                res.raise_for_status()
                data = res.json()

                if data.get("status") == "ok":
                    sol = data.get("solution", {})
                    html = sol.get("response", "")
                    raw_cookies = sol.get("cookies", [])
                    cookie_list = []
                    for c in raw_cookies:
                        cookie_list.append(
                            {
                                "name": c.get("name"),
                                "value": c.get("value"),
                                "domain": c.get("domain") or host,
                                "path": c.get("path") or "/",
                            }
                        )
                    return html, cookie_list
                else:
                    msg = data.get("message", "Unknown FlareSolverr error")
                    logger.warning("FlareSolverr returned status '%s': %s", data.get("status"), msg)
                    raise Exception(f"FlareSolverr error: {msg}")
        except Exception as exc:
            logger.error("FlareSolverr request failed: %s", repr(exc))
            raise exc

    def _get_with_crawl4ai(self, url: str) -> tuple[str, list[dict]] | str:
        """Fetch *url* via headless/headful browser, escalating through two stealth tiers."""
        from network.http_client import _apply_playwright_channel_patch, _get_platform_user_agent, _run_coroutine_sync

        _apply_playwright_channel_patch()

        import crawl4ai.async_webcrawler

        crawl4ai.async_webcrawler.is_blocked = lambda status_code, html, error_message=None: (False, "")

        from crawl4ai import (
            AsyncWebCrawler,
            BrowserConfig,
            CrawlerRunConfig,
            CacheMode,
            UndetectedAdapter,
        )
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
        from monitoring.logger import get_logger

        logger = get_logger(__name__)

        async def _run_tier(strategy, run_config) -> tuple[str, list[dict]]:
            async with AsyncWebCrawler(crawler_strategy=strategy) as crawler:
                res = await crawler.arun(url=url, config=run_config)
                if res and res.success:
                    cookies = []
                    try:
                        bm = crawler.crawler_strategy.browser_manager
                        for context in bm.contexts_by_config.values():
                            try:
                                ctx_cookies = await context.cookies()
                                cookies.extend(ctx_cookies)
                            except Exception as exc:
                                logger.debug("Failed to extract cookies from Crawl4AI context: %s", exc)
                    except Exception as exc:
                        logger.debug("Failed to access Crawl4AI browser manager: %s", exc)
                    return res.html, cookies
                raise Exception(res.error_message if res else "Unknown crawler error")

        async def _run_crawler() -> tuple[str, list[dict]]:
            from monitoring.logger import get_logger

            logger = get_logger(__name__)

            parsed = urlparse(url)
            host = parsed.netloc or parsed.hostname or ""
            domain_slug = re.sub(r"[^\w\-]", "_", host)
            raw_profile = self._get_browser_profile_path(host)
            profile_path = Path(raw_profile) if raw_profile else None

            is_windows = sys.platform.startswith("win")
            is_macos = sys.platform == "darwin"
            is_local_gui = is_windows or is_macos
            headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))

            session_cookies = self.session_manager.load_session(host) or {}
            playwright_cookies = []
            for k, v in session_cookies.items():
                playwright_cookies.append(
                    {"name": k, "value": v, "domain": host, "path": "/"}
                )

            run_config = CrawlerRunConfig(
                word_count_threshold=0,
                cache_mode=CacheMode.BYPASS,
                magic=True,
                simulate_user=True,
                override_navigator=True,
                delay_before_return_html=6.0,
                page_timeout=30000,
                session_id=f"session_{domain_slug}",
                js_code="""
                const scrollInterval = setInterval(() => {
                    window.scrollTo(0, document.body.scrollHeight);
                }, 1000);
                setTimeout(() => clearInterval(scrollInterval), 5000);
                """
            )

            async def _run_with_chrome_fallback(
                headless: bool, enable_stealth: bool, browser_adapter=None, run_cfg=None
            ) -> tuple[str, list[dict]]:
                proxy_val = self.get_proxy()

                def _make_browser_cfg(channel_opt=None):
                    kwargs = {
                        "browser_type": "chromium",
                        "headless": headless,
                        "verbose": False,
                        "enable_stealth": enable_stealth,
                        "user_agent": _get_platform_user_agent(),
                        "extra_args": ["--disable-gpu"] if headless else [],
                        "use_persistent_context": True,
                        "cookies": playwright_cookies,
                    }
                    if profile_path:
                        kwargs["user_data_dir"] = str(profile_path.resolve())
                    if channel_opt:
                        kwargs["channel"] = channel_opt
                        kwargs["chrome_channel"] = channel_opt
                    if proxy_val:
                        kwargs["proxy"] = proxy_val
                    return BrowserConfig(**kwargs)

                def _make_strategy(b_cfg):
                    kwargs = {"browser_config": b_cfg}
                    if browser_adapter is not None:
                        kwargs["browser_adapter"] = browser_adapter
                    return AsyncPlaywrightCrawlerStrategy(**kwargs)

                try:
                    cfg = _make_browser_cfg("chrome")
                    strat = _make_strategy(cfg)
                    return await _run_tier(strat, run_cfg)
                except Exception as exc:
                    logger.warning(
                        "Crawl4AI fallback run with channel='chrome' failed: %s. Retrying with default Playwright Chromium...",
                        exc,
                    )
                    cfg_fallback = _make_browser_cfg()
                    strat_fallback = _make_strategy(cfg_fallback)
                    return await _run_tier(strat_fallback, run_cfg)

            logger.info(
                "Crawl4AI Fallback: Trying Tier 1 (Standard Stealth) for %s...", url
            )
            try:
                html, cookies = await _run_with_chrome_fallback(
                    headless=headless_mode,
                    enable_stealth=True,
                    browser_adapter=None,
                    run_cfg=run_config,
                )
                if not self._is_blocked_page(html, url):
                    logger.info("Crawl4AI Tier 1 succeeded for %s.", url)
                    return html, cookies
                logger.warning(
                    "Crawl4AI Tier 1 hit a block or challenge for %s. Escalating to Tier 2...",
                    url,
                )
            except Exception as exc:
                logger.warning(
                    "Crawl4AI Tier 1 failed for %s: %s. Escalating to Tier 2...",
                    url,
                    exc,
                )

            is_windows = sys.platform.startswith("win")
            is_macos = sys.platform == "darwin"
            is_local_gui = is_windows or is_macos
            headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))

            if not headless_mode:
                logger.warning(
                    "\n"
                    "========================================================================\n"
                    "CLOUDFLARE TURNSTILE DETECTED ON: %s\n"
                    "Running Browser in HEADFUL (visible) mode for 20 seconds.\n"
                    "Please solve/click the Turnstile checkbox if prompted in the window.\n"
                    "========================================================================",
                    url,
                )
            else:
                logger.info(
                    "CLOUDFLARE TURNSTILE DETECTED ON: %s - Running browser in HEADLESS mode.",
                    url,
                )

            run_config_2 = CrawlerRunConfig(
                word_count_threshold=0,
                cache_mode=CacheMode.BYPASS,
                magic=True,
                simulate_user=True,
                override_navigator=True,
                delay_before_return_html=20.0,
                page_timeout=30000,
                session_id=f"session_{domain_slug}",
                js_code="""
                const scrollInterval = setInterval(() => {
                    window.scrollTo(0, document.body.scrollHeight);
                }, 1000);
                setTimeout(() => clearInterval(scrollInterval), 18000);
                """
            )
            try:
                html, cookies = await _run_with_chrome_fallback(
                    headless=headless_mode,
                    enable_stealth=True,
                    browser_adapter=UndetectedAdapter(),
                    run_cfg=run_config_2,
                )
                if not self._is_blocked_page(html, url):
                    logger.info("Crawl4AI Tier 2 succeeded for %s.", url)
                    return html, cookies
                raise Exception("Crawl4AI Tier 2 hit a block or challenge page.")
            except Exception as exc:
                raise Exception(
                    f"All Crawl4AI fallback tiers failed for {url}: {exc}"
                ) from exc

        parsed_url = urlparse(url)
        host = parsed_url.netloc or parsed_url.hostname or ""
        lock = self._fallback_lock_for(host)
        with lock:
            return _run_coroutine_sync(_run_crawler())
