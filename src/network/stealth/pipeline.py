from __future__ import annotations

from typing import Any
from monitoring.logger import get_logger
from .base import StealthResponse, StealthStrategy, _StrategyCircuitBreaker
from .strategies import (
    HttpxStrategy,
    CurlCffiStrategy,
    CrawleeStrategy,
    Crawl4AIStrategy,
    DrissionPageStrategy,
    HeliumStrategy,
    FlareSolverrStrategy,
    NodriverStrategy,
    CamoufoxStrategy,
)

logger = get_logger(__name__)


class StealthPipeline:
    """Orchestrates sequential execution of StealthStrategy instances with per-tier circuit-breaking."""

    def __init__(self, strategies: list[StealthStrategy] | None = None) -> None:
        from captcha.captcha_strategy import ThirdPartyCaptchaStrategy

        self.circuit_breaker = _StrategyCircuitBreaker()
        if strategies is not None:
            self.strategies = strategies
        else:
            self.strategies = [
                HttpxStrategy(),
                CurlCffiStrategy(),
                ThirdPartyCaptchaStrategy(),
                CrawleeStrategy(),
                Crawl4AIStrategy(),
                DrissionPageStrategy(),
                HeliumStrategy(),
                FlareSolverrStrategy(),
                NodriverStrategy(),
                CamoufoxStrategy(),
            ]

    def get_ordered_strategies(self, host: str, client: Any = None, preferred_engine: str | None = None) -> list[StealthStrategy]:
        """Return strategies re-ordered according to preferred_engine hint if specified or cached in client."""
        ordered = list(self.strategies)
        engine_hint = preferred_engine
        if not engine_hint and client and hasattr(client, "_preferred_engine_by_host"):
            engine_hint = client._preferred_engine_by_host.get(host)
        if engine_hint:
            preferred_name = engine_hint.lower()
            pref_matches = [s for s in ordered if s.name.lower() == preferred_name]
            other = [s for s in ordered if s.name.lower() != preferred_name]
            ordered = pref_matches + other
        return ordered

    def execute(
        self, url: str, client: Any, skip_httpx: bool = False, preferred_engine: str | None = None
    ) -> StealthResponse:
        from network.http_client import ScraperBypassError
        from monitoring.logger import get_logger

        logger = get_logger(__name__)
        host = client._hostname(url)
        ordered_strategies = self.get_ordered_strategies(host, client=client, preferred_engine=preferred_engine)

        valid_strategies = []
        cf_blocked = False
        if client and hasattr(client.__class__, "_cloudflare_blocked_hosts"):
            cf_blocked = host in client.__class__._cloudflare_blocked_hosts

        for strategy in ordered_strategies:
            if skip_httpx and strategy.name == "httpx":
                continue

            if cf_blocked and strategy.name in ("crawlee", "crawl4ai", "httpx", "curl_cffi"):
                logger.debug("Skipping strategy '%s' because host '%s' is Cloudflare-blocked", strategy.name, host)
                continue

            if not strategy.is_available() or not strategy.can_handle(url, host):
                continue

            if self.circuit_breaker.is_cooling_down(strategy.name, host):
                logger.debug(
                    "Skipping strategy '%s' for host '%s' due to active circuit breaker",
                    strategy.name,
                    host,
                )
                continue
                
            valid_strategies.append(strategy)

        if not valid_strategies:
            raise ScraperBypassError(f"No available stealth fallback tiers for {url}")

        def _run_strategy(strategy: StealthStrategy) -> StealthResponse | None:
            logger.info("Attempting stealth fallback tier '%s' for %s", strategy.name, url)
            try:
                res = strategy.execute(url, client)
                if res is not None and res.status_code < 400:
                    return res
            except Exception as e:
                logger.debug("Strategy '%s' execution error on %s: %s", strategy.name, url, e)
            return None

        # Sequential fallback execution
        for strategy in valid_strategies:
            res = _run_strategy(strategy)
            
            if res is not None:
                try:
                    from monitoring.telemetry import broadcast_telemetry_event
                    broadcast_telemetry_event("waf_bypass", {
                        "strategy": strategy.name,
                        "host": host,
                        "url": url,
                        "status_code": res.status_code
                    })
                except Exception as e:
                    logger.debug("Failed to emit waf_bypass telemetry: %s", e)

                self.circuit_breaker.record_success(strategy.name, host)
                with client._waf_solve_lock:
                    client._waf_solve_counts[strategy.name] = (
                        client._waf_solve_counts.get(strategy.name, 0) + 1
                    )
                if hasattr(client, "_preferred_engine_by_host"):
                    with client._preferred_engine_lock:
                        client._preferred_engine_by_host[host] = strategy.name

                # Auto-persist harvested cookies and user-agent if present
                if (res.cookies or res.user_agent) and hasattr(client, "_session_pool"):
                    try:
                        client._session_pool.update_session(host, cookies=res.cookies, user_agent=res.user_agent)
                        if hasattr(client, "session_manager"):
                            existing = client.session_manager.load_session(host) or {}
                            if res.cookies:
                                existing.update(res.cookies)
                            client.session_manager.save_session(host, existing)
                    except Exception as c_err:
                        logger.warning(
                            "Failed to persist harvested session for %s: %s", host, c_err
                        )
                return res
            else:
                # Record failure if tier did not yield a clean response
                self.circuit_breaker.record_failure(strategy.name, host)

        raise ScraperBypassError(
            f"All stealth fallback tiers failed to bypass anti-bot protection for {url}"
        )


