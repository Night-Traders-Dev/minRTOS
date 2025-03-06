import multiprocessing
import time
import sys  # For memory usage simulation (optional)

class Task:
    """Real-time task class for minRTOS"""
    def __init__(self, name, update_func, period=0, priority=1, deadline=None, 
                 overrun_action="kill", event_driven=False):
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
        # Resource metrics: exec_time, missed_deadlines, cpu_usage, memory_usage (dummy)
        self.metrics = multiprocessing.Manager().dict({
            "exec_time": 0, 
            "missed_deadlines": 0, 
            "cpu_usage": 0,
            "memory_usage": 0  # Dummy value, can be replaced with actual memory tracking if needed
        })
        self.process = multiprocessing.Process(target=self.run)

    def run(self):
        """Task execution loop with fault tolerance and resource management."""
        while self.running.value:
            now = time.perf_counter()

            if self.event:
                if not self.event.wait(timeout=0.1):  # Non-blocking wait
                    continue
                self.event.clear()

            if now >= self.next_run:
                try:
                    start_time = time.perf_counter()
                    self.update()
                    end_time = time.perf_counter()
                except Exception as e:
                    # Log error and mark task as failed
                    self.metrics["missed_deadlines"] += 1
                    print(f"❌ Task {self.name} encountered error: {e}")
                    self.running.value = False
                    continue

                execution_time = end_time - start_time
                self.metrics["exec_time"] = execution_time

                # Estimate CPU usage as (execution_time / period)*100 (if period > 0)
                if self.period > 0:
                    self.metrics["cpu_usage"] = (execution_time / self.period) * 100
                else:
                    self.metrics["cpu_usage"] = execution_time * 100

                # Dummy memory usage: using sys.getsizeof(self) as a rough approximation
                self.metrics["memory_usage"] = sys.getsizeof(self)

                if self.deadline and execution_time > self.deadline:
                    self.metrics["missed_deadlines"] += 1
                    if self.overrun_action == "kill":
                        self.running.value = False
                        continue
                    elif self.overrun_action == "pause":
                        self.event.wait()

                self.next_run = now + self.period if self.period > 0 else now

            time.sleep(0.001)

    def stop(self):
        """Stop task execution"""
        self.running.value = False
        if self.event:
            self.event.set()
