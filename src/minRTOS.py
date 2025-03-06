import multiprocessing
import queue
import time
import os
import signal
import threading

LOG_FILE = "minRTOS_log.txt"

class Mutex:
    """Mutex with priority inheritance"""
    def __init__(self):
        self.lock = multiprocessing.Lock()
        self.owner = None
        self.waiting_tasks = []
        self.original_priorities = {}

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
                # Save original priority before boosting (if not already saved)
                if self.owner.name not in self.original_priorities:
                    self.original_priorities[self.owner.name] = self.owner.priority

                print(f"⚡ Boosting priority of {self.owner.name} from {self.owner.priority} to {highest_priority}")
                self.owner.priority = highest_priority

class Task:
    """Real-time task class for minRTOS"""
    def __init__(self, name, update_func, period=0, priority=1, deadline=None, overrun_action="kill", event_driven=False):
        self.name = name
        self.update = update_func
        self.period = period
        self.priority = priority
        self.original_priority = priority
        self.deadline = deadline
        self.overrun_action = overrun_action
        self.next_run = time.perf_counter()
        self.running = multiprocessing.Value('b', True)
        self.event = multiprocessing.Event() if event_driven else None
        self.metrics = multiprocessing.Manager().dict({"exec_time": 0, "missed_deadlines": 0, "cpu_usage": 0})
        self.process = multiprocessing.Process(target=self.run)

    def run(self):
        """Task execution loop"""
        while self.running.value:
            now = time.perf_counter()

            # Handle event-driven tasks
            if self.event:
                if not self.event.wait(timeout=0.1):  # Non-blocking wait
                    continue
                self.event.clear()

            if now >= self.next_run:
                start_time = time.perf_counter()
                self.update()
                end_time = time.perf_counter()

                execution_time = end_time - start_time
                self.metrics["exec_time"] = execution_time

                # Handle deadline overrun
                if self.deadline and execution_time > self.deadline:
                    self.metrics["missed_deadlines"] += 1
                    if self.overrun_action == "kill":
                        self.running.value = False
                        return
                    elif self.overrun_action == "pause":
                        self.event.wait()

                self.next_run = now + self.period if self.period > 0 else now

            time.sleep(0.001)  # Small sleep to avoid busy waiting

    def stop(self):
        """Stop task execution"""
        self.running.value = False
        if self.event:
            self.event.set()

class Scheduler:
    """Real-time task scheduler with multiprocessing"""
    def __init__(self, scheduling_policy="EDF"):
        self.task_queue = []
        self.tasks = {}
        self.message_queues = {}
        self.lock = threading.Lock()
        self.schedule_cond = threading.Condition(self.lock)
        self.scheduling_policy = scheduling_policy
        self.scheduler_running = threading.Event()
        self.log_queue = queue.Queue()

        signal.signal(signal.SIGUSR1, self._signal_handler)

    def add_task(self, task):
        """Add a task to the scheduler"""
        with self.schedule_cond:
            self.tasks[task.name] = task
            self.message_queues[task.name] = multiprocessing.Queue()  # Initialize message queue
            task.process.start()
            self.log(f"✅ Task {task.name} added.")
            self.schedule_cond.notify()  # Notify the scheduler

    def remove_task(self, task_name):
        """Remove a task dynamically"""
        with self.schedule_cond:
            if task_name in self.tasks:
                task = self.tasks.pop(task_name)
                task.stop()
                task.process.terminate()
                task.process.join()
                self.log(f"❌ Task {task_name} removed.")
                self.schedule_cond.notify()

    def _get_task_priority(self, task):
        """Determine priority based on scheduling policy"""
        if self.scheduling_policy == "EDF":
            return task.deadline if task.deadline else float('inf')
        elif self.scheduling_policy == "RMS":
            return task.period if task.period > 0 else float('inf')
        return task.priority

    def run_scheduler(self):
        """Continuously manage task execution order"""
        while self.scheduler_running.is_set():
            with self.schedule_cond:
                self.schedule_cond.wait()  # Wait for new tasks or scheduling events
                self.task_queue = sorted(self.tasks.values(), key=self._get_task_priority)
                
                # Enforce task preemption
                if self.task_queue:
                    highest_priority_task = self.task_queue[0]
                    for task in self.tasks.values():
                        if task is not highest_priority_task:
                            task.stop()  # Stop lower-priority tasks

    def start(self):
        """Start the scheduler in a separate thread."""
        self.scheduler_running.set()
        self.log(f"🟢 minRTOS running with {self.scheduling_policy} scheduling.")
        threading.Thread(target=self.run_scheduler, daemon=True).start()

    def stop_all(self):
        """Stop all tasks and terminate the scheduler"""
        with self.schedule_cond:
            self.scheduler_running.clear()
            for task in list(self.tasks.values()):
                task.stop()
                task.process.terminate()
                task.process.join()
            self.tasks.clear()
            self.log("🛑 All tasks stopped.")
            self.schedule_cond.notify()

    def trigger_task(self, task_name):
        """Manually trigger an event-driven task"""
        if task_name in self.tasks:
            task = self.tasks[task_name]
            if task.event:
                task.event.set()

    def log(self, message):
        """Log messages to a file and console"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(LOG_FILE, "a") as log_file:
            log_file.write(log_message + "\n")

    def _signal_handler(self, signum, frame):
        """Handle OS-level signal for scheduling"""
        self.log("🔔 Interrupt received, rescheduling tasks...")
