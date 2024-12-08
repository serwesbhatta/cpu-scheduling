class SystemClock:
    def __init__(self, start_clock=0):
        """Initializes the clock with the given start time."""
        self.current_time = start_clock  # Use an instance attribute

    def increment(self, amount=1):
        """Increments the clock by the given amount."""
        self.current_time += amount

    def get_time(self):
        """Returns the current time."""
        return self.current_time

    def reset(self):
        """Resets the clock to 0."""
        self.current_time = 0


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
        if self.burst_duration == 0:
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


class Queue:
    def __init__(self):
        self.jobs = []

    def enqueue(self, index, item):
        """Adds an item to the front of the queue."""
        self.jobs.insert(index, item)

    def dequeue(self):
        """Removes and returns the last item in the queue."""
        return self.jobs.pop()

    def is_empty(self):
        """Returns True if the queue is empty."""
        return not self.jobs

    def peek(self):
        """Returns the last item in the queue."""
        if self.is_empty():
            return None
        return self.jobs[-1]

    def size(self):
        """Returns the size of the queue."""
        return len(self.jobs)


class Device:
    def __init__(self, name):
        self.name = name
        self.job = None

    def load_job(self, job):
        """Loads a job onto the device."""
        self.job = job

    def process_job(self):
        """Processes the current burst of the job."""
        self.job.decrement_duration()

    def is_free(self):
        """Returns True if the device is free."""
        return self.job is None

class MultiDevice:
    def __init__(self, devices_names):
        self.devices = [Device(name) for name in devices_names]

    def assign_job(self, job):
        """Assigns a job to the first available device."""
        for device in self.devices:
            if device.is_free():
                device.load_job(job)
                break

    def process_bursts(self):
        """Processes the bursts of all devices."""
        for device in self.devices:
            if not device.is_free():
                device.process_burst()


class Scheduler:
    def __init__(self, clock, cpus, ios):
        self.new_queue = Queue()
        self.ready_queue = Queue()
        self.running_queue = Queue()
        self.waiting_queue = Queue()
        self.io_queue = Queue()
        self.exit_queue = Queue()
        self.clock = clock
        self.ios = ios
        self.cpus = cpus

    def fetch_jobs(self, client_id, session_id, clock_time):
        """Fetches new jobs from the /jobs endpoint."""
        """Retrieves jobs arriving at the current time and places them in the new_queue."""
        route = f"http://profgriffin.com:8000/job?client_id={client_id}&session_id={session_id}&clock_time={clock_time}"
        r = requests.get(route)
        if r.status_code == 200:
            response = r.json()
            print(response)
            if response["data"]:
                for job in response["data"]:
                    job_id = job["job_id"]
                    arrival_time = job["arrival_time"]
                    priority = job["priority"]
                    new_job = Job(job_id, arrival_time, priority)
                    self.new_queue.enqueue(0, new_job)
                    print("Job added to new queue")
        else:
            print(f"Error: {r.status_code}")
            return None

    def move_to_ready_queue(self,client_id, session_id):
        """Moves jobs from the new queue to the ready queue."""
        while not self.new_queue.is_empty():
            job = self.new_queue.dequeue()
            job.get_job_burst(client_id, session_id, job.job_id)
            self.ready_queue.enqueue(0, job)
            print("Job added to ready queue")

    def scheduling_algorithm(self):
        """Determines the scheduling algorithm to use."""
        """Implements First-Come-First-Serve (FCFS) scheduling."""
        if not self.ready_queue.is_empty():
            job = self.ready_queue.dequeue()

            job = self.ready_queue.dequeue()
            self.devices.assign_job(job)  # Assign the job to a free device
            self.running_queue.enqueue(job)

    def process_ready_queue(self):
        """Processes the ready queue."""
        for cpu in self.cpus:
            if cpu.is_free():
                if not self.ready_queue.is_empty():
                    job = self.ready_queue.dequeue()
                    cpu.load_job(job)
                    self.running_queue.enqueue(0, job)
                    print("Job added to running queue")

    def process_waiting_queue(self):
        """Processes the waiting queue."""
        for io in self.ios:
            if io.is_free():
                if not self.waiting_queue.is_empty():
                    job = self.waiting_queue.dequeue()
                    io.load_job(job)
                    self.io_queue.enqueue(0, job)

    def process_running_queue(self):
        """Processes the running queue."""
        if not self.running_queue.is_empty():
            for cpu in self.cpus:
                if not cpu.is_free():
                    cpu.process_job()
                    if cpu.job.burst_complete():
                        cpu.job.get_job_burst(client_id, session_id, cpu.job.job_id)
                        self.exit_queue.enqueue(0, cpu.job)
                        cpu.job = None
                    else:
                        self.waiting_queue.enqueue(0, cpu.job)
                        cpu.job = None

    def print_queues(self):
        """Prints the contents of all queues."""
        pass

    def is_done(self):
        """Returns True if all queues are empty."""
        return all(
            queue.is_empty()
            for queue in [
                self.new_queue,
                self.ready_queue,
                self.running_queue,
                self.waiting_queue,
                self.io_queue,
                self.exit_queue,
            ]
        )

    def run(self, filters):
        """Runs the scheduler."""
        client_id = filters["client_id"]
        session_id = filters["session_id"]
        clock_time = filters["clock_time"]
        while True:
            self.clock.increment()
            clock_time = self.clock.get_time()
            self.fetch_jobs(client_id, session_id, clock_time)
            self.move_to_ready_queue(client_id, session_id)
            self.process_ready_queue()
            self.scheduling_algorithm()
            self.process_running_queue()
            self.process_waiting_queue()
            self.print_queues()
            # if self.is_done():
            #     break


class Stats:
    def __init__(self):
        self.total_jobs = 0
        self.total_turnaround_time = 0
        self.total_cpu_wait_time = 0
        self.total_io_wait_time = 0
        self.total_time = 0

    def calculate_stats(self, jobs):
        """Calculates the total statistics for all jobs."""
        """Calculates statistics for all jobs."""
        total_turnaround_time = 0
        total_wait_time = 0
        total_jobs = len(self.jobs)

        for job in self.jobs:
            total_turnaround_time += job.turnaround_time
            total_wait_time += job.cpu_wait_time + job.io_wait_time

        avg_turnaround_time = total_turnaround_time / total_jobs if total_jobs else 0
        avg_wait_time = total_wait_time / total_jobs if total_jobs else 0

        print(f"Total Jobs: {total_jobs}")
        print(f"Average Turnaround Time: {avg_turnaround_time}")
        print(f"Average Wait Time: {avg_wait_time}")

    def print_stats(self):
        """Prints the total statistics."""
        pass


def api_start():
    config = {
        "client_id": "serwes",
        "min_jobs": 5,
        "max_jobs": 10,
        "min_bursts": 5,
        "max_bursts": 15,
        "min_job_interval": 5,
        "max_job_interval": 10,
        "burst_type_ratio": 0.7,
        "min_cpu_burst_interval": 10,
        "max_cpu_burst_interval": 70,
        "min_io_burst_interval": 30,
        "max_io_burst_interval": 100,
        "min_ts_interval": 5,
        "max_ts_interval": 25,
        "priority_levels": [1, 2, 3, 4, 5],
    }
    response = init(config)
    print(f"Response: {response}")
    session_id = response["session_id"]
    start_clock = response["start_clock"]
    return start_clock, session_id


import requests


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
    r = requests.post(route, json=config)
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


if __name__ == "__main__":
    start_clock, session_id = api_start()
    cpus_names = ["CPU1", "CPU2", "CPU3", "CPU4"]
    cpus = []
    for cpu_name in cpus_names:
        cpus.append(Device(cpu_name))
    
    ios_names= ["IO1", "IO2"]
    ios = []
    for io_name in ios_names:
        ios.append(Device(io_name))
        
    system_clock = SystemClock(start_clock)
    scheduler = Scheduler(system_clock, cpus, ios)
    clock_time = system_clock.get_time()
    filters = {
        "client_id": "serwes",
        "session_id": session_id,
        "clock_time": clock_time,
    }
    scheduler.run(filters)
    stats = Stats()
    stats.calculate_stats(scheduler.exit_queue)
    stats.print_stats()
