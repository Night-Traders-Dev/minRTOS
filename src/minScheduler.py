import threading
import time
import multiprocessing
import queue
import signal
from minTasks import Task
from minMutex import Mutex

LOG_FILE = "minRTOS_log.txt"

class Scheduler:
    """Real-time task scheduler with multiprocessing and dynamic task management."""
    def __init__(self, scheduling_policy="EDF"):
        self.tasks = {}  # Mapping of task names to Task objects
        self.message_queues = {}  # Message queues for inter-task communication
        self.lock = threading.Lock()
        self.schedule_cond = threading.Condition(self.lock)
        self.scheduling_policy = scheduling_policy
        self.scheduler_running = threading.Event()
        self.log_queue = queue.Queue()
        signal.signal(signal.SIGUSR1, self._signal_handler)

    def add_task(self, task):
        """Add a task to the scheduler dynamically."""
        with self.schedule_cond:
            self.tasks[task.name] = task
            self.message_queues[task.name] = multiprocessing.Queue()
            task.process.start()
            self.log(f"✅ Task {task.name} added.")
            self.schedule_cond.notify()

    def remove_task(self, task_name):
        """Remove a task dynamically."""
        with self.schedule_cond:
            if task_name in self.tasks:
                task = self.tasks.pop(task_name)
                task.stop()  # Gracefully stop the task
                task.process.terminate()  # Terminate the task process
                task.process.join(timeout=1)  # Ensure the process terminates
                if task.process.is_alive():
                    self.log(f"⚠️ Task {task_name} did not terminate, forcing kill.")
                    task.process.kill()
                if task_name in self.message_queues:
                    del self.message_queues[task_name]
                self.log(f"❌ Task {task_name} removed.")
            self.schedule_cond.notify()

    def _get_task_priority(self, task):
        """Determine priority based on scheduling policy."""
        if self.scheduling_policy == "EDF":
            return task.deadline if task.deadline else float('inf')
        elif self.scheduling_policy == "RMS":
            return task.period if task.period > 0 else float('inf')
        return task.priority

    def dynamic_policy_switch(self):
        """Dynamically switch scheduling policy based on task metrics."""
        total_missed = 0
        with self.lock:
            for task in self.tasks.values():
                total_missed += int(task.metrics["missed_deadlines"])
        new_policy = "fixed"
        if total_missed > 0:
            new_policy = "EDF"
        elif all(task.period > 0 for task in self.tasks.values()):
            new_policy = "RMS"
        if new_policy != self.scheduling_policy:
            self.log(f"🔄 Switching scheduling policy from {self.scheduling_policy} to {new_policy}")
            self.scheduling_policy = new_policy

    def monitor_tasks(self):
        """Monitor tasks and restart any that have failed."""
        with self.lock:
            for task in list(self.tasks.values()):
                if not task.process.is_alive():
                    self.log(f"⚠️ Task {task.name} is not alive. Restarting...")
                    new_task = Task(
                        task.name, task.update, period=task.period, priority=task.priority,
                        deadline=task.deadline, overrun_action=task.overrun_action, event_driven=(task.event is not None)
                    )
                    self.tasks[task.name] = new_task
                    self.message_queues[task.name] = multiprocessing.Queue()
                    new_task.process.start()

    def run_scheduler(self):
        """Continuously manage task execution order and perform dynamic policy switching."""
        timeout_counter = 0  # Exit condition counter
        while self.scheduler_running.is_set():
            with self.schedule_cond:
                self.schedule_cond.wait(timeout=1)
                self.dynamic_policy_switch()
                task_queue = sorted(self.tasks.values(), key=self._get_task_priority)
                if not task_queue:
                    timeout_counter += 1
                    if timeout_counter > 5:  # Exit if idle for 5 seconds
                        self.log("⏹️ Scheduler exiting due to inactivity.")
                        break
                else:
                    timeout_counter = 0  # Reset counter when active
                if task_queue:
                    highest_priority_task = task_queue[0]
                    for task in self.tasks.values():
                        if task is not highest_priority_task:
                            task.stop()  # Preempt lower-priority tasks for illustration
            self.monitor_tasks()
            time.sleep(0.001)

        self.log("🔴 Scheduler loop exited.")

    def start(self):
        """Start the scheduler in a separate thread."""
        self.scheduler_running.set()
        self.log(f"🟢 minRTOS running with {self.scheduling_policy} scheduling.")
        threading.Thread(target=self.run_scheduler, daemon=True).start()

    def stop_all(self):
        """Forcefully stop all tasks and ensure scheduler exits."""
        self.scheduler_running.clear()
        with self.schedule_cond:
            for task in list(self.tasks.values()):
                task.stop()
                if task.process.is_alive():
                    task.process.terminate()
                    task.process.join(timeout=1)
                    if task.process.is_alive():
                        self.log(f"⚠️ Task {task.name} did not terminate, forcing kill.")
                        task.process.kill()
                self.tasks.clear()
            self.schedule_cond.notify()
        self.log("🛑 All tasks stopped.")

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

    def log(self, message):
        """Log messages to a file and console."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(LOG_FILE, "a") as log_file:
            log_file.write(log_message + "\n")

    def _signal_handler(self, signum, frame):
        """Handle OS-level signal for scheduling."""
        self.log("🔔 Interrupt received, rescheduling tasks...")
