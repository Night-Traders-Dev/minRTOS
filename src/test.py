import time
from minRTOS import Task, Scheduler, Mutex

mutex = Mutex()  # Initialize Mutex
scheduler = None  # Define scheduler globally

def low_priority_task():
    """Low priority task that locks a mutex."""
    global scheduler
    print("🟢 Low-Priority Task Started")
    low_task = Task("LowPriority", lambda: None, priority=1)
    if mutex.acquire(low_task):  # Explicitly passing Task
        print("🔒 Low-Priority Task Acquired Mutex")
        time.sleep(2)  # Simulate work
        low_task.stop()
        mutex.release()

        print("🔓 Low-Priority Task Released Mutex")
    else:
        print("🛑 Low-Priority Task Could Not Acquire Mutex")

def high_priority_task():
    """High priority task that needs the mutex."""
    global scheduler
    print("🚀 High-Priority Task Started")
    time.sleep(0.5)  # Ensure the low-priority task locks the mutex first
    high_task = Task("HighPriority", lambda: None, priority=5)
    if mutex.acquire(high_task):  # Explicitly passing Task
        print("✅ High-Priority Task Acquired Mutex")
        time.sleep(1)
        high_task.stop()
        mutex.release()
        print("🔓 High-Priority Task Released Mutex")
    else:
        print("🛑 High-Priority Task Could Not Acquire Mutex")

def periodic_task():
    """Task that runs periodically every second."""
    print("⏳ Periodic Task Executing...")

def event_driven_task():
    """Task triggered externally."""
    print("🔵 Event-Driven Task Executed")

if __name__ == "__main__":
    # Initialize mutex and scheduler
    scheduler = Scheduler(scheduling_policy="EDF")

    # Create tasks
    scheduler.add_task(Task(name="LowPriority", update_func=low_priority_task, priority=1))
    scheduler.add_task(Task(name="HighPriority", update_func=high_priority_task, priority=5))
    scheduler.add_task(Task(name="Periodic", update_func=periodic_task, period=1, priority=3))
    scheduler.add_task(Task(name="EventTask", update_func=event_driven_task, priority=2, event_driven=True))

    # Start the scheduler
    scheduler.start()

    # Trigger event-driven task after 3 seconds
    time.sleep(3)
    scheduler.trigger_task("EventTask")

    # Run for 5 seconds then stop everything
    time.sleep(5)
    scheduler.stop_all()

    print("✅ Test Complete")
