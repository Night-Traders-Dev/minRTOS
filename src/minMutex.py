import multiprocessing

class Mutex:
    """Mutex with priority inheritance"""
    def __init__(self, enable_priority_inheritance=True):
        self.lock = multiprocessing.Lock()  # Mutex lock
        self.owner = None  # The current task holding the mutex
        self.waiting_tasks = []  # List of tasks waiting for the mutex
        self.original_priorities = {}  # Store original priorities for restoration
        self.enable_priority_inheritance = enable_priority_inheritance

    def acquire(self, task):
        """Acquire the mutex with priority inheritance."""
        with self.lock:
            if self.owner is None:
                # If no task owns the mutex, the current task acquires it
                self.owner = task
                print(f"✅ {task.name} acquired Mutex")
                return True
            else:
                # If the mutex is owned, the task needs to wait for it
                print(f"🚀 {task.name} wants Mutex (owned by {self.owner.name})")
                if task not in self.waiting_tasks:
                    self.waiting_tasks.append(task)
                    self._boost_priority()
                return False

    def release(self):
        """Release the mutex and restore priority."""
        with self.lock:
            if self.owner:
                # Restore the owner's priority
                original_priority = self.original_priorities.pop(self.owner.name, None)
                if original_priority is not None:
                    print(f"🔓 {self.owner.name} released Mutex (Restoring priority: {original_priority})")
                    self.owner.priority = original_priority
                self.owner = None

            # Transfer the ownership of the mutex to the next task in line
            if self.waiting_tasks:
                self.owner = self.waiting_tasks.pop(0)  # Give the mutex to the highest-priority waiting task
                print(f"✅ {self.owner.name} acquired Mutex from queue")
                self._boost_priority()

    def _boost_priority(self):
        """Boost the owner's priority if higher-priority tasks are waiting."""
        if self.owner and self.waiting_tasks:
            highest_priority = max(task.priority for task in self.waiting_tasks)
            if highest_priority > self.owner.priority:
                if self.owner.name not in self.original_priorities:
                    self.original_priorities[self.owner.name] = self.owner.priority
                print(f"⚡ Boosting priority of {self.owner.name} from {self.owner.priority} to {highest_priority}")
                self.owner.priority = highest_priority
