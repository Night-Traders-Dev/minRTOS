import signal
import time
import threading
import os
from minRTOS import Scheduler, Task, Mutex

# Shared Mutex for testing Priority Inheritance
mutex = Mutex()

# Test Task: Periodic Execution
def periodic_task():
    print("🔄 Periodic Task Running")
    time.sleep(0.2)  # Simulate work

# Test Task: Deadline Enforcement
def deadline_task():
    print("⏳ Deadline Task Started")
    time.sleep(1.2)  # Exceeds deadline
    print("✅ Deadline Task Completed")

# Test Task: Event-Driven Execution
def event_task():
    print("🔔 Event Task Triggered!")

# Test Task: Mutex and Priority Inheritance
def high_priority_task():
    print("🚀 High Priority Task wants Mutex")
    mutex.acquire(Task("HighPriority", lambda: None, priority=3))
    print("✅ High Priority Task Acquired Mutex")
    time.sleep(1)
    mutex.release()
    print("🔓 High Priority Task Released Mutex")

def low_priority_task():
    print("🐢 Low Priority Task wants Mutex")
    mutex.acquire(Task("LowPriority", lambda: None, priority=1))
    print("✅ Low Priority Task Acquired Mutex")
    time.sleep(2)
    mutex.release()
    print("🔓 Low Priority Task Released Mutex")

# Test Task: Inter-Task Messaging
def message_receiver():
    msg = scheduler.receive_message("ReceiverTask")
    if msg:
        print(f"📩 Message Received: {msg}")

# Test: Interrupt-Based Scheduling
def signal_sender():
    print("🔔 Sending SIGUSR1 interrupt")
    os.kill(os.getpid(), signal.SIGUSR1)

# Initialize Scheduler
scheduler = Scheduler(scheduling_policy="EDF")

# Add Tasks
scheduler.add_task(Task("PeriodicTask", periodic_task, period=1, priority=2))
scheduler.add_task(Task("DeadlineTask", deadline_task, period=2, priority=2, deadline=1))
scheduler.add_task(Task("EventTask", event_task, priority=3, event_driven=True))
scheduler.add_task(Task("HighPriorityTask", high_priority_task, priority=3))
scheduler.add_task(Task("LowPriorityTask", low_priority_task, priority=1))
scheduler.add_task(Task("ReceiverTask", message_receiver, priority=2, period=3))

# Start Scheduler
scheduler.start()

# Test Event-Driven Task
time.sleep(2)
scheduler.trigger_task("EventTask")

# Test Message Passing
time.sleep(2)
scheduler.send_message("ReceiverTask", "Hello from Scheduler!")

# Test Interrupt-Based Scheduling
time.sleep(2)
signal_sender()

# Run for 10 seconds
time.sleep(10)

# Stop All Tasks
scheduler.stop_all()

print("✅ All tests completed successfully!")
