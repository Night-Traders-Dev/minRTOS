import time
from minRTOS import Scheduler, Task, Mutex

def simple_update():
    print("Task is running.")
    time.sleep(0.05)

def deadline_update():
    print("Deadline task running.")
    time.sleep(0.2)  # Intentionally longer than deadline

def mutex_update(mutex, name):
    print(f"{name} attempting to acquire mutex...")
    acquired = mutex.acquire(task=Task(name, lambda: None))
    if acquired:
        print(f"{name} acquired mutex!")
        time.sleep(0.1)
        mutex.release()
        print(f"{name} released mutex!")
    else:
        print(f"{name} failed to acquire mutex!")

def main():
    print("--- minRTOS Test Start ---")
    scheduler = Scheduler()

    # Test: Add a simple periodic task
    task1 = Task("SimpleTask", simple_update, period=0.1, priority=2, max_runs=3)
    scheduler.add_task(task1)

    # Test: Add a deadline task (should be killed after deadline overrun)
    task2 = Task("DeadlineTask", deadline_update, period=0.1, priority=1, deadline=0.1, overrun_action="kill", max_runs=2)
    scheduler.add_task(task2)

    # Test: Mutex with two tasks
    mutex = Mutex()
    def mutex_task1():
        mutex_update(mutex, "MutexTask1")
    def mutex_task2():
        mutex_update(mutex, "MutexTask2")
    mtask1 = Task("MutexTask1", mutex_task1, period=0.15, priority=3, max_runs=2)
    mtask2 = Task("MutexTask2", mutex_task2, period=0.15, priority=4, max_runs=2)
    scheduler.add_task(mtask1)
    scheduler.add_task(mtask2)

    scheduler.start()
    time.sleep(2)  # Let tasks run
    scheduler.stop_all()
    scheduler.join()
    print("--- minRTOS Test End ---")

if __name__ == "__main__":
    main()
