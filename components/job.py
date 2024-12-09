from api import getBurst


class Job:
    def __init__(self, job_id, arrival_time, priority):
        self.job_id = job_id
        self.arrival_time = arrival_time
        self.priority = priority
        self.cpu_wait_time = 0
        self.turnaround_time = 0
        self.io_wait_time = 0
        self.burst_id = 0
        self.burst_type = ""
        self.burst_duration = 0

    def is_complete(self):
        """Returns True if the job has no more bursts."""
        return not self.bursts

    def burst_complete(self):
        """Returns True if the current burst is complete."""
        if self.burst_duration <= 0:
            return True
        else:
            return False

    def decrement_duration(self):
        """Decrements the current burst of the job."""
        self.burst_duration -= 1

    def get_next_burst(self):
        """Returns the next burst of the job."""
        return self.bursts.pop(0)

    def get_job_burst(self, client_id, session_id, job_id):
        """Returns the type of the current burst of the job."""
        burst_response = getBurst(client_id, session_id, job_id)

        self.burst_id = burst_response["data"]["burst_id"]
        self.burst_type = burst_response["data"]["burst_type"]
        self.burst_duration = burst_response["data"]["duration"]

    def increment_cpu_wait_time(self):
        self.cpu_wait_time += 1

    def increment_io_wait_time(self):
        self.io_wait_time += 1
