import threading
import time

class RateLimiter:
    def __init__(self, delay):
        self.delay = delay
        self.lock = threading.Lock()
        self.last_call = 0

    def __enter__(self):
        with self.lock:
            if time.time() < self.last_call + self.delay:
                time.sleep(self.last_call + self.delay - time.time())
            self.last_call = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
