import multiprocessing
import queue
import time
import signal
import threading

LOG_FILE = "minRTOS_log.txt"

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
            self.message_queues[task.name] = multiprocessing.Queue()  
            task.process.start()
            self.log(f"✅ Task {task.name} added.")
            self.schedule_cond.notify()  

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
                self.schedule_cond.wait()  
                self.task_queue = sorted(self.tasks.values(), key=self._get_task_priority)
                
                if self.task_queue:
                    highest_priority_task = self.task_queue[0]
                    for task in self.tasks.values():
                        if task is not highest_priority_task:
                            task.stop()  

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
