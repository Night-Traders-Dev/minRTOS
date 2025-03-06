import multiprocessing
import time
import sys

class Task:
    """Real-time task class for minRTOS"""
    def __init__(self, name, update_func, period=0, priority=1, deadline=None,
                 overrun_action="kill", event_driven=False, max_runs=None):
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
        self.metrics = multiprocessing.Manager().dict({
            "exec_time": 0,
            "missed_deadlines": 0,
            "cpu_usage": 0,
            "memory_usage": 0
        })
        self.process = multiprocessing.Process(target=self.run)
        self.max_runs = max_runs  # Maximum number of times the task runs

    def run(self):
        """Task execution loop with fault tolerance and resource management."""
        run_count = 0

        while self.running.value:
            if self.max_runs is not None and run_count >= self.max_runs:
                self.running.value = False
                print(f"Task {self.name} has reached maximum run limit and is exiting.")
                break

            now = time.perf_counter()

            if self.event:
                if not self.event.wait(timeout=0.1):
                    continue
                self.event.clear()

            if now >= self.next_run:
                try:
                    start_time = time.perf_counter()
                    self.update()
                    end_time = time.perf_counter()
                except Exception as e:
                    self.metrics["missed_deadlines"] += 1
                    print(f"❌ Task {self.name} encountered error: {e}")
                    self.running.value = False
                    continue

                execution_time = end_time - start_time
                self.metrics["exec_time"] = execution_time

                if self.period > 0:
                    self.metrics["cpu_usage"] = (execution_time / self.period) * 100
                else:
                    self.metrics["cpu_usage"] = execution_time * 100

                self.metrics["memory_usage"] = sys.getsizeof(self)

                if self.deadline and execution_time > self.deadline:
                    self.metrics["missed_deadlines"] += 1
                    if self.overrun_action == "kill":
                        self.running.value = False
                        continue
                    elif self.overrun_action == "pause":
                        self.event.wait()

                self.next_run = now + self.period if self.period > 0 else now
                run_count += 1  # Increment run counter

            time.sleep(0.001)

    def stop(self):
        """Stop task execution"""
        self.running.value = False
        if self.event:
            self.event.set()
