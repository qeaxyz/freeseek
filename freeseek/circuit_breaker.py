import time
from .utils import HelperFunctions

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"

    def _open(self):
        self.state = "OPEN"
        self.last_failure_time = time.time()
        HelperFunctions.logger.warning("Circuit breaker opened.")

    def _close(self):
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        HelperFunctions.logger.info("Circuit breaker closed.")

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise APIError("Circuit breaker is open. Request aborted.")
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self._open()
            raise e
        else:
            if self.state == "HALF_OPEN":
                self._close()
            return result