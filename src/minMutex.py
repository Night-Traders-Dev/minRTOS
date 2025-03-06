import multiprocessing

class Mutex:
    """Mutex with priority inheritance"""
    def __init__(self):
        self.lock = multiprocessing.Lock()
        self.owner = None
        self.waiting_tasks = []
        self.original_priorities = {}

    def enter(self, task):
        self.acquire(self.task)

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def acquire(self, task):
        """Acquire the mutex with priority inheritance."""
        with self.lock:
            if self.owner is None:
                self.owner = task
                print(f"✅ {task.name} acquired Mutex")
                return True
            else:
                print(f"🚀 {task.name} wants Mutex (owned by {self.owner.name})")
                if task not in self.waiting_tasks:
                    self.waiting_tasks.append(task)
                    self._boost_priority()
                return False

    def release(self):
        """Release the mutex and restore priority."""
        with self.lock:
            if self.owner:
                original_priority = self.original_priorities.pop(self.owner.name, None)
                if original_priority is not None:
                    print(f"🔓 {self.owner.name} released Mutex (Restoring priority: {original_priority})")
                    self.owner.priority = original_priority  # Only restore if it was boosted
                self.owner = None

            if self.waiting_tasks:
                self.owner = self.waiting_tasks.pop(0)
                print(f"✅ {self.owner.name} acquired Mutex from queue")
                self._boost_priority()

    def _boost_priority(self):
        """Boost owner's priority if higher-priority tasks are waiting."""
        if self.owner and self.waiting_tasks:
            highest_priority = max(task.priority for task in self.waiting_tasks)
            if highest_priority > self.owner.priority:
                if self.owner.name not in self.original_priorities:
                    self.original_priorities[self.owner.name] = self.owner.priority
                print(f"⚡ Boosting priority of {self.owner.name} from {self.owner.priority} to {highest_priority}")
                self.owner.priority = highest_priority
