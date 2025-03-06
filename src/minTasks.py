import multiprocessing
import time

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

            if self.event:
                if not self.event.wait(timeout=0.1):  
                    continue
                self.event.clear()

            if now >= self.next_run:
                start_time = time.perf_counter()
                self.update()
                end_time = time.perf_counter()

                execution_time = end_time - start_time
                self.metrics["exec_time"] = execution_time

                if self.deadline and execution_time > self.deadline:
                    self.metrics["missed_deadlines"] += 1
                    if self.overrun_action == "kill":
                        self.running.value = False
                        return
                    elif self.overrun_action == "pause":
                        self.event.wait()

                self.next_run = now + self.period if self.period > 0 else now

            time.sleep(0.001)

    def stop(self):
        """Stop task execution"""
        self.running.value = False
        if self.event:
            self.event.set()
