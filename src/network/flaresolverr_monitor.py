import logging
import subprocess
import threading
import time

from monitoring.logger import get_logger

LOGGER = get_logger(__name__)

class FlareSolverrMonitor:
    """
    Actively monitors FlareSolverr health by periodically reading its Docker container logs.
    If it detects signs that Cloudflare is blocking FlareSolverr, it flags the monitor status as unhealthy.
    """

    def __init__(self, container_name: str = "flaresolverr", check_interval: int = 15):
        self.container_name = container_name
        self.check_interval = check_interval
        self._is_healthy = True
        self._running = False
        self._thread = None
        
        # Patterns that indicate FlareSolverr is failing to bypass Cloudflare
        self.failure_patterns = [
            "Cloudflare challenge not solved",
            "Error: Timeout",
            "Error: Cloudflare",
            "Unable to solve challenge"
        ]

    def start(self):
        """Starts the background telemetry thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="FlareSolverrMonitor")
        self._thread.start()
        LOGGER.info(f"Started FlareSolverr telemetry monitor (container: {self.container_name})")

    def stop(self):
        """Stops the background telemetry thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def is_healthy(self) -> bool:
        """Returns True if the container is running and not emitting failure logs."""
        return self._is_healthy

    def _monitor_loop(self):
        while self._running:
            try:
                # Tail the last 50 lines of the container logs
                # In Windows, we use subprocess with shell=True for docker commands
                result = subprocess.run(
                    f"docker logs --tail 50 {self.container_name}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                
                if result.returncode != 0:
                    # If docker is not running or container doesn't exist, it's unhealthy
                    LOGGER.debug(f"FlareSolverr container '{self.container_name}' not found or docker not running.")
                    self._is_healthy = False
                else:
                    logs = result.stdout + result.stderr
                    is_failing = any(pattern.lower() in logs.lower() for pattern in self.failure_patterns)
                    
                    if is_failing and self._is_healthy:
                        LOGGER.warning("FlareSolverr monitor detected Cloudflare bypass failures in Docker logs! Quarantining...")
                        self._is_healthy = False
                    elif not is_failing and not self._is_healthy:
                        LOGGER.info("FlareSolverr logs are clear again. Restoring health status.")
                        self._is_healthy = True

            except subprocess.TimeoutExpired:
                LOGGER.warning("Timeout while trying to read docker logs.")
            except Exception as e:
                LOGGER.debug(f"FlareSolverr monitor error: {e}")
                self._is_healthy = False

            # Wait for next check interval
            time.sleep(self.check_interval)
