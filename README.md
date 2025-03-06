# minRTOS

A lightweight real-time operating system (RTOS) for Python, designed to utilize Python 3.14’s no-GIL threading for true parallel execution.


---

# Features

✅ Preemptive Scheduling (EDF & RMS)<br>
✅ Priority Inheritance for Mutexes (Prevents priority inversion)<br>
✅ High-Precision Timing (Using time.perf_counter())<br>
✅ Event-Driven Tasks (Tasks triggered externally)<br>
✅ Dynamic Task Creation & Removal<br>
✅ Task Deadline Enforcement<br>
✅ Thread-Based Execution<br>
✅ Mutex-Based Synchronization (With proper ownership tracking)<br>
✅ Inter-Task Communication (Using message queues)<br>


---

# Installation

Clone the repository:
```bash
git clone https://github.com/Night-Trader-Dev/minRTOS.git
cd minRTOS
```
Ensure you are using Python 3.14+ (for no-GIL threading).


---

# Usage

1️⃣ Creating and Running Tasks

Create tasks and add them to the scheduler:
```python
import time
from minRTOS import Scheduler, Task

def my_task():
    print("🔧 Task Running")
    time.sleep(0.5)

scheduler = Scheduler(scheduling_policy="EDF")
task1 = Task("Task1", my_task, period=1, priority=1, deadline=1.5)

scheduler.add_task(task1)
scheduler.start()

time.sleep(5)
scheduler.stop_all()  # Stop all tasks
```

---

2️⃣ Event-Driven Tasks

Tasks can wait for an external trigger:
```python
def event_task():
    print("🔔 Event Task Triggered!")

event_driven_task = Task("EventTask", event_task, priority=3, event_driven=True)
scheduler.add_task(event_driven_task)

# Trigger the task manually
time.sleep(2)
scheduler.trigger_task("EventTask")
```

---

3️⃣ Mutex Synchronization with Priority Inheritance

Prevent priority inversion when accessing shared resources:
```python
from minRTOS import Mutex, Task, Scheduler
import time

mutex = Mutex()

def low_priority_task():
    print(f"🔵 Low Priority Task Trying to Acquire Mutex at {time.perf_counter():.4f}")
    if mutex.acquire(low_task):
        print(f"🔵 Low Priority Task Holding Mutex")
        time.sleep(3)  # Simulating work
        mutex.release()
        print(f"🔵 Low Priority Task Released Mutex")

def high_priority_task():
    time.sleep(1)  # Give low-priority task time to acquire mutex
    print(f"🔴 High Priority Task Trying to Acquire Mutex at {time.perf_counter():.4f}")
    if mutex.acquire(high_task):
        print(f"🔴 High Priority Task Got Mutex")
        mutex.release()
        print(f"🔴 High Priority Task Released Mutex")

scheduler = Scheduler()

low_task = Task("LowTask", low_priority_task, priority=1)
high_task = Task("HighTask", high_priority_task, priority=5)

scheduler.add_task(low_task)
time.sleep(0.1)  # Ensure low-priority task starts first
scheduler.add_task(high_task)

scheduler.start()
time.sleep(5)
scheduler.stop_all()
```

---

4️⃣ Removing Tasks Dynamically
```python
scheduler.remove_task("Task1")
```

---

# Scheduler Policies

 🔹 Earliest Deadline First (EDF)<br>

Tasks with the earliest deadline run first.<br>

Dynamically adjusts execution order at runtime.


# To use EDF:
```python
scheduler = Scheduler(scheduling_policy="EDF")
```
 🔹 Rate Monotonic Scheduling (RMS)<br>

Shorter-period tasks get higher priority.


# To use RMS:
```python
scheduler = Scheduler(scheduling_policy="RMS")
```

---

# Upcoming Features

🚀 Time-Based Task Preemption (Soft real-time guarantees)<br>
🚀 Interrupt-Based Scheduling (Using Python signals)<br>
🚀 Real-Time Performance Metrics (Tracking CPU usage & task overruns)<br>


---

# License

This project is licensed under the MIT License.



