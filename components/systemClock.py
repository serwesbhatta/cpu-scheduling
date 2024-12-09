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
