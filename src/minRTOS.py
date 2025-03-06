import threading
import queue
import time
import heapq
import signal
import os

class Mutex:
    def __init__(self):
        self.lock = threading.Lock()
        self.owner = None
        self.waiting_tasks = []

    def acquire(self, task):
        """Acquire the mutex with priority inheritance."""
        with self.lock:
            if self.owner is None:
                self.owner = task
                task.held_mutexes.append(self)
                return True
            else:
                if task not in self.waiting_tasks:
                    self.waiting_tasks.append(task)
                    self._boost_priority()
                    print(f"🔒 {task.name} waiting for mutex held by {self.owner.name}")
                return False

    def release(self):
        """Release the mutex and restore priority."""
        with self.lock:
            if self.owner:
                self.owner.held_mutexes.remove(self)
                self.owner.restore_priority()

            if self.waiting_tasks:
                self.owner = self.waiting_tasks.pop(0)
                print(f"🔓 Mutex now owned by {self.owner.name}")
                self.owner.held_mutexes.append(self)
                self._boost_priority()
            else:
                self.owner = None

    def _boost_priority(self):
        """Boost owner's priority if higher-priority tasks are waiting."""
        if self.owner and self.waiting_tasks:
            highest_priority = max(task.priority for task in self.waiting_tasks)
            if highest_priority > self.owner.priority:
                self.owner.priority = highest_priority

class Task:
    def __init__(self, name, update_func, period=0, priority=1, deadline=None, overrun_action="kill", event_driven=False):
        self.name = name
        self.update = update_func
        self.period = period
        self.priority = priority
        self.original_priority = priority
        self.deadline = deadline
        self.overrun_action = overrun_action
        self.next_run = time.perf_counter()
        self.running = True
        self.lock = threading.Lock()
        self.event = threading.Event() if event_driven else None
        self.thread = None
        self.held_mutexes = []
        self.metrics = {"exec_time": 0, "missed_deadlines": 0, "cpu_usage": 0}

    def __lt__(self, other):
        """Defines task comparison for heapq based on scheduling policy."""
        return self.priority > other.priority  # Higher priority runs first

    def stop(self):
        """Stop the task and release held mutexes."""
        self.running = False
        for mutex in self.held_mutexes:
            mutex.release()
        if self.event:
            self.event.set()

    def restore_priority(self):
        """Restore the original priority after releasing a mutex."""
        self.priority = self.original_priority

    def run(self):
        """Execute the task with deadline tracking and performance monitoring."""
        while self.running:
            now = time.perf_counter()
            if self.event:
                self.event.wait()
                self.event.clear()

            if now >= self.next_run:
                start_time = time.perf_counter()
                with self.lock:
                    self.update()
                end_time = time.perf_counter()

                execution_time = end_time - start_time
                self.metrics["exec_time"] = execution_time

                if self.deadline and execution_time > self.deadline:
                    print(f"⚠️ Task {self.name} exceeded deadline! [{execution_time:.6f}s]")
                    self.metrics["missed_deadlines"] += 1
                    if self.overrun_action == "kill":
                        self.running = False
                        print(f"❌ Task {self.name} terminated.")
                        return
                    elif self.overrun_action == "pause":
                        print(f"⏸ Task {self.name} paused.")
                        self.event.wait()

                self.next_run = now + self.period if self.period > 0 else now
            time.sleep(0.0001)

    def sleep(self, duration):
        """Pause task execution for a specified duration."""
        time.sleep(duration)

    def acquire_mutex(self, mutex):
        """Attempt to acquire a mutex."""
        return mutex.acquire(self)

    def release_mutex(self, mutex):
        """Release a mutex."""
        if mutex in self.held_mutexes:
            mutex.release()
            self.held_mutexes.remove(mutex)

class Scheduler:
    def __init__(self, scheduling_policy="EDF"):
        self.task_queue = []
        self.tasks = {}
        self.message_queues = {}
        self.lock = threading.Lock()
        self.scheduling_policy = scheduling_policy
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)

        signal.signal(signal.SIGUSR1, self._signal_handler)

    def add_task(self, task):
        """Add a task to the scheduler."""
        with self.lock:
            heapq.heappush(self.task_queue, (self._get_task_priority(task), task))
            self.tasks[task.name] = task
            self.message_queues[task.name] = queue.Queue()
            task.thread = threading.Thread(target=task.run)
            task.thread.start()
            print(f"✅ Task {task.name} added.")

    def remove_task(self, task_name):
        """Remove a task dynamically."""
        with self.lock:
            if task_name in self.tasks:
                task = self.tasks.pop(task_name)
                task.stop()
                task.thread.join()
                print(f"❌ Task {task_name} removed.")

    def _get_task_priority(self, task):
        """Determine priority based on scheduling policy."""
        if self.scheduling_policy == "EDF":
            return task.deadline if task.deadline else float('inf')
        elif self.scheduling_policy == "RMS":
            return task.period if task.period > 0 else float('inf')
        return task.priority  

    def run_scheduler(self):
        """Continuously manage task execution order."""
        while self.scheduler_running:
            with self.lock:
                self.task_queue = sorted(self.task_queue, key=lambda x: self._get_task_priority(x[1]))
            time.sleep(0.001)

    def start(self):
        """Start the scheduler."""
        self.scheduler_thread.start()
        print(f"🟢 minRTOS running with {self.scheduling_policy} scheduling.")

    def stop_all(self):
        """Stop all tasks and terminate the scheduler."""
        with self.lock:
            self.scheduler_running = False
            for task in list(self.tasks.values()):
                task.stop()
                task.thread.join()
            self.tasks.clear()
            print("🛑 All tasks stopped.")

    def trigger_task(self, task_name):
        """Manually trigger an event-driven task."""
        if task_name in self.tasks:
            task = self.tasks[task_name]
            if task.event:
                task.event.set()

    def send_message(self, to_task, message):
        """Send a message to another task."""
        if to_task in self.message_queues:
            self.message_queues[to_task].put(message)

    def receive_message(self, task_name):
        """Receive a message from the task's queue."""
        if task_name in self.message_queues:
            try:
                return self.message_queues[task_name].get_nowait()
            except queue.Empty:
                return None

    def _signal_handler(self, signum, frame):
        """Handle OS-level signal for scheduling."""
        print("🔔 Interrupt received, rescheduling tasks...")
