from minRTOS import Task, Scheduler, Mutex
import time

mutex = Mutex()

def low_priority_task():
    print(f"🔵 Low Priority Task Acquiring Mutex at {time.perf_counter():.4f}")
    if mutex.acquire(task=low_task):
        print(f"🔵 Low Priority Task Holding Mutex at {time.perf_counter():.4f}")
        time.sleep(3)  # Simulate work while holding mutex
        mutex.release()
        print(f"🔵 Low Priority Task Released Mutex at {time.perf_counter():.4f}")

def high_priority_task():
    time.sleep(1)  # Give low-priority task time to acquire mutex
    print(f"🔴 High Priority Task Trying to Acquire Mutex at {time.perf_counter():.4f}")
    if mutex.acquire(task=high_task):
        print(f"🔴 High Priority Task Got Mutex at {time.perf_counter():.4f}")
        mutex.release()
        print(f"🔴 High Priority Task Released Mutex at {time.perf_counter():.4f}")
    else:
        print(f"⚠️ High Priority Task Waiting for Mutex!")

scheduler = Scheduler()

low_task = Task(name="LowTask", update_func=low_priority_task, priority=1)
high_task = Task(name="HighTask", update_func=high_priority_task, priority=5)

scheduler.add_task(low_task)
time.sleep(0.1)  # Ensure low-priority task starts first
scheduler.add_task(high_task)

scheduler.start()
time.sleep(5)
scheduler.stop_all()
