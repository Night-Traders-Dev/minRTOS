import threading
import queue
import time
import heapq

class Task:
    def __init__(self, name, update_func, period=0, priority=1, deadline=None, overrun_action="kill", event_driven=False):
        self.name = name
        self.update = update_func
        self.period = period
        self.priority = priority
        self.deadline = deadline
        self.overrun_action = overrun_action
        self.next_run = time.perf_counter()
        self.running = True
        self.lock = threading.Lock()
        self.event = threading.Event() if event_driven else None  # Only set event if event-driven
        self.thread = None  

    def run(self):
        """Execute the task with deadline tracking and real-time scheduling."""
        while self.running:
            now = time.perf_counter()
            if self.event:
                self.event.wait()  # Wait for external trigger
                self.event.clear()  # Reset after execution
            
            if now >= self.next_run:
                start_time = time.perf_counter()
                
                with self.lock:
                    self.update()
                
                end_time = time.perf_counter()
                execution_time = end_time - start_time

                if self.deadline and execution_time > self.deadline:
                    print(f"⚠️ Task {self.name} exceeded its deadline! [{execution_time:.6f}s]")
                    if self.overrun_action == "kill":
                        self.running = False
                        print(f"❌ Task {self.name} has been terminated.")
                        return
                    elif self.overrun_action == "pause":
                        print(f"⏸ Task {self.name} is paused due to overrun.")
                        self.event.wait()
                
                self.next_run = now + self.period if self.period > 0 else now
            
            time.sleep(0.0001)  

    def stop(self):
        """Stop the task."""
        self.running = False
        if self.event:
            self.event.set()  # Wake up event-driven task so it can exit cleanly

class Scheduler:
    def __init__(self, scheduling_policy="EDF"):
        self.task_queue = []
        self.tasks = {}
        self.message_queues = {}
        self.lock = threading.Lock()
        self.scheduling_policy = scheduling_policy
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)

    def add_task(self, task):
        """Dynamically add a task to the system."""
        with self.lock:
            heapq.heappush(self.task_queue, (self._get_task_priority(task), task))
            self.tasks[task.name] = task
            self.message_queues[task.name] = queue.Queue()
            task.thread = threading.Thread(target=task.run)
            task.thread.start()
            print(f"✅ Task {task.name} added.")

    def remove_task(self, task_name):
        """Dynamically remove a task by name."""
        with self.lock:
            if task_name in self.tasks:
                task = self.tasks.pop(task_name)
                task.stop()
                task.thread.join()
                print(f"❌ Task {task_name} removed.")
            else:
                print(f"⚠️ Task {task_name} not found.")

    def _get_task_priority(self, task):
        """Determine task priority based on scheduling policy."""
        if self.scheduling_policy == "EDF":
            return task.deadline if task.deadline else float('inf')
        elif self.scheduling_policy == "RMS":
            return task.period if task.period > 0 else float('inf')
        return task.priority  

    def run_scheduler(self):
        """Scheduler loop for dynamic task execution based on EDF or RMS."""
        while self.scheduler_running:
            with self.lock:
                self.task_queue = sorted(self.task_queue, key=lambda x: self._get_task_priority(x[1]))
            time.sleep(0.001)

    def start(self):
        """Start the global scheduler thread."""
        self.scheduler_thread.start()
        print(f"🟢 minRTOS running with {self.scheduling_policy} scheduling.")

    def stop_all(self):
        """Stop all running tasks."""
        with self.lock:
            self.scheduler_running = False
            for task in list(self.tasks.values()):
                task.stop()
                task.thread.join()
            self.tasks.clear()
            print("🛑 All tasks stopped.")

    def trigger_task(self, task_name):
        """Trigger an event-driven task safely."""
        if task_name in self.tasks:
            task = self.tasks[task_name]
            if task.event:
                task.event.set()
