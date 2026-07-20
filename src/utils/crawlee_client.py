import httpx
import logging
import subprocess
import atexit
import time
from pathlib import Path
import sys
import os

logger = logging.getLogger(__name__)

class CrawleeClient:
    _instance = None
    _process = None
    _port = 10002
    _base_url = f"http://localhost:{_port}"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._start_server()
            atexit.register(cls._instance._stop_server)
        return cls._instance

    def _start_server(self):
        """Starts the Node.js Express server running the Crawlee bridge."""
        if self._is_server_running():
            return
            
        script_path = Path(__file__).parent.parent.parent / "crawlee_bridge" / "index.mjs"
        if not script_path.exists():
            logger.error("Crawlee bridge script not found at %s", script_path)
            return

        logger.info("Starting Crawlee Node.js bridge server on port %d...", self._port)
        
        env = os.environ.copy()
        env["CRAWLEE_PORT"] = str(self._port)
        
        # Open log file for debugging
        self._log_file = open("crawlee_bridge.log", "w")
        self._process = subprocess.Popen(
            ["node", str(script_path)],
            stdout=self._log_file,
            stderr=subprocess.STDOUT,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

        
        # Wait for server to boot
        for _ in range(10):
            if self._is_server_running():
                logger.info("Crawlee bridge server started successfully.")
                return
            time.sleep(1)
        
        logger.error("Failed to start Crawlee bridge server.")

    def _stop_server(self):
        if self._process:
            self._process.terminate()
            self._process = None
            if hasattr(self, '_log_file') and self._log_file:
                self._log_file.close()
            logger.info("Crawlee bridge server stopped.")


    def _is_server_running(self):
        try:
            with httpx.Client(timeout=1.0) as client:
                # A simple GET / to check if port is alive (even if it 404s, it means server is up)
                client.get(self._base_url)
                return True
        except httpx.RequestError:
            return False

    def scrape(self, url: str, mode: str, proxy: str | None = None) -> dict:
        """
        Calls the Crawlee bridge to scrape a URL.
        :param url: The URL to scrape
        :param mode: 'cheerio' or 'puppeteer'
        :param proxy: Optional proxy URL to use
        :return: JSON response from the bridge (contains 'html', 'cookies', 'title')
        """
        if not self._is_server_running():
            self._start_server()

        logger.info("Sending %s request to Crawlee for %s", mode, url)
        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(
                    f"{self._base_url}/scrape",
                    json={"url": url, "mode": mode, "proxy": proxy}
                )
                res.raise_for_status()
                return res.json()
        except httpx.HTTPStatusError as e:
            logger.error("Crawlee bridge returned HTTP %d: %s", e.response.status_code, e.response.text)
            raise e
        except Exception as e:
            logger.error("Crawlee bridge request failed: %s", repr(e))
            raise e

    def get_with_cheerio(self, url: str, proxy: str | None = None) -> str:
        """Returns the HTML string using Cheerio (fast)."""
        data = self.scrape(url, "cheerio", proxy=proxy)
        return data.get("html", "")

    def get_with_puppeteer(self, url: str, proxy: str | None = None) -> tuple[str, list]:
        """Returns the HTML string and cookies list using Puppeteer (stealth)."""
        data = self.scrape(url, "puppeteer", proxy=proxy)
        return data.get("html", ""), data.get("cookies", [])
