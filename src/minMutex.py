import multiprocessing
import time

class Mutex:
    """Mutex with priority inheritance and timeout handling."""
    def __init__(self, enable_priority_inheritance=True):
        self.lock = multiprocessing.RLock()  # Reentrant lock to prevent deadlocks
        self.owner = None  # The current task holding the mutex
        self.waiting_tasks = []  # List of tasks waiting for the mutex
        self.original_priorities = {}  # Store original priorities for restoration
        self.enable_priority_inheritance = enable_priority_inheritance

    def acquire(self, task, timeout=None):
        """Attempt to acquire the mutex, optionally with a timeout."""
        start_time = time.time()
        while True:
            with self.lock:
                if self.owner is None:
                    self.owner = task
                    print(f"✅ {task.name} acquired Mutex")
                    return True
                else:
                    if task not in self.waiting_tasks:
                        self.waiting_tasks.append(task)
                        self._boost_priority()
                    
            if timeout and (time.time() - start_time) >= timeout:
                print(f"⏳ {task.name} timed out waiting for Mutex")
                return False
            
            time.sleep(0.01)  # Small delay to prevent busy-waiting

    def release(self):
        """Release the mutex and restore priority if necessary."""
        with self.lock:
            if self.owner:
                # Restore the owner's priority only if it holds no other mutexes
                if self.owner.name in self.original_priorities:
                    print(f"🔓 {self.owner.name} released Mutex (Restoring priority)")
                    self.owner.priority = self.original_priorities.pop(self.owner.name)
                self.owner = None

            # Assign mutex to the next highest-priority waiting task
            if self.waiting_tasks:
                self.waiting_tasks.sort(key=lambda t: t.priority, reverse=True)
                self.owner = self.waiting_tasks.pop(0)
                print(f"✅ {self.owner.name} acquired Mutex from queue")
                self._boost_priority()

    def _boost_priority(self):
        """Boost the owner's priority if higher-priority tasks are waiting."""
        if self.owner and self.waiting_tasks and self.enable_priority_inheritance:
            highest_priority = max(task.priority for task in self.waiting_tasks)
            if highest_priority > self.owner.priority:
                if self.owner.name not in self.original_priorities:
                    self.original_priorities[self.owner.name] = self.owner.priority
                print(f"⚡ Boosting priority of {self.owner.name} from {self.owner.priority} to {highest_priority}")
                self.owner.priority = highest_priority
