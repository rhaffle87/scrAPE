from __future__ import annotations

import json
import logging
import time
from pathlib import Path
import psutil

LOGGER = logging.getLogger(__name__)


class HardwareLoadGovernor:
    """
    Monitors system CPU % and RAM % utilization via psutil and calculates dynamic
    worker thread scale factors (0.25x to 1.0x) to prevent system freezes.
    """

    def __init__(
        self,
        config_path: str | Path = "data/domain_config.json",
        max_cpu_percent: float = 85.0,
        min_ram_percent: float = 15.0,
        poll_interval_s: float = 5.0,
        min_disk_percent: float = 10.0,
    ):
        self.config_path = Path(config_path)
        self.max_cpu_percent = max_cpu_percent
        self.min_ram_percent = min_ram_percent
        self.poll_interval_s = poll_interval_s
        self.min_disk_percent = min_disk_percent
        
        self.disk_critical = False
        self._disk_alert_sent = False

        self._last_poll_time = 0.0
        self._cached_metrics: dict[str, float] = {"cpu_percent": 0.0, "ram_percent_available": 100.0}
        self._load_config()

    def _load_config(self) -> None:
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                gov_cfg = data.get("hardware_governor", {})
                self.max_cpu_percent = float(gov_cfg.get("max_cpu_percent", self.max_cpu_percent))
                self.min_ram_percent = float(gov_cfg.get("min_ram_percent", self.min_ram_percent))
                self.poll_interval_s = float(gov_cfg.get("poll_interval_s", self.poll_interval_s))
                self.min_disk_percent = float(gov_cfg.get("min_disk_percent", self.min_disk_percent))
            except Exception as e:
                LOGGER.warning("Failed to load hardware_governor config from %s: %s", self.config_path, e)

    def get_metrics(self) -> dict[str, float]:
        """Poll and return current CPU % and available RAM %."""
        now = time.time()
        if now - self._last_poll_time >= self.poll_interval_s:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram_mem = psutil.virtual_memory()
                ram_avail_pct = (ram_mem.available / ram_mem.total) * 100.0
                
                # Check disk space
                disk = psutil.disk_usage('/')
                disk_avail_pct = (disk.free / disk.total) * 100.0
                
                self._cached_metrics = {
                    "cpu_percent": cpu,
                    "ram_percent_available": ram_avail_pct,
                    "disk_percent_available": disk_avail_pct
                }
                
                # Update critical disk state
                was_critical = self.disk_critical
                self.disk_critical = disk_avail_pct < self.min_disk_percent
                
                if self.disk_critical and not self._disk_alert_sent:
                    LOGGER.critical("🚨 DISK SPACE CRITICAL: Only %.1f%% free. Downloads will be paused.", disk_avail_pct)
                    try:
                        from notifications.notification_manager import NotificationPipeline
                        NotificationPipeline().notify_watchdog_status(f"🚨 <b>DISK SPACE CRITICAL</b>\nOnly {disk_avail_pct:.1f}% free space remaining. Downloads are paused until space is freed.")
                        self._disk_alert_sent = True
                    except Exception:
                        pass
                elif not self.disk_critical and was_critical:
                    LOGGER.info("✅ Disk space recovered to %.1f%%. Resuming downloads.", disk_avail_pct)
                    self._disk_alert_sent = False
                    
                self._last_poll_time = now
            except Exception as e:
                LOGGER.warning("HardwareLoadGovernor psutil metric poll failed: %s", e)
        return self._cached_metrics

    def get_concurrency_scale_factor(self) -> float:
        """Calculate dynamic scale factor for active worker threads (0.25 to 1.0)."""
        metrics = self.get_metrics()
        cpu = metrics.get("cpu_percent", 0.0)
        ram_avail = metrics.get("ram_percent_available", 100.0)

        # Critical load threshold check
        if cpu >= 95.0 or ram_avail <= 5.0:
            LOGGER.warning("CRITICAL SYSTEM LOAD: CPU=%.1f%%, RAM Avail=%.1f%%. Throttling workers to 0.25x.", cpu, ram_avail)
            self.trigger_memory_cleanup()
            return 0.25
        elif cpu >= self.max_cpu_percent or ram_avail <= self.min_ram_percent:
            LOGGER.warning("HIGH SYSTEM LOAD: CPU=%.1f%%, RAM Avail=%.1f%%. Throttling workers to 0.50x.", cpu, ram_avail)
            self.trigger_memory_cleanup()
            return 0.50

        return 1.0

    def trigger_memory_cleanup(self) -> int:
        """Triggers explicit Python garbage collection to release unreferenced memory objects."""
        import gc
        collected = gc.collect()
        LOGGER.info("HardwareLoadGovernor: Explicit GC cycle collected %d unreferenced objects.", collected)
        return collected


_GOVERNOR_INSTANCE: HardwareLoadGovernor | None = None

def get_governor() -> HardwareLoadGovernor:
    """Returns a globally shared singleton instance of the HardwareLoadGovernor."""
    global _GOVERNOR_INSTANCE
    if _GOVERNOR_INSTANCE is None:
        _GOVERNOR_INSTANCE = HardwareLoadGovernor()
    return _GOVERNOR_INSTANCE
