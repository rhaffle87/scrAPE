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
                # In Windows, we use subprocess without shell=True by passing arguments as a list
                result = subprocess.run(  # nosec B603 B607
                    ["docker", "logs", "--tail", "50", self.container_name],
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
                        LOGGER.warning("FlareSolverr monitor detected Cloudflare bypass failures in Docker logs! Restarting container...")
                        self._is_healthy = False
                        
                        try:
                            LOGGER.info(f"Executing: docker restart {self.container_name}")
                            subprocess.run(  # nosec B603 B607
                                ["docker", "restart", self.container_name],
                                check=True,
                                timeout=20.0
                            )
                            LOGGER.info("FlareSolverr container restarted successfully. Backing off for 30s to allow startup...")
                            time.sleep(30.0)
                            self._is_healthy = True
                        except Exception as restart_exc:
                            LOGGER.error(f"Failed to restart FlareSolverr container: {restart_exc}")
                            
                    elif not is_failing and not self._is_healthy:
                        LOGGER.info("FlareSolverr logs are clear again. Restoring health status.")
                        self._is_healthy = True

            except subprocess.TimeoutExpired:
                try:
                    LOGGER.warning("Timeout while trying to read docker logs.")
                except ValueError:
                    pass
            except ValueError:
                # Python is shutting down and logging streams are closed
                pass
            except Exception as e:
                try:
                    LOGGER.debug(f"FlareSolverr monitor error: {e}")
                except ValueError:
                    pass
                self._is_healthy = False

            # Wait for next check interval interruptibly
            for _ in range(self.check_interval):
                if not self._running:
                    break
                time.sleep(1.0)
