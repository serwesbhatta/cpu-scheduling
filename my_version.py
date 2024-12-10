from time import sleep

from components import Device, Job, Queue, SystemClock, Stats
from api import getJob, init

from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.panel import Panel


class Scheduler:
    def __init__(self, clock, cpus, ios):
        self.jobs = Queue()
        self.new_queue = Queue()
        self.ready_queue = Queue()
        self.running_queue = Queue()
        self.waiting_queue = Queue()
        self.io_queue = Queue()
        self.exit_queue = Queue()
        self.clock = clock
        self.ios = ios
        self.cpus = cpus

    def generate_table(self):
        # Main layout
        layout = Layout()

        # Queue Table
        self.queue_table = Table(title="Job Queues")
        self.queue_table.add_column(
            "Queue", justify="center", style="cyan", no_wrap=True
        )
        self.queue_table.add_column(
            "Jobs", justify="center", style="magenta", no_wrap=True
        )

        # Populate queue table
        self.queue_table.add_row("New Queue", self.format_jobs(self.new_queue.jobs))
        self.queue_table.add_row("Ready Queue", self.format_jobs(self.ready_queue.jobs))
        self.queue_table.add_row(
            "Running Queue", self.format_jobs(self.running_queue.jobs)
        )
        self.queue_table.add_row(
            "Waiting Queue", self.format_jobs(self.waiting_queue.jobs)
        )
        self.queue_table.add_row("IO Queue", self.format_jobs(self.io_queue.jobs))
        self.queue_table.add_row("Exit Queue", self.format_jobs(self.exit_queue.jobs))

        # CPU Table
        self.cpu_table = Table(title="CPU Status")
        self.cpu_table.add_column("CPU", justify="center", style="yellow", no_wrap=True)
        self.cpu_table.add_column("Job", justify="center", style="green", no_wrap=True)

        for cpu in self.cpus:
            if cpu.is_free():
                self.cpu_table.add_row(cpu.name, Text("Idle", style="dim red"))
            else:
                self.cpu_table.add_row(cpu.name, self.format_jobs([cpu.job]))

        # IO Table
        self.io_table = Table(title="IO Devices Status")
        self.io_table.add_column(
            "IO Device", justify="center", style="blue", no_wrap=True
        )
        self.io_table.add_column("Job", justify="center", style="green", no_wrap=True)

        for io in self.ios:
            if io.is_free():
                self.io_table.add_row(io.name, Text("Idle", style="dim red"))
            else:
                self.io_table.add_row(io.name, self.format_jobs([io.job]))

        # Job Table
        self.job_table = Table(title="Job Status")
        self.job_table.add_column(
            "Job ID", justify="center", style="cyan", no_wrap=True
        )
        self.job_table.add_column(
            "Arrival Time", justify="center", style="magenta", no_wrap=True
        )
        self.job_table.add_column(
            "Priority", justify="center", style="yellow", no_wrap=True
        )
        self.job_table.add_column(
            "Burst Type", justify="center", style="green", no_wrap=True
        )
        self.job_table.add_column(
            "Burst Duration", justify="center", style="blue", no_wrap=True
        )

        for job in self.jobs.jobs:
            self.job_table.add_row(
                str(job.job_id),
                str(job.arrival_time),
                str(job.priority),
                job.burst_type,
                str(job.burst_duration),
            )

        left_column = Layout(name="left")
        # Add tables to layout
        left_column.split(
            Layout(Panel(self.queue_table, title="Queues"), ratio=5, size=None),
            Layout(Panel(self.cpu_table, title="CPU"), size=None, ratio=5),
            Layout(Panel(self.io_table, title="IO Devices"), size=None, ratio=5),
        )

        right_column = Layout(name="right")
        # right_column.update(Panel(self.job_table, title="Job Status"))
        right_column.split(
            Layout(Panel(self.job_table, title="Job Status"), ratio=5, size=None),
            Layout(
                Panel(str(self.clock.current_time), title="Clock"), size=None, ratio=5
            ),
        )

        # Combine left and right columns
        layout.split_row(left_column, right_column)
        return layout

    def format_jobs(self, jobs):
        """Format jobs as colorful blocks."""
        if not jobs:
            return Text("Empty", style="dim")
        return ", ".join([f"[bold cyan]Job {job.job_id}[/]" for job in jobs])

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
                    self.jobs.enqueue(new_job, 0)
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

    def process_ready_queue(self, priority=False):
        """Processes the ready queue."""
        for cpu in self.cpus:
            if cpu.is_free():
                if not self.ready_queue.is_empty():
                    if priority:
                        self.ready_queue.jobs.sort(
                            key=lambda x: x.priority, reverse=True
                        )
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

    def process_running_queue(
        self, client_id, session_id, algorithm, time_quantum=5, preemptive=False
    ):
        """Processes the running queue."""
        if not self.running_queue.is_empty():
            for job in self.running_queue.jobs:
                if algorithm == "FCFS":
                    job.decrement_duration()
                    if job.burst_complete():
                        for cpu in cpus:
                            if cpu.job and cpu.job.job_id == job.job_id:
                                cpu.free()
                        job.get_job_burst(client_id, session_id, job.job_id)
                        if job.burst_type == "IO":
                            self.waiting_queue.enqueue(job, 0)
                            self.running_queue.remove(job)
                        elif job.burst_type == "EXIT":
                            self.exit_queue.enqueue(job, 0)
                            self.running_queue.remove(job)
                        else:
                            self.ready_queue.enqueue(job)
                            self.running_queue.remove(job)
                elif algorithm == "RR":
                    if job.time_slice_remaining is None:
                        job.time_slice_remaining = time_quantum

                    job.decrement_duration()
                    job.time_slice_remaining -= 1

                    if job.burst_complete():
                        for cpu in self.cpus:
                            if cpu.job and cpu.job.job_id == job.job_id:
                                cpu.free()
                        job.get_job_burst(client_id, session_id, job.job_id)
                        if job.burst_type == "IO":
                            self.waiting_queue.enqueue(job, 0)
                            self.running_queue.remove(job)
                        elif job.burst_type == "EXIT":
                            self.exit_queue.enqueue(job, 0)
                            self.running_queue.remove(job)
                        else:
                            self.ready_queue.enqueue(job)
                            self.running_queue.remove(job)
                    elif job.time_slice_remaining == 0:
                        for cpu in self.cpus:
                            if cpu.job and cpu.job.job_id == job.job_id:
                                cpu.free()
                        job.time_slice_remaining = time_quantum
                        self.ready_queue.enqueue(job)
                        self.running_queue.remove(job)

            if algorithm == "PR":
                for job in self.running_queue.jobs:
                    job.decrement_duration()

                for job in self.running_queue.jobs:
                    if job.burst_complete():
                        for cpu in self.cpus:
                            if cpu.job and cpu.job.job_id == job.job_id:
                                cpu.free()
                        job.get_job_burst(client_id, session_id, job.job_id)
                        if job.burst_type == "IO":
                            self.waiting_queue.enqueue(job, 0)
                            self.running_queue.remove(job)
                        elif job.burst_type == "EXIT":
                            self.exit_queue.enqueue(job, 0)
                            self.running_queue.remove(job)
                        else:
                            self.ready_queue.enqueue(job)
                            self.running_queue.remove(job)

                if not self.ready_queue.is_empty():
                    if preemptive:
                        if not self.running_queue.is_empty():
                            highest_priority_job = min(
                                self.ready_queue.jobs, key=lambda x: x.priority
                            )

                            lowest_priority_job = max(
                                self.running_queue.jobs, key=lambda x: x.priority
                            )

                            if lowest_priority_job.priority > highest_priority_job.priority:
                                for cpu in self.cpus:
                                    if cpu.job and cpu.job.job_id == lowest_priority_job.job_id:
                                        cpu.free()
                                        cpu.load_job(highest_priority_job)
                                self.ready_queue.enqueue(lowest_priority_job)
                                self.running_queue.remove(lowest_priority_job)
                                self.running_queue.enqueue(highest_priority_job)
                                self.ready_queue.jobs.remove(highest_priority_job)

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
                        self.io_queue.remove(job)
                    elif job.burst_type == "EXIT":
                        self.exit_queue.enqueue(job, 0)
                        self.io_queue.remove(job)
                    else:
                        self.ready_queue.enqueue(job)
                        self.io_queue.remove(job)
                else:
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

        with Live(self.generate_table(), refresh_per_second=20) as live:
            while True:
                self.clock.increment()
                clock_time = self.clock.get_time()
                self.fetch_jobs(client_id, session_id, clock_time)
                self.move_to_ready_queue(client_id, session_id)
                self.process_ready_queue()
                self.process_running_queue(
                    client_id, session_id, algorithm="PR", preemptive=False
                )
                self.process_waiting_queue()
                self.process_io_queue(client_id, session_id)
                live.update(self.generate_table())
                sleep(0.5)


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
