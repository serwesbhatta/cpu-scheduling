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
