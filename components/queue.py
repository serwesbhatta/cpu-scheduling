class Queue:
    def __init__(self):
        self.jobs = []

    def enqueue(self, item, index = None):
        """Adds an item to the front of the queue."""
        if index == None:
            self.jobs.append(item)
        else:
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
