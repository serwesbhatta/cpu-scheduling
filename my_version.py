from time import sleep

from components import Device, Job, Queue, SystemClock, Stats
from api import getJob, init

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
        response = getJob(client_id, session_id, clock_time)
        if response["success"]:
            response = response["message"]
            if response["data"]:
                for job in response["data"]:
                    job_id = job["job_id"]
                    arrival_time = job["arrival_time"]
                    priority = job["priority"]
                    new_job = Job(job_id, arrival_time, priority)
                    self.new_queue.enqueue(new_job, 0)
        else:
            print(f"Error: {response.status_code}")
            return None

    def move_to_ready_queue(self, client_id, session_id):
        """Moves jobs from the new queue to the ready queue."""
        while not self.new_queue.is_empty():
            job = self.new_queue.dequeue()
            job.get_job_burst(client_id, session_id, job.job_id)
            self.ready_queue.enqueue(job, 0)

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
                    self.running_queue.enqueue(job, 0)

    def process_waiting_queue(self):
        """Processes the waiting queue."""
        for io in self.ios:
            if io.is_free():
                if not self.waiting_queue.is_empty():
                    job = self.waiting_queue.dequeue()
                    io.load_job(job)
                    self.io_queue.enqueue(job, 0)

    def process_running_queue(self, client_id, session_id):
        """Processes the running queue."""
        if not self.running_queue.is_empty():
            for job in self.running_queue.jobs:
                job.decrement_duration()
                if job.burst_complete():
                    for cpu in cpus:
                        if cpu.job and cpu.job.job_id == job.job_id:
                            cpu.free()
                    job.get_job_burst(client_id, session_id, job.job_id)
                    if job.burst_type == "IO":
                        self.waiting_queue.enqueue(job, 0)
                        self.running_queue.dequeue()
                    elif job.burst_type == "EXIT":
                        self.exit_queue.enqueue(job, 0)
                        self.running_queue.dequeue()
                    else:
                        self.ready_queue.enqueue(job)
                        self.running_queue.dequeue()

    def process_io_queue(self, client_id, session_id):
        if not self.io_queue.is_empty():
            for job in self.io_queue.jobs:
                if job.burst_complete():
                    for io in ios:
                        if io.job and io.job.job_id == job.job_id:
                            io.free()
                    job.get_job_burst(client_id, session_id, job.job_id)
                    if job.burst_type == "IO":
                        self.waiting_queue.enqueue(job)
                        self.io_queue.dequeue()
                    elif job.burst_type == "EXIT":
                        self.exit_queue.enqueue(job, 0)
                        self.io_queue.dequeue()
                    else:
                        self.ready_queue.enqueue(job)
                        self.io_queue.dequeue()
                job.decrement_duration()

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
            # self.scheduling_algorithm()
            self.process_running_queue(client_id, session_id)
            self.process_waiting_queue()
            self.process_io_queue(client_id, session_id)
            # self.print_queues()
            # if self.is_done():
            #     break

            sleep(3)


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


if __name__ == "__main__":
    start_clock, session_id = api_start()
    cpus_names = ["CPU1", "CPU2", "CPU3", "CPU4"]
    cpus = []
    for cpu_name in cpus_names:
        cpus.append(Device(cpu_name))

    ios_names = ["IO1", "IO2"]
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
