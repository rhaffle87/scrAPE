import json
import logging
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin

import httpx

from notifications.notification_manager import NotificationPipeline

LOGGER = logging.getLogger(__name__)

class DomainProfiler:
    """
    Auto-Profiling Engine
    Evaluates unmapped domains, handles auth gates via Telegram relay,
    and performs 3-stage validation for regex rules.
    """
    
    def __init__(self, state_cache=None, notifier: NotificationPipeline | None = None):
        self.state_cache = state_cache
        self.notifier = notifier or NotificationPipeline()
        self.domain_config_path = Path("data/domain_config.json")
        self.rules_config_path = Path("data/url_normalisation_rules.json")
        self.sessions_dir = Path("data/sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.domain_config = {}
        self.rules_config = {}
        self._load_configs()
        
    def _load_configs(self):
        try:
            with open(self.domain_config_path, "r", encoding="utf-8") as f:
                self.domain_config = json.load(f)
        except Exception:
            self.domain_config = {}
            
        try:
            with open(self.rules_config_path, "r", encoding="utf-8") as f:
                self.rules_config = json.load(f)
        except Exception:
            self.rules_config = {}

    def _save_domain_config(self):
        with open(self.domain_config_path, "w", encoding="utf-8") as f:
            json.dump(self.domain_config, f, indent=4)
            
    def _save_rules_config(self):
        with open(self.rules_config_path, "w", encoding="utf-8") as f:
            json.dump(self.rules_config, f, indent=4)
            
    async def evaluate_domain(self, domain: str) -> str:
        """
        Evaluate an unmapped domain.
        Returns:
            "OK": Domain is safe to crawl (config was updated or no action needed).
            "AWAITING_AUTH": Domain is paused for 15 minutes waiting for Telegram cookie relay.
            "SKIPPED": Cooldown active or fatal error.
        """
        # 1. Check cooldown
        if self.state_cache and self.state_cache.is_in_profiler_cooldown(domain):
            LOGGER.debug(f"Auto-Profiler: {domain} is in cooldown, skipping.")
            return "SKIPPED"
            
        # 2. Check if we already have a session for it
        session_file = self.sessions_dir / f"{domain.replace('.', '_')}.json"
        if session_file.exists():
            # Already authorized previously
            self._mark_domain_mapped(domain)
            return "OK"

        LOGGER.info(f"Auto-Profiler: Analyzing unmapped domain {domain}...")
        
        # 3. Stage 1: Network Probe
        target_url = f"https://{domain}/"
        try:
            async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=10.0) as client:
                resp = await client.get(target_url)
                
                if resp.status_code == 429:
                    self._update_rate_limit(domain, 0.5)
                    self._mark_domain_mapped(domain)
                    return "OK"
                elif resp.status_code in (403, 401) or "cloudflare" in resp.text.lower():
                    # Auth gate or Cloudflare detected
                    return await self._handle_auth_gate(domain)
                
                # If successful, do DOM extraction for Stage 1, 2 & 3.
                if resp.status_code == 200:
                    await self._generate_normalisation_rules(domain, resp.text, client)
                    
                self._mark_domain_mapped(domain)
                return "OK"
                
        except Exception as e:
            LOGGER.warning(f"Auto-Profiler: Network probe failed for {domain}: {e}")
            if self.state_cache:
                self.state_cache.set_profiler_cooldown(domain, cooldown_hours=24)
            return "SKIPPED"

    async def _handle_auth_gate(self, domain: str) -> str:
        """Handles the Telegram Interactive Relay for Auth Gates."""
        LOGGER.info(f"Auto-Profiler: Auth Gate detected on {domain}. Requesting cookie via Telegram...")
        
        if self.notifier:
            for p in self.notifier.providers:
                if hasattr(p, 'bot') and p.bot:
                    login_url = f"https://{domain}/login"
                    msg = (
                        f"[ALERT] <b>Auth Gate Detected</b>\n\n"
                        f"<b>Domain:</b> <code>{domain}</code>\n"
                        f"<b>Action Required:</b> Please click the link below to login on your device, export the cookie JSON, and reply.\n"
                        f"-> <a href=\"{login_url}\">Login to {domain}</a>\n\n"
                        f"<b>Command:</b> <code>/auth {domain} [JSON_STRING]</code>\n\n"
                        f"<i>(This domain is paused. You have 15 minutes to reply before it times out.)</i>"
                    )
                    p.bot.send_message(msg)
                    break
            
        # Do not block here. The crawler loop will handle parking the domain
        # and checking for the session file.
        return "AWAITING_AUTH"

    def _update_rate_limit(self, domain: str, rps: float):
        self._load_configs()
        if "rate_limits" not in self.domain_config:
            self.domain_config["rate_limits"] = {}
        self.domain_config["rate_limits"][domain] = rps
        self._save_domain_config()
        LOGGER.info(f"Auto-Profiler: Injected {rps} RPS rate limit for {domain}.")
        
    def _mark_domain_mapped(self, domain: str):
        self._load_configs()
        if "auto_mapped" not in self.domain_config:
            self.domain_config["auto_mapped"] = []
        if domain not in self.domain_config["auto_mapped"]:
            self.domain_config["auto_mapped"].append(domain)
            self._save_domain_config()
            LOGGER.info(f"Auto-Profiler: Marked {domain} as mapped.")

    async def _generate_normalisation_rules(self, domain: str, html: str, client: httpx.AsyncClient):
        """3-Stage Waterfall Verification Pipeline to auto-generate regex rules."""
        try:
            from bs4 import BeautifulSoup
            import difflib
            
            soup = BeautifulSoup(html, "html.parser")
            a_tags = soup.find_all("a", href=True)
            
            for a in a_tags:
                if not hasattr(a, "find"):
                    continue
                img = a.find("img", src=True) # type: ignore
                if not img:
                    continue
                    
                href = str(a.get("href")) # type: ignore
                src = str(img.get("src")) # type: ignore
                
                # Stage 1: Structural DOM Context Analysis (The Fast Filter)
                is_ad = False
                parent = a.parent
                levels = 0
                while parent and levels < 3:
                    class_id_str = str(parent.get("class", "")) + " " + str(parent.get("id", ""))
                    if re.search(r"(ad|sponsor|promo|banner|sidebar)", class_id_str, re.I):
                        is_ad = True
                        break
                    parent = parent.parent
                    levels += 1
                    
                if is_ad:
                    continue
                    
                # Standardize URLs
                href = urljoin(f"https://{domain}/", href)
                src = urljoin(f"https://{domain}/", src)
                    
                src_path = urlparse(src).path
                href_path = urlparse(href).path
                
                src_filename = src_path.split("/")[-1]
                href_filename = href_path.split("/")[-1]
                
                if not src_filename or not href_filename:
                    continue
                    
                # Stage 2: Strict String Similarity
                similarity = difflib.SequenceMatcher(None, src_filename, href_filename).ratio()
                if similarity < 0.8:
                    continue
                    
                if src_filename == href_filename:
                    continue # No normalization needed if they are identical
                    
                # Basic inference: src has a suffix that href doesn't have (e.g. _thumb, -300x300, _280px)
                # Find what is in src but not in href
                src_stem = src_filename.rsplit(".", 1)[0]
                href_stem = href_filename.rsplit(".", 1)[0]
                
                if src_stem.startswith(href_stem) and len(src_stem) > len(href_stem):
                    suffix = src_stem[len(href_stem):]
                    
                    if not suffix:
                        continue
                        
                    # Stage 3: Pre-flight Head Verification (The Ultimate Truth)
                    # We guess the high-res URL (which is just href)
                    # But the point of the rule is to map future src -> href
                    
                    # Verify href is a valid media file
                    try:
                        head_resp = await client.head(href, follow_redirects=True, timeout=5.0)
                        if head_resp.status_code == 200:
                            content_type = head_resp.headers.get("content-type", "").lower()
                            if content_type.startswith("image/") or content_type.startswith("video/"):
                                # Passed Stage 3! Add the rule
                                escaped_suffix = re.escape(suffix)
                                escaped_domain = re.escape(domain)
                                
                                rule = {
                                    "description": f"Auto-generated rule for {domain} stripping {suffix}",
                                    "pattern": f"({escaped_domain}/.*?){escaped_suffix}(\\.[a-zA-Z0-9]{{3,4}})$",
                                    "replacement": "\\1\\2"
                                }
                                
                                # Avoid adding duplicates
                                existing_patterns = [r.get("pattern") for r in self.rules_config.get("rules", [])]
                                if rule["pattern"] not in existing_patterns:
                                    if "rules" not in self.rules_config:
                                        self.rules_config["rules"] = []
                                    self.rules_config["rules"].append(rule)
                                    self._save_rules_config()
                                    LOGGER.info(f"Auto-Profiler: Injected new URL normalization rule for {domain}")
                                    
                                # Only need to find one solid rule per domain usually
                                break
                    except Exception as e:
                        LOGGER.debug(f"Auto-Profiler: Stage 3 HEAD request failed for {href}: {e}")
                        
        except Exception as e:
            LOGGER.warning(f"Auto-Profiler: Rule generation failed for {domain}: {e}")
