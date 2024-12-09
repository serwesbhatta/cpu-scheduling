from .job import Job

class Device:
    def __init__(self, name):
        self.name = name
        self.job: Job = None

    def load_job(self, job: Job):
        """Loads a job onto the device."""
        self.job = job

    def process_job(self):
        """Processes the current burst of the job."""
        self.job.decrement_duration()

    def is_free(self):
        """Returns True if the device is free."""
        return self.job is None

    def free(self):
        """Frees the device."""
        self.job = None