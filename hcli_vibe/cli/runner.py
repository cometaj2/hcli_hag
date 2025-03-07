import io
import re
import logger
import threading
import jobqueue as j
import time

logging = logger.Logger()

# Singleton Runner
class Runner:
    instance = None
    is_running = False
    lock = None
    terminate = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.lock = threading.Lock()
            self.job_queue = j.JobQueue()
            self.exception_event = threading.Event()
            self.terminate = False

        return self.instance

    # simple runner
    def run(self, inputstream):
        self.is_running = True
        self.terminate = False
        ins = io.StringIO(inputstream.getvalue().decode())

        try:
            self.check_termination()
            time.sleep(0.01)

        except TerminationException as e:
            self.abort()
        except Exception as e:
            self.abort()
        finally:
            self.terminate = False
            self.is_running = False

        return

    def check_termination(self):
        if self.terminate:
            raise TerminationException("[ vibe ] terminated")

    def abort(self):
        self.is_running = False
        self.terminate = False

class TerminationException(Exception):
    pass
