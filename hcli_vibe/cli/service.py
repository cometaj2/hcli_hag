import io
import os
import time
import inspect
import logger
import jobqueue as j
import threading
import runner as r
import repo
import config
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from collections import OrderedDict

logging = logger.Logger()
logging.setLevel(logger.INFO)


class Service:
    scheduler = None
    runner = None
    root = os.path.dirname(inspect.getfile(lambda: None))

    def __init__(self):
        global scheduler

        executors = {
            'default': ThreadPoolExecutor(10)
        }

        scheduler = BackgroundScheduler(executors=executors)
        self.config = config.Config()
        self.runner = r.Runner()
        self.signature = repo.Signature()
        self.job_queue = j.JobQueue()
        self.process = self.schedule(self.process_job_queue)
        scheduler.start()

        return

    # we schedule immediate single instance job executions.
    def schedule(self, function):
        return scheduler.add_job(function, 'date', run_date=datetime.now(), max_instances=1)

    def sig(self, path):
        return self.signature.sig(path)

    def jobs(self):
        result = {}
        jobs = self.job_queue.list()
        for i, job in enumerate(jobs, start=1):
            result[i] = job[0]  # Use integer keys instead of strings

        reversal = OrderedDict(sorted(result.items(), key=lambda x: x[0], reverse=True))

        if reversal:
            logging.info("[ vibe ] ------------------------------------------")
            for key, value in reversal.items():
                logging.info(f"[ vibe ] job {key}: {value}")

        return reversal

    def process_job_queue(self):
        with self.runner.lock:
            while True:
                if not self.runner.is_running and not self.job_queue.empty():
                    # we display all jobs in the queue for reference before streaming the next job.
                    jobs = self.jobs()

                    queuedjob = self.job_queue.get()
                    jobname = queuedjob[0]
                    lambdajob = queuedjob[1]
                    job = self.schedule(lambdajob)
                    logging.info("[ vibe ] running " + jobname)

                time.sleep(0.1)
