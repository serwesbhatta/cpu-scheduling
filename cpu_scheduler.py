import requests
import json
import os
from rich import print
import random
def init(config):
    """
    Description:
        This function will initialize the client and return the `session_id` (next integer used by your client_id) and `clock_start`
    Args:
        config (dict): A dictionary containing the configuration for the client
    Returns:
        dict: A dictionary containing the session_id and clock_start
    """
    route = f"http://profgriffin.com:8000/init"
    r = requests.post(route,json=config)
    if r.status_code == 200:
        response = r.json()
        return response
    else:
        print(f"Error: {r.status_code}")
        return None
def getJob(client_id,session_id,clock_time):
    """
    Description:
        This function will get the jobs available at the current clock time
    Args:
        client_id (str): The client_id
        session_id (int): The session_id
        clock_time (int): The current clock time
    Returns:
        dict: A dictionary containing the jobs available at the current clock time
    Example Response:
        "data": [
            {
            "job_id": 1,
            "session_id": 13,
            "arrival_time": 1989,
            "priority": 2
            }
        ]
    """
    route = f"http://profgriffin.com:8000/job?client_id={client_id}&session_id={session_id}&clock_time={clock_time}"
    r = requests.get(route)
    if r.status_code == 200:
        response = r.json()
        return response
    else:
        print(f"Error: {r.status_code}")
        return None
def getBurst(client_id, session_id, job_id):
    """
    Description:
        This function will get the burst for a job
    Args:
        client_id (str): The client_id
        session_id (int): The session_id
        job_id (int): The job_id
    Returns:
        dict: A dictionary containing the burst for the job
    Example Response:
        "data": {
            "burst_id": 1,
            "burst_type": "CPU",  # CPU, IO, EXIT
            "duration": 11
        }
    """
    route = f"http://profgriffin.com:8000/burst?client_id={client_id}&session_id={session_id}&job_id={job_id}"
    r = requests.get(route)
    if r.status_code == 200:
        response = r.json()
        return response
    else:
        print(f"Error: {r.status_code}")
        return None
def getBurstsLeft(client_id, session_id, job_id):
    """
    Description:
        This function will get the number of bursts left for a job
    Args:
        client_id (str): The client_id
        session_id (int): The session_id
        job_id (int): The job_id
    Returns:
        int: Simply an integer with count of bursts left zero otherwise
    Example Response:
        3
    """
    route = f"http://profgriffin.com:8000/burstsLeft?client_id={client_id}&session_id={session_id}&job_id={job_id}"
    r = requests.get(route)
    if r.status_code == 200:
        response = r.json()
        return response
    else:
        print(f"Error: {r.status_code}")
        return None
def getJobsLeft(client_id, session_id):
    """
    Description:
        This function will get the number of jobs left for a session
    Args:
        client_id (str): The client_id
        session_id (int): The session_id
    Returns:
        int: Simply an integer with count of jobs left zero otherwise
    Example Response:
        11
    """
    route = f"http://profgriffin.com:8000/jobsLeft?client_id={client_id}&session_id={session_id}"
    r = requests.get(route)
    if r.status_code == 200:
        response = r.json()
        return response
    else:
        print(f"Error: {r.status_code}")
        return None
def api_start():
    config = {
        "client_id": "f1a1c4c0",
        "client_name": "CPU Scheduler",
        "algorithm": "Round Robin",
        "session_id": 1,
        "num_cpus": 1,
        "quantum": 1
    }
    response = init(config)
    session_id = response['session_id']
    start_clock = response['clock_start']
    return start_clock,session_id

class SystemClock:
    _shared_state = {}  # Shared state for all instances
    def __init__(self):
        # Share the state among all instances
        self.__dict__ = self._shared_state
        # Initialize the clock if it hasn't been already
        if not hasattr(self, "current_time"):
            self.current_time = 0  # Start clock at 0
    def increment(self, amount=1):
        """Increment the clock by a specified amount (default is 1)."""
        self.current_time += amount
    def reset(self):
        """Reset the clock to zero."""
        self.current_time = 0
    def get_time(self):
        """Return the current system clock time."""
        return self.current_time
    
class Job:
    def __init__(self, job_id, arrival_time, priority):
        self.job_id = job_id
        self.arrival_time = arrival_time
        self.priority = priority
        self.bursts = []
        self.cpu_wait_time = 0
        self.turnaround_time = 0
        self.io_wait_time = 0

class Queue:
    def __init__(self):
        self.jobs = []
    def enqueue(self, item):
        self.jobs.insert(0, item)
    def empty(self):
        return self.jobs == []
    def dequeue(self):
        return self.jobs.pop()
    def peek(self):
        return self.jobs[-1]
    def is_empty(self):
        return not self.jobs
    def size(self):
        return len(self.jobs)
    def __str__(self):
        return str(self.jobs)
    def __repr__(self):
        return str(self.jobs)
    def processJobs(self,queueName):
        for job in self.jobs:
            if queueName == 'ready':
                job.cpu_wait_time += 1
            elif queueName == 'wait':
                job.io_wait_time += 1

class Device:
    def __init__(self,num_cpus=1):
        self.job = None
    def loadJob(self,job):
        self.job = job
    def processBurst(self):
        self.job.current_burst -= 1

class MultiDevice:
    def __init__(self,num_devices=1):
        self.clock - SystemClock()
        self.cpus = [Device() for _ in range(num_devices)]

class Scheduler:
    def __init__(self):
        self.ready_queue = Queue()
        self.wait_queue = Queue()
        self.terminated_queue = Queue()
        self.new_queue = Queue()
        self.clock = SystemClock()
    def run(self):
        start_clock,session_id = api_start()
        while True:
            self.clock.increment()
            # call api
            self.ready_queue.processJobs('ready')
            self.wait_queue.processJobs('wait')
            print(f"Clock: {self.clock.get_time()}")
            print(f"Ready Queue: {self.ready_queue}")
            print(f"Wait Queue: {self.wait_queue}")
            print(f"Terminated Queue: {self.terminated_queue}")
            print(f"New Queue: {self.new_queue}")
            print("\n")
            if self.clock.get_time() == 10:
                break

class IO:
    pass

if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.run()
    cpus = MultiDevice(4)
    
